# cython: language=c
# cython: language_level=3

__all__ = (
    "Entry", "Frame", "FrameDelta", "Trace",
)

from typing import Any, Dict, FrozenSet, List, Set, Tuple, Union

from .. import types
from ..abc.method import Method
from ..analysis.graph cimport ExceptionEdge, InsnBlock, InsnEdge, JsrFallthroughEdge, JsrJumpEdge, RetEdge
from ..analysis.source import InstructionInBlock
from ..types import BaseType, ReferenceType
from ..types.reference import ArrayType
from ..types.verification import This, UninitializedThis
from ..verifier import BasicTypeChecker, ErrorType
from ..verifier._verifier cimport Error, Verifier


cdef class Entry:
    """
    A stack/locals entry.
    """

    property null:
        """
        Is this entry null?
        """

        def __get__(self) -> bool:
            return self.type == types.null_t or self.value == types.null_t

    property nullable:
        """
        Is this entry null at any point?
        """

        def __get__(self) -> bool:
            if self.null:
                return True
            # Don't need to account for This, Uninitialised or UninitialisedThis types because those can't be null. (They
            # don't inherit from ReferenceType).
            return isinstance(self.type, ReferenceType) and (self.parent is None or self.parent.nullable)

    def __init__(
            self,
            source: Union[Source, None],
            type_: BaseType,
            parent: Union[Entry, None] = None,
            value: Union[Constant, None] = None,
    ) -> None:
        """
        :param source: The source that creates this entry.
        :param type_: The type of this entry.
        """

        self.source = source
        self.type = type_
        self.parent = parent
        self.value = value

    def __repr__(self) -> str:
        return "<Entry(source=%r, type=%s, value=%r) at %x>" % (self.source, self.type, self.value, id(self))

    def __str__(self) -> str:
        if self.value is not None:
            return "%s (%s)" % (self.type, self.value)
        return str(self.type)

    def __eq__(self, other: Any) -> bool:
        return other is self or (self.parent is not None and other == self.parent)

    def __hash__(self) -> int:
        return hash((self.type, self.parent, self.value))

    def cast(self, source: Union[Source, None], type_: BaseType) -> Entry:
        """
        Casts this entry down to another type.
        """

        return Entry(source, type_, parent=self, value=self.value)


cdef class Frame:
    """
    A stack frame. Contains the stack and locals.
    """

    @classmethod
    def initial(cls, method: Method, verifier: Union[Verifier, None] = None) -> Frame:
        """
        Creates the initial (bootstrap) frame for a method.
        This is done by populating the locals with the parameters and a this pointer.

        :param method: The method to create the initial frame for.
        :param verifier: The verifier to use.
        """

        frame = cls(verifier)

        if not method.is_static:
            this_class = method.class_.get_type()
            if method.name == "<init>" and method.return_type == types.void_t:
                frame.set(0, UninitializedThis(this_class))
            else:
                frame.set(0, This(this_class))

        for argument_type in method.argument_types:
            argument_type = argument_type.to_verification_type()
            frame.set(frame.max_locals, argument_type)

        return frame

    property source:
        """
        The current source creating the delta.
        """

        def __get__(self) -> Union[Source, None]:
            return self._source

    def __init__(self, verifier: Verifier) -> None:
        """
        :param verifier: The verifier to use when performing operations on the stack or locals.
        """

        self.verifier = verifier

        self._delta = False
        self._source = None

        self._pops = []
        self._pushes = []
        self._swaps = ()
        self._dups = {}
        self._overwrites = {}

        self.top = Entry(None, types.top_t)

        self.stack = []
        self.locals = {}
        self.accesses = []
        self.consumed = set()

        self.max_stack = 0
        self.max_locals = 0

    def __repr__(self) -> str:
        return "<Frame(stack=[%s], locals={%s}, max_stack=%i, max_locals=%i) at %x>" % (
            ", ".join(map(str, self.stack)), ", ".join({"%i=%s" % pair for pair in self.locals.items()}),
            self.max_stack, self.max_locals, id(self),
        )

    cdef bint _check_type(self, object expect, Entry entry, bint allow_return_address = False):
        """
        Checks that the provided entry matches the provided type expectation.
        """

        if expect == types.top_t or entry.type == types.top_t:  # AKA no type checking needed
            return True

        if expect is None:
            if allow_return_address and entry.type == types.return_address_t:
                return True
            elif self.verifier.checker.check_reference(entry.type):
                return True
            self.verifier.report_expected_reference_type(self._source, entry.type, entry.source)

        # More specific type checking

        elif expect is ArrayType:
            if not self.verifier.checker.check_array(entry.type):
                self.verifier.report(Error(  # FIXME
                    ErrorType.INVALID_TYPE, self._source,
                    "expected array type", "got %s (via %s)" % (entry.type, entry.source),
                ))
            # Always return true as otherwise we'll attempt to merge the ArrayType class with the entry type, which
            # isn't possible.
            return True

        else:
            if self.verifier.checker.check_merge(expect, entry.type):
                return True
            self.verifier.report_invalid_type(self._source, expect, entry.type, entry.source)

        return False

    def copy(self, deep: bool = False) -> Frame:
        """
        Creates a copy of this frame as it currently is.

        :param deep: Copies more information such as the local accesses and consumed entries.
        """

        cdef Frame frame = Frame(self.verifier)

        frame.stack.extend(self.stack)
        frame.locals.update(self.locals)

        if deep:
            frame.accesses.extend(self.accesses)
            frame.consumed.update(self.consumed)

        frame.max_stack = self.max_stack
        frame.max_locals = self.max_locals

        return frame

    # ------------------------------ Delta computation ------------------------------ #

    def start(self, source: Union[Source, None]) -> None:
        """
        Starts creating a frame delta from this frame, given the source.
        """

        # if self._delta and self._source != source:
        #     raise ValueError("Already creating a stack delta with source %r." % self._source)

        self._delta = True
        self._source = source

        self._pops.clear()
        self._pushes.clear()
        self._swaps = ()
        self._dups.clear()
        self._overwrites.clear()

    def finish(self) -> FrameDelta:
        """
        Finishes creating the frame delta and returns it.
        """

        if not self._delta:
            raise ValueError("Not creating a stack delta.")
        self._delta = False

        # cdef set consumed
        # for entry in self._consumed:
        #     if entry in self.consumed:
        #         consumed.add(entry)

        return FrameDelta(
            self._source,
            tuple(self._pops), tuple(self._pushes),
            self._swaps, self._dups.copy(),
            self._overwrites.copy(),
        )

    # ------------------------------ Misc operations ------------------------------ #

    def replace(self, old: Entry, new: BaseType) -> None:
        """
        Replaces all occurrences of an entry with the given type. Does not modify the underlying entry however.

        :param old: The old entry to replace.
        :param new: The type of the new entry.
        """

        cdef Entry entry = Entry(old.source if self._source is None else self._source, new, parent=old)

        for index, entry_ in enumerate(self.stack):
            if entry_ is old:
                self.stack[index] = entry

        for index, entry_ in self.locals.items():
            if entry_ is old:
                self.locals[index] = entry

    # ------------------------------ Stack operations ------------------------------ #

    def push(self, entry_or_type: Union[Entry, BaseType], value: Union[Constant, None] = None) -> None:
        """
        :param entry_or_type: An entry to push or a type used to create an entry.
        :param value: The value of the entry (if a type is being pushed).
        """

        cdef Entry entry
        try:
            entry = <Entry?>entry_or_type
        except TypeError:
            entry = Entry(self._source, entry_or_type, value=value)

        if self._delta:
            self._pushes.append(entry)
        self.stack.append(entry)

        if entry.type.internal_size > 1:
            self.stack.append(self.top)

        cdef int stack_size = len(self.stack)
        if stack_size > self.max_stack:
            self.max_stack = stack_size

    def pop(self, count: int = 1, *, tuple_: bool = False, expect: Union[BaseType, None] = types.top_t) -> Union[Tuple[Entry, ...], Entry]:
        """
        :param count: The number of entries to pop off the stack.
        :param tuple_: Should we return the entries as a tuple, even if there is only one?
        :param expect: The type expectation for the entry. If a Top type is provided, no type checking is performed.
        """

        if count == 1 and not tuple_:  # Very common, so we'll just process it quickly here
            try:
                entry = self.stack.pop()

                if not self._check_type(expect, entry):
                    entry = entry.cast(self._source, self.verifier.checker.merge(expect, entry.type))
                if not self.verifier.checker.check_category(entry.type, 1):
                    self.verifier.report_invalid_type_category(self._source, 1, entry.type, entry.source)

                if self._delta:
                    self._pops.append(entry)
                if not entry in self.stack and not entry in self.locals.values():
                    self.consumed.add(entry)

                return entry

            except IndexError:
                self.verifier.report_stack_underflow(self._source, -1)
                return self.top

        cdef list entries = []
        cdef int underflow = 0
        cdef int index

        for index in range(count):
            try:
                entry = self.stack.pop()

                if not self._check_type(expect, entry):
                    entry = entry.cast(self._source, self.verifier.checker.merge(expect, entry.type))

                if self._delta:
                    self._pops.append(entry)
                if not entry in self.stack and not entry in self.locals.values():
                    self.consumed.add(entry)

            except IndexError:
                underflow += 1
                entry = self.top
            entries.append(entry)

        # TODO: Check that we haven't popped half a wide type too
        if not self.verifier.checker.check_category(entries[0].type, 1):
            self.verifier.report_invalid_type_category(self._source, 1, entries[0].type, entries[0].source)
        if underflow:
            self.verifier.report_stack_underflow(self._source, -underflow)

        return tuple(entries)

    def dup(self, displace: int = 0) -> None:
        """
        Duplicates the top value on the stack.

        :param displace: How many entries to displace the duplicated value backwards by.
        """

        cdef Entry entry

        if not displace:
            if self._delta:
                self._swaps = (0, ..., 0)
            try:
                entry = self.stack[-1]
                if not self.verifier.checker.check_category(entry.type, 1):  # [ ..., double ]
                    self.verifier.report_invalid_type_category(self._source, 1, entry.type, entry.source)
                try:
                    if not self.verifier.checker.check_category(self.stack[-2].type, 1):  # [ double, top ]
                        self.verifier.report_invalid_type_category(
                            self._source, 1, self.stack[-2].type, self.stack[-2].source,
                        )
                except IndexError:
                    ...
                self.stack.append(entry)
            except IndexError:
                self.verifier.report_stack_underflow(self._source, -1)
                self.stack.append(self.top)

        else:
            if self._delta:
                self._swaps = (0, *(index for index in range(1 + displace, 0, -1)), 0, ...)
            try:
                entry = self.stack[-1]
            except IndexError:
                self.verifier.report_stack_underflow(self._source, -1)
                entry = self.top

            # Check we're not trying to dup a category two type. Sidenote: we don't actually need to check that it isn't a
            # top substitute for the wide types ([ *top*, double ]) as this can't occur without an invalid stack state.
            try:
                if not self.verifier.checker.check_category(self.stack[-2].type, 1):  # [ double, top ]
                    self.verifier.report_invalid_type_category(
                        self._source, 1, self.stack[-2].type, self.stack[-2].source,
                    )
            except IndexError:
                ...

            # Now also check that we're not trying to dup part of / around a category 2 type.
            try:
                # dup_x1 [ ..., double, top ] -> [ ..., top, double, top ]
                if not self.verifier.checker.check_category(self.stack[-(1 + displace)].type, 1):
                    self.verifier.report_invalid_type_category(  # FIXME: Error could be more informative as to the situation
                        self._source, 1, self.stack[-(1 + displace)].type, self.stack[-(1 + displace)].source,
                    )
                # dup_x1 [ double, top, int ] -> [ double, int, top, int ]
                if not self.verifier.checker.check_category(self.stack[-(2 + displace)].type, 1):
                    self.verifier.report_invalid_type_category(
                        self._source, 1, self.stack[-(2 + displace)].type, self.stack[-(2 + displace)].source,
                    )
            except IndexError:
                ...  # Will already have been dealt with above, no need to report anything

            self.stack.insert(-(1 + displace), entry)

        cdef int stack_size = len(self.stack)
        if stack_size > self.max_stack:
            self.max_stack = stack_size

    def dup2(self, displace: int = 0) -> None:
        """
        Duplicates the top two values on the stack.

        :param displace: How many entries to displace the duplicated values back by.
        """

        cdef int underflow = 0
        cdef Entry entry
        cdef Entry entry_a
        cdef Entry entry_b

        if not displace:
            if self._delta:
                self._swaps = (1, 0, ..., 1, 0)

            try:
                entry = self.stack[-2]
                if self._delta:
                    self._dups[entry] = self._dups.get(entry, 0) + 1
                # Check we're not duping half of a category two type
                try:
                    if not self.verifier.checker.check_category(self.stack[-3].type, 1):  # [ double, top, int ]
                        self.verifier.report_invalid_type_category(
                            self._source, 1, self.stack[-3].type, self.stack[-3].source,
                        )
                except IndexError:
                    ...
                self.stack.append(entry)
            except IndexError:
                underflow += 1
                self.stack.append(self.top)
            try:
                entry = self.stack[-2]
                if self._delta:
                    self._dups[entry] = self._dups.get(entry, 0) + 1
                self.stack.append(entry)  # Equivalent to self.stack[-1] before the first push
            except IndexError:
                underflow += 1
                self.stack.append(self.top)

            if underflow:
                self.verifier.report_stack_underflow(self._source, -underflow)

        else:
            if self._delta:
                self._swaps = (1, 0, *(index for index in range(1 + displace * 2, 1, -1)), 1, 0, ...)

            try:
                entry_a, entry_b = self.stack[-2:]
                if self._delta:
                    self._dups[entry_a] = self._dups.get(entry_a, 0) + 1
                    self._dups[entry_b] = self._dups.get(entry_b, 0) + 1
            except (IndexError, ValueError):
                entry_a = self.top
                try:
                    entry_b = self.stack[-1]
                    if self._delta:
                        self._dups[entry_b] = self._dups.get(entry_b, 0) + 1
                    self.verifier.report_stack_underflow(self._source, -1)
                except IndexError:
                    entry_b = self.top
                    self.verifier.report_stack_underflow(self._source, -2)

            try:
                if not self.verifier.checker.check_category(self.stack[-3].type, 1):  # [ ..., double, top, int ]
                    self.verifier.report_invalid_type_category(
                        self._source, 1, self.stack[-3].type, self.stack[-3].source,
                    )
                # dup2_x1 [ double, top, float, int, int ] -> [ double, int, int, top, float, int, int ]
                if not self.verifier.checker.check_category(self.stack[-(2 + displace * 2)].type, 1):
                    # This mostly won't happen, so idrc about performance here
                    self.verifier.report_invalid_type_category(
                        self._source, 1, self.stack[-(2 + displace * 2)].type, self.stack[-(2 + displace * 2)].source,
                    )
            except IndexError:
                ...

            self.stack.insert(-(1 + displace * 2), entry_a)
            self.stack.insert(-(1 + displace * 2), entry_b)

        cdef int stack_size = len(self.stack)
        if stack_size > self.max_stack:
            self.max_stack = stack_size

    def swap(self) -> None:
        """
        Swaps the top two values on the stack.
        """

        if self._delta:
            self._swaps = (0, 1, ...)

        try:
            entry_a, entry_b = self.stack[-2:]
        except (IndexError, ValueError):
            try:
                entry_b = self.stack[-1]
                self.verifier.report_stack_underflow(self._source, -1)
            except IndexError:
                self.stack.append(self.top)
                entry_b = self.top
                self.verifier.report_stack_underflow(self._source, -2)
                return  # Nothing to swap as we have two tops on the stack

            self.stack.append(self.top)
            entry_a = self.top

        if not self.verifier.checker.check_category(entry_a.type, 1):  # [ double, top, int ]
            self.verifier.report_invalid_type_category(self._source, 1, entry_a.type, entry_a.source)
        if not self.verifier.checker.check_category(entry_b.type, 1):  # [ double, top ]
            self.verifier.report_invalid_type_category(self._source, 1, entry_b.type, entry_b.source)

        self.stack[-2] = entry_b
        self.stack[-1] = entry_a

    # ------------------------------ Locals operations ------------------------------ #

    def get(self, index: int, *, expect: Union[BaseType, None] = types.top_t) -> Entry:
        """
        :param index: The local variable index to get the entry at.
        :param expect: The expected type of the local to check against. If a Top type is provided, no type checking is performed.
        :return: The entry at that index.
        """

        cdef Entry entry = self.locals.get(index, None)

        if entry is not None:
            if not self._check_type(expect, entry):
                entry = entry.cast(self._source, self.verifier.checker.merge(expect, entry.type))
            self.accesses.append((True, index, entry))
            return entry

        self.verifier.report_unknown_local(self._source, index)
        return self.top

    def set(
            self,
            index: int,
            entry_or_type: Union[Entry, BaseType],
            value: Union[Constant, None] = None,
            *,
            expect: Union[BaseType, None] = types.top_t,
    ) -> None:
        """
        :param index: The local variable index to set.
        :param entry_or_type: The entry or type to set the local to.
        :param value: The value of the entry to create, if an entry was not provided.
        :param expect: The type expectation of the entry. If a Top type is provided, no type checking is performed.
        """

        cdef Entry entry
        try:
            entry = <Entry?>entry_or_type
        except TypeError:
            entry = Entry(self._source, entry_or_type, value=value)

        cdef Entry local = self.locals.get(index, None)
        if local == entry:
            return  # Nothing to do as the value is already set to this one

        if not self._check_type(expect, entry, allow_return_address=True):
            entry = entry.cast(self._source, self.verifier.checker.merge(expect, entry.type))

        if self._delta:
            self._overwrites[index] = (local, entry)
        self.locals[index] = entry
        self.accesses.append((False, index, entry))

        index += 1
        if entry.type.internal_size > 1:
            self.locals[index] = self.top
            index += 1

        if index > self.max_locals:
            self.max_locals = index


cdef class FrameDelta:
    """
    The difference between two frames.
    """

    def __init__(
            self,
            source: Union[Source, None],
            pops: Tuple[Entry, ...],
            pushes: Tuple[Entry, ...],
            swaps: Tuple[int, ...],
            dups: Dict[Entry, int],
            overwrites: Dict[int, Tuple[Entry, Entry]],
    ) -> None:
        """
        :param source: The source of this delta.
        :param pops: The number of entries that were popped off the stack.
        :param pushes: Entries that were pushed to the stack.
        :param swaps: Information about swaps.
        :param dups: Any entries that were duplicated, and how many times they were.
        :param overwrites: Locals overwrites.
        """

        self.source = source
        self.pops = pops
        self.pushes = pushes
        self.swaps = swaps
        self.dups = dups
        self.overwrites = overwrites

        self._hash = hash((pops, pushes, swaps, tuple(dups.items()), tuple(overwrites.items())))

    def __repr__(self) -> str:
        # Conditions are mutually exclusive if used correctly, so shouldn't run into any issues here.
        if self.pops and self.pushes:
            return "<FrameDelta(source=%r, pops=[%s], pushes=[%s]) at %x>" % (
                str(self.source), ", ".join(map(str, self.pops)), ", ".join(map(str, self.pushes)), id(self),
            )
        elif self.pops and self.overwrites:
            return "<FrameDelta(source=%r, pops=[%s], overwrites={%s}) at %x>" % (
                str(self.source), ", ".join(map(str, self.pops)),
                ", ".join({"%i=%s->%s" % (index, *pair) for index, pair in self.overwrites.items()}), id(self),
            )
        elif self.pops:
            return "<FrameDelta(source=%r, pops=[%s]) at %x>" % (
                str(self.source), ", ".join(map(str, self.pops)), id(self),
            )
        elif self.pushes:
            return "<FrameDelta(source=%r, pushes=[%s]) at %x>" % (
                str(self.source), ", ".join(map(str, self.pushes)), id(self),
            )
        elif self.overwrites:
            return "<FrameDelta(source=%r, overwrites={%s}) at %x>" % (
                str(self.source), ", ".join({"%i=%s->%s" % (index, *pair) for index, pair in self.overwrites.items()}), id(self),
            )
        elif self.swaps and self.dups:
            return "<FrameDelta(source=%r, swaps=%r, dups={%s}) at %x>" % (
                str(self.source), self.swaps, ", ".join({"%i=%s" % pair for pair in self.dups}), id(self),
            )
        elif self.swaps:
            return "<FrameDelta(source=%r, swaps=%r) at %x>" % (str(self.source), self.swaps, id(self))
        return "<FrameDelta(source=%r) at %x>" % (str(self.source), id(self))

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, FrameDelta) and
            (<FrameDelta>other).pops == self.pops and
            (<FrameDelta>other).pushes == self.pushes and
            (<FrameDelta>other).swaps == self.swaps and
            (<FrameDelta>other).dups == self.dups and
            (<FrameDelta>other).overwrites == self.overwrites
        )

    def __hash__(self) -> int:
        return self._hash


# ------------------------------ Trace computation ------------------------------ #

cdef inline RetEdge _resolve_opaque_edge(InsnGraph graph, Verifier verifier, dict subroutines, InsnEdge edge, Frame frame):
    """
    Resolves an opaque edge (which are just ret edges).
    """

    if not isinstance(edge, RetEdge):
        verifier.report(Error(ErrorType.INVALID_EDGE, edge, "unknown opaque edge type"))
        return None

    return_address = frame.locals.get(edge.instruction.index, None)
    if return_address is None:
        verifier.report(Error(ErrorType.INVALID_EDGE, edge, "no return address at local index %i" % edge.instruction.index))
        return None
    # Even if we have no type checker, there really is nothing we can do if we have not been given a return address.
    elif return_address.type != types.return_address_t:
        verifier.report_invalid_type(edge, types.return_address_t, return_address.type, return_address.source)
        return None

    cdef bint multiple_edges = False

    cdef JsrJumpEdge jsr_jump_edge = None
    cdef JsrFallthroughEdge jsr_fallthrough_edge = None

    for edge_ in <set>graph._forward_edges[return_address.source.from_]:
        if isinstance(edge_, JsrJumpEdge):
            if not multiple_edges and jsr_jump_edge is not None:
                multiple_edges = True
            jsr_jump_edge = edge_
        elif isinstance(edge_, JsrFallthroughEdge):
            if not multiple_edges and jsr_fallthrough_edge is not None:
                multiple_edges = True
            jsr_fallthrough_edge = edge_

    if multiple_edges:  # TODO: Handling?
        verifier.report(Error(ErrorType.INVALID_BLOCK, return_address.source.from_, "multiple jsr edges on block"))

    if jsr_jump_edge is None:  # We can still continue to resolve the subroutine if we can't find the jump edge
        verifier.report(Error(ErrorType.INVALID_BLOCK, return_address.source.from_, "no jsr jump edge on block"))
    if jsr_fallthrough_edge is None:
        verifier.report(Error(ErrorType.INVALID_BLOCK, return_address.source.from_, "no jsr fallthrough edge on block"))
        return None  # Cannot resolve as we don't know where to jump back to

    # A sidenote on subroutines: we can also handle multi-exit subroutines with this, even though they are not allowed
    # in Java. I'm planning to keep this functionality because it allows us to do analysis on unverifiable code (and
    # therefore create it).

    edge = RetEdge(edge.from_, jsr_fallthrough_edge.to, edge.instruction)
    (<set>subroutines.setdefault(jsr_jump_edge, set())).add(edge)
    return edge


cdef inline bint _setup_edge_trace(Verifier verifier, InsnEdge edge, Frame frame, list constraints) except *:
    """
    Sets up the frame for the given edge (mainly for exception edges) and also verifies that we have not visited it with
    the same constraints beforehand.
    """

    if isinstance(edge, JsrFallthroughEdge):
        return False  # Skip this edge as we only "visit" it when returning from a subroutine

    # The JVM spec mandates that when jumping to an exception handler, the locals must be the same as they were and the
    # stack must contain only one item on it, that being the exception that was thrown.
    if isinstance(edge, ExceptionEdge):
        frame.stack.clear()
        if not verifier.checker.check_merge(types.throwable_t, (<ExceptionEdge>edge).throwable):
            verifier.report_invalid_type(edge, types.throwable_t, (<ExceptionEdge>edge).throwable, None)

        # "Push" the exception to the stack (before checking if we can merge it with java/lang/Throwable).
        merged = verifier.checker.merge(types.throwable_t, (<ExceptionEdge>edge).throwable, fallback=types.throwable_t)
        frame.stack.append(Entry(edge, merged))

    # Now attempt to find any existing constraint that the current frame conforms to. If we can find one, this means
    # that we already know what happens and skip computing the states for this block.

    cdef bint skip = False

    cdef Frame entry_constraint
    cdef Frame exit_constraint

    cdef Entry entry_a
    cdef Entry entry_b

    cdef set live = set()  # Locals that are live in the final state
    cdef set overwritten = set()  # Locals that were overwritten

    for entry_constraint, exit_constraint in constraints:
        if len(entry_constraint.stack) != len(frame.stack):  # Definitely can't merge, so skip
            continue

        skip = False
        for entry_a, entry_b in zip(entry_constraint.stack, frame.stack):
            if entry_a.type != entry_b.type or entry_a.value != entry_b.value:
                skip = True
                break
            # Return addresses are also inherently tied to their origins and merging them solely based on type would
            # lead to incorrect behaviour, so check if they also have the same origins.
            elif (
                entry_a.type == types.return_address_t and
                entry_b.type == types.return_address_t and
                entry_a.source != entry_b.source
            ):
                skip = True
                break

        if skip:
            continue

        live.clear()
        overwritten.clear()

        for read, index, _ in exit_constraint.accesses:
            if read and not index in overwritten:
                live.add(index)
            else:
                overwritten.add(index)

        for index, entry_a in entry_constraint.locals.items():
            if index in overwritten:  # The index is overwritten in this frame, so it doesn't matter what it is going in
                continue
            entry_b = frame.locals.get(index)
            # It really is just too slow to check the constant values if the local isn't live specifically in this
            # block, and yes, it does result in some unvisited paths, I would assume. Idk, I might come back to this
            # issue in the future.
            # FIXME: ^^^
            if entry_b is None or entry_a.type != entry_b.type or (index in live and entry_a.value != entry_b.value):
                skip = True
                break
            elif (  # Same deal as above
                entry_a.type == types.return_address_t and
                entry_b.type == types.return_address_t and
                entry_a.source != entry_b.source
            ):
                skip = True
                break

        if not skip:
            return False  # The frame conforms to this constraint, so we don't need to compute the states again

    return True  # If the loop completes, we can't find any valid constraints, so we haven't computed the states for this frame yet


cdef class Trace:
    """
    A computed trace.
    """

    # TODO: From path and initial frame

    @classmethod
    def from_graph(
            cls,
            graph: InsnGraph,
            verifier: Union[Verifier, None] = None,
            *,
            compute_deltas: bool = True,
            compute_sources: bool = True,
    ) -> Trace:
        """
        Computes a trace from the provided graph.

        :param graph: The instruction graph to use.
        :param verifier: The verifier to use.
        :param compute_deltas: Should we compute frame deltas? It's faster not to, but you don't get as much information.
        :param compute_sources: Should we compute the sources of entries? It's also faster not to.
        :return: The computed trace.
        """

        if verifier is None:
            verifier = Verifier(BasicTypeChecker())  # We only really need a basic type checker for this

        cdef bint skip_source = not compute_sources

        cdef dict states = {}
        cdef dict deltas = {}

        # It's also useful to record leaf edges and back edges.
        cdef set leaf_edges = set()
        cdef set back_edges = set()
        cdef dict subroutines = {}  # (And we'll also compute the entry and exit points of subroutines in the graph.)

        cdef int max_stack = 0
        cdef int max_locals = 0

        # We'll use a (somewhat modified) iterative DFS to compute states, but we'll also keep track of the edges and
        # repeat state computation if we find a path with different constraints.
        cdef list traversed = []
        cdef list to_visit = [(False, None, Frame.initial(graph.method, verifier), [InsnEdge(None, graph.entry_block)])]

        cdef InsnEdge root
        cdef Frame frame
        cdef list edges  # TODO: Is an iterator faster/better?

        # Variable declarations for inside the loop.
        cdef InsnEdge edge
        cdef InsnBlock block

        cdef list constraints
        cdef list deltas_  # Good naming, I know /s
        cdef InsnEdge edge_

        while True:
            back_edge, root, frame, edges = to_visit[-1]
            if not edges:
                if root is not None and not <set>graph._forward_edges.get(root.to, False):
                    leaf_edges.add(root)
                if not traversed:  # Nothing more to do
                    break

                traversed.pop()
                to_visit.pop()
                continue

            edge = edges.pop()
            block = edge.to

            if block is None:
                if not edge in graph._opaque_edges:
                    verifier.report(Error(ErrorType.INVALID_EDGE, edge, "unknown opaque edge"))
                    continue

                edge = _resolve_opaque_edge(graph, verifier, subroutines, edge, frame)
                if edge is None:  # Could not resolve, error will have been reported by `_resolve_opaque` so just skip.
                    continue
                block = edge.to

            # FIXME: I don't think this is a 100% accurate solution, might be better to find SCCs?
            if not back_edge and block in traversed:
                back_edges.add(edge)
                back_edge = True

            constraints = states.setdefault(block, [])
            frame = frame.copy()
            if not _setup_edge_trace(verifier, edge, frame, constraints):
                continue

            entry = frame.copy()

            if compute_deltas:
                deltas_ = []

                for index, instruction in enumerate(block._instructions):
                    frame.start(None if skip_source else InstructionInBlock(block, instruction, index))
                    instruction.trace(frame)
                    deltas_.append(frame.finish())

                for edge_ in <set>graph._forward_edges[block]:
                    if edge_.instruction is None:  # Nothing to trace
                        continue
                    frame.start(None if skip_source else edge_)
                    edge_.instruction.trace(frame)
                    deltas_.append(frame.finish())
                    break  # Anymore instructions in edges is undefined behaviour, as it isn't possible
                    # TODO: ^^ report error

                (<list>deltas.setdefault(block, [])).append(deltas_)

            else:
                for index, instruction in enumerate(block._instructions):
                    frame.start(None if skip_source else InstructionInBlock(block, instruction, index))
                    instruction.trace(frame)

                for edge_ in <set>graph._forward_edges[block]:
                    if edge_.instruction is None:  # Nothing to trace
                        continue
                    frame.start(None if skip_source else edge_)
                    edge_.instruction.trace(frame)
                    break

            constraints.append((entry, frame))

            if frame.max_stack > max_stack:
                max_stack = frame.max_stack
            if frame.max_locals > max_locals:
                max_locals = frame.max_locals

            # Update the DFS stack and to visit with the new information
            traversed.append(block)
            to_visit.append((back_edge, edge, frame.copy(), list(graph._forward_edges[block])))

        return cls(graph, states, deltas, leaf_edges, back_edges, subroutines, max_stack, max_locals)

    def __init__(
            self,
            graph: InsnGraph,
            frames: Dict[InsnBlock, List[Tuple[Frame, Frame]]],
            deltas: Dict[InsnBlock, List[List[FrameDelta]]],
            leaf_edges: Set[InsnEdge],
            back_edges: set[InsnEdge],
            subroutines: Dict[JsrJumpEdge, Set[RetEdge]],
            max_stack: int,
            max_locals: int,
    ) -> None:
        """
        :param frames: The computed entry and exit constraints (as frames) for blocks.
        :param deltas: The individual stack deltas for each instruction.
        :param leaf_edges: All the edges in the graph that lead to leaves (that were visited).
        :param back_edges: All the back edges in the graph that were visited.
        :param subroutines: All the resolved subroutines in the graph.
        """

        self.graph = graph

        self.frames = frames
        self.deltas = deltas

        self.leaf_edges = leaf_edges
        self.back_edges = back_edges
        self.subroutines = subroutines

        self.max_stack = max_stack
        self.max_locals = max_locals

    def __repr__(self) -> str:
        return "<Trace(frames=%i, max_stack=%i, max_locals=%i) at %x>" % (
            len(self.frames), self.max_stack, self.max_locals, id(self),
        )

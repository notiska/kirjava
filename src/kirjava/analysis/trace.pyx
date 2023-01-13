# cython: language=c
# cython: language_level=3

__all__ = (
    "Trace", "Entry", "State",
)

"""
Stack and local state tracing.
"""

import logging
from frozendict import frozendict, FrozenOrderedDict
from typing import Any, Dict, FrozenSet, List, Set, Tuple, Union

from .graph cimport *
from .source import InstructionInBlock
from .. import types
from ..abc import Constant, Source, TypeChecker
from ..classfile.instructions import Instruction
from ..classfile.members import MethodInfo
from ..types import VerificationType
from ..types.verification import This, UninitializedThis
from ..verifier import BasicTypeChecker, Error

logger = logging.getLogger("kirjava.analysis.trace")


cdef inline bint _same_entry(Entry entry_a, Entry entry_b):
    """
    Checks if two entries are the same, taking into account returnAddress paradigms.
    """

    if entry_a.type != entry_b.type:
        return False
    elif (  # More specific checks for returnAddress origins
        entry_a.type == types.return_address_t and
        entry_b.type == types.return_address_t and
        entry_a.source != entry_b.source
    ):
        return False
    return True


# ------------------------------ Classes ------------------------------ #

cdef class Entry:
    """
    An entry on either the stack or in the locals of a state.
    """

    def __init__(
            self,
            id_: int,
            source: Union[Source, None],
            type_: VerificationType,
            value: Union[Constant, None] = None,
            parents: Tuple["Entry", ...] = (),
            merges: Tuple["Entry", ...] = (),
    ) -> None:
        """
        :param id_: A unique ID provided by the state, for identification and hashing.
        :param source: The source that created the entry.
        :param type_: The type of the entry.
        :param value: The actual value of this entry, if it has one.
        :param parents: Any parents to this entry.
        :param merges: Like parents, but only from the direct result of merging two types.
        """

        self.id = id_
        self.source = source
        self.type = type_
        self.value = value
        self.parents = parents
        self.merges = merges

    def __repr__(self) -> str:
        return "<Entry(source=%s, type=%r, value=%r) at %x>" % (
            self.source, self.type, self.value, id(self),
        )

    def __str__(self) -> str:
        if self.value is not None:
            return "%s (%s)" % (self.type, self.value)
        return str(self.type)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        elif isinstance(other, Entry) and (<Entry>other).id == self.id and (<Entry>other).type == self.type:
            return True
        for merge in self.merges:
            if merge is self:  # Avoid any recursion here
                continue
            if other == merge:
                return True
        return False

    def __hash__(self) -> int:
        return hash((self.id, self.type))


cdef class State:
    """
    A stack and locals state representation (also called stackmap frames, I think).
    """

    @classmethod
    def initial(cls, method: MethodInfo, errors: Union[List[Error], None] = None) -> "State":
        """
        Creates the initial stack state for a given method.

        :param method: The method to create the initial state for.
        :param errors: The errors to add to.
        :return: The new state.
        """

        state = cls(0, errors)

        offset = 0
        if not method.is_static:
            this_class = method.class_.get_type()
            if method.name == "<init>" and method.return_type == types.void_t:  # Constructor method?
                state.set(None, 0, UninitializedThis(class_=this_class))
            else:
                state.set(None, 0, This(this_class))
            offset += this_class.internal_size

        for index, argument_type in enumerate(method.argument_types):
            argument_type = argument_type.to_verification_type()
            state.set(None, offset, argument_type)
            offset += argument_type.internal_size

        state.max_locals = offset  # Also adjust the max locals
        # These don't actually count as local accesses, lmao, you would not believe how LONG it took me to find this
        # fucking bug, good job Iska!!!!
        state.local_accesses.clear()

        return state

    property id:
        def __get__(self) -> int:
            cdef int id_ = self._id
            self._id += 1
            return id_

    def __init__(self, id_: int, errors: Union[List[Error], None] = None) -> None:
        """
        :param id_: The starting entry ID for this state.
        :param errors: The list of errors to add to.
        """

        self._id = id_
        if errors is not None:
            self._errors = errors
        else:
            self._errors = []

        self._top = Entry(-65536, None, types.top_t)

        self.stack: List[Entry] = []
        self.locals: Dict[int, Entry] = {}

        self.max_stack = 0
        self.max_locals = 0

        # Record locals that were accessed and the type access for liveness tracing later. True means the local was read
        # from and False means it was written to. The intention is that the order of these accesses is maintained so that
        # we can store liveness on a per-block level rather than a per-instruction level, hopefully saving memory and
        # processing time.
        self.local_accesses: List[Tuple[int, Union[Entry, None], Entry, bool]] = []

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        elif other.__class__ is FrozenState:
            return other.__eq__(self)
        return (
            isinstance(other, State) and
            (<State>other).stack == self.stack and
            (<State>other).locals == self.locals and
            (<State>other).max_stack == self.max_stack and
            (<State>other).max_locals == self.max_locals
        )

    def __hash__(self) -> int:
        return hash((tuple(self.stack), frozendict(self.locals), self.max_stack, self.max_locals))

    # ------------------------------ Public API ------------------------------ #

    def freeze(self) -> "FrozenState":
        """
        Freezes this state.

        :return: The frozen state.
        """

        return FrozenState(self)

    def copy(self, id_: Union[int, None] = None, deep: bool = True) -> "State":
        """
        Creates a copy of this state.

        :param id_: The ID to give the state, if None, the ID on this one is passed through.
        :param deep: Copies extra trace information in this state such as the local accesses.
        :return: The copied state.
        """

        state = State(self._id if id_ is None else id_, self._errors)

        state.stack.extend(self.stack)
        state.locals.update(self.locals)

        state.max_stack = self.max_stack
        state.max_locals = self.max_locals

        if deep:
            state.local_accesses.extend(self.local_accesses)

        return state

    def replace(
            self,
            source: Union[Source, None],
            old: Entry,
            type_: VerificationType,
            parents: Tuple[Entry, ...] = (),
            merges: Tuple[Entry, ...] = (),
    ) -> None:
        """
        Replaces all occurrences of an old entry with a new one.

        :param source: The source of the call.
        :param old: The old entry to replace.
        :param type_: Type type of the new entry.
        :param parents: Any extra parent entries to give the new entry.
        :param merges: If direct type merging resulted in this entry, the entries that were merged.
        """

        new = Entry(self._id, source, type_, parents=parents, merges=merges)
        self._id += 1

        for index, entry in enumerate(self.stack):
            if entry == old:
                self.stack[index] = new

        for index, entry in self.locals.items():
            if entry == old:
                self.locals[index] = new

    def pop(self, source: Union[Source, None], amount: int = 1, tuple_: bool = False) -> Union[Tuple[Entry, ...], Entry]:
        """
        Pops one or multiple entries off the stack.

        :param source: The source of the call.
        :param amount: The number of entries to pop off the stack.
        :param tuple_: Should the output be returned as a tuple?
        :return: The entry (or multiple entries) that was/were popped off the stack.
        """

        if amount == 1 and not tuple_:
            try:
                return self.stack.pop()
            except IndexError:
                self._errors.append(Error(Error.Type.STACK_UNDERFLOW, source, "-1 entries"))
                return Entry(self.id, source, types.top_t)

        entries = []
        try:
            for index in range(amount):
                entries.append(self.stack.pop())
        except IndexError:
            self._errors.append(Error(Error.Type.STACK_UNDERFLOW, source, "%i entries" % (len(entries) - amount)))
            for index in range(amount - len(entries)):
                entries.append(Entry(self.id, source, types.top_t))

        return tuple(entries)

    def push(
            self,
            source: Union[Source, None],
            entry_or_type: Union[Entry, VerificationType],
            value: Union[Constant, None] = None,
            parents: Tuple[Entry, ...] = (),
            merges: Tuple[Entry, ...] = (),
    ) -> None:
        """
        Pushes the provided entry onto the stack.

        :param source: The source of the call.
        :param entry_or_type: The entry to push or the type of the entry.
        :param value: The value of the entry, if applicable.
        :param parents: Any parents to the type, if an entry was not given.
        :param merges: If a type is given due to a merge, the merge entries should be provided through this.
        """

        if entry_or_type.__class__ is Entry:
            entry = entry_or_type
        else:
            entry = Entry(self._id, source, entry_or_type, value, parents, merges)
            self._id += 1

        if entry.type.internal_size > 1:
            self.stack.append(self._top)
        self.stack.append(entry)

        stack_size = len(self.stack) + 1  # FIXME: Doesn't this actually overshoot by 1?
        if stack_size > self.max_stack:
            self.max_stack = stack_size

    def get(self, source: Union[Source, None], index: int) -> Entry:
        """
        Gets the value of the local at a given index.

        :param source: The source of the call.
        :param index: The index of the local variable to get.
        :return: The local variable entry.
        """

        entry = self.locals.get(index, None)
        if entry is None:
            self._errors.append(Error(Error.Type.UNKNOWN_LOCAL, source, "no local at index %i" % index))
            entry = Entry(self.id, source, types.top_t)
        self.local_accesses.append((index, None, entry, True))
        return entry

    def set(
            self,
            source: Union[Source, None],
            index: int,
            entry_or_type: Union[Entry, VerificationType],
            value: Union[Constant, None] = None,
            parents: Tuple[Entry, ...] = (),
            merges: Tuple[Entry, ...] = (),
    ) -> None:
        """
        Sets the value of the local at a given index to the provided entry.

        :param source: The source of the call.
        :param index: The index of the local to set.
        :param entry_or_type: The entry or type to set the local to.
        :param value: The value of the entry, if applicable.
        :param parents: Any parents of the type, if a direct entry was not specified.
        :param merges: If a type was given due to a type merge, the merge entries should be specified here.
        """

        previous = self.locals.get(index, None)
        # if previous is not None and previous.type == types.null_t and isinstance(entry.type, ReferenceType):
        #     # If the previous was null, note down that this reference type may be null by adding the previous to the
        #     # parents of the entry.
        #     entry = Entry(self._id, instruction, entry.type, entry.parents, (entry, previous))
        #     self._id += 1

        if entry_or_type.__class__ is Entry:
            entry = entry_or_type
        else:
            entry = Entry(self.id, source, entry_or_type, value, parents, merges)

        self.local_accesses.append((index, previous, entry, False))
        self.locals[index] = entry
        if entry.type.internal_size > 1:
            index += 1
            self.locals[index] = self._top

        index += 1
        if index > self.max_locals:
            self.max_locals = index


cdef class FrozenState:
    """
    A frozen state object.
    """

    def __init__(self, state: State) -> None:
        """
        :param state: The state to freeze.
        """

        self._top = state._top

        self.stack: Tuple[Entry, ...] = tuple(state.stack)
        self.locals: FrozenOrderedDict[int, Entry] = frozendict(state.locals)

        self.max_stack = state.max_stack
        self.max_locals = state.max_locals

        self.local_accesses: Tuple[Tuple[int, Union[Instruction, None], Entry, bool], ...] = tuple(state.local_accesses)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        elif isinstance(other, State):
            return (
                tuple((<State>other).stack) == self.stack and
                (<State>other).locals == self.locals and
                (<State>other).max_stack == self.max_stack and
                (<State>other).max_locals == self.max_locals
            )
        return (
            isinstance(other, FrozenState) and
            (<FrozenState>other).stack == self.stack and
            (<FrozenState>other).locals == self.locals and
            (<FrozenState>other).max_stack == self.max_stack and
            (<FrozenState>other).max_locals == self.max_locals
        )

    def __hash__(self) -> int:
        return hash((self.stack, self.locals, self.max_stack, self.max_locals))

    def unfreeze(self, id_: int = 0) -> State:
        """
        Unfreezes this state.

        :param id_: The ID to give the unfrozen state.
        :return: The unfrozen state.
        """

        state = State(id_)

        state.stack.extend(self.stack)
        state.locals.update(self.locals)

        state.max_stack = self.max_stack
        state.max_locals = self.max_locals

        state.local_accesses.extend(self.local_accesses)

        return state


cdef class Trace:
    """
    Trace information that has been computed.
    """

    @classmethod
    def from_graph(cls, graph: InsnGraph, checker: TypeChecker = BasicTypeChecker(), exact: bool = False) -> "Trace":
        """
        Creates a trace from the provided graph.

        :param graph: The graph to trace.
        :param checker: The type checker implementation to use.
        :param exact: Traces exact states for every instruction, rather than just block entry and exit constraints.
        :return: The trace instance.
        """

        cdef:
            # Variables that'll be used as the "final" value
            list errors = []

            InsnEdge start = InsnEdge(graph.entry_block, graph.entry_block)
            State state = State.initial(graph.method, errors)

            list traversed = []  # Iterative DFS stack so we can detect loops
            list to_visit = [(None, state, [start])]
            dict visited = {}

            set leaf_edges = set()
            set back_edges = set()
            dict subroutines = {}

            int max_stack = state.max_stack
            int max_locals = state.max_locals

            dict states = {}

            # Pre-defined temporary variables from inside the loop
            InsnEdge root
            list edges

            InsnEdge edge
            InsnBlock block
            dict constraints
            set adjacent

            bint is_back_edge
            bint is_adjacent_visited

            set live
            set overwritten

            FrozenState entry
            FrozenState exit

        while to_visit:
            root, state, edges = to_visit[-1]
            if not edges:
                if root is not None and not graph.out_edges(root.to):
                    leaf_edges.add(root)
                if not traversed:
                    break

                traversed.pop()
                to_visit.pop()
                continue

            edge = edges.pop()
            if isinstance(edge, JsrFallthroughEdge):  # Don't handle these here, they are really only placeholders
                continue
            block = edge.to

            if block is None:
                if not edge in graph._opaque_edges:
                    errors.append(Error(Error.Type.INVALID_EDGE, edge, "unknown opaque edge"))
                    continue

                if isinstance(edge, RetEdge):
                    return_address = state.locals.get(edge.instruction.index, None)
                    if return_address is None or return_address.type != types.return_address_t:
                        errors.append(Error(  # FIXME: More specific error type
                            Error.Type.INVALID_TYPE, edge, "cannot resolve subroutine origin due to invalid local",
                        ))
                        continue  # Really nothing else we can do here

                    # Find the corresponding jsr jump and fallthrough edges
                    jsr_jump_edge: Union[JsrJumpEdge, None] = None
                    jsr_fallthrough_edge: Union[JsrFallthroughEdge, None] = None

                    for edge_ in graph.out_edges(return_address.source.from_):
                        if isinstance(edge_, JsrJumpEdge):
                            if jsr_jump_edge is not None:
                                # Even if handling multi-entry subroutines, we can't allow multiple jsr edges on a block
                                errors.append(Error(
                                    Error.Type.INVALID_BLOCK, return_address.source.from_,
                                    "multiple jsr jump edges found on block",
                                ))
                            jsr_jump_edge = edge_

                        elif isinstance(edge_, JsrFallthroughEdge):
                            if jsr_fallthrough_edge is not None:
                                errors.append(Error(
                                    Error.Type.INVALID_BLOCK, return_address.source.from_,
                                    "multiple jsr fallthrough edges found on block",
                                ))
                            jsr_fallthrough_edge = edge_

                    if jsr_jump_edge is None:
                        errors.append(Error(Error.Type.INVALID_BLOCK, block, "ret edge to block with no jsr jump edge"))
                        # We can still handle this technically, we'll just count it as an absolute jump though, the error
                        # should also be sufficient.
                        subroutine_edges = set()
                    else:
                        subroutine_edges = subroutines.setdefault(jsr_jump_edge, set())

                    if jsr_fallthrough_edge is None:
                        errors.append(Error(
                            Error.Type.INVALID_BLOCK, block, "ret edge to block with no jsr fallthrough edge",
                        ))
                        # If this is the case, there's nothing we can do about this subroutine as we don't know where
                        # to fall through to. We can mark it as a subroutine though, it'll just be a partial one.
                        subroutine_edges.add(edge)
                        continue

                    # Overwrite the old edge with our new resolved edge
                    edge = RetEdge(edge.from_, jsr_fallthrough_edge.to, edge.instruction)
                    block = edge.to
                    subroutine_edges.add(edge)

                    # A sidenote on subroutines: we can also handle multi-exit subroutines with this, even though they
                    # are not allowed in Java. I'm planning to keep this functionality because it allows us to do
                    # analysis on unverifiable code, which is nice.

                else:
                    # This is an internal error, so raise
                    raise ValueError("Don't know how to handle opaque edge %r." % edge)

            # print(root, edge, ", ".join(map(str, traversed + [block])))

            state = state.copy(deep=False)

            constraints = states.setdefault(block, {})
            adjacent = visited.setdefault(root, set())

            is_back_edge = block in traversed
            is_adjacent_visited = edge in adjacent

            # Special handling for exception edges. A valid stack state is one in which there is only one item on the
            # stack, that being the exception that was thrown.
            if isinstance(edge, ExceptionEdge):
                state.stack.clear()
                if not checker.check_merge(types.throwable_t, (<ExceptionEdge>edge).throwable):
                    errors.append(Error(
                        Error.Type.INVALID_TYPE, edge,
                        "expected type java/lang/Throwable for exception edge", "got %s" % (<ExceptionEdge>edge).throwable,
                    ))
                    state.push(None, checker.merge(types.throwable_t, (<ExceptionEdge>edge).throwable))
                else:
                    state.push(None, (<ExceptionEdge>edge).throwable)

            # If we have already visited the edge, and it has the same entry constraints as it did before, then we
            # already know the exit constraints, and therefore further computation is unnecessary, so we can check for
            # that here.
            if is_back_edge or is_adjacent_visited:
                found = False

                # Check the locals more specifically, taking into account if any of the locals actually used in
                # the block are different.
                for entry, (*_, exit) in constraints.items():
                    live = set()
                    overwritten = set()

                    for index, _, _, read in exit.local_accesses:
                        if not read:
                            overwritten.add(index)
                            continue
                        elif index in live or index in overwritten:  # Already checked this, no need to again
                            continue

                        live.add(index)
                        if not _same_entry(<Entry>state.locals[index], <Entry>entry.locals[index]):
                            break  # Breaks out of the inner, which continues the outer loop
                    else:
                        # The locals that aren't overwritten can still be used later in the method, so double check
                        # that they're all valid too.
                        for index, entry_a in state.locals.items():
                            if index in live or index in overwritten or not index in entry.locals:
                                continue
                            if not _same_entry(<Entry>entry_a, <Entry>entry.locals[index]):
                                break
                        else:
                            # Now we also need to check if the stacks are equal, because they may not be
                            if len(state.stack) == len(entry.stack):
                                for entry_a, entry_b in zip(state.stack, entry.stack):
                                    if not _same_entry(<Entry>entry_a, <Entry>entry_b):
                                        break
                                else:
                                    found = True
                                    break
                    continue

                if found:
                    if is_back_edge:
                        back_edges.add(edge)
                    continue

            else:
                adjacent.add(edge)

            # print(root, edge)
            entry = state.freeze()
            out_edges = graph.out_edges(block)

            if exact:
                instruction_states = []
                for index, instruction in enumerate(block._instructions):
                    instruction.trace(InstructionInBlock(block, instruction, index), state, errors, checker)
                    instruction_states.append(state.freeze())
                for edge in out_edges:
                    if edge.instruction is None:
                        continue
                    edge.instruction.trace(edge, state, errors, checker)
                    instruction_states.append(state.freeze())
                    break
                constraints[entry] = tuple(instruction_states)
            else:
                for index, instruction in enumerate(block._instructions):
                    instruction.trace(InstructionInBlock(block, instruction, index), state, errors, checker)
                for edge in out_edges:
                    if edge.instruction is None:
                        continue
                    edge.instruction.trace(edge, state, errors, checker)
                    break  # Only trace one edge instruction as the block should only have one jump instruction, if any
                constraints[entry] = (state.freeze(),)

            # Adjust stack and local maxes too
            if state.max_stack > max_stack:
                max_stack = state.max_stack
            if state.max_locals > max_locals:
                max_locals = state.max_locals

            traversed.append(block)
            to_visit.append((edge, state, list(out_edges)))

        for block, constraints in states.items():
            states[block] = frozendict(constraints)
        for edge, edges_ in subroutines.items():
            subroutines[edge] = frozenset(edges_)

        return cls(  # Ughhh the formatting, not sure how to make this look pretty lol
            graph,
            frozendict(states),
            tuple(errors),
            frozenset(leaf_edges),
            frozenset(back_edges),
            frozendict(subroutines),
            max_stack,
            max_locals,
        )

    # @property
    # def loops(self) -> Tuple["Path", ...]:
    #     """
    #     :return: All the paths in this trace that are loops.
    #     """

    #     return tuple(filter(lambda path: path.loop, self.paths))

    def __init__(
            self,
            graph: InsnGraph,
            states,  # : FrozenOrderedDict[InsnBlock, FrozenOrderedDict[FrozenState, Tuple[FrozenState, ...]]],
            errors: Tuple[Error, ...],
            leaf_edges: FrozenSet[InsnEdge],
            back_edges: FrozenSet[InsnEdge],
            subroutines,  # : FrozenOrderedDict[InsnEdge, FrozenSet[InsnEdge]],
            max_stack: int,
            max_locals: int,
    ) -> None:
        self.graph = <InsnGraph?>graph

        # self.paths: Tuple[Path, ...] = ()
        self.states = states
        self.errors = errors

        self.leaf_edges = leaf_edges
        self.back_edges = back_edges
        self.subroutines = subroutines

        self.max_stack = max_stack
        self.max_locals = max_locals

    def __eq__(self, other: Any) -> bool:
        return other is self or (other.__class__ is Trace and other.states == self.states)

    def __hash__(self) -> int:
        return hash(self.states)

    ...  # FIXME: Better API, ability to fetch states and block entry/exits and at instructions if exact

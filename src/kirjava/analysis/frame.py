#!/usr/bin/env python3

__all__ = (
    "Entry", "Frame",
)

"""
Stack frames (and others).
"""

import operator
import typing
from typing import Any, Iterator, Optional

from ..abc import Method, Source
from ..error import MergeDepthError, MergeMissingLocalError
from ..types import (
    array_t, null_t, object_t, reserved_t, top_t, uninitialized_this_t, void_t,
    Array, Class, Reference, Type, Uninitialized, Verification,
)

if typing.TYPE_CHECKING:
    from .graph import InsnEdge


class Entry:
    """
    A type entry in a stack frame.
    """

    __slots__ = ("generic", "merges", "parent", "source", "_consumers", "_constraints")

    @property
    def type(self) -> Type:
        """
        :return: The type of this local. May change over time.
        """

        types = self.inference(as_vtypes=False)
        if len(types) > 1:
            return self.generic  # Can't narrow down the type without any extra information.
        for type_ in types:
            return type_

    @property
    def adjacent(self) -> tuple["Entry", ...]:
        """
        :return: All adjacent entries (also called merges) to this entry.
        """

        return tuple(self._iter_merges())

    @property
    def parents(self) -> tuple["Entry", ...]:
        """
        :return: All the parents of this entry.
        """

        parents = set(self._iter_parents())
        for entry in self._iter_merges():
            parents.update(entry._iter_parents())

        # Although it is slower to copy this to a tuple, sets are more annoying to work with in an interactive shell.
        # Tuples also indicate that the data provided is immutable.
        return tuple(parents)

    @property
    def constraints(self) -> tuple["Entry.Constraint", ...]:
        """
        :return: All type constraints for this entry. Note: this is not necessarily all the types this entry could be.
        """

        constraints = self._constraints.copy()

        for entry in self._iter_merges_and_parents():
            constraints.update(entry._constraints)

        return tuple(constraints)

    @property
    def producers(self) -> tuple[Source, ...]:
        """
        :return: All the sources that "produced" this entry.
        """

        producers = []

        for entry in self._iter_merges():
            if entry.source is not None:
                producers.append(entry.source)
        if self.source is not None:
            producers.append(self.source)

        return tuple(producers)

    @property
    def consumers(self) -> tuple[Source, ...]:
        """
        :return: All the sources that "consumed" this entry.
        """

        consumers = []

        for entry in self._iter_merges_and_parents():
            consumers.extend(entry._consumers)
        consumers.extend(self._consumers)

        return tuple(consumers)

    # @property
    # def null(self) -> bool:
    #     """
    #     Is this entry null?
    #     """
    #
    #     return self.type is null_t
    #
    # @property
    # def nullable(self) -> bool:
    #     """
    #     Is this entry null at any point?
    #     """
    #
    #     if self.type is null_t:
    #         return True
    #     elif not isinstance(self.type, Reference):
    #         return False
    #     return any(parent.nullable for parent in self.parents)

    @classmethod
    def _generify(cls, type_: Type) ->tuple[Verification, set[Type]]:
        # We can generify all reference types (except uninitialized types) to java/lang/Object. The idea is that the
        # type will be inferred from constraints, later on.
        if isinstance(type_, Reference) and not isinstance(type_, Uninitialized):
            return object_t, {type_}

        vtype = type_.as_vtype()
        if type_ != vtype:
            return vtype, {type_}

        return vtype, set()

    def __init__(self, type_: Type, source: Source | None = None, parent: Optional["Entry"] = None) -> None:
        """
        :param type_: The type of this entry.
        :param source: The source that created this entry.
        :param parent: The parent entry.
        """

        self.generic, constraints = self._generify(type_)

        self.merges: set[Entry] = set()

        self.parent = parent
        self.source = source
        self._consumers: list[Source] = []

        self._constraints = set(Entry.Constraint(constraint, source, original=True) for constraint in constraints)

        # self._hash = hash((self.type, self.origin))

    def __repr__(self) -> str:
        constraints = set(constraint.type for constraint in self.constraints)
        return "<Entry(type=%s, constraints={%s}) at %x>" % (
            self.type, ", ".join(map(str, constraints)), id(self),
        )

    # def __eq__(self, other: Any) -> bool:
    #     return type(other) is Entry and self.type == other.type
    #
    # def __hash__(self) -> int:
    #     return self._hash

    def __str__(self) -> str:
        return str(self.type)

    def _iter_merges(self) -> Iterator["Entry"]:
        """
        Non-recursive iterator for all merges of this entry.
        """

        visited = {self}
        stack = [iter(self.merges)]

        while stack:
            merges = stack[-1]
            for entry in merges:
                if entry in visited:
                    continue
                visited.add(entry)
                stack.append(iter(entry.merges))
                yield entry
                break
            else:
                stack.pop()

    def _iter_parents(self) -> Iterator["Entry"]:
        """
        A non-recursive iterator for all parents of this entry.
        """

        entry = self
        while entry.parent is not None:
            entry = entry.parent
            yield entry

    def _iter_merges_and_parents(self) -> Iterator["Entry"]:
        """
        A non-recursive iterator for all merges, parents and parents of merges.
        """

        visited = {self}
        stack = [iter(self.merges)]

        # Too lazy to copy-paste code from right above :p. How much slower can it really be?
        yield from self._iter_parents()

        while stack:
            merges = stack[-1]
            for entry in merges:
                if entry in visited:
                    continue
                visited.add(entry)
                stack.append(iter(entry.merges))
                yield entry

                while entry.parent is not None:
                    entry = entry.parent
                    if entry in visited:
                        break
                    # visited.add(entry)
                    yield entry

                break
            else:
                stack.pop()

    # ------------------------------ Public API ------------------------------ #

    def inference(self, *, as_vtypes: bool = True, no_nullable: bool = False) -> set[Type]:
        """
        :param as_vtypes: Turns all constraints into verification types.
        :param no_nullable: Removes the null_t in nullable types.
        :return: A set of types this entry could be.
        """

        types = {self.generic}

        # Apparently generators are slower, or is it set.update that's slower? Either way, using a for loop is faster,
        # which is why I'm using it here.
        # types.update(constraint.type for constraint in self._constraints if constraint.original)
        for constraint in self._constraints:
            if constraint.original:
                types.add(constraint.type)
        for entry in self._iter_merges():
            # types.update(constraint.type for constraint in entry._constraints if constraint.original)
            for constraint in entry._constraints:
                if constraint.original:
                    types.add(constraint.type)

        if as_vtypes:
            types = {type_.as_vtype() for type_ in types}

        all_refs = False

        if len(types) > 1 and self.generic is object_t:
            all_refs = True
            for type_ in types:
                # If there isn't a reference type in the types (for some reason), don't remove as we want to maintain
                # the information that this should be a reference type.
                if not isinstance(type_, Reference):
                    all_refs = False
                    break
            else:
                types.remove(self.generic)

        if all_refs and no_nullable and len(types) > 1:
            types.discard(null_t)

        return types

    # ------------------------------ Trace methods ------------------------------ #

    def constrain(self, type_: Type, source: Source | None = None, *, original: bool = False) -> bool:
        """
        Adds a type constraint to this entry.

        :param type_: The type constraint.
        :param source: The source that constrained this entry's type.
        :return: Was this constraint added?
        """

        if type_ == self.generic:
            return False
        constraint = Entry.Constraint(type_, source, original=original)
        if constraint in self._constraints:
            return False
        self._constraints.add(constraint)
        return True

    def cast(self, type_: Type, source: Source | None = None) -> "Entry":
        """
        Casts this entry to another type.

        :param type_: The type to cast to.
        :param source: The source creating the new entry.
        """

        if type_ == self.generic:
            return self

        entry = Entry(type_, source, self)

        # This can happen when for example, initialising an object. Uninitialised types are not mergeable with reference
        # types yet we still want to maintain a link to the original.
        if not self.generic.mergeable(type_):
            return entry
        elif isinstance(self.generic, Reference):
            # A note with checkcast instructions: we can't actually confirm that the class we're trying to cast to is a
            # valid subtype nor can we verify if the class exists, so we'll add it as a constraint (which are meant to
            # be taken with a grain of salt).
            self._constraints.add(Entry.Constraint(type_, source))

        return entry

    # ------------------------------ Classes ------------------------------ #

    class Constraint:
        """
        A type constraint with an optional source.
        """

        __slots__ = ("type", "source", "original", "_hash")

        def __init__(self, type_: Type, source: Source | None = None, original: bool = False) -> None:
            self.type = type_
            self.source = source
            self.original = original

            self._hash = hash((self.type, self.source, original))

        def __repr__(self) -> str:
            return "<Entry.Constraint(type=%s, source=%s, original=%s)>" % (self.type, self.source, self.original)

        def __str__(self) -> str:
            return str(self.type)

        def __eq__(self, other: Any) -> bool:
            return (
                type(other) is Entry.Constraint and
                self.source == other.source and
                self.type == other.type and
                self.original == other.original
            )

        def __hash__(self) -> int:
            return self._hash


# class Delta:
#     """
#     A delta between two frames.
#     """
#
#     __slots__ = ("pushes", "pops", "overwrites", "_hash")
#
#     def __init__(
#             self,
#             pushes: Iterable[Union[Entry, "Delta.Identity"]],
#             pops: Iterable[Union[Entry, "Delta.Identity"]],
#             # Excellent typing...
#             overwrites: Iterable[tuple[int, Union[Entry, "Delta.Identity"] | None, Union[Entry, "Delta.Identity"] | None]],
#     ) -> None:
#         """
#         :param pushes: The entries pushed to the stack.
#         :param pops: The entries popped from the stack.
#         :param overwrites: The entries overwritten in the locals.
#         """
#
#         self.pushes = tuple(pushes)
#         self.pops = tuple(pops)
#         self.overwrites = tuple(overwrites)
#
#         self._hash = hash((self.pushes, self.pops, self.overwrites))
#
#     def __repr__(self) -> str:
#         return "<Delta(pushes=[%s], pops=[%s], overwrites={%s})>" % (
#             ", ".join(map(str, self.pushes)), ", ".join(map(str, self.pops)),
#             ", ".join(
#                 "%i=%s->%s" % (index, old, new)
#                 for index, old, new in sorted(self.overwrites, key=operator.itemgetter(0))
#             ),
#         )
#
#     def __eq__(self, other: Any) -> bool:
#         return (
#             type(other) is Delta and
#             self.pushes == other.pushes and
#             self.pops == other.pops and
#             self.overwrites == other.overwrites
#         )
#
#     def __hash__(self) -> int:
#         return self._hash
#
#     class Identity:
#         """
#         A representation of a generalised entry.
#         """
#
#         __slots__ = ("id", "expect",)
#
#         def __init__(self, id_: int, expect: Type | None = None) -> None:
#             """
#             :param id_: An ID to represent this identity, unique to the delta it's in.
#             :param expect: The expected type of this entry.
#             """
#
#             self.id = id_
#             self.expect = expect
#
#         def __repr__(self) -> str:
#             return "<Identity(id=%i, expect=%s)>" % (self.id, self.expect)
#
#         def __str__(self) -> str:
#             return "id=%i" % self.id


class Frame:
    """
    A stack frame.
    """

    __slots__ = ("stack", "locals", "tracked", "max_stack", "max_locals")

    TOP = Entry(top_t)

    @classmethod
    def initial(cls, method: Method) -> "Frame":
        """
        Creates the initial frame of a method, given the method.
        """

        frame = cls()
        index = 0

        if not method.is_static:
            if method.name == "<init>" and method.return_type == void_t:  # and method.class_.is_super:
                entry = Entry(uninitialized_this_t, cls.Parameter(0, uninitialized_this_t, method))
            else:
                type_ = method.class_.get_type()
                entry = Entry(type_, cls.Parameter(0, type_, method))
            frame.locals[0] = entry
            frame.tracked.add(entry)
            index = 1

        for type_ in method.argument_types:
            frame.locals[index] = Entry(type_, cls.Parameter(index, type_, method))
            frame.tracked.add(frame.locals[index])
            index += 1

            if type_.wide:
                frame.locals[index] = Entry(reserved_t, cls.Parameter(index - 1, type_, method))
                frame.tracked.add(frame.locals[index])
                index += 1

        frame.max_locals = index

        return frame

    def __init__(self) -> None:
        self.stack: list[Entry] = []
        self.locals: dict[int, Entry] = {}
        self.tracked: set[Entry] = set()

        self.max_stack = 0
        self.max_locals = 0

    def __repr__(self) -> str:
        return "<Frame(stack=[%s], locals={%s}) at %x>" % (
            ", ".join(map(str, self.stack)),
            ", ".join("%i=%s" % local for local in sorted(self.locals.items(), key=operator.itemgetter(0))),
            id(self),
        )

    def __eq__(self, other: Any) -> bool:
        return type(other) is Frame and self.stack == other.stack and self.locals == other.locals

    # def __add__(self, other: Any) -> "Frame":
    #     if type(other) is not Delta:
    #         raise TypeError("Unsupported operand type(s) for +: %r and %r." % (Frame, type(other)))
    #
    #     frame = Frame(self)
    #     frame.add(other)
    #     return frame
    #
    # def __sub__(self, other: Any) -> Union[Delta, "Frame"]:
    #     if type(other) is Frame:
    #         return self.delta(other)
    #     elif type(other) is Delta:
    #         frame = Frame(self)
    #         frame.sub(other)
    #         return frame
    #     else:
    #         raise TypeError("Unsupported operand type(s) for -: %r and %r." % (Frame, type(other)))

    # ------------------------------ Misc operations ------------------------------ #

    def copy(self, *, deep: bool = True) -> "Frame":
        """
        Copies this frame.
        """

        frame = Frame()

        if deep:
            copied: dict[Entry, Entry] = {}
            for old_entry in self.tracked:
                copied[old_entry] = new_entry = Entry(old_entry.generic, None)
                new_entry.merges.add(old_entry)
                old_entry.merges.add(new_entry)

            # Just in case this is in the tracked entries, we'll make sure that it remains the exact same.
            copied[self.TOP] = self.TOP

            frame.stack.extend(copied[entry] for entry in self.stack)
            frame.locals.update({index: copied[entry] for index, entry in self.locals.items()})

            # We'll only update the tracked entries of the new frame with ones that we know are still on the stack or in
            # the locals, this acts to stop build up of unused entries.
            frame.tracked.update(frame.stack)
            frame.tracked.update(frame.locals.values())

        else:
            frame.stack.extend(self.stack)
            frame.locals.update(self.locals)
            frame.tracked.update(self.tracked)

            frame.max_stack = self.max_stack
            frame.max_locals = self.max_locals

        return frame

    def merge(
            self,
            other: "Frame",
            edge: "InsnEdge",
            live_locals: set[int] | None = None,
            check_depth: bool = True,
            merge_non_live: bool = True,
    ) -> bool:
        """
        Checks that this frame can merge with the other frame and if possible, merges it.

        :param other: The other frame to check against.
        :param edge: The edge causing the merge (for debug info).
        :param live_locals: Optional local liveness information. If not specified, all locals are checked.
        :param check_depth: Should we check the stack to see if they're equal?
        :param merge_non_live: Attempts to merge non-live locals anyway, may provide some extra insight.
        :return: Is this a valid merge?
        """

        if live_locals is None:
            live_locals = self.locals.keys()

        valid = True

        # Basic preconditions checks to see if the frame merge is immediately invalid.
        if check_depth and len(self.stack) != len(other.stack):
            raise MergeDepthError(edge, len(other.stack), len(self.stack))

        for entry_a, entry_b in zip(self.stack, other.stack):
            if not entry_a.generic.mergeable(entry_b.generic):
                valid = False
                break

        for index in live_locals:
            entry_a, entry_b = self.locals[index], other.locals.get(index)
            if entry_b is None:
                raise MergeMissingLocalError(edge, index, entry_a.type)
            elif not entry_a.generic.mergeable(entry_b.generic):
                valid = False

        if not valid:
            return False

        for entry_a, entry_b in zip(self.stack, other.stack):
            # They are in a way, the same entry, which is why we're doing this.
            entry_a.merges.add(entry_b)
            entry_b.merges.add(entry_a)

        # It's useful to try this because it can actually provide extra insight into entries that would otherwise be
        # deemed "incorrect". When assembling, we don't really care about non-live locals as those will be written as 
        # tops anyway, but for more in-depth analysis this may be useful.
        if merge_non_live:
            for index in self.locals.keys() - live_locals:
                entry_a, entry_b = self.locals[index], other.locals.get(index)
                if entry_b is None or not entry_a.generic.mergeable(entry_b.generic):
                    continue
                entry_a.merges.add(entry_b)
                entry_b.merges.add(entry_a)
        else:
            for index in live_locals:
                entry_a, entry_b = self.locals[index], other.locals[index]
                entry_a.merges.add(entry_b)
                entry_b.merges.add(entry_a)

        return True

    # def add(self, delta: Delta) -> None:
    #     """
    #     Adds a frame delta to this frame, in place.
    #     """
    #
    #     if len(delta.pops) > len(self.stack):
    #         raise ValueError("Delta %r cannot be applied to frame %r." % (delta, self))
    #
    #     identities = {}
    #
    #     for index, entry in enumerate(delta.pops):
    #         actual = self.stack[-index]
    #         if actual == entry:
    #             continue
    #         elif type(entry) is Delta.Identity and (entry.expect is None or entry.expect == actual.type):
    #             identities[entry.id] = actual
    #             continue
    #         raise ValueError("Delta %r cannot be applied to frame %r." % (delta, self))
    #
    #     for index, old, new in delta.overwrites:
    #         actual = self.locals.get(index)
    #         if actual == old:
    #             continue
    #         elif type(old) is Delta.Identity and actual is not None and (old.expect is None or old.expect == actual.type):
    #             identities[old.id] = actual
    #             continue
    #         raise ValueError("Delta %r cannot be applied to frame %r." % (delta, self))
    #
    #     for entry in delta.pops:
    #         self.stack.pop()
    #
    #     for index, entry in enumerate(delta.pushes):
    #         if type(entry) is Delta.Identity:
    #             self.stack.append(identities[entry.id])
    #         else:
    #             self.stack.append(entry)
    #
    #     for index, old, new in delta.overwrites:
    #         if new is None:
    #             self.locals.pop(index)
    #         elif type(new) is Delta.Identity:
    #             self.locals[index] = identities[new.id]
    #         else:
    #             self.locals[index] = new
    #
    # def sub(self, delta: Delta) -> None:
    #     """
    #     Subtracts a frame delta from this frame, in place.
    #     """
    #
    #     if len(delta.pushes) > len(self.stack):
    #         raise ValueError("Delta %r cannot be applied to frame %r." % (delta, self))
    #
    #     identities = {}
    #
    #     for index, entry in enumerate(delta.pushes):
    #         actual = self.stack[-index]
    #         if actual == entry:
    #             continue
    #         elif type(entry) is Delta.Identity and (entry.expect is None or entry.expect == actual.type):
    #             identities[entry.id] = actual
    #             continue
    #         raise ValueError("Delta %r cannot be applied to frame %r." % (delta, self))
    #
    #     for index, old, new in delta.overwrites:
    #         actual = self.locals.get(index)
    #         if actual == new:
    #             continue
    #         elif type(new) is Delta.Identity and actual is not None and (new.expect is None or new.expect == actual.type):
    #             identities[new.id] = actual
    #             continue
    #         raise ValueError("Delta %r cannot be applied to frame %r." % (delta, self))
    #
    #     for entry in delta.pushes:
    #         self.stack.pop()
    #
    #     for entry in delta.pops:
    #         if type(entry) is Delta.Identity:
    #             self.stack.append(identities[entry.id])
    #         else:
    #             self.stack.append(entry)
    #
    #     for index, old, new in delta.overwrites:
    #         if old is None:
    #             self.locals.pop(index)
    #             continue
    #         elif type(old) is Delta.Identity:
    #             old = identities[old.id]
    #         else:
    #             self.locals[index] = old
    #
    # def delta(self, other: "Frame") -> Delta:
    #     """
    #     Calculates the delta between this frame and another.
    #
    #     :param other: The other frame.
    #     """
    #
    #     pushes = []
    #     pops = []
    #     overwrites = []
    #
    #     index = 0
    #     for index, (entry_a, entry_b) in enumerate(zip(self.stack, other.stack)):
    #         # Direct comparison because == checks for parents too, which may not be what we want in all cases
    #         if entry_a is not entry_b and entry_a != self.TOP and entry_b != self.TOP:
    #             break
    #
    #     for entry in self.stack[index:]:
    #         pops.append(entry)
    #     for entry in other.stack[index:]:
    #         pushes.append(entry)
    #
    #     for index, entry in other.locals.items():
    #         if not index in self.locals or entry != self.locals[index]:
    #             overwrites.append((index, self.locals.get(index), entry))
    #     for index, entry in self.locals.items():
    #         if not index in other.locals:
    #             overwrites.append((index, entry, None))
    #
    #     return Delta(pushes, pops, overwrites)

    # ------------------------------ Stack operations ------------------------------ #

    def push(self, entry: Entry) -> None:
        """
        Pushes an entry onto the top of the stack.

        :param entry: The entry to push.
        """

        self.stack.append(entry)
        self.tracked.add(entry)
        if len(self.stack) > self.max_stack:
            self.max_stack = len(self.stack)

    def pop(self, count: int = 1) -> list[Entry]:
        """
        Pops one or more entries from the stack.

        :param count: The number of entries to pop.
        """

        popped = []

        if count < len(self.stack):  # Optimisations?
            for index in range(count):
                popped.append(self.stack.pop())
            return popped

        popped.extend(reversed(self.stack))
        popped.extend(self.TOP for index in range(count - len(popped)))
        self.stack.clear()
        return popped

    def dup(self, count: int = 1, displace: int = 0) -> None:
        """
        Duplicates the top entry.

        :param count: The number of entries to duplicate.
        :param displace: How far back to displace the duplicated entries.
        """

        entries = self.stack[-count:]
        entries.extend(self.TOP for index in range(count - len(entries)))

        if not displace:
            self.stack.extend(entries)
            return
        for index, entry in enumerate(reversed(entries)):
            self.stack.insert(-count - displace - index, entry)

    def swap(self) -> None:
        """
        Swaps the top two entries.
        """

        if not self.stack:
            return
        elif len(self.stack) == 1:
            self.stack.append(self.TOP)
        self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

    # ------------------------------ Locals operations ------------------------------ #

    def set(self, index: int, entry: Entry) -> None:
        """
        Sets the local entry at a given index.

        :param index: The index of the local to set.
        :param entry: The entry to set it to.
        """

        # old = self.locals.get(index)
        # if old is not None:
        #     self.untracked.add(old)

        self.locals[index] = entry
        self.tracked.add(entry)
        index += 1
        if index > self.max_locals:
            self.max_locals = index

    def get(self, index: int) -> Entry:
        """
        :param index: The index of the local to get.
        """

        return self.locals.get(index, self.TOP)

    # ------------------------------ Classes ------------------------------ #

    class Parameter(Source):
        """
        Represents a parameter to a method.
        """

        __slots__ = ("index", "type", "method", "_hash")

        def __init__(self, index: int, type_: Type, method: Method) -> None:
            self.index = index
            self.type = type_
            self.method = method

            self._hash = hash((self.index, self.type, self.method))

        def __repr__(self) -> str:
            return "<Frame.Parameter(index=%i, type=%s, method=%s)>" % (self.index, self.type, self.method)

        def __str__(self) -> str:
            return "param %i of %s" % (self.index, self.method)

        def __eq__(self, other: Any) -> bool:
            return (
                type(other) is Frame.Parameter and
                self.method == other.method and
                self.index == other.index and
                self.type == other.type
            )

        def __hash__(self) -> int:
            return self._hash

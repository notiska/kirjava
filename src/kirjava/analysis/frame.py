#!/usr/bin/env python3

__all__ = (
    "Entry", "Frame",
)

"""
Stack frames (and others).
"""

import operator
import typing
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from .. import types
from ..abc import Method, Source
from ..error import MergeDepthError, MergeMissingLocalError
from ..types import null_t, object_t, Array, Class, Primitive, Type, Verification

if typing.TYPE_CHECKING:
    from .graph import InsnEdge


class Entry:
    """
    A type entry in a stack frame.
    """

    __slots__ = ("type", "consumers", "producers", "parents", "_constraints", "_constraints_cache")

    @property
    def constraints(self) -> FrozenSet["Entry.Constraint"]:
        """
        An immutable copy of all the constraints for this entry (also included via its parents). Should only be used
        after the trace has been computed.
        """

        if self._constraints_cache is not None:
            return self._constraints_cache

        constraints = self._constraints
        return self._collect_constraints(constraints, [])

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
    def _generify(cls, type_: Type, definite: bool) -> Tuple[Verification, Set[Type]]:
        vtype = type_.as_vtype()
        constraints = set()

        if not definite and (vtype is null_t or isinstance(vtype, Array) or isinstance(vtype, Class)):
            vtype = object_t
        if vtype != type_:
            constraints.add(type_)

        return vtype, constraints

    def __init__(
            self,
            type_: Type,
            origin: Optional[Source] = None,
            parent: Optional["Entry"] = None,
            *,
            definite: bool = False,
    ) -> None:
        """
        :param type_: The type of this entry.
        :param origin: The source that created this entry.
        :param parent: The parent entry.
        :param definite: If the provided type is a class, is it definitely that class?
        """

        self.type, constraints = self._generify(type_, definite)

        self.consumers: List[Source] = []
        self.producers: List[Source] = []
        self.parents: Set[Entry] = set()

        if origin is not None:
            self.producers.append(origin)
        if parent is not None:
            self.parents.add(parent)

        self._constraints = set(Entry.Constraint(constraint, origin) for constraint in constraints)
        self._constraints_cache: Optional[FrozenSet[Entry.Constraint]] = None

        # self._hash = hash((self.type, self.origin))

    def __repr__(self) -> str:
        return "<Entry(type=%s, constraints={%s}) at %x>" % (
            self.type, ", ".join(set(map(str, self.constraints))), id(self),
        )

    # def __eq__(self, other: Any) -> bool:
    #     return type(other) is Entry and self.type == other.type
    #
    # def __hash__(self) -> int:
    #     return self._hash

    def __str__(self) -> str:
        # if len(self.constraints) == 1:
        #     for constraint in self.constraints:
        #         return str(constraint)
        return str(self.type)

    def _collect_constraints(self, constraints: Set["Entry.Constraint"], stack: List["Entry"]) -> FrozenSet["Entry.Constraint"]:
        if self in stack:  # Can happen due to back edges.
            return self._constraints_cache
        stack.append(self)
        constraints.update(self._constraints)
        for parent in self.parents:
            parent._collect_constraints(constraints, stack)
        self._constraints_cache = frozenset(constraints)
        return self._constraints_cache

    def constrain(self, type_: Type, source: Optional[Source] = None) -> bool:
        """
        Adds a type constraint to this entry.

        :param type_: The type constraint.
        :param source: The source that constrained this entry's type.
        :return: Was this type already a constraint?
        """

        if type_ is self.type:  # TODO: Profile, faster?
            return True
        # https://stackoverflow.com/questions/27427067/python-how-to-check-if-an-item-was-added-to-a-set-without-2x-hash-lookup
        # Honestly not sure how much faster this is, but I'll give it a shot since I've been doing a similar thing with
        # dictionaries.
        constraint = Entry.Constraint(type_, source)
        length = len(self._constraints)
        self._constraints.add(constraint)
        return len(self._constraints) != length

    def cast(self, type_: Type, source: Optional[Source] = None) -> "Entry":
        """
        Casts this entry to another type.

        :param type_: The type to cast to.
        :param source: The source creating the new entry.
        """

        if type_ == self.type:
            return self

        # This can happen when for example, initialising an object. Uninitialised types are not mergeable with reference
        # types yet we still want to maintain a link to the original.
        if not self.type.mergeable(type_):
            return Entry(type_, source, self)
        # Primitive types also adhere to this behaviour simply because they are immutable by nature.
        elif isinstance(self.type, Primitive):
            return Entry(type_, source, self)
        # Otherwise, we know that this type is merely a constraint on the original type.
        self._constraints.add(Entry.Constraint(type_, source))
        return self

    class Constraint:
        """
        A type constraint with an optional source.
        """

        __slots__ = ("type", "source", "_hash")

        def __init__(self, type_: Type, source: Optional[Source] = None) -> None:
            self.type = type_
            self.source = source

            self._hash = hash((self.type, self.source))

        def __repr__(self) -> str:
            return "<Entry.Constraint(type=%s, source=%s)>" % (self.type, self.source)

        def __str__(self) -> str:
            return str(self.type)

        def __eq__(self, other: Any) -> bool:
            return type(other) is Entry.Constraint and self.type == other.type and self.source == other.source

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
#             overwrites: Iterable[Tuple[int, Optional[Union[Entry, "Delta.Identity"]], Optional[Union[Entry, "Delta.Identity"]]]],
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
#         def __init__(self, id_: int, expect: Optional[Type] = None) -> None:
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

    __slots__ = ("stack", "locals", "untracked", "max_stack", "max_locals")

    TOP      = Entry(types.top_t, definite=True)
    RESERVED = Entry(types.reserved_t, definite=True)

    @classmethod
    def initial(cls, method: Method) -> "Frame":
        """
        Creates the initial frame of a method, given the method.
        """

        frame = cls()
        index = 0

        if not method.is_static:
            if method.name == "<init>" and method.return_type == types.void_t:  # and method.class_.is_super:
                frame.locals[index] = Entry(types.uninitialized_this_t)
            else:
                frame.locals[0] = Entry(method.class_.get_type(), definite=True)
            index += 1

        for type_ in method.argument_types:
            frame.locals[index] = Entry(type_, definite=True)
            index += 1
            if type_.wide:
                frame.locals[index] = cls.RESERVED
                index += 1

        frame.max_locals = index

        return frame

    def __init__(self) -> None:
        self.stack: List[Entry] = []
        self.locals: Dict[int, Entry] = {}
        self.untracked: Set[Entry] = set()

        self.max_stack = 0
        self.max_locals = 0

    def __repr__(self) -> str:
        return "<Frame(stack=[%s], locals={%s}) at %x>" % (
            ", ".join(map(str, self.stack)),
            ", ".join("%i=%s" % (index, entry) for index, entry in sorted(self.locals.items(), key=operator.itemgetter(0))),
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
            frame.stack.extend(Entry(entry.type, None, entry, definite=True) for entry in self.stack)
            frame.locals.update({
                index: Entry(entry.type, None, entry, definite=True) for index, entry in self.locals.items()
            })
        else:
            frame.stack.extend(self.stack)
            frame.locals.update(self.locals)

        return frame

    def merge(self, other: "Frame", edge: "InsnEdge", live_locals: Optional[Set[int]] = None) -> bool:
        """
        Checks that this frame can merge with the other frame and if possible, merges it.

        :param other: The other frame to check against.
        :param edge: The edge causing the merge (for debug info).
        :param live_locals: Optional local liveness information. If not specified, all locals are checked.
        :return: Is this a valid merge?
        """

        invalid = False

        if live_locals is None:
            live_locals = self.locals.keys()

        # Basic preconditions checks to see if the frame merge is immediately invalid.
        if len(self.stack) != len(other.stack):
            raise MergeDepthError(edge, len(other.stack), len(self.stack))

        for entry_a, entry_b in zip(self.stack, other.stack):
            if not entry_a.type.mergeable(entry_b.type):
                invalid = True
                break

        for index in live_locals:
            entry_a, entry_b = self.locals[index], other.locals.get(index)
            if entry_b is None:
                raise MergeMissingLocalError(edge, index, entry_a.type)
            elif not entry_a.type.mergeable(entry_b.type):
                invalid = True

        if not invalid:
            for entry_a, entry_b in zip(self.stack, other.stack):
                # They are in a way, the same entry, which is why we're doing this.
                entry_a.parents.add(entry_b)
                entry_b.parents.add(entry_a)

            for index in live_locals:
                entry_a, entry_b = self.locals[index], other.locals[index]
                entry_a.parents.add(entry_b)
                entry_b.parents.add(entry_a)

        return not invalid

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
        if len(self.stack) > self.max_stack:
            self.max_stack = len(self.stack)

    def pop(self, count: int = 1) -> List[Entry]:
        """
        Pops one or more entries from the stack.

        :param count: The number of entries to pop.
        """

        popped = []

        try:
            for index in range(count):
                popped.append(self.stack.pop())
        except IndexError:
            for index in range(count - len(popped)):
                popped.append(self.TOP)

        self.untracked.update(popped)
        return popped

    def dup(self, count: int = 1, displace: int = 0) -> None:
        """
        Duplicates the top entry.

        :param count: The number of entries to duplicate.
        :param displace: How far back to displace the duplicated entries.
        """

        entries = self.stack[-count:]
        # Fill in any missing entries with tops
        for index in range(count - len(entries)):
            entries.append(self.TOP)

        if not displace:
            self.stack.extend(entries)
            return
        for index, entry in enumerate(reversed(entries)):
            self.stack.insert(-count - displace + index, entry)

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

        old = self.locals.get(index)
        if old is not None:
            self.untracked.add(old)

        self.locals[index] = entry
        index += 1
        if index > self.max_locals:
            self.max_locals = index

    def get(self, index: int) -> Entry:
        """
        :param index: The index of the local to get.
        """

        return self.locals.get(index, self.TOP)

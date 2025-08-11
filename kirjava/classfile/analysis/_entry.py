#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Entry",
)

import typing
from copy import copy
from typing import Any, Optional, Generic

from ..._compat import Self, TypeVar
from ...backend import Result
from ...model.types import object_t, Reference, Type, Uninitialized, Verification
from ...model.values import Constant, Value

if typing.TYPE_CHECKING:
    from ..insns import Instruction


# T = TypeVar("T", bound=Constant[Any])
#
#
# class Range(Generic[T], Constraint):
#     """
#     A range constraint for numeric types.
#
#     Specifies that the numeric value of an entry must fall within this range.
#
#     Attributes
#     ----------
#     upper: T
#         The upper bound of the range.
#     lower: T
#         The lower bound of the range.
#     """
#
#     __slots__ = ("_upper", "_lower", "_hash")
#
#     @property
#     def upper(self) -> T:
#         return self._upper
#
#     @property
#     def lower(self) -> T:
#         return self._lower
#
#     def __init__(self, upper: T, lower: T) -> None:
#         self._upper = upper
#         self._lower = lower
#         self._hash = hash((Range, upper, lower))
#
#     def __repr__(self) -> str:
#         return f"<Range(upper={self._upper!s}, lower={self._lower!s})>"
#
#     def __str__(self) -> str:
#         return f"range({self._lower!s},{self._upper!s})"
#
#     def __eq__(self, other: object) -> bool:
#         return isinstance(other, Range) and self._upper == other._upper and self._lower == other._lower
#
#     def __hash__(self) -> int:
#         return self._hash
#
#     def add(self, value: T) -> Result["Range[T]"]:
#         """
#         Creates a new range constraint, given a certain value being added to the
#         entry.
#
#         Parameters
#         ----------
#         value: T
#             The value to add to the range.
#
#         Returns
#         -------
#         Result[Range[T]]
#             The new range constraint.
#         """
#
#         with Result[Range[T]].meta(__name__) as result:
#             upper = self._upper + value
#             lower = self._lower + value
#             if upper < lower:
#                 result.debug("Upper bound overflows lower bound after addition.")
#                 upper, lower = lower, upper  # FIXME: True, false?
#             return result.ok(Range(upper, lower))
#         return result
#
#     def sub(self, value: T) -> Result["Range[T]"]:
#         """
#         Creates a new range constraint, given a certain value being subtracted from
#         the entry.
#
#         Parameters
#         ----------
#         value: T
#             The value to subtract from the range.
#
#         Returns
#         -------
#         Result[Range[T]]
#             The new range constraint.
#         """
#
#         with Result[Range[T]].meta(__name__) as result:
#             upper = self._upper - value
#             lower = self._lower - value
#             if upper < lower:
#                 result.debug("Lower bound underflows upper bound after subtraction.")
#                 upper, lower = lower, upper
#             return result.ok(Range(upper, lower))
#         return result


class Entry:
    """
    An entry on either the operand stack or in the local variable array.

    Attributes
    ----------
    type: Verification
        The type of this entry.
    insn: Instruction | None
        The instruction that created this entry, or `None` if unknown.
    lodword: bool
        Whether this represents the low DWORD of a wide type.
    split: bool
        Whether this entry has been split from a wide type.
    narrow: bool
        Whether this entry is narrowly typed (only applicable for reference types).
    parent: Entry | None
        The parent of this entry, or `None` if this entry has no parent.
        Used for determining the source of an entry that has been cast.
    adjacent: frozenset[Entry]
        Other entries that are adjacent to this one.
        Adjacent entries are essentially the same as this one, but have been created
        from merged jump sites, etc.
    value: Value | None
        The value of this entry, or `None` if unknown.
    escapes: set[Instruction]
        Instructions where this entry escapes the method.
    conflicts: set[Entry.Conflict]
        Collected type conflicts for this entry.
    hints: set[Entry.Hint]
        Collected type hints for this entry.
    constraints: set[Entry.Constraint]
        Collected type constraints for this entry.
    """

    __slots__ = (
        "_type", "_insn", "_lodword", "split", "_narrow",
        "_parent", "_adjacent", "value",
        "escapes", "conflicts", "hints", "constraints",
    )

    @property
    def type(self) -> Verification:
        return self._type

    @property
    def insn(self) -> Optional["Instruction"]:
        return self._insn

    @property
    def lodword(self) -> bool:
        return self._lodword

    @property
    def narrow(self) -> bool:
        return self._narrow

    @property
    def parent(self) -> Optional["Entry"]:
        return self._parent

    def __init__(self, type: Type, insn: Optional["Instruction"] = None, *, lodword: bool = False) -> None:
        self._type = type.verification()
        self._insn = insn
        self._lodword = lodword
        self.split = False
        self._narrow = True

        self._parent: Entry | None = None
        self._adjacent: set[Entry] = set()

        self.value: Value | None = None

        self.escapes: set["Instruction"] = set()

        self.conflicts:     set[Entry.Conflict] = set()
        self.hints:             set[Entry.Hint] = set()
        self.constraints: set[Entry.Constraint] = set()
        # TODO: Value constraints.

    def __copy__(self) -> "Entry":
        copied = Entry(self._type, self._insn, lodword=self._lodword)

        # Copying only the "essential" information across.
        copied.split = self.split
        copied._narrow = self._narrow
        copied._parent = self._parent
        copied._adjacent.add(self)
        copied.value = self.value
        # copied.escapes.update(self.escapes)

        return copied

    def __repr__(self) -> str:
        return f"<Entry(type={self._type!s}, value={self.value!s}, lodword={self._lodword}, narrow={self._narrow})>"

    def __str__(self) -> str:
        string = str(self.value) if isinstance(self.value, Constant) else str(self._type)
        if not self._narrow:  # Broadened types will not be primitives, by nature.
            return f"broad({string})"
        elif not self._type.wide:
            return string
        elif self._lodword:
            return f"lodword({string})"
        else:
            return f"hidword({string})"

    def copy(self) -> "Entry":
        """
        Creates a copy of this entry.
        """

        return copy(self)

    def broaden(self) -> "Entry":
        """
        Creates a broadened copy of this entry, if applicable.

        Only initialised reference types will be broadened. In any other case, a
        copy of this entry will be returned.

        Returns
        -------
        Entry
            Either a copy of this entry or the broadened copy of this entry.
        """

        if (
            not self._narrow or  # Already broadened type.
            not isinstance(self._type, Reference) or
            self._type == object_t or
            isinstance(self._type, Uninitialized)
        ):
            entry = self.copy()
            entry.value = None
            return entry

        entry = Entry(object_t)

        entry._narrow = False
        entry._adjacent.add(self)
        # entry.escapes.update(self.escapes)
        # entry.constraints.add(Entry.Constraint(self.type, self.source))

        return entry

    def cast(self, type: Type, insn: Optional["Instruction"] = None) -> "Entry":
        """
        Casts this entry to a different type.

        Parameters
        ----------
        type: Type
            The type to cast the entry to.
        insn: Instruction | None
            The instruction responsible for the type cast.

        Returns
        -------
        Entry
            The type casted entry.
        """

        if self._type == type:
            return self

        entry = Entry(type, insn)
        entry._parent = self
        if self._type.assignable(type):
            self.constraints.add(Entry.Constraint(entry._type, insn))
        return entry

    def constrain(self, type: Type, insn: Optional["Instruction"] = None) -> Result["Entry"]:
        """
        Adds a type constraint to this entry.

        Parameters
        ----------
        type: Type
            The type constraint to add.
        insn: Instruction | None
            The instruction responsible for the type constraint.

        Returns
        -------
        Result[Entry]
            Either this entry or a new one with the correct type, if the current
            type does not fall within the specified type bound.
        """

        with Result["Entry"]() as result:
            if self._type == type:
                return result.ok(self)
            elif not type.assignable(self._type):
                result.err(TypeError(f"{self._type!s} is not assignable to {type!s}"))
                entry = Entry(type, insn)
                entry._parent = self
                self.conflicts.add(Entry.Conflict(entry, type, insn))
                # print(self, type_)
                # raise Exception()
                return result.ok(entry)

            # We won't add abstract types as constraints if we know that the current type of this entry already satisfies
            # said constraint because they don't add any more typing information.
            if not type.abstract:
                self.constraints.add(Entry.Constraint(type.verification(), insn))
            return result.ok(self)
        return result

    def hint(self, type: Type, insn: Optional["Instruction"] = None) -> None:
        """
        Adds a type hint to this entry.

        Parameters
        ----------
        type: Type
            The type hint to add.
        instruction: Instruction | None
            The instruction providing the type hint.
        """

        if self._type == type:
            return
        self.hints.add(Entry.Hint(type, insn))

    # ------------------------------ Classes ------------------------------ #

    class Conflict:
        """
        Information about a type conflict.

        Attributes
        ----------
        entry: Entry
            The resulting entry with the correct type, created due to this type conflict.
        type: Type
            The expected type of the entry.
        insn: Instruction | None
            The instruction that caused this type conflict, or `None` if unknown.
        """

        __slots__ = ("_entry", "_type", "_insn", "_hash")

        @property
        def entry(self) -> "Entry":
            return self._entry

        @property
        def type(self) -> Type:
            return self._type

        @property
        def insn(self) -> Optional["Instruction"]:
            return self._insn

        def __init__(self, entry: "Entry", type: Type, insn: Optional["Instruction"]) -> None:
            self._entry = entry
            self._type = type
            self._insn = insn
            self._hash = hash((entry, type))

        def __repr__(self) -> str:
            if self._insn is not None:
                return f"<Entry.Conflict(entry={self._entry!r}, type={self._type!s}, insn={self._insn!s})>"
            return f"<Entry.Conflict(entry={self._entry!r}, type={self._type!s})>"

        def __str__(self) -> str:
            return f"conflict({self._entry!s},{self._type!s})"

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Entry.Conflict) and self._entry == other._entry and self._type == other._type

        def __hash__(self) -> int:
            return self._hash

    class Hint:
        """
        A type hint.

        Specifies that an entry's type could be this type.

        Attributes
        ----------
        type: Type
            The type hint.
        insn: Instruction | None
            The instruction that added the type hint, or `None` if unknown.
        """

        __slots__ = ("_type", "_insn", "_hash")

        @property
        def type(self) -> Type:
            return self._type

        @property
        def insn(self) -> Optional["Instruction"]:
            return self._insn

        def __init__(self, type: Type, insn: Optional["Instruction"]) -> None:
            self._type = type
            self._insn = insn
            self._hash = hash(type)

        def __repr__(self) -> str:
            if self._insn is not None:
                return f"<Entry.Hint(type={self._type!s}, insn={self._insn!s})>"
            return f"<Entry.Hint(type={self._type!s})>"

        def __str__(self) -> str:
            return f"hint({self._type!s})"

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Entry.Hint) and self._type == other._type

        def __hash__(self) -> int:
            return self._hash

    class Constraint:
        """
        Information about a type constraint.

        Attributes
        ----------
        type: Verification
            The type constraint.
        insn: Instruction | None
            The instruction that added the type constraint, or `None` if unknown.
        """

        __slots__ = ("_type", "_insn", "_hash")

        @property
        def type(self) -> Verification:
            return self._type

        @property
        def insn(self) -> Optional["Instruction"]:
            return self._insn

        def __init__(self, type: Verification, insn: Optional["Instruction"]) -> None:
            self._type = type
            self._insn = insn
            self._hash = hash(type)

        def __repr__(self) -> str:
            if self._insn is not None:
                return f"<Entry.Constraint(type={self._type!s}, insn={self._insn!s})>"
            return f"<Entry.Constraint(type={self._type!s})>"

        def __str__(self) -> str:
            return f"constraint({self._type!s})"

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Entry.Constraint) and self._type == other._type

        def __hash__(self) -> int:
            return self._hash

        # class Type(Enum):
        #     """
        #     The type of bound represented.
        #     """

        #     UPPER   = "upper"
        #     LOWER   = "lower"
        #     UNKNOWN = "unknown"

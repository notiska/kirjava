#!/usr/bin/env python3

__all__ = (
    "Frame",
)

import typing
from operator import itemgetter
from typing import Iterable, Mapping, Optional

from ..._compat import Self
from ...backend import Err, Ok, Result

if typing.TYPE_CHECKING:
    from ..graph import Block
    from ...model.types import Verification


class Frame:
    """
    A basic execution frame.

    Only stores the bare minimum needed for verifying code as valid.

    Attributes
    ----------
    stack: list[Verification]
        All verification types on the stack.
    locals: dict[int, Verification]
        All verification types in the local variable array.

    Methods
    -------
    pop(self, expect: Verification) -> Result[Verification]
        Pops the item off the top of the stack.
    push(self, value: Verification) -> None
        Pushes an item on to the top of the stack.
    get(self, local: int, expect: Verification) -> Result[Verification]
        Gets an item from the local variable array.
    set(self, local: int, item: Verification) -> None
        Sets an item in the local variable array.
    rget(self, local: int, expect: Verification) -> None
        "Reverse gets" an item in the local variable array.
    rset(self, local: int, expect: Verification) -> None
        "Reverse sets" an item in the local variable array.
    dup(self) -> Result[Self]
        Duplicates the item on the top of the stack.
    dup_x1(self) -> Result[Self]
    dup_x2(self) -> Result[Self]
    dup2(self) -> Result[Self]
        Duplicates the two items on the top of the stack.
    dup2_x1(self) -> Result[Self]
    dup2_x2(self) -> Result[Self]
    rdup(self) -> Result[Self]
    rdup_x1(self) -> Result[Self]
    rdup_x2(self) -> Result[Self]
    rdup2(self) -> Result[Self]
    rdup2_x1(self) -> Result[Self]
    rdup2_x2(self) -> Result[Self]
    swap(self) -> Result[Self]
        Swaps the two items on the top of the stack.
    """

    __slots__ = ("stack", "locals")

    def __init__(
            self, stack: Iterable["Verification"] | None = None,
            locals_: Mapping[int, "Verification"] | None = None,
    ) -> None:
        self.stack: list["Verification"] = []
        self.locals: dict[int, "Verification"] = {}

        if stack is not None:
            self.stack.extend(stack)
        if locals_ is not None:
            self.locals.update(locals_)

    def __repr__(self) -> str:
        stack_str = ", ".join(map(str, self.stack))
        locals_str = ", ".join(f"{index}: {type_!s}" for index, type_ in sorted(self.locals.items(), key=itemgetter(0)))
        return f"<Frame(stack=[{stack_str}], locals={{{locals_str}}})>"

    def __str__(self) -> str:
        stack_str = ",".join(map(str, self.stack))
        locals_str = ",".join(f"{index}={type_!s}" for index, type_ in sorted(self.locals.items(), key=itemgetter(0)))
        return f"frame([{stack_str}],{{{locals_str}}})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Frame) and
            self.stack == other.stack and
            self.locals == other.locals
        )

    def pop(self, expect: "Verification") -> Result["Verification"]:
        """
        Pops the item off the top of the stack.

        Parameters
        ----------
        expect: Verification
            The type that is expected to be on the top of the stack.
        """

        if self.stack:
            item = self.stack.pop()
            if not expect.assignable(item):
                return Err(TypeError(f"{item!s} is not assignable to {expect!s}"))
            return Ok(item)
        return Err(IndexError("pop from empty stack"))

    def push(self, item: "Verification") -> None:
        """
        Pushes an item on to the top of the stack.
        """

        self.stack.append(item)

    def get(self, index: int, expect: "Verification") -> Result["Verification"]:
        """
        Gets an item from the local variable array.

        Parameters
        ----------
        index: int
            The local variable array index to get.
        expect: Verification
            The type that is expected to be in the local variable slot.
        """

        item = self.locals.get(index)
        if item is not None:
            if not expect.assignable(item):
                return Err(TypeError(f"{item!s} is not assignable to {expect!s}"))
            return Ok(item)
        return Err(IndexError(f"local index {index} empty"))

    def set(self, index: int, item: "Verification") -> None:
        """
        Sets an item in the local variable array.
        """

        self.locals[index] = item

    def rget(self, index: int, expect: "Verification") -> None:
        """
        "Reverse gets" an item in the local variable array.

        Sets the item in the provided local slot if, and only if, it is not
        assignable to the expected type, or empty.

        Parameters
        ----------
        index: int
            The local variable array index to "reverse get".
        expect: Verification
            The type that is expected to be in the local variable slot.
            If the item is not assignable to this type, this type becomes the item.
        """

        item = self.locals.get(index)
        if item is None or not expect.assignable(item):
            self.locals[index] = expect

    def rset(self, index: int, expect: "Verification") -> None:
        """
        "Reverse sets" an item in the local variable array.

        Removes the item in the provided local index slot, if it matches the
        expected type.
        Naturally, it is lossy to reverse the `set()` operation.

        Parameters
        ----------
        index: int
            The local variable array index to "reverse set".
        expect: Verification
            The type that is expected to be in the local variable slot.
        """

        item = self.locals.get(index)
        if item is not None and expect.assignable(item):
            del self.locals[index]

    def dup(self) -> Result[Self]:
        """
        Duplicates the top item on the stack.
        """

        raise NotImplementedError()

    def dup_x1(self) -> Result[Self]:
        raise NotImplementedError()

    def dup_x2(self) -> Result[Self]:
        raise NotImplementedError()

    def dup2(self) -> Result[Self]:
        """
        Duplicates the two items on the top of the stack.
        """

        raise NotImplementedError()

    def dup2_x1(self) -> Result[Self]:
        raise NotImplementedError()

    def dup2_x2(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup_x1(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup_x2(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup2(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup2_x1(self) -> Result[Self]:
        raise NotImplementedError()

    def rdup2_x2(self) -> Result[Self]:
        raise NotImplementedError()

    def swap(self) -> Result[Self]:
        """
        Swaps the two items on the top of the stack.
        """

        raise NotImplementedError()

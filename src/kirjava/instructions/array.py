#!/usr/bin/env python3

__all__ = (
    "ArrayLoadInstruction", "ArrayStoreInstruction", "ArrayLengthInstruction",
)

"""
Instructions related to arrays.
"""

import typing

from . import Instruction
from ..types import array_t, int_t, Array, Class

if typing.TYPE_CHECKING:
    from ..analysis import Context


class ArrayLoadInstruction(Instruction):
    """
    Loads a value from an array.
    """

    __slots__ = ()

    throws = (
        Class("java/lang/ArrayIndexOutOfBoundsException"),
        Class("java/lang/NullPointerException"),
    )

    type: Array = ...

    def trace(self, context: "Context") -> None:
        context.constrain(context.pop(), int_t)
        context.constrain(context.pop(), self.type)
        entry = context.push(self.type.element.as_vtype())
        context.constrain(entry, self.type.element, original=True)


class ArrayStoreInstruction(Instruction):
    """
    Stores a value in an array.
    """

    __slots__ = ()

    throws = (
        Class("java/lang/ArrayIndexOutOfBoundsException"),
        Class("java/lang/ArrayStoreException"),
        Class("java/lang/NullPointerException"),
    )

    type: Array = ...

    def trace(self, context: "Context") -> None:
        *_, entry = context.pop(1 + self.type.element.wide, as_tuple=True)
        context.constrain(entry, self.type.element)
        context.constrain(context.pop(), int_t)
        context.constrain(context.pop(), self.type)


class ArrayLengthInstruction(Instruction):
    """
    Gets the length of an array.
    """

    __slots__ = ()

    throws = (Class("java/lang/NullPointerException"),)

    def trace(self, context: "Context") -> None:
        context.constrain(context.pop(), array_t)
        context.push(int_t)

#!/usr/bin/env python3

__all__ = (
    "UnaryOperationInstruction", "BinaryOperationInstruction", "ComparisonInstruction",
    "AdditionInstruction", "SubtractionInstruction", "MultiplicationInstruction", "DivisionInstruction", "RemainderInstruction",
    "NegationInstruction",
    "ShiftLeftInstruction", "ShiftRightInstruction", "UnsignedShiftRightInstruction",
    "BitwiseAndInstruction", "BitwiseOrInstruction", "BitwiseXorInstruction",
)

"""
Arithmetic related instructions.
"""

import typing

from . import Instruction
from .. import types
from ..abc import Constant
from ..types import Type, Verification

if typing.TYPE_CHECKING:
    from ..analysis import Context


class UnaryOperationInstruction(Instruction):
    """
    A unary arithmetic operation.
    """

    __slots__ = ()

    type: Verification = ...

    def trace(self, context: "Context") -> None:
        *_, entry = context.pop(1 + self.type.wide, as_tuple=True)
        context.constrain(entry, self.type)
        context.push(entry, self.type)


class BinaryOperationInstruction(Instruction):
    """
    A binary arithmetic operation.
    """

    __slots__ = ()

    type_a: Verification = ...
    type_b: Verification = ...

    def trace(self, context: "Context") -> None:
        *_, entry_a = context.pop(1 + self.type_a.wide, as_tuple=True)
        context.constrain(entry_a, self.type_a)
        *_, entry_b = context.pop(1 + self.type_b.wide, as_tuple=True)
        context.constrain(entry_b, self.type_b)

        context.push(self.type_b)


class ComparisonInstruction(BinaryOperationInstruction):
    """
    Compares two values on the stack.
    """

    type: Verification = ...

    def trace(self, context: "Context") -> None:
        *_, entry_a = context.pop(1 + self.type.wide, as_tuple=True)
        context.constrain(entry_a, self.type)
        *_, entry_b = context.pop(1 + self.type.wide, as_tuple=True)
        context.constrain(entry_b, self.type)

        context.push(types.int_t)


class AdditionInstruction(BinaryOperationInstruction):
    """
    Adds two values.
    """

    ...


class SubtractionInstruction(BinaryOperationInstruction):
    """
    Subtracts two values.
    """

    ...


class MultiplicationInstruction(BinaryOperationInstruction):
    """
    Multiplies two values.
    """

    ...


class DivisionInstruction(BinaryOperationInstruction):
    """
    Divides two values.
    """

    ...


class RemainderInstruction(BinaryOperationInstruction):
    """
    Gets the module of the first value by the second.
    """

    ...


class NegationInstruction(UnaryOperationInstruction):
    """
    Negates a value.
    """

    ...


class ShiftLeftInstruction(BinaryOperationInstruction):
    """
    Shifts the first value left by the second.
    """

    ...


class ShiftRightInstruction(BinaryOperationInstruction):
    """
    Shifts the first value right by the second.
    """

    ...


class UnsignedShiftRightInstruction(BinaryOperationInstruction):
    """
    Shifts the first value right by the second, does not conserve the sign.
    """

    ...


class BitwiseAndInstruction(BinaryOperationInstruction):
    """
    The bitwise and of two values.
    """

    ...


class BitwiseOrInstruction(BinaryOperationInstruction):
    """
    The bitwise or of two values.
    """

    ...


class BitwiseXorInstruction(BinaryOperationInstruction):
    """
    The bitwise xor of two values.
    """

    ...

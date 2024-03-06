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

    def apply(self, value_a: Constant, value_b: Constant) -> Constant | None:
        ...  # TODO


class AdditionInstruction(BinaryOperationInstruction):
    """
    Adds two values.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = AdditionExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class SubtractionInstruction(BinaryOperationInstruction):
    """
    Subtracts two values.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = SubtractionExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class MultiplicationInstruction(BinaryOperationInstruction):
    """
    Multiplies two values.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = MultiplicationExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class DivisionInstruction(BinaryOperationInstruction):
    """
    Divides two values.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = DivisionExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class RemainderInstruction(BinaryOperationInstruction):
    """
    Gets the module of the first value by the second.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = ModuloExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class NegationInstruction(UnaryOperationInstruction):
    """
    Negates a value.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = NegationExpression(associations[delta.pops[-1]])
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class ShiftLeftInstruction(BinaryOperationInstruction):
    """
    Shifts the first value left by the second.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = ShiftLeftExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class ShiftRightInstruction(BinaryOperationInstruction):
    """
    Shifts the first value right by the second.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = ShiftRightExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class UnsignedShiftRightInstruction(BinaryOperationInstruction):
    """
    Shifts the first value right by the second, does not conserve the sign.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = UnsignedShiftRightExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class BitwiseAndInstruction(BinaryOperationInstruction):
    """
    The bitwise and of two values.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = BitwiseAndExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class BitwiseOrInstruction(BinaryOperationInstruction):
    """
    The bitwise or of two values.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = BitwiseOrExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)


class BitwiseXorInstruction(BinaryOperationInstruction):
    """
    The bitwise xor of two values.
    """

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry, = delta.pushes
    #     if entry.value is None:
    #         associations[entry] = BitwiseXorExpression(
    #             associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
    #         )
    #     else:
    #         associations[entry] = ConstantValue(entry.value)

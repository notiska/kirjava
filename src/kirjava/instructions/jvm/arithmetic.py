#!/usr/bin/env python3

"""
Arithmetic related instructions.
"""

from typing import Dict, Union

from . import Instruction
from ..ir.arithmetic import (
    AdditionExpression, BitwiseAndExpression, BitwiseOrExpression,
    BitwiseXorExpression, DivisionExpression, ModuloExpression,
    MultiplicationExpression, NegationExpression, ShiftLeftExpression,
    ShiftRightExpression, SubtractionExpression, UnsignedShiftRightExpression,
)
from ... import types
from ...abc import Constant, Value
from ...analysis.ir.variable import Scope
from ...analysis.trace import Entry, Frame, FrameDelta
from ...instructions.ir.value import ConstantValue
from ...types import BaseType


class UnaryOperationInstruction(Instruction):
    """
    A unary arithmetic operation.
    """

    type_: BaseType = ...

    def trace(self, frame: Frame) -> None:
        *_, entry = frame.pop(self.type_.internal_size, tuple_=True, expect=self.type_)
        frame.push(frame.verifier.checker.merge(self.type_, entry.type))


class BinaryOperationInstruction(Instruction):
    """
    A binary arithmetic operation.
    """

    type_a: BaseType = ...
    type_b: BaseType = ...

    def trace(self, frame: Frame) -> None:
        entry_a, *_ = frame.pop(self.type_a.internal_size, tuple_=True, expect=self.type_a)
        entry_b, *_ = frame.pop(self.type_b.internal_size, tuple_=True, expect=self.type_b)
        frame.push(self.type_b)


class ComparisonInstruction(BinaryOperationInstruction):
    """
    Compares two values on the stack.
    """

    def trace(self, frame: Frame) -> None:
        entry_a, *_ = frame.pop(self.type_.internal_size, tuple_=True, expect=self.type_)
        entry_b, *_ = frame.pop(self.type_.internal_size, tuple_=True, expect=self.type_)
        frame.push(types.int_t)

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        ...  # TODO


class AdditionInstruction(BinaryOperationInstruction):
    """
    Adds two values.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = AdditionExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)


class SubtractionInstruction(BinaryOperationInstruction):
    """
    Subtracts two values.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = SubtractionExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)


class MultiplicationInstruction(BinaryOperationInstruction):
    """
    Multiplies two values.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = MultiplicationExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)


class DivisionInstruction(BinaryOperationInstruction):
    """
    Divides two values.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = DivisionExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)


class RemainderInstruction(BinaryOperationInstruction):
    """
    Gets the module of the first value by the second.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = ModuloExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)


class NegationInstruction(UnaryOperationInstruction):
    """
    Negates a value.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = NegationExpression(associations[delta.pops[-1]])
        else:
            associations[entry] = ConstantValue(entry.value)


class ShiftLeftInstruction(BinaryOperationInstruction):
    """
    Shifts the first value left by the second.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = ShiftLeftExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)


class ShiftRightInstruction(BinaryOperationInstruction):
    """
    Shifts the first value right by the second.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = ShiftRightExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)


class UnsignedShiftRightInstruction(BinaryOperationInstruction):
    """
    Shifts the first value right by the second, does not conserve the sign.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = UnsignedShiftRightExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)


class BitwiseAndInstruction(BinaryOperationInstruction):
    """
    The bitwise and of two values.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = BitwiseAndExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)


class BitwiseOrInstruction(BinaryOperationInstruction):
    """
    The bitwise or of two values.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = BitwiseOrExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)


class BitwiseXorInstruction(BinaryOperationInstruction):
    """
    The bitwise xor of two values.
    """

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry, = delta.pushes
        if entry.value is None:
            associations[entry] = BitwiseXorExpression(
                associations[delta.pops[-1]], associations[delta.pops[-(1 + self.type_b.internal_size)]],
            )
        else:
            associations[entry] = ConstantValue(entry.value)

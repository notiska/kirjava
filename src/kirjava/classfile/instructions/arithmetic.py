#!/usr/bin/env python3

"""
Arithmetic related instructions.
"""

from abc import abstractmethod, ABC
from typing import Dict, List, Union

from . import Instruction
from ... import types
from ...abc import Constant, Source, TypeChecker, Value
from ...analysis.ir.arithmetic import (
    AdditionExpression, BitwiseAndExpression, BitwiseOrExpression,
    BitwiseXorExpression, DivisionExpression, ModuloExpression,
    MultiplicationExpression, NegationExpression, ShiftLeftExpression,
    ShiftRightExpression, SubtractionExpression, UnsignedShiftRightExpression,
)
from ...analysis.trace import Entry, State
from ...types import BaseType
from ...verifier import Error


class UnaryOperationInstruction(Instruction, ABC):
    """
    A unary arithmetic operation.
    """

    type_: BaseType = ...

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry, *_ = state.pop(source, self.type_.internal_size, tuple_=True)
        if not checker.check_merge(self.type_, entry.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected type %s" % self.type_, "got %s (via %s)" % (entry.type, entry.source),
            ))

        if entry.value is None:
            value = None
        else:
            value = self.apply(entry.value)

        state.push(source, checker.merge(self.type_, entry.type), value, parents=(entry,))

    @abstractmethod
    def apply(self, value: Constant) -> Union[Constant, None]:
        """
        Applies this instruction to any absolute values on the stack.

        :param value: The value on the stack.
        :return: The new computed result, or None if it could not be computed.
        """

        ...


class BinaryOperationInstruction(Instruction, ABC):
    """
    A binary arithmetic operation.
    """

    type_a: BaseType = ...
    type_b: BaseType = ...

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry_a, *_ = state.pop(source, self.type_a.internal_size, tuple_=True)
        entry_b, *_ = state.pop(source, self.type_b.internal_size, tuple_=True)

        valid = entry_b.type
        if not checker.check_merge(self.type_b, entry_b.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected type %s" % self.type_b, "got %s (via %s)" % (entry_b.type, entry_b.source),
            ))
            valid = entry_a.type
        if not checker.check_merge(self.type_a, entry_a.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected type %s" % self.type_a, "got %s (via %s)" % (entry_a.type, entry_a.source),
            ))
            valid = self.type_b  # Just resort to what we should expect it to be at this point

        value_a = entry_b.value  # Yes, technically the other way around
        value_b = entry_a.value

        if value_a is None or value_b is None:
            value = None
        elif value_a.__class__ != value_b.__class__:
            value = None
        else:
            value = self.apply(value_a, value_b)

        state.push(source, checker.merge(self.type_b, valid), value, parents=(entry_a, entry_b))

    @abstractmethod
    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        """
        Applies the arithmetic operation to the two values on the stack.

        :param value_a: The first value.
        :param value_b: The second value.
        :return: The computed constant, or None if it could not be computed.
        """

        ...


class ComparisonInstruction(BinaryOperationInstruction, ABC):
    """
    Compares two values on the stack.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry_a, *_ = state.pop(source, self.type_.internal_size, tuple_=True)
        entry_b, *_ = state.pop(source, self.type_.internal_size, tuple_=True)

        if not checker.check_merge(self.type_, entry_a.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected type %s" % self.type_, "got %s (via %s)" % (entry_a.type, entry_a.source),
            ))
        if not checker.check_merge(self.type_, entry_b.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected type %s" % self.type_, "got %s (via %s)" % (entry_b.type, entry_b.source),
            ))

        state.push(source, types.int_t, parents=(entry_a, entry_b))

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        ...  # TODO


class AdditionInstruction(BinaryOperationInstruction):
    """
    Adds two values.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = AdditionExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        return value_a + value_b


class SubtractionInstruction(BinaryOperationInstruction):
    """
    Subtracts two values.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = SubtractionExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        return value_a - value_b


class MultiplicationInstruction(BinaryOperationInstruction):
    """
    Multiplies two values.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = MultiplicationExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        return value_a * value_b


class DivisionInstruction(BinaryOperationInstruction):
    """
    Divides two values.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = DivisionExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        try:
            return value_a / value_b
        except ZeroDivisionError:
            return None


class RemainderInstruction(BinaryOperationInstruction):
    """
    Gets the module of the first value by the second.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = ModuloExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        try:
            return value_a % value_b
        except ZeroDivisionError:
            return None


class NegationInstruction(UnaryOperationInstruction):
    """
    Negates a value.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = NegationExpression(associations[pre.stack[-1]])

    def apply(self, value: Constant) -> Union[Constant, None]:
        return -value


class ShiftLeftInstruction(BinaryOperationInstruction):
    """
    Shifts the first value left by the second.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = ShiftLeftExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        return value_a << value_b


class ShiftRightInstruction(BinaryOperationInstruction):
    """
    Shifts the first value right by the second.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = ShiftRightExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        return value_a >> value_b


class UnsignedShiftRightInstruction(BinaryOperationInstruction):
    """
    Shifts the first value right by the second, does not conserve the sign.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = UnsignedShiftRightExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        return value_a >> value_b  # FIXME


class BitwiseAndInstruction(BinaryOperationInstruction):
    """
    The bitwise and of two values.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = BitwiseAndExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        return value_a & value_b


class BitwiseOrInstruction(BinaryOperationInstruction):
    """
    The bitwise or of two values.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = BitwiseOrExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        return value_a | value_b


class BitwiseXorInstruction(BinaryOperationInstruction):
    """
    The bitwise xor of two values.
    """

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = BitwiseXorExpression(
            associations[pre.stack[-(1 + self.type_b.internal_size)]], associations[pre.stack[-1]],
        )

    def apply(self, value_a: Constant, value_b: Constant) -> Union[Constant, None]:
        return value_a ^ value_b

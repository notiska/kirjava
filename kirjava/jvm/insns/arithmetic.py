#!/usr/bin/env python3

__all__ = (
    "iadd", "ladd", "fadd", "dadd",
    "isub", "lsub", "fsub", "dsub",
    "imul", "lmul", "fmul", "dmul",
    "idiv", "ldiv", "fdiv", "ddiv",
    "irem", "lrem", "frem", "drem",
    "ineg", "lneg", "fneg", "dneg",
    "ishl", "lshl", "ishr", "lshr", "iushr", "lushr",
    "iand", "land", "ior", "lor", "ixor", "lxor",
    "lcmp", "fcmpl", "fcmpg", "dcmpl", "dcmpg",
    "BinOp", "Shift", "Comparison",
    "Addition", "Subtraction", "Multiplication", "Division", "Remainder", "Negate",
    "ShiftLeft", "ShiftRight", "ShiftRightUnsigned",
    "BitwiseAnd", "BitwiseOr", "BitwiseXor",
    "IntegralCompare", "FloatLCompare", "FloatGCompare",
)

import typing
from typing import IO

from . import Instruction
from ...model.types import *
# from ...model.values import Value
# from ...model.values.constants import Integer

if typing.TYPE_CHECKING:
    # from ..analyse.frame import Frame
    # from ..analyse.state import State
    from ..fmt import ConstPool


class BinOp(Instruction):
    """
    A binary operation instruction base.

    Performs a arithmetic operation on two stack values.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    type: Type

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "BinOp":
        return cls()

    def __repr__(self) -> str:
        raise NotImplementedError("repr() is not implemented for %r" % type(self))

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError("== is not implemented for %r" % type(self))

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     right = frame.pop(self.type, self)
    #     left = frame.pop(self.type, self)
    #
    #     if left.value is not None and right.value is not None:
    #         metadata = self.evaluate(frame, left.value, right.value)
    #         if metadata is not None:
    #             if frame.thrown is not None:
    #                 return state.step(self, (left, right), None, metadata)
    #             return state.step(self, (left, right), frame.push(metadata.result or self.type, self), metadata)
    #     return state.step(self, (left, right), frame.push(self.type, self))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> Optional["BinOp.Metadata"]:
    #     """
    #     Evaluates the binary operation with the given left and right values.
    #
    #     Parameters
    #     ----------
    #     frame: Frame
    #         The frame to evaluate this operation in.
    #     left: Value
    #         The left operand value.
    #     right: Value
    #         The right operand value.
    #
    #     Returns
    #     -------
    #     BinOp.Metadata | None
    #         The evaluation metadata, including the resulting value, if applicable.
    #     """
    #
    #     raise NotImplementedError("evaluate() is not implemented for %r" % self)

    # class Metadata(Source.Metadata):
    #
    #     __slots__ = ("result",)
    #
    #     def __init__(self, source: "BinOp", result: Value | None) -> None:
    #         super().__init__(source, logger)
    #         self.result = result
    #
    #     def __repr__(self) -> str:
    #         return "<BinOp.Metadata(result=%s)>" % self.result


class Shift(BinOp):
    """
    A shift base instruction.

    Performs a shift on an integral stack value with an int stack value.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Shift(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<Shift(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Shift) and self.opcode == other.opcode

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     right = frame.pop(int_t, self)
    #     left = frame.pop(self.type, self)
    #
    #     if left.value is not None and right.value is not None:
    #         metadata = self.evaluate(frame, left.value, right.value)
    #         if metadata is not None:
    #             return state.step(self, (left, right), frame.push(metadata.result or self.type), metadata)
    #
    #     return state.step(self, (left, right), frame.push(self.type, self))


class Comparison(BinOp):
    """
    A comparison instruction base.

    Compares two numeric stack values.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Comparison(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<Comparison(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Comparison) and self.opcode == other.opcode

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     right = frame.pop(self.type, self)
    #     left = frame.pop(self.type, self)
    #
    #     if left.value is not None and right.value is not None:
    #         metadata = self.evaluate(frame, left.value, right.value)
    #         if metadata is not None:
    #             return state.step(self, (left, right), frame.push(metadata.result or int_t), metadata)
    #
    #     return state.step(self, (left, right), frame.push(int_t, self))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> Integer | None:
    #     raise NotImplementedError("evaluate() is not implemented for %r" % self)


class Addition(BinOp):
    """
    An addition instruction base.

    Computes the sum of two numeric stack values.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Addition(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<Addition(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Addition) and self.opcode == other.opcode

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:  # Constant propagation.
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRAddition(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left + right
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s + %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class Subtraction(BinOp):
    """
    A subtraction instruction base.

    Computes the difference of two numeric stack values.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Subtraction(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<Subtraction(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Subtraction) and self.opcode == other.opcode

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRSubtraction(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left - right
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s - %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class Multiplication(BinOp):
    """
    A multiplication instruction base.

    Computes the product of two numeric stack values.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Multiplication(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<Multiplication(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Multiplication) and self.opcode == other.opcode

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRMultiplication(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left * right
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s * %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class Division(BinOp):
    """
    A division instruction base.

    Computes the division of two numeric stack values.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Division(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<Division(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Division) and self.opcode == other.opcode

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRDivision(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left / right
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s / %s", left, right)
    #         return metadata
    #     except ZeroDivisionError:
    #         frame.throw(Class("java/lang/ArithmeticException"), self)
    #         metadata = BinOp.Metadata(self, None)
    #         metadata.debug("%s / %s (zero division error)", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class Remainder(BinOp):
    """
    A remainder (modulo) instruction base.

    Computes the remainder of two numeric stack values.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Remainder(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<Remainder(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Remainder) and self.opcode == other.opcode

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(Modulo(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left % right
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s %% %s", left, right)
    #         return metadata
    #     except ZeroDivisionError:
    #         frame.throw(Class("java/lang/ArithmeticException"), self)
    #         metadata = BinOp.Metadata(self, None)
    #         metadata.debug("%s %% %s (zero division error)", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class Negate(Instruction):
    """
    A negation instruction base.

    Negates a numeric stack value.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    type: Type

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Negate":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Negate(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<Negate(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Negate) and self.opcode == other.opcode

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.pop(self.type, self)
    #
    #     if value.value is not None:
    #         try:
    #             result = -value.value
    #             metadata = Negate.Metadata(self, result)
    #             metadata.debug("-%s" % value.value)
    #             return state.step(self, (value,), frame.push(result, self), metadata)
    #         except TypeError:
    #             ...
    #
    #     return state.step(self, (value,), frame.push(self.type, self))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRNegate(step, variable, codegen.value(step.inputs[0])))

    # class Metadata(Source.Metadata):
    #
    #     __slots__ = ("result",)
    #
    #     def __init__(self, source: "Negate", result: Value) -> None:
    #         super().__init__(source, logger)
    #         self.result = result
    #
    #     def __repr__(self) -> str:
    #         return "<Negate.Metadata(result=%s)>" % self.result


class ShiftLeft(Shift):
    """
    A left shift instruction base.

    Performs a left shift on an integral stack value with an int stack value.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<ShiftLeft(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<ShiftLeft(type=%s)>" % self.type

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRShiftLeft(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left << right
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s << %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class ShiftRight(Shift):
    """
    A right shift instruction base.

    Performs a right shift on an integral stack value with an int stack value.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<ShiftRight(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<ShiftRight(type=%s)>" % self.type

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRShiftRight(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left >> right
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s >> %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class ShiftRightUnsigned(Shift):
    """
    An unsigned shift right instruction base.

    Performs an unsigned right shift (that is, the sign bit is also shifted) on an
    integral stack value with an int stack value.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<ShiftRightUnsigned(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<ShiftRightUnsigned(type=%s)>" % self.type

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRShiftRightUnsigned(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left.ushr(right)
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s >>> %s", left, right)
    #         return metadata
    #     except (AttributeError, TypeError):
    #         return None


class BitwiseAnd(BinOp):
    """
    A bitwise AND instruction base.

    Performs a bitwise AND operation on two integral stack values.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<BitwiseAnd(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<BitwiseAnd(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BitwiseAnd) and self.opcode == other.opcode

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRBitwiseAnd(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left & right
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s & %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class BitwiseOr(BinOp):
    """
    A bitwise OR instruction base.

    Performs a bitwise OR operation on two integral stack values.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<BitwiseOr(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<BitwiseOr(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BitwiseOr) and self.opcode == other.opcode

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRBitwiseOr(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left | right
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s | %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class BitwiseXor(BinOp):
    """
    A bitwise XOR instruction base.

    Performs a bitwise XOR operation on two integral stack values.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<BitwiseXor(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<BitwiseXor(type=%s)>" % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BitwiseXor) and self.opcode == other.opcode

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRBitwiseXor(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         result = left ^ right
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s ^ %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class IntegralCompare(Comparison):
    """
    A integral comparison instruction base.

    Compares two integral stack values.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<IntegralCompare(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<IntegralCompare(type=%s)>" % self.type

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRNumericCompare(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         if left > right:
    #             result = Integer(1)
    #         elif left == right:
    #             result = Integer(0)
    #         elif left < right:
    #             result = Integer(-1)
    #         else:
    #             assert False, "bad comparison result between %s <=> %s" % (left, right)
    #
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s <=> %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class FloatLCompare(Comparison):
    """
    A float comparison instruction base.

    Compares two floats, if either one or two of them are NaN, -1 is pushed to the
    stack.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<FloatLCompare(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<FloatLCompare(type=%s)>" % self.type

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRFloatLCompare(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         # TODO: Handling NaN and infinities.
    #
    #         if left > right:
    #             result = Integer(1)
    #         elif left == right:
    #             result = Integer(0)
    #         elif left < right:
    #             result = Integer(-1)
    #         else:
    #             assert False, "bad comparison result between %s <=> %s" % (left, right)
    #
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s <=> %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


class FloatGCompare(Comparison):
    """
    A float comparison instruction base.

    Compares two floats, if either one or two of them are NaN, 1 is pushed to the
    stack.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<FloatGCompare(offset=%i, type=%s)>" % (self.offset, self.type)
        return "<FloatGCompare(type=%s)>" % self.type

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     left, right = step.inputs
    #     variable = codegen.variable(self.type)
    #     step.output.value = variable
    #     codegen.emit(IRFloatGCompare(step, variable, codegen.value(left), codegen.value(right)))

    # def evaluate(self, frame: "Frame", left: Value, right: Value) -> BinOp.Metadata | None:
    #     try:
    #         # TODO: Handling NaN and infinities.
    #
    #         if left > right:
    #             result = Integer(1)
    #         elif left == right:
    #             result = Integer(0)
    #         elif left < right:
    #             result = Integer(-1)
    #         else:
    #             assert False, "bad comparison result between %s <=> %s" % (left, right)
    #
    #         metadata = BinOp.Metadata(self, result)
    #         metadata.debug("%s <=> %s", left, right)
    #         return metadata
    #     except TypeError:
    #         return None


_throws = frozenset({Class("java/lang/ArithmeticException")})

iadd            = Addition.make(0x60, "iadd", type=int_t)
ladd            = Addition.make(0x61, "ladd", type=long_t)
fadd            = Addition.make(0x62, "fadd", type=float_t)
dadd            = Addition.make(0x63, "dadd", type=double_t)
isub         = Subtraction.make(0x64, "isub", type=int_t)
lsub         = Subtraction.make(0x65, "lsub", type=long_t)
fsub         = Subtraction.make(0x66, "fsub", type=float_t)
dsub         = Subtraction.make(0x67, "dsub", type=double_t)
imul      = Multiplication.make(0x68, "imul", type=int_t)
lmul      = Multiplication.make(0x69, "lmul", type=long_t)
fmul      = Multiplication.make(0x6a, "fmul", type=float_t)
dmul      = Multiplication.make(0x6b, "dmul", type=double_t)
idiv            = Division.make(0x6c, "idiv", throws=_throws, type=int_t)
ldiv            = Division.make(0x6d, "ldiv", throws=_throws, type=long_t)
fdiv            = Division.make(0x6e, "fdiv", type=float_t)
ddiv            = Division.make(0x6f, "ddiv", type=double_t)
irem           = Remainder.make(0x70, "irem", throws=_throws, type=int_t)
lrem           = Remainder.make(0x71, "lrem", throws=_throws, type=long_t)
frem           = Remainder.make(0x72, "frem", type=float_t)
drem           = Remainder.make(0x73, "drem", type=double_t)
ineg              = Negate.make(0x74, "ineg", type=int_t)
lneg              = Negate.make(0x75, "lneg", type=long_t)
fneg              = Negate.make(0x76, "fneg", type=float_t)
dneg              = Negate.make(0x77, "dneg", type=double_t)
ishl           = ShiftLeft.make(0x78, "ishl", type=int_t)
lshl           = ShiftLeft.make(0x79, "lshl", type=long_t)
ishr          = ShiftRight.make(0x7a, "ishr", type=int_t)
lshr          = ShiftRight.make(0x7b, "lshr", type=long_t)
iushr = ShiftRightUnsigned.make(0x7c, "iushr", type=int_t)
lushr = ShiftRightUnsigned.make(0x7d, "lushr", type=long_t)
iand          = BitwiseAnd.make(0x7e, "iand", type=int_t)
land          = BitwiseAnd.make(0x7f, "land", type=long_t)
ior            = BitwiseOr.make(0x80, "ior", type=int_t)
lor            = BitwiseOr.make(0x81, "lor", type=long_t)
ixor          = BitwiseXor.make(0x82, "ixor", type=int_t)
lxor          = BitwiseXor.make(0x83, "lxor", type=long_t)

lcmp = IntegralCompare.make(0x94, "lcmp", type=long_t)
fcmpl  = FloatLCompare.make(0x95, "fcmpl", type=float_t)
fcmpg  = FloatGCompare.make(0x96, "fcmpg", type=float_t)
dcmpl  = FloatLCompare.make(0x97, "dcmpl", type=double_t)
dcmpg  = FloatGCompare.make(0x98, "dcmpg", type=double_t)

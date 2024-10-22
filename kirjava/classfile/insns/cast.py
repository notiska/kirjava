#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "i2l", "i2f", "i2d", "l2i", "l2f", "l2d", "f2i", "f2l", "f2d", "d2i", "d2l", "d2f", "i2b", "i2c", "i2s",
    "checkcast", "instanceof",  # "checkcast_l", "instanceof_l",
    "ValueCast", "Truncate",
    "CheckCast", "InstanceOf",  # "CheckCastLinked", "InstanceOfLinked",
)

import sys
import typing
from copy import deepcopy
from typing import IO

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from . import Instruction
from .._struct import *
from ...model.types import *
# from ...model.values.constants import *

if typing.TYPE_CHECKING:
    # from ..analyse.frame import Frame
    # from ..analyse.state import State
    from ..fmt import ConstInfo, ConstPool


class ValueCast(Instruction):
    """
    A value cast instruction.

    Performs a value cast (primitive to primitive) on a primitive stack value.
    """

    __slots__ = ()

    rt_throws = frozenset()
    lt_throws = frozenset()
    linked = True

    type_in:  Primitive
    type_out: Primitive

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<ValueCast(offset={self.offset}, type_in={self.type_in!s}, type_out={self.type_out!s})>"
        return f"<ValueCast(type_in={self.type_in!s}, type_out={self.type_out!s})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ValueCast) and self.opcode == other.opcode

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.pop(self.in_type, self)
    #
    #     metadata = Source.Metadata(self, logger)
    #     if value.value is not None:
    #         try:
    #             result = value.value.vcast(self.out_type)
    #             metadata.debug("(%s)%s", self.out_type, value.value)
    #             return state.step(self, (value,), frame.push(result, self), metadata)
    #         except ValueError as error:
    #             metadata.error("%s", error)
    #     return state.step(self, (value,), frame.push(self.out_type, self), metadata)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     value, = step.inputs
    #     variable = codegen.variable(self.out_type)
    #     step.output.value = variable
    #     codegen.emit(IRValueCast(step, variable, self.out_type, codegen.value(value)))


class Truncate(ValueCast):
    """
    A truncation instruction.

    Truncates a primitive stack value to a smaller fake primitive type, i.e.
    int->short or int->boolean.
    """

    __slots__ = ()

    type_in = int_t

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Truncate(offset={self.offset}, type_out={self.type_out!s})>"
        return f"<Truncate(type_out={self.type_out!s})>"


class CheckCast(Instruction):
    """
    A `checkcast` instruction.

    Performs a type cast (reference to reference) on a reference stack value.

    Attributes
    ----------
    classref: ConstInfo
        A class constant, used as the type to cast to.
    """

    __slots__ = ("classref",)

    lt_throws = frozenset({error_t})
    rt_throws = frozenset({Class("java/lang/ClassCastException")})

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, classref: "ConstInfo") -> None:
        super().__init__()
        self.classref = classref

    def __copy__(self) -> "CheckCast":
        copy = checkcast(self.classref)
        copy.offset = self.offset
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "CheckCast":
        copy = checkcast(deepcopy(self.classref, memo))
        copy.offset = self.offset
        return copy

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<CheckCast(offset={self.offset}, classref={self.classref!s})>"
        return f"<CheckCast(classref={self.classref!s})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:checkcast({self.classref!s})"
        return f"checkcast({self.classref!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CheckCast) and self.classref == other.classref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.classref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.class_, ClassInfo):
    #         verifier.report("class is not a class constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     class_type = self.class_.unwrap().as_rtype()
    #     value = frame.pop(reference_t, self)
    #     result = frame.push(value.cast(class_type), self)
    #     return state.step(self, (value,), result)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     value, = step.inputs
    #     variable = codegen.variable(self.class_.unwrap().as_rtype())
    #     step.output.value = variable
    #     codegen.emit(IRTypeCast(step, variable, self.class_.unwrap().as_rtype(), codegen.value(value)))


class InstanceOf(Instruction):
    """
    An `instanceof` instruction.

    Checks if a reference stack value is an instance of a class or pseudo-class
    (arrays).

    Attributes
    ----------
    classref: ConstInfo
        A class constant, used as the type to check against.
    """

    __slots__ = ("classref",)

    lt_throws = frozenset({error_t})
    rt_throws = frozenset()

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, classref: "ConstInfo") -> None:
        super().__init__()
        self.classref = classref

    def __copy__(self) -> "InstanceOf":
        copy = instanceof(self.classref)
        copy.offset = self.offset
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "InstanceOf":
        copy = instanceof(deepcopy(self.classref, memo))
        copy.offset = self.offset
        return copy

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<InstanceOf(offset={self.offset}, classref={self.classref!s})>"
        return f"<InstanceOf(classref={self.classref!s})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:instanceof({self.classref!s})"
        return f"instanceof({self.classref!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, InstanceOf) and self.classref == other.classref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.classref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.class_, ClassInfo):
    #         verifier.report("class is not a class constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     class_type = self.class_.unwrap().as_rtype()
    #     value = frame.pop(reference_t, self)
    #
    #     metadata = Source.Metadata(self, logger)
    #     if value.type == class_type or class_type == object_t:
    #         # A point on the same classes loaded from different classloaders: this won't fail (I don't think) because
    #         # if you were to cast an object to a class loaded by a different classloader, you would get a
    #         # java/lang/ClassCastException.
    #         result = frame.push(Integer(1), self)
    #         metadata.debug("%s instanceof %s (exact type match)", value, class_type)
    #     elif value.type is null_t or isinstance(value.value, Null):
    #         result = frame.push(Integer(0), self)
    #         metadata.debug("%s instanceof %s (null type/value match)", value, class_type)
    #     else:
    #         result = frame.push(int_t, self)
    #
    #     return state.step(self, (value,), result, metadata)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     value, = step.inputs
    #     variable = codegen.variable(int_t)
    #     step.output.value = variable
    #     codegen.emit(IRInstanceOf(step, variable, codegen.value(value), self.class_.unwrap().as_rtype()))


# class CheckCastLinked(CheckCast):
#     """
#     A linked `checkcast` instruction.
#     """
#
#     lt_throws = frozenset()
#     linked = True
#
#
# class InstanceOfLinked(InstanceOf):
#     """
#     A linked `instanceof` instruction.
#     """
#
#     lt_throws = frozenset()
#     linked = True


i2l = ValueCast.make(0x85, "i2l", type_in=int_t, type_out=long_t)
i2f = ValueCast.make(0x86, "i2f", type_in=int_t, type_out=float_t)
i2d = ValueCast.make(0x87, "i2d", type_in=int_t, type_out=double_t)
l2i = ValueCast.make(0x88, "l2i", type_in=long_t, type_out=int_t)
l2f = ValueCast.make(0x89, "l2f", type_in=long_t, type_out=float_t)
l2d = ValueCast.make(0x8a, "l2d", type_in=long_t, type_out=double_t)
f2i = ValueCast.make(0x8b, "f2i", type_in=float_t, type_out=int_t)
f2l = ValueCast.make(0x8c, "f2l", type_in=float_t, type_out=long_t)
f2d = ValueCast.make(0x8d, "f2d", type_in=float_t, type_out=double_t)
d2i = ValueCast.make(0x8e, "d2i", type_in=double_t, type_out=int_t)
d2l = ValueCast.make(0x8f, "d2l", type_in=double_t, type_out=long_t)
d2f = ValueCast.make(0x90, "d2f", type_in=double_t, type_out=float_t)

i2b = Truncate.make(0x91, "i2b", type_out=byte_t)
i2c = Truncate.make(0x92, "i2c", type_out=char_t)
i2s = Truncate.make(0x93, "i2s", type_out=short_t)

checkcast           = CheckCast.make(0xc0, "checkcast")
instanceof         = InstanceOf.make(0xc1, "instanceof")
# checkcast_l   = CheckCastLinked.make(0xc0, "checkcast_l")
# instanceof_l = InstanceOfLinked.make(0xc1, "instanceof_l")

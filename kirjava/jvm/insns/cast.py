#!/usr/bin/env python3

__all__ = (
    "i2l", "i2f", "i2d", "l2i", "l2f", "l2d", "f2i", "f2l", "f2d", "d2i", "d2l", "d2f", "i2b", "i2c", "i2s",
    "checkcast", "instanceof",
    "ValueCast", "Truncate", "CheckCast", "InstanceOf",
)

import typing
from typing import IO

from . import Instruction
from .._struct import *
from ..fmt.constants import ConstInfo
from ...model.types import *
# from ...model.values.constants import *

if typing.TYPE_CHECKING:
    # from ..analyse.frame import Frame
    # from ..analyse.state import State
    from ..fmt import ConstPool
    # from ..verify import Verifier


class ValueCast(Instruction):
    """
    A value cast instruction base.

    Performs a value cast (primitive to primitive) on a primitive stack value.
    """

    __slots__ = ()

    throws = False

    type_in:  Primitive
    type_out: Primitive

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "ValueCast":
        return cls()

    def __repr__(self) -> str:
        return "<ValueCast(offset=%s, type_in=%r, type_out=%r)>" % (self.offset, self.type_in, self.type_out)

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
    A truncation instruction base.

    Truncates a primitive stack value to a smaller fake primitive type, i.e.
    int->short or int->boolean.
    """

    __slots__ = ()

    type_in = int_t

    def __repr__(self) -> str:
        return "<Truncate(offset=%s, type_out=%r)>" % (self.offset, self.type_out)


class CheckCast(Instruction):
    """
    A `checkcast` instruction.

    Performs a type cast (reference to reference) on a reference stack value.
    """

    __slots__ = ("class_",)

    throws = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "CheckCast":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, class_: ConstInfo) -> None:
        super().__init__()
        self.class_ = class_

    def __repr__(self) -> str:
        return "<CheckCast(offset=%s, class_=%r)>" % (self.offset, self.class_)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: checkcast %s" % (self.offset, self.class_)
        return "checkcast %s" % self.class_

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CheckCast) and self.class_ == other.class_

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.class_)))

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
    """

    __slots__ = ("class_",)

    throws = True  # Can throw if the class is not found. How annoying.

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "InstanceOf":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, class_: ConstInfo) -> None:
        super().__init__()
        self.class_ = class_

    def __repr__(self) -> str:
        return "<InstanceOf(offset=%s, class_=%r)>" % (self.offset, self.class_)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: instanceof %s" % (self.offset, self.class_)
        return "instanceof %s" % self.class_

    def __eq__(self, other: object) -> bool:
        return isinstance(other, InstanceOf) and self.class_ == other.class_

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.class_)))

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


i2l = ValueCast.make(0x85, "i2l", in_type=int_t, out_type=long_t)
i2f = ValueCast.make(0x86, "i2f", in_type=int_t, out_type=float_t)
i2d = ValueCast.make(0x87, "i2d", in_type=int_t, out_type=double_t)
l2i = ValueCast.make(0x88, "l2i", in_type=long_t, out_type=int_t)
l2f = ValueCast.make(0x89, "l2f", in_type=long_t, out_type=float_t)
l2d = ValueCast.make(0x8a, "l2d", in_type=long_t, out_type=double_t)
f2i = ValueCast.make(0x8b, "f2i", in_type=float_t, out_type=int_t)
f2l = ValueCast.make(0x8c, "f2l", in_type=float_t, out_type=long_t)
f2d = ValueCast.make(0x8d, "f2d", in_type=float_t, out_type=double_t)
d2i = ValueCast.make(0x8e, "d2i", in_type=double_t, out_type=int_t)
d2l = ValueCast.make(0x8f, "d2l", in_type=double_t, out_type=long_t)
d2f = ValueCast.make(0x90, "d2f", in_type=double_t, out_type=float_t)

i2b = Truncate.make(0x91, "i2b", out_type=byte_t)
i2c = Truncate.make(0x92, "i2c", out_type=char_t)
i2s = Truncate.make(0x93, "i2s", out_type=short_t)

checkcast  = CheckCast.make(0xc0, "checkcast")
instanceof = InstanceOf.make(0xc1, "instanceof")

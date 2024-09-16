#!/usr/bin/env python3

__all__ = (
    "iaload", "laload", "faload", "daload", "aaload", "baload", "caload", "saload",
    "iastore", "lastore", "fastore", "dastore", "aastore", "bastore", "castore", "sastore",
    "newarray", "anewarray", "multianewarray", "arraylength",
)

import logging
import typing
from typing import IO

from . import Instruction
from .._struct import *
from ..fmt.constants import ClassInfo, ConstInfo
from ...model.types import *
from ...model.values.constants import Integer, Null
from ...model.values.objects import Array as ArrayValue

if typing.TYPE_CHECKING:
    from ..analyse.frame import Frame
    from ..analyse.state import State
    from ..fmt import ConstPool
    from ..verify import Verifier

logger = logging.getLogger("ijd.jvm.insns.array")


class ArrayLoad(Instruction):

    __slots__ = ()

    can_throw = True

    type: Type

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "ArrayLoad":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     index = frame.pop(int_t, self)
    #     array = frame.pop(Array(self.type), self)
    #
    #     if isinstance(array.value, Null) or array.type is null_t:
    #         frame.throw(Class("java/lang/NullPointerException"), self)
    #         return state.step(self, (array, index))
    #     elif isinstance(index.value, Integer) and isinstance(array.value, ArrayValue) and array.value.sizes:
    #         size = array.value.sizes[0]
    #         if isinstance(size, Integer) and index.value >= size:
    #             if frame.throw(Class("java/lang/ArrayIndexOutOfBoundsException")):
    #                 return state.step(self, (array, index))
    #
    #     if isinstance(array.type, Array):
    #         result = frame.push(array.type.element, self)
    #         if isinstance(result.type, Reference):
    #             result.constrain(null_t, self)
    #     elif self.type is reference_t:
    #         result = frame.push(object_t, self)
    #         result.constrain(null_t, self)
    #     else:
    #         result = frame.push(self.type, self)
    #
    #     return state.step(self, (array, index), result)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     array, index = step.inputs
    #     variable = codegen.variable(step.output.type)
    #     step.output.value = variable
    #     codegen.emit(IRArrayLoad(step, variable, codegen.value(array), codegen.value(index)))


class ArrayStore(Instruction):

    __slots__ = ()

    can_throw = True

    type: Type

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "ArrayStore":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     item = frame.pop(self.type, self)
    #     index = frame.pop(int_t, self)
    #     array = frame.pop(Array(self.type), self)
    #
    #     # TODO: Which is thrown first? Could impact a lot.
    #
    #     if isinstance(array.value, Null) or array.type is null_t:
    #         if frame.throw(Class("java/lang/NullPointerException"), self):
    #             return state.step(self, (array, index, item))
    #     elif isinstance(index.value, Integer) and isinstance(array.value, ArrayValue) and array.value.sizes:
    #         size = array.value.sizes[0]
    #         if isinstance(size, Integer) and index.value >= size:
    #             if frame.throw(Class("java/lang/ArrayIndexOutOfBoundsException")):
    #                 return state.step(self, (array, index, item))
    #
    #     if isinstance(array.type, Array):
    #         item.hint(array.type.element, self)
    #
    #     return state.step(self, (array, index, item))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     array, index, item = step.inputs
    #     codegen.emit(IRArrayStore(step, codegen.value(array), codegen.value(index), codegen.value(item)))


class NewArray(Instruction):

    __slots__ = ("tag",)

    can_throw = True

    _FWD_TAGS = {
        4:  boolean_t,
        5:  char_t,
        6:  float_t,
        7:  double_t,
        8:  byte_t,
        9:  short_t,
        10: int_t,
        11: long_t,
    }
    _REV_TAGS = {
        boolean_t: 4,
        char_t:    5,
        float_t:   6,
        double_t:  7,
        byte_t:    8,
        short_t:   9,
        int_t:     10,
        long_t:    11,
    }

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "NewArray":
        tag, = stream.read(1)
        return cls(tag)

    def __init__(self, tag: int) -> None:
        self.offset = None
        self.tag = tag

    def __repr__(self) -> str:
        return "<NewArray(offset=%s, tag=%i)>" % (self.offset, self.tag)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: newarray %i" % (self.offset, self.tag)
        return "newarray %i" % self.tag

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, self.tag)))

    def verify(self, verifier: "Verifier") -> None:
        if not self.tag in NewArray._FWD_TAGS:
            verifier.report("invalid type tag", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     array_type = Array(self.type)
    #     size = frame.pop(int_t, self)
    #
    #     metadata = Source.Metadata(self, logger)
    #     if size.value is None:
    #         array = frame.push(array_type, self)
    #     # TODO: We could also check for potential heap allocation limit errors in the future.
    #     elif isinstance(size.value, Integer) and size.value < Integer(0):
    #         if frame.throw(Class("java/lang/NegativeArraySizeException"), self):
    #             metadata.debug("size %s (negative array size)", size.value)
    #             return state.step(self, (size,), None, metadata)
    #         array = frame.push(array_type, self)
    #     else:
    #         array = frame.push(ArrayValue(array_type, (size.value,)), self)
    #         metadata.debug("size %s", size.value)
    #
    #     return state.step(self, (size,), array, metadata)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     variable = codegen.variable(step.output.type)
    #     step.output.value = variable
    #     sizes = list(map(codegen.value, step.inputs))
    #     codegen.emit(IRNewArray(step, variable, Array(self.type), sizes))


class ANewArray(Instruction):

    __slots__ = ("class_",)

    can_throw = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "ANewArray":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, class_: ConstInfo) -> None:
        self.offset = None
        self.class_ = class_

    def __repr__(self) -> str:
        return "<ANewArray(offset=%s, class=%s)>" % (self.offset, self.class_)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: anewarray %s" % (self.offset, self.class_)
        return "anewarray %s" % self.class_

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.class_)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types and not isinstance(self.class_, ClassInfo):
            verifier.report("class is not a class constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     array_type = Array(self.class_.unwrap().as_rtype())
    #     size = frame.pop(int_t, self)
    #
    #     metadata = Source.Metadata(self, logger)
    #     if size.value is None:
    #         array = frame.push(array_type, self)
    #     elif isinstance(size.value, Integer) and size.value < Integer(0):
    #         if frame.throw(Class("java/lang/NegativeArraySizeException"), self):
    #             metadata.debug("size %s (negative array size)", size.value)
    #             return state.step(self, (size,), None, metadata)
    #         array = frame.push(array_type, self)
    #     else:
    #         array = frame.push(ArrayValue(array_type, (size.value,)), self)
    #         metadata.debug("size %s", size.value)
    #
    #     return state.step(self, (size,), array, metadata)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     variable = codegen.variable(step.output.type)
    #     step.output.value = variable
    #     sizes = list(map(codegen.value, step.inputs))
    #     codegen.emit(IRNewArray(step, variable, Array(self.class_.unwrap().as_rtype()), sizes))


class MultiANewArray(Instruction):

    __slots__ = ("class_", "dimensions")

    can_throw = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "MultiANewArray":
        index, dimensions = unpack_HB(stream.read(3))
        return cls(pool[index], dimensions)

    def __init__(self, class_: ConstInfo, dimensions: int) -> None:
        self.offset = None
        self.class_ = class_
        self.dimensions = dimensions

    def __repr__(self) -> str:
        return "<MultiANewArray(offset=%s, class_=%s, dimensions=%i)>" % (self.offset, self.class_, self.dimensions)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: multianewarray %s dimension %i" % (self.offset, self.class_, self.dimensions)
        return "multianewarray %s dimension %i" % (self.class_, self.dimensions)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHB(self.opcode, pool.add(self.class_), self.dimensions))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.dimensions <= 255):
            verifier.report("invalid dimensions", instruction=self)
        if verifier.check_const_types and not isinstance(self.class_, ClassInfo):
            verifier.report("class is not a class constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     array_type = self.class_.unwrap().as_rtype()
    #     assert isinstance(array_type, Array), "invalid array type %r" % array_type
    #
    #     metadata = Source.Metadata(self, logger)
    #
    #     valid = True
    #     sizes = []
    #     for _ in range(self.dimensions):
    #         size = frame.pop(int_t, self)
    #         sizes.append(size)
    #
    #         if size.value is not None:
    #             if isinstance(size.value, Integer) and size.value < Integer(0):
    #                 if frame.throw(Class("java/lang/NegativeArraySizeException"), self):
    #                     metadata.debug("size %s (negative array size)", size.value)
    #                     return state.step(self, tuple(sizes), None, metadata)
    #         else:
    #             valid = False
    #
    #     if not valid:
    #         array = frame.push(array_type, self)
    #     else:
    #         array = frame.push(ArrayValue(array_type, tuple(size.value for size in reversed(sizes))), self)
    #         metadata.debug("size(s) " + ", ".join("%s" for _ in range(len(sizes))), *sizes)
    #
    #     return state.step(self, tuple(sizes), array, metadata)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     variable = codegen.variable(step.output.type)
    #     step.output.value = variable
    #     sizes = list(map(codegen.value, step.inputs))
    #     codegen.emit(IRNewArray(step, variable, self.class_.unwrap().as_rtype(), sizes))


class ArrayLength(Instruction):

    __slots__ = ()

    can_throw = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "ArrayLength":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     metadata = Source.Metadata(self, logger)
    #
    #     array = frame.pop(array_t, self)
    #
    #     if isinstance(array.value, Null) or array.type is null_t:
    #         if frame.throw(Class("java/lang/NullPointerException"), self):
    #             metadata.debug("%s.length (null pointer)", array)
    #             return state.step(self, (array,), None, metadata)
    #         length = frame.push(int_t, self)
    #     elif isinstance(array.value, ArrayValue) and array.value.sizes:
    #         length = frame.push(array.value.sizes[0], self)
    #         metadata.debug("%s.length", array.value)
    #     else:
    #         length = frame.push(int_t, self)
    #
    #     return state.step(self, (array,), length, metadata)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if step.output.value is not None:
    #         return
    #     array, = step.inputs
    #     variable = codegen.variable(step.output.type)
    #     step.output.value = variable
    #     codegen.emit(IRArrayLength(step, variable, codegen.value(array)))


iaload = ArrayLoad.make(0x2e, "iaload", type=int_t)
laload = ArrayLoad.make(0x2f, "laload", type=long_t)
faload = ArrayLoad.make(0x30, "faload", type=float_t)
daload = ArrayLoad.make(0x31, "daload", type=double_t)
aaload = ArrayLoad.make(0x32, "aaload", type=reference_t)
baload = ArrayLoad.make(0x33, "baload", type=byte_t)
caload = ArrayLoad.make(0x34, "caload", type=char_t)
saload = ArrayLoad.make(0x35, "saload", type=short_t)

iastore = ArrayStore.make(0x4f, "iastore", type=int_t)
lastore = ArrayStore.make(0x50, "lastore", type=long_t)
fastore = ArrayStore.make(0x51, "fastore", type=float_t)
dastore = ArrayStore.make(0x52, "dastore", type=double_t)
aastore = ArrayStore.make(0x53, "aastore", type=reference_t)
bastore = ArrayStore.make(0x54, "bastore", type=byte_t)
castore = ArrayStore.make(0x55, "castore", type=char_t)
sastore = ArrayStore.make(0x56, "sastore", type=short_t)

newarray             = NewArray.make(0xbc, "newarray")
anewarray           = ANewArray.make(0xbd, "anewarray")
multianewarray = MultiANewArray.make(0xc5, "multianewarray")

arraylength = ArrayLength.make(0xbe, "arraylength")

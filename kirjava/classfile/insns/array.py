#!/usr/bin/env python3

__all__ = (
    "iaload", "laload", "faload", "daload", "aaload", "baload", "caload", "saload",
    "iastore", "lastore", "fastore", "dastore", "aastore", "bastore", "castore", "sastore",
    "newarray", "anewarray", "multianewarray",  # "anewarray_l", "multianewarray_l",
    "arraylength",
    "ArrayLoad", "ArrayStore", "NewArray",
    "ANewArray", "MultiANewArray",  # "ANewArrayLinked", "MultiANewArrayLinked",
    "ArrayLength",
)

import typing
from copy import deepcopy
from typing import IO

from . import Instruction
from .._struct import *
from ..fmt.constants import ClassInfo, ConstInfo
from ...model.types import *
# from ...model.values.constants import Integer, Null
# from ...model.values.objects import Array as ArrayValue

if typing.TYPE_CHECKING:
    # from ..analyse.frame import Frame
    # from ..analyse.state import State
    from ..fmt import ConstPool
    from ..verify import Verifier


class ArrayLoad(Instruction):
    """
    An array load instruction base.

    Loads an element from an array.

    Attributes
    ----------
    type: Type
        The type of array element to load.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset({Class("java/lang/ArrayIndexOutOfBoundsException"), Class("java/lang/NullPointerException")})
    linked = True

    type: Type

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "ArrayLoad":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<ArrayLoad(offset={self.offset}, type={self.type!s})>"
        return f"<ArrayLoad(type={self.type!s})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ArrayLoad) and self.opcode == other.opcode

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
    """
    An array store instruction base.

    Stores an element in an array.

    Attributes
    ----------
    type: Type
        The type of array element to store.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset({Class("java/lang/ArrayIndexOutOfBoundsException"), Class("java/lang/NullPointerException")})
    linked = True

    type: Type

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "ArrayStore":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<ArrayStore(offset={self.offset}, type={self.type!s})>"
        return f"<ArrayStore(type={self.type!s})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ArrayStore) and self.opcode == other.opcode

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
    """
    A `newarray` instruction.

    Creates a new primitive type array.

    Attributes
    ----------
    TAG_BOOLEAN: int
        Indicates that the array is of type `boolean`.
    TAG_CHAR: int
        Indicates that the array is of type `char`.
    TAG_FLOAT: int
        Indicates that the array is of type `float`.
    TAG_DOUBLE: int
        Indicates that the array is of type `double`.
    TAG_BYTE: int
        Indicates that the array is of type `byte`.
    TAG_SHORT: int
        Indicates that the array is of type `short`.
    TAG_INT: int
        Indicates that the array is of type `int`.
    TAG_LONG: int
        Indicates that the array is of type `long`.
    tag: int
        A byte tag indicating the type of the array to create.
    """

    __slots__ = ("tag",)

    lt_throws = frozenset()
    rt_throws = frozenset({Class("java/lang/NegativeArraySizeException")})
    linked = True

    TAG_BOOLEAN = 4
    TAG_CHAR    = 5
    TAG_FLOAT   = 6
    TAG_DOUBLE  = 7
    TAG_BYTE    = 8
    TAG_SHORT   = 9
    TAG_INT     = 10
    TAG_LONG    = 11

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "NewArray":
        tag, = stream.read(1)
        return cls(tag)

    def __init__(self, tag: int) -> None:
        super().__init__()
        self.tag = tag

    def __copy__(self) -> "NewArray":
        # FIXME: Type ignored because we need to support 3.10, so can't use Self type. If support is dropped, need to
        #        update all occurrences of this.
        copy = newarray(self.tag)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<NewArray(offset={self.offset}, tag={self.tag})>"
        return f"<NewArray(tag={self.tag})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:newarray({self.tag})"
        return f"newarray({self.tag})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NewArray) and self.tag == other.tag

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, self.tag)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not self.tag in NewArray._FWD_TAGS:
    #         verifier.report("invalid type tag", instruction=self)

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
    """
    An `anewarray` instruction.

    Creates a new reference type array.

    Attributes
    ----------
    classref: ConstInfo
        A class constant, used as the type of the array to create.
    """

    __slots__ = ("classref",)

    lt_throws = frozenset({error_t})
    rt_throws = frozenset({Class("java/lang/NegativeArraySizeException")})

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "ANewArray":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, classref: ConstInfo) -> None:
        super().__init__()
        self.classref = classref

    def __copy__(self) -> "ANewArray":
        copy = anewarray(self.classref)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __deepcopy__(self, memo: dict[int, object]) -> "ANewArray":
        copy = anewarray(deepcopy(self.classref, memo))  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<ANewArray(offset={self.offset}, classref={self.classref!s})>"
        return f"<ANewArray(classref={self.classref!s})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:anewarray({self.classref!s})"
        return f"anewarray({self.classref!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ANewArray) and self.classref == other.classref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.classref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.class_, ClassInfo):
    #         verifier.report("class is not a class constant", instruction=self)

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
    """
    A `multianewarray` instruction.

    Creates a new multidimensional reference type array.

    Attributes
    ----------
    classref: ConstInfo
        A class constant, used as the type of the array to create.
    dimensions: int
        The number of dimensions to create.
    """

    __slots__ = ("classref", "dimensions")

    lt_throws = frozenset({error_t})
    rt_throws = frozenset({Class("java/lang/NegativeArraySizeException")})

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "MultiANewArray":
        index, dimensions = unpack_HB(stream.read(3))
        return cls(pool[index], dimensions)

    def __init__(self, classref: ConstInfo, dimensions: int) -> None:
        super().__init__()
        self.classref = classref
        self.dimensions = dimensions

    def __copy__(self) -> "MultiANewArray":
        copy = multianewarray(self.classref, self.dimensions)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __deepcopy__(self, memo: dict[int, object]) -> "MultiANewArray":
        copy = multianewarray(deepcopy(self.classref, memo), self.dimensions)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<MultiANewArray(offset={self.offset}, classref={self.classref!s}, dimensions={self.dimensions})>"
        return f"<MultiANewArray(classref={self.classref!s}, dimensions={self.dimensions})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:multianewarray({self.classref!s},{self.dimensions})"
        return f"multianewarray({self.classref!s},{self.dimensions})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, MultiANewArray) and
            self.classref == other.classref and
            self.dimensions == other.dimensions
        )

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHB(self.opcode, pool.add(self.classref), self.dimensions))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.dimensions <= 255):
    #         verifier.report("invalid dimensions", instruction=self)
    #     if verifier.check_const_types and not isinstance(self.class_, ClassInfo):
    #         verifier.report("class is not a class constant", instruction=self)

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


# FIXME: A clean way of doing linked instructions.
# class ANewArrayLinked(ANewArray):
#     """
#     A linked `anewarray` instruction.
#     """
#
#     lt_throws = frozenset()
#     linked = True


# class MultiANewArrayLinked(MultiANewArray):
#     ...


class ArrayLength(Instruction):
    """
    An `arraylength` instruction.

    Gets the length of an array.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset({Class("java/lang/NullPointerException")})
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "ArrayLength":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<ArrayLength(offset={self.offset})>"
        return "<ArrayLength>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ArrayLength)

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

newarray                     = NewArray.make(0xbc, "newarray")
anewarray                   = ANewArray.make(0xbd, "anewarray")
multianewarray         = MultiANewArray.make(0xc5, "multianewarray")
# anewarray_l           = ANewArrayLinked.make(0xbd, "anewarray_l")
# multianewarray_l = MultiANewArrayLinked.make(0xc5, "multianewarray_l")

arraylength = ArrayLength.make(0xbe, "arraylength")

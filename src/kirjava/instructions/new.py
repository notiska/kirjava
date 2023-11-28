#!/usr/bin/env python3

__all__ = (
    "NewInstruction", "NewArrayInstruction", "ANewArrayInstruction", "MultiANewArrayInstruction",
)

"""
Instructions that create new references.
"""

import typing
from typing import Any, IO

from . import Instruction
from .. import _argument, types
from ..constants import Class as ClassConstant
from ..types import int_t, Array, Class as ClassType, Primitive, Reference, Uninitialized

if typing.TYPE_CHECKING:
    from ..analysis import Context
    from ..classfile import ClassFile


class NewInstruction(Instruction):
    """
    Creates a new class.
    """

    __slots__ = ("type", "_index")

    operands = {"_index": ">H"}

    def __init__(self, type_: _argument.ReferenceType) -> None:
        """
        :param type_: The new type to create.
        """

        self.type = _argument.get_reference_type(type_)

    def __repr__(self) -> str:
        return "<NewInstruction(opcode=0x%x, mnemonic=%s, type=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.type)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.type == self.type) or other is type(self)

    def copy(self) -> "NewInstruction":
        return type(self)(self.type)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].class_type

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(ClassConstant(self.type))
        super().write(class_file, buffer, wide)

    def trace(self, context: "Context") -> None:
        # if not frame.verifier.checker.check_class(self.type):
        #     frame.verifier.report(Error(
        #         Error.Type.INVALID_TYPE, frame.source, "expected class or interface type", "got %s" % self.type,
        #     ))
        context.push(Uninitialized(context.source))

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     associations[delta.pushes[0]] = NewExpression(self.type)
    #     # Technically this has no side effects (invoking the constructor does), so there's no need to return anything.


class NewArrayInstruction(Instruction):
    """
    Creates a new primitive array.
    """

    __slots__ = ("type", "_atype")

    operands = {"_atype": ">B"}

    _FORWARD_TYPES = {
        4:  types.boolean_t,
        5:  types.char_t,
        6:  types.float_t,
        7:  types.double_t,
        8:  types.byte_t,
        9:  types.short_t,
        10: types.int_t,
        11: types.long_t,
    }
    _BACKWARD_TYPES = {
        types.boolean_t: 4,
        types.char_t:    5,
        types.float_t:   6,
        types.double_t:  7,
        types.byte_t:    8,
        types.short_t:   9,
        types.int_t:     10,
        types.long_t:    11,
    }

    def __init__(self, type_: Array | Primitive) -> None:
        """
        :param type_: Either the array type itself, or the element type of the array.
        """

        if type(type_) is not Array:
            type_ = Array(type_)
        self.type = type_

    def __repr__(self) -> str:
        return "<NewArrayInstruction(opcode=0x%x, mnemonic=%s, type=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.type)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.type == self.type) or other is type(self)

    def copy(self) -> "NewArrayInstruction":
        return type(self)(self.type)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = Array(self._FORWARD_TYPES[self._atype])

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        self._atype = self._BACKWARD_TYPES[self.type.element]
        super().write(class_file, buffer, wide)

    def trace(self, context: "Context") -> None:
        context.constrain(context.pop(), int_t)
        context.push(self.type)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     associations[delta.pushes[0]] = NewArrayExpression(self.type, (associations[delta.pops[-1]],))


class ANewArrayInstruction(Instruction):
    """
    Creates a new array with a given reference type.
    """

    __slots__ = ("type", "_index")

    operands = {"_index": ">H"}
    throws = (ClassType("java/lang/NegativeArraySizeException"),)

    def __init__(self, type_: Array | Reference) -> None:
        """
        :param type_: Either the array type, or the element type in the array.
        """

        if type(type_) is not Array:
            type_ = Array(type_)
        self.type = type_

    def __repr__(self) -> str:
        return "<ANewArrayInstruction(opcode=0x%x, mnemonic=%s, type=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.type)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.type == self.type) or other is type(self)

    def copy(self) -> "ANewArrayInstruction":
        return type(self)(self.type)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = Array(class_file.constant_pool[self._index].class_type)

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(ClassConstant(self.type.element))
        super().write(class_file, buffer, wide)

    def trace(self, context: "Context") -> None:
        context.constrain(context.pop(), int_t)
        context.push(self.type)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     associations[delta.pushes[0]] = NewArrayExpression(self.type, (associations[delta.pops[-1]],))


class MultiANewArrayInstruction(Instruction):
    """
    Creates a new multidimensional array with the given reference type.
    """

    __slots__ = ("type", "dimension", "_index")

    operands = {"_index": ">H", "dimension": ">B"}

    def __init__(self, type_: Array | Reference, dimension: int) -> None:
        """
        :param type_: Either the array type, or the element type in the array.
        :param dimension: The dimensions of the array to initialise.
        """

        if type(type_) is not Array:
            type_ = Array(type_)
        self.type = type_
        self.dimension = dimension

    def __repr__(self) -> str:
        return "<MultiANewArrayInstruction(opcode=0x%x, mnemonic=%s, type=%r, dimension=%i) at %x>" % (
            self.opcode, self.mnemonic, self.type, self.dimension, id(self),
        )

    def __str__(self) -> str:
        return "%s %s dimension %i" % (self.mnemonic, self.type, self.dimension)

    def __eq__(self, other: Any) -> bool:
        return (
            type(other) is type(self) and
            other.dimension == self.dimension and
            other.type == self.type
        ) or other is type(self)

    def copy(self) -> "MultiANewArrayInstruction":
        instruction = type(self)(self.type, self.dimension)
        if type(self.type) is not Array:
            # Otherwise it will be automatically converted, which may not be correct in some cases.
            instruction.type = self.type
        return instruction

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].class_type

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(ClassConstant(self.type))
        super().write(class_file, buffer, wide)

    def trace(self, context: "Context") -> None:
        # if self.dimension > self.type.dimension:
        #     frame.verifier.report(Error(
        #         Error.Type.INVALID_INSTRUCTION, frame.source,
        #         "instruction dimension exceeds array dimension", "%i > %i" % (self.dimension, self.type.dimension),
        #     ))

        for entry in context.pop(self.dimension):
            context.constrain(entry, int_t)
        context.push(self.type)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     associations[delta.pushes[-1]] = NewArrayExpression(self.type, tuple(map(associations.get, delta.pops)))

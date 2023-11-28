#!/usr/bin/env python3

__all__ = (
    "ConversionInstruction", "TruncationInstruction", "CheckCastInstruction", "InstanceOfInstruction",
)

"""
Conversion instructions.
"""

import typing
from typing import Any, IO

from . import Instruction
from .. import _argument
from ..constants import Class as ClassConstant
from ..types import int_t, Class as ClassType, Primitive

if typing.TYPE_CHECKING:
    from ..analysis import Context
    from ..classfile import ClassFile


class ConversionInstruction(Instruction):
    """
    Converts one type into another.
    """

    __slots__ = ()

    type_in: Primitive = ...
    type_out: Primitive = ...

    def __repr__(self) -> str:
        return "<ConversionInstruction(opcode=0x%x, mnemonic=%s, type_in=%r, type_out=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type_in, self.type_out, id(self),
        )

    def trace(self, context: "Context") -> None:
        *_, entry = context.pop(1 + self.type_in.wide, as_tuple=True)
        context.constrain(entry, self.type_in)
        context.push(entry.cast(self.type_out, context.source))

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     associations[delta.pushes[0]] = ValueCastExpression(associations[delta.pops[-1]], self.type_out)


class TruncationInstruction(ConversionInstruction):
    """
    Truncates integer primitive types.
    """

    __slots__ = ()

    type_in = int_t

    def __repr__(self) -> str:
        return "<TruncationInstruction(opcode=0x%x, mnemonic=%s, type_out=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type_out, id(self),
        )


class CheckCastInstruction(Instruction):
    """
    Checks if the top value on the stack is of a certain type.
    """

    __slots__ = ("type", "_index")

    operands = {"_index": ">H"}
    throws = (ClassType("java/lang/ClassCastException"),)

    def __init__(self, type_: _argument.ReferenceType) -> None:
        """
        :param type_: The type to cast to.
        """

        self.type = _argument.get_reference_type(type_)

    def __repr__(self) -> str:
        return "<CheckCastInstruction(opcode=0x%x, mnemonic=%s, type=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.type)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.type == self.type) or other is type(self)

    def copy(self) -> "CheckCastInstruction":
        return type(self)(self.type)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].class_type

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(ClassConstant(self.type))
        super().write(class_file, buffer, wide)

    def trace(self, context: "Context") -> None:
        entry = context.pop()
        context.constrain(entry, self.type)
        context.push(entry.cast(self.type, context.source))

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     associations[delta.pushes[0]] = TypeCastExpression(associations[delta.pops[-1]], self.type)


class InstanceOfInstruction(Instruction):
    """
    Determines if the top value on the stack is of a certain type.
    """

    __slots__ = ("type", "_index")

    operands = {"_index": ">H"}

    def __init__(self, type_: _argument.ReferenceType) -> None:
        """
        :param type_: The type to check if the value is an instance of.
        """

        self.type = _argument.get_reference_type(type_)

    def __repr__(self) -> str:
        return "<InstanceOfInstruction(opcode=0x%x, mnemonic=%s, type=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.type)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.type == self.type) or other is type(self)

    def copy(self) -> "InstanceOfInstruction":
        return type(self)(self.type)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].class_type

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(ClassConstant(self.type))
        super().write(class_file, buffer, wide)

    def trace(self, context: "Context") -> None:
        context.constrain(context.pop(), self.type)
        context.push(int_t)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     associations[delta.pushes] = InstanceOfExpression(associations[delta.pops[-1]], self.type)

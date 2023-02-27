#!/usr/bin/env python3

"""
Conversion instructions.
"""

from typing import Any, Dict, IO

from . import Instruction
from ... import _argument, types
from ...abc import Value
from ...analysis.ir.variable import Scope
from ...analysis.trace import Entry, Frame, FrameDelta
from ...classfile import descriptor, ClassFile
from ...classfile.constants import Class, Double, Float, Integer, Long
from ...instructions.ir.cast import InstanceOfExpression, TypeCastExpression, ValueCastExpression
from ...types import PrimitiveType
from ...types.reference import ClassOrInterfaceType


class ConversionInstruction(Instruction):
    """
    Converts one type into another.
    """

    type_in: PrimitiveType = ...
    type_out: PrimitiveType = ...

    def __repr__(self) -> str:
        return "<ConversionInstruction(opcode=0x%x, mnemonic=%s, type_in=%r, type_out=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type_in, self.type_out, id(self),
        )

    def trace(self, frame: Frame) -> None:
        *_, entry = frame.pop(self.type_in.internal_size, tuple_=True, expect=self.type_in)
        value = None

        # if entry.value is None:
        #     value = None
        # else:
        #     abs_value = entry.value.value
        #
        #     if self.type_out in (types.byte_t, types.char_t, types.short_t, types.int_t):  # FIXME FIXME FIXME
        #         # FIXME: 32 bit floating point precision is not accurate with actual Java, Python uses doubles
        #         value = Integer((int(abs(abs_value)) & 0xffffffff) * (1 if abs_value >= 0 else -1))
        #     elif self.type_out == types.long_t:
        #         value = Long(int(abs_value))
        #     elif self.type_out == types.float_t:
        #         value = Float(float(abs_value))
        #     elif self.type_out == types.double_t:
        #         value = Double(float(abs_value))

        frame.push(self.type_out.to_verification_type(), value)

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        associations[delta.pushes[0]] = ValueCastExpression(associations[delta.pops[-1]], self.type_out)


class TruncationInstruction(ConversionInstruction):
    """
    Truncates integer primitive types.
    """

    type_in = types.int_t

    def __repr__(self) -> str:
        return "<TruncationInstruction(opcode=0x%x, mnemonic=%s, type_out=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type_out, id(self),
        )


class CheckCastInstruction(Instruction):
    """
    Checks if the top value on the stack is of a certain type.
    """

    __slots__ = ("type",)

    operands = {"_index": ">H"}
    throws = (types.classcastexception_t,)

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
        return (type(other) is self.__class__ and other.type == self.type) or other is self.__class__

    def copy(self) -> "CheckCastInstruction":
        return self.__class__(self.type)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].type

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if type(self.type) is ClassOrInterfaceType:
            self._index = class_file.constant_pool.add(Class(self.type.name))
        else:
            self._index = class_file.constant_pool.add(Class(descriptor.to_descriptor(self.type)))
        super().write(class_file, buffer, wide)

    def trace(self, frame: Frame) -> None:
        entry = frame.pop(expect=None)
        frame.push(entry.cast(frame.source, self.type))

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        associations[delta.pushes[0]] = TypeCastExpression(associations[delta.pops[-1]], self.type)


class InstanceOfInstruction(Instruction):
    """
    Determines if the top value on the stack is of a certain type.
    """

    __slots__ = ("type",)

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
        return (type(other) is self.__class__ and other.type == self.type) or other is self.__class__

    def copy(self) -> "InstanceOfInstruction":
        return self.__class__(self.type)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].type

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if type(self.type) is ClassOrInterfaceType:
            self._index = class_file.constant_pool.add(Class(self.type.name))
        else:
            self._index = class_file.constant_pool.add(Class(descriptor.to_descriptor(self.type)))
        super().write(class_file, buffer, wide)

    def trace(self, frame: Frame) -> None:
        frame.pop(expect=None)
        frame.push(types.int_t)

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        associations[delta.pushes] = InstanceOfExpression(associations[delta.pops[-1]], self.type)

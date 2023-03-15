#!/usr/bin/env python3

"""
Field access instructions.
"""

from typing import Any, Dict, IO, Union

from . import Instruction
from ..ir.field import GetFieldExpression, GetStaticFieldExpression, SetFieldStatement, SetStaticFieldStatement
from ... import _argument, types
from ...abc import Value
from ...analysis.ir.variable import Scope
from ...analysis.trace import Entry, Frame, FrameDelta
from ...classfile import descriptor, ClassFile
from ...classfile.constants import Class, FieldRef, NameAndType
from ...types import ClassOrInterfaceType


class FieldInstruction(Instruction):
    """
    An instruction that references a field in some way.
    """

    __slots__ = ("class_", "name", "type")

    throws = (types.nullpointerexception_t,)  # FIXME: Get has more specific throws

    static: bool = ...

    def __init__(self, class_: _argument.ReferenceType, name: str, type_: _argument.FieldDescriptor) -> None:
        """
        :param class_: The class that the field belongs to.
        :param name: The name of the field.
        :param type_: The type of the field.
        """

        self.class_ = _argument.get_reference_type(class_)
        self.name = name
        self.type = _argument.get_field_descriptor(type_)

    def __repr__(self) -> str:
        return "<FieldInstruction(opcode=0x%x, mnemonic=%s, class=%s, name=%r, type=%s) at %x>" % (
            self.opcode, self.mnemonic, self.class_, self.name, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s#%s %s" % (self.mnemonic, self.class_, self.type, self.name)

    def __eq__(self, other: Any) -> bool:
        return (
            type(other) is self.__class__ and
            other.class_ == self.class_ and
            other.type == self.type and
            other.name == self.name
        ) or other is self.__class__

    def copy(self) -> "FieldInstruction":
        return self.__class__(self.class_, self.name, self.type)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)

        field_ref = class_file.constant_pool[self._index]
        self.class_ = field_ref.class_.type
        self.name = field_ref.name_and_type.name
        self.type = descriptor.parse_field_descriptor(field_ref.name_and_type.descriptor)

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if type(self.class_) is ClassOrInterfaceType:
            class_ = Class(self.class_.name)
        else:
            class_ = Class(descriptor.to_descriptor(self.class_))
        field_ref = FieldRef(class_, NameAndType(self.name, descriptor.to_descriptor(self.type)))
        self._index = class_file.constant_pool.add(field_ref)

        super().write(class_file, buffer, wide)


class GetFieldInstruction(FieldInstruction):
    """
    Gets the value from a field.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        if not self.static:
            frame.pop(expect=None)
        frame.push(self.type.to_verification_type())

    def lift(self, delta: FrameDelta, scope: "Scope", associations: Dict[Entry, Value]) -> None:
        if self.static:
            associations[delta.pushes[0]] = GetStaticFieldExpression(self.class_, self.name, self.type)
        else:
            associations[delta.pushes[0]] = GetFieldExpression(associations[delta.pops[-1]], self.name, self.type)


class PutFieldInstruction(FieldInstruction):
    """
    Sets the value of a field.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        type_ = self.type.to_verification_type()
        frame.pop(type_.internal_size, tuple_=True, expect=type_)
        if not self.static:
            frame.pop(expect=None)

    def lift(self, delta: FrameDelta, scope: "Scope", associations: Dict[Entry, Value]) -> Union[SetFieldStatement, SetStaticFieldStatement]:
        if self.static:
            return SetStaticFieldStatement(self.class_, self.name, associations[delta.pops[-1]])
        else:
            entry = delta.pops[0]
            # TODO: Check if the class reference is the supertype of the current class and substitute it for the super variable
            # if entry.type == types.this_t or entry.type == types.uninit_this_t:
            #     if self.class_ ==
            return SetFieldStatement(
                instance=associations[entry],
                name=self.name,
                value=associations[delta.pops[-1]],
            )

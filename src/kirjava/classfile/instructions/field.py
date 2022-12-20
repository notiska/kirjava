#!/usr/bin/env python3

"""
Fields related instructions.
"""

from abc import ABC
from typing import Any, IO, List, Union

from . import Instruction, MetaInstruction
from .. import descriptor, ClassFile
from ..constants import Class as Class_, FieldRef, NameAndType
from ... import _argument, types
from ...abc import Class
from ...analysis import Error
from ...analysis.trace import _check_reference_type, Entry, State
from ...types import BaseType, ReferenceType
from ...types import ClassOrInterfaceType


class FieldInstruction(Instruction, ABC):
    """
    An instruction that references a field in some way.
    """

    __slots__ = ("class_", "name", "type")

    throws = (types.nullpointerexception_t,)  # FIXME: Get has more specific throws

    get: bool = ...
    static: bool = ...

    def __init__(
            self, class_: Union[ReferenceType, Class, Class_, str], name: str, type: Union[BaseType, str],
    ) -> None:
        """
        :param class_: The class that the field belongs to.
        :param name: The name of the field.
        :param type: The type of the field.
        """

        self.class_ = _argument.get_reference_type(class_)
        self.name = name
        self.type = _argument.get_field_descriptor(type)

    def __repr__(self) -> str:
        return "<FieldInstruction(opcode=0x%x, mnemonic=%s, class=%s, name=%r, type=%s) at %x>" % (
            self.opcode, self.mnemonic, self.class_, self.name, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s#%s %s" % (self.mnemonic, self.class_, self.type, self.name)

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, MetaInstruction) and other == self.__class__) or (
            other.__class__ == self.__class__ and
            other.class_ == self.class_ and
            other.type == self.type and
            other.name == self.name
        )

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)

        field_ref = class_file.constant_pool[self._index]
        self.class_ = field_ref.class_.get_type()
        self.name = field_ref.name_and_type.name
        self.type = descriptor.parse_field_descriptor(field_ref.name_and_type.descriptor)

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if isinstance(self.class_, ClassOrInterfaceType):
            class_ = Class_(self.class_.name)
        else:
            class_ = Class_(descriptor.to_descriptor(self.class_))
        field_ref = FieldRef(class_, NameAndType(self.name, descriptor.to_descriptor(self.type)))
        self._index = class_file.constant_pool.add(field_ref)

        super().write(class_file, buffer, wide)

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        type_ = self.type.to_verification_type()

        if not self.get:
            entry, *_ = state.pop(type_.internal_size, tuple_=True)
            if not type_.can_merge(entry.type):
                errors.append(Error(offset, self, "expected type %s, got %s" % (type_, entry.type)))

        if not self.static:
            entry = state.pop()
            errors.append(_check_reference_type(offset, self, entry.type))

        if self.get:
            state.push(Entry(offset, type_))            

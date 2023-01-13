#!/usr/bin/env python3

"""
Field access instructions.
"""

from abc import ABC
from typing import Any, Dict, IO, List, Union

from . import Instruction
from .. import descriptor, ClassFile
from ..constants import Class as Class_, FieldRef, NameAndType
from ... import _argument, types, verifier
from ...abc import Source, TypeChecker, Value
from ...analysis.ir.field import GetFieldExpression, GetStaticFieldExpression, SetFieldStatement, SetStaticFieldStatement
from ...analysis.trace import Entry, State
from ...types import ClassOrInterfaceType
from ...verifier import Error


class FieldInstruction(Instruction, ABC):
    """
    An instruction that references a field in some way.
    """

    __slots__ = ("class_", "name", "type")

    throws = (types.nullpointerexception_t,)  # FIXME: Get has more specific throws

    get: bool = ...
    static: bool = ...

    def __init__(
            self, class_: "_argument.ReferenceType", name: str, type_: "_argument.FieldDescriptor",
    ) -> None:
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
            other.__class__ is self.__class__ and
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
        if self.class_.__class__ is ClassOrInterfaceType:
            class_ = Class_(self.class_.name)
        else:
            class_ = Class_(descriptor.to_descriptor(self.class_))
        field_ref = FieldRef(class_, NameAndType(self.name, descriptor.to_descriptor(self.type)))
        self._index = class_file.constant_pool.add(field_ref)

        super().write(class_file, buffer, wide)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        type_ = self.type.to_verification_type()

        if not self.get:
            entry, *_ = state.pop(source, type_.internal_size, tuple_=True)
            if not checker.check_merge(type_, entry.type):
                errors.append(Error(
                    Error.Type.INVALID_TYPE, source,
                    "expected type %s" % type_, "got %s (via %s)" % (entry.type, entry.source),
                ))

        if not self.static:
            entry = state.pop(source)
            if not checker.check_reference(entry.type):
                errors.append(Error(
                    Error.Type.INVALID_TYPE, source,
                    "expected reference type", "got %s (via %s)" % (entry.type, entry.source),
                ))

            if self.get:
                state.push(source, type_, parents=(entry,))

        elif self.get:
            state.push(source, type_)

    def lift(
            self, pre: State, post: State, associations: Dict[Entry, Value],
    ) -> Union[SetFieldStatement, SetStaticFieldStatement, None]:
        if self.get:
            if self.static:
                associations[post.stack[-1]] = GetStaticFieldExpression(self.class_, self.name, self.type)
            else:
                associations[post.stack[-1]] = GetFieldExpression(associations[pre.stack[-1]], self.name, self.type)
            return None

        if self.static:
            return SetStaticFieldStatement(self.class_, self.name, associations[pre.stack[-1]])
        else:
            return SetFieldStatement(
                associations[pre.stack[-(1 + pre.stack[-1].type.internal_size)]],
                self.name, associations[pre.stack[-1]],
            )

#!/usr/bin/env python3

__all__ = (
    "FieldInstruction", "GetFieldInstruction", "PutFieldInstruction",
)

"""
Field access instructions.
"""

import typing
from typing import Any, Dict, IO, Union

from . import Instruction
from ..ir.field import *
from ... import types
from ...abc import Value
from ...constants import FieldRef
from ...types import Class

if typing.TYPE_CHECKING:
    from ...analysis import Context
    from ...classfile import ClassFile


class FieldInstruction(Instruction):
    """
    An instruction that references a field in some way.
    """

    __slots__ = ("_index", "reference")

    throws = (Class("java/lang/NullPointerException"),)  # FIXME: Get has more specific throws

    static: bool = ...

    def __init__(self, reference: FieldRef) -> None:
        """
        :param reference: The field reference that this instruction uses.
        """

        self.reference = reference

    def __repr__(self) -> str:
        return "<FieldInstruction(opcode=0x%x, mnemonic=%s, reference=%r) at %x>" % (
            self.opcode, self.mnemonic, self.reference, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.reference)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.reference == self.reference) or other is type(self)

    def copy(self) -> "FieldInstruction":
        return type(self)(self.reference)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.reference = class_file.constant_pool[self._index]

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(self.reference)
        super().write(class_file, buffer, wide)


class GetFieldInstruction(FieldInstruction):
    """
    Gets the value from a field.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        if not self.static:
            context.constrain(context.pop(), self.reference.class_.class_type)
        context.push(self.reference.field_type)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
    #     if self.static:
    #         associations[delta.pushes[0]] = GetStaticFieldExpression(self.reference)
    #     else:
    #         associations[delta.pushes[0]] = GetFieldExpression(associations[delta.pops[-1]], self.reference)


class PutFieldInstruction(FieldInstruction):
    """
    Sets the value of a field.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        *_, entry = context.pop(1 + self.reference.field_type.wide, as_tuple=True)
        context.constrain(entry, self.reference.field_type)
        if not self.static:
            context.constrain(context.pop(), self.reference.class_.class_type)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> Union[SetFieldStatement, SetStaticFieldStatement]:
    #     if self.static:
    #         return SetStaticFieldStatement(associations[delta.pops[-1]], self.reference)
    #     else:
    #         entry = delta.pops[0]
    #         # TODO: Check if the class reference is the supertype of the current class and substitute it for the super variable
    #         # if entry.type == types.this_t or entry.type == types.uninit_this_t:
    #         #     if self.class_ ==
    #         return SetFieldStatement(associations[entry], associations[delta.pops[-1]], self.reference)

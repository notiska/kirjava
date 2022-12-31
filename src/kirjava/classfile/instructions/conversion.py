#!/usr/bin/env python3

"""
Conversion instructions.
"""

from abc import ABC
from typing import Any, IO, List, Union

from . import Instruction, MetaInstruction
from .. import descriptor, ClassFile
from ..constants import Class as Class_
from ... import _argument, types
from ...abc import Class, Error, Source, TypeChecker
from ...analysis.trace import State
from ...types import PrimitiveType, ReferenceType
from ...types.reference import ClassOrInterfaceType


class ConversionInstruction(Instruction, ABC):
    """
    Converts one type into another.
    """

    type_in: PrimitiveType = ...
    type_out: PrimitiveType = ...

    def __repr__(self) -> str:
        return "<ConversionInstruction(opcode=0x%x, mnemonic=%s, type_in=%r, type_out=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type_in, self.type_out, id(self),
        )

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry, *_ = state.pop(source, self.type_in.internal_size, tuple_=True)
        if not checker.check_merge(self.type_in, entry.type):
            errors.append(Error(
                source, "expected type %s" % self.type_in, "got %s (via %s)" % (entry.type, entry.source),
            ))
        state.push(source, self.type_out.to_verification_type(), parents=(entry,))


class TruncationInstruction(ConversionInstruction, ABC):
    """
    Truncates integer primitive types.
    """

    type_in = types.int_t

    def __repr__(self) -> str:
        return "<TruncationInstruction(opcode=0x%x, mnemonic=%s, type_out=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type_out, id(self),
        )


class CheckCastInstruction(Instruction, ABC):
    """
    Checks if the top value on the stack is of a certain type.
    """

    __slots__ = ("type",)

    operands = {"_index": ">H"}
    throws = (types.classcastexception_t,)

    def __init__(self, type_: Union[ReferenceType, Class, Class_, str]) -> None:
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
        return (other.__class__ is self.__class__ and other.type == self.type) or other is self.__class__

    def copy(self) -> "CheckCastInstruction":
        return self.__class__(self.type)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].get_actual_type()

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if isinstance(self.type, ClassOrInterfaceType):
            self._index = class_file.constant_pool.add(Class_(self.type.name))
        else:
            self._index = class_file.constant_pool.add(Class_(descriptor.to_descriptor(self.type)))
        super().write(class_file, buffer, wide)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_reference(entry.type):
            errors.append(Error(source, "expected reference type", "got %s (via %s)" % (entry.type, entry.source)))

        if not entry.type in (types.null_t, self.type):
            # Technically the same entry, so specify the merge entry too
            state.push(source, self.type, parents=(entry,), merges=(entry,))
        else:
            state.push(source, entry)


class InstanceOfInstruction(Instruction, ABC):
    """
    Determines if the top value on the stack is of a certain type.
    """

    __slots__ = ("type",)

    operands = {"_index": ">H"}

    def __init__(self, type_: Union[ReferenceType, Class, Class_, str]) -> None:
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
        return (other.__class__ is self.__class__ and other.type == self.type) or other is self.__class__

    def copy(self) -> "InstanceOfInstruction":
        return self.__class__(self.type)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].get_actual_type()

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if isinstance(self.type, ClassOrInterfaceType):
            self._index = class_file.constant_pool.add(Class_(self.type.name))
        else:
            self._index = class_file.constant_pool.add(Class_(descriptor.to_descriptor(self.type)))
        super().write(class_file, buffer, wide)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_reference(entry.type):
            errors.append(Error(source, "expected reference type", "got %s (via %s)" % (entry.type, entry.source)))
        state.push(source, types.int_t, parents=(entry,))

#!/usr/bin/env python3

"""
Instructions that create new references.
"""

from abc import ABC
from typing import Any, IO, List, Union

from . import Instruction
from .. import descriptor, ClassFile
from ..constants import Class as Class_
from ... import _argument, types
from ...abc import Error, Source, TypeChecker
from ...analysis.trace import State
from ...types import PrimitiveType, ReferenceType
from ...types.reference import ArrayType, ClassOrInterfaceType
from ...types.verification import Uninitialized


class NewInstruction(Instruction, ABC):
    """
    Creates a new class.
    """

    __slots__ = ("type",)

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
        return (other.__class__ is self.__class__ and other.type == self.type) or other is self.__class__

    def copy(self) -> "NewInstruction":
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
        state.push(source, Uninitialized(class_=self.type))


class NewArrayInstruction(Instruction, ABC):
    """
    Creates a new primitive array.
    """

    __slots__ = ("type",)

    operands = {"_atype": ">B"}

    _FORWARD_TYPES = {
        4: types.bool_t,
        5: types.char_t,
        6: types.float_t,
        7: types.double_t,
        8: types.byte_t,
        9: types.short_t,
        10: types.int_t,
        11: types.long_t,
    }
    _BACKWARD_TYPES = {
        types.bool_t: 4,
        types.char_t: 5,
        types.float_t: 6,
        types.double_t: 7,
        types.byte_t: 8,
        types.short_t: 9,
        types.int_t: 10,
        types.long_t: 11,
    }

    def __init__(self, type_: Union[ArrayType, PrimitiveType]) -> None:  # TODO: _argument array type parsing
        """
        :param type_: Either the array type itself, or the element type of the array.
        """

        if not isinstance(type_, ArrayType):
            type_ = ArrayType(type_)

        self.type = type_

    def __repr__(self) -> str:
        return "<NewArrayInstruction(opcode=0x%x, mnemonic=%s, type=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.type)

    def __eq__(self, other: Any) -> bool:
        return (other.__class__ is self.__class__ and other.type == self.type) or other is self.__class__

    def copy(self) -> "NewArrayInstruction":
        return self.__class__(self.type)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = ArrayType(self._FORWARD_TYPES[self._atype])

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        self._atype = self._BACKWARD_TYPES[self.type.element_type]
        super().write(class_file, buffer, wide)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_merge(types.int_t, entry.type):
            errors.append(Error(source, "expected type int", "got %s (via %s)" % (entry.type, entry.source)))
        state.push(source, self.type, parents=(entry,))


class ANewArrayInstruction(Instruction, ABC):
    """
    Creates a new array with a given reference type.
    """

    __slots__ = ("type",)

    operands = {"_index": ">H"}
    throws = (types.negativearraysizeexception_t,)

    def __init__(self, type_: Union[ArrayType, ReferenceType]) -> None:
        """
        :param type_: Either the array type, or the element type in the array.
        """

        if not isinstance(type_, ArrayType):
            type_ = ArrayType(type_)

        self.type = type_

    def __repr__(self) -> str:
        return "<ANewArrayInstruction(opcode=0x%x, mnemonic=%s, type=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.type)

    def __eq__(self, other: Any) -> bool:
        return (other.__class__ is self.__class__ and other.type == self.type) or other is self.__class__

    def copy(self) -> "ANewArrayInstruction":
        return self.__class__(self.type)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].get_actual_type()
        if isinstance(self.type, ArrayType):
            self.type = ArrayType(self.type.element_type, self.type.dimension + 1)
        else:
            self.type = ArrayType(self.type)

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if isinstance(self.type.element_type, ClassOrInterfaceType) and self.type.dimension == 1:
            self._index = class_file.constant_pool.add(Class_(self.type.element_type.name))
        else:
            self._index = class_file.constant_pool.add(Class_(
                descriptor.to_descriptor(ArrayType(self.type.element_type, self.type.dimension - 1)),
            ))
        super().write(class_file, buffer, wide)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_merge(types.int_t, entry.type):
            errors.append(Error(source, "expected type int", "got %s (via %s)" % (entry.type, entry.source)))
        state.push(source, self.type, parents=(entry,))


class MultiANewArrayInstruction(Instruction, ABC):
    """
    Creates a new multidimensional array with the given reference type.
    """

    operands = {"_index": ">H", "dimension": ">B"}

    def __init__(self, type_: Union[ArrayType, ReferenceType], dimension: int) -> None:
        """
        :param type_: Either the array type, or the element type in the array.
        :param dimension: The dimensions of the array to initialise.
        """

        if not isinstance(type_, ArrayType):
            type_ = ArrayType(type_)

        self.type = type_
        self.dimension = dimension

    def __repr__(self) -> str:
        return "<ANewArrayInstruction(opcode=0x%x, mnemonic=%s, type=%r, dimension=%i) at %x>" % (
            self.opcode, self.mnemonic, self.type, self.dimension, id(self),
        )

    def __str__(self) -> str:
        return "%s %s dimension %i" % (self.mnemonic, self.type, self.dimension)

    def __eq__(self, other: Any) -> bool:
        return (
            other.__class__ is self.__class__ and
            other.dimension == self.dimension and
            other.type == self.type
        ) or other is self.__class__

    def copy(self) -> "MultiANewArrayInstruction":
        return self.__class__(self.type, self.dimension)

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].get_actual_type()

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(Class_(descriptor.to_descriptor(self.type)))
        super().write(class_file, buffer, wide)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        if self.dimension > self.type.dimension:
            errors.append(Error(
                source, "instruction dimension exceeds array dimension", "%i > %i" % (self.dimension, self.type.dimension),
            ))

        entries = []
        for index in range(self.dimension):
            entry = state.pop(source)
            entries.append(entry)
            if not checker.check_merge(types.int_t, entry.type):
                errors.append(Error(source, "expected type int", "got %s (via %s)" % (entry.type, entry.source)))

        state.push(source, self.type, parents=tuple(entries))

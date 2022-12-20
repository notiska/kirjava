#!/usr/bin/env python3

"""
Instructions that create new references.
"""

from abc import ABC
from typing import Any, IO, List, Union

from . import Instruction, MetaInstruction
from .. import descriptor, ClassFile
from ..constants import Class as Class_
from ... import _argument, types
from ...abc import Class
from ...analysis import Error
from ...analysis.trace import Entry, State
from ...types import ReferenceType
from ...types.reference import ArrayType, ClassOrInterfaceType
from ...types.verification import Uninitialized


class NewInstruction(Instruction, ABC):
    """
    Creates a new class.
    """

    __slots__ = ("type",)

    operands = {"_index": ">H"}

    def __init__(self, type_: Union[ReferenceType, Class, Class_, str]) -> None:
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
        return (
            (isinstance(other, MetaInstruction) and other == self.__class__) or
            (other.__class__ == self.__class__ and other.type == self.type)
        )

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].get_type()

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if isinstance(self.type, ClassOrInterfaceType):
            self._index = class_file.constant_pool.add(Class_(self.type.name))
        else:
            self._index = class_file.constant_pool.add(Class_(descriptor.to_descriptor(self.type)))
        super().write(class_file, buffer, wide)

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        state.push(Entry(offset, Uninitialized(offset, self.type)))


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

    def __init__(self, type_: ArrayType) -> None:
        self.type = type_

    def __repr__(self) -> str:
        return "<NewArrayInstruction(opcode=0x%x, mnemonic=%s, type=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.type)

    def __eq__(self, other: Any) -> bool:
        return (
            (isinstance(other, MetaInstruction) and other == self.__class__) or
            (other.__class__ == self.__class__ and other.type == self.type)
        )

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = ArrayType(self._FORWARD_TYPES[self._atype])

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        self._atype = self._BACKWARD_TYPES[self.type.element_type]
        super().write(class_file, buffer, wide)

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry = state.pop()
        if not types.int_t.can_merge(entry.type):
            errors.append(Error(offset, self, "expected type int, got %s" % entry.type))
        state.push(Entry(offset, self.type))


class ANewArrayInstruction(Instruction, ABC):
    """
    Creates a new array with a given reference type.
    """

    __slots__ = ("type",)

    operands = {"_index": ">H"}
    throws = (types.negativearraysizeexception_t,)

    def __init__(self, type_: ArrayType) -> None:
        self.type = type_

    def __repr__(self) -> str:
        return "<ANewArrayInstruction(opcode=0x%x, mnemonic=%s, type=%r) at %x>" % (
            self.opcode, self.mnemonic, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s %s" % (self.mnemonic, self.type)

    def __eq__(self, other: Any) -> bool:
        return (
            (isinstance(other, MetaInstruction) and other == self.__class__) or
            (other.__class__ == self.__class__ and other.type == self.type)
        )

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].get_type()
        if not isinstance(self.type, ArrayType):
            self.type = ArrayType(self.type)

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        if isinstance(self.type.element_type, ClassOrInterfaceType) and self.type.dimension == 1:
            self._index = class_file.constant_pool.add(Class_(self.type.element_type.name))
        else:
            self._index = class_file.constant_pool.add(Class_(descriptor.to_descriptor(self.type)))
        super().write(class_file, buffer, wide)

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry = state.pop()
        if not types.int_t.can_merge(entry.type):
            errors.append(Error(offset, self, "expected type int, got %s" % entry.type))
        state.push(Entry(offset, self.type))


class MultiANewArrayInstruction(ANewArrayInstruction, ABC):
    """
    Creates a new multidimensional array with the given reference type.
    """

    __slots__ = ("dimension",)

    operands = {"_index": ">H", "_dimension": ">B"}

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        super().read(class_file, buffer, wide)
        self.type = class_file.constant_pool[self._index].get_type()
        if not isinstance(self.type, ArrayType):
            self.type = ArrayType(self.type, self._dimension)
        # TODO: Need to verify dimensions of the target array?

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        self._index = class_file.constant_pool.add(Class_(descriptor.to_descriptor(self.type)))
        self._dimension = self.type.dimension
        super().write(class_file, buffer, wide)

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        for index in range(self.type.dimension):
            entry = state.pop()
            if not types.int_t.can_merge(entry.type):
                errors.append(Error(offset, self, "expected type int, got %s" % entry.type))

        state.push(Entry(offset, self.type))

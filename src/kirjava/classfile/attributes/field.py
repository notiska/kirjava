#!/usr/bin/env python3

__all__ = (
    "ConstantValue",
)

"""
Attributes that are only found in fields info structures.
"""

from typing import IO, Union

from . import AttributeInfo
from .. import ClassFile
from .._struct import *
from ..constants import ConstantInfo
from ..members import FieldInfo
from ...version import Version


class ConstantValue(AttributeInfo):
    """
    Present in a field if it is static, final and has a value that can be stored in the constant pool.
    """

    __slots__ = ("value",)

    name_ = "ConstantValue"
    since = Version(45, 0)
    locations = (FieldInfo,)

    def __init__(self, parent: FieldInfo, value: Union[ConstantInfo, None] = None) -> None:
        super().__init__(parent, ConstantValue.name_)

        self.value = value

    def __repr__(self) -> str:
        return "<ConstantValue(%r) at %x>" % (self.value, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes], fail_fast: bool = True) -> None:
        value_index, = unpack_H(buffer.read(2))
        self.value = class_file.constant_pool[value_index]

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add(self.value)))

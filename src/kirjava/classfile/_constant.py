#!/usr/bin/env python3

__all__ = (
    "ConstantPool", "Index"
)

import logging
import typing
from typing import Any, IO, Iterable

from .._struct import *
from ..constants import _constant_map, Class, ConstantInfo, String, UTF8
from ..version import Version

if typing.TYPE_CHECKING:
    from . import ClassFile

logger = logging.getLogger("kirjava.classfile._constant")


class Index(ConstantInfo):
    """
    A special type of constant that represents an invalid index in the constant pool.
    """

    __slots__ = ("index",)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> None:
        raise Exception("Tried to read index type.")

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to dereference index type.")

    def __init__(self, index: int) -> None:
        """
        :param index: The constant pool index.
        """

        super().__init__(index)
        self.index = index

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        ...


class ConstantPool:
    """
    The constant pool structure.
    """

    __slots__ = ("min_deref", "_index", "_forward_entries", "_backward_entries")

    @classmethod
    def read(cls, version: Version, buffer: IO[bytes]) -> "ConstantPool":
        """
        Reads a constant pool from a buffer.

        :param version: The version of the classfile.
        :param buffer: The binary buffer to read from.
        :return: The constant pool that was read.
        """

        constant_pool = cls()

        constants_count, = unpack_H(buffer.read(2))
        # logger.debug("Reading %i constant pool entries..." % (constants_count - 1))

        uncomputed = []  # Constants we haven't computed yet
        offset = 1  # The constant pool starts at offset 1

        while offset < constants_count:
            tag, = buffer.read(1)
            constant = _constant_map.get(tag)
            if constant is None:
                raise ValueError("Unknown constant tag: %i." % tag)
            if constant.since > version:
                raise ValueError("Constant %r is not supported in version %s." % (constant, version))

            info = constant.read(buffer)

            if isinstance(info, ConstantInfo):
                constant_pool._forward_entries[offset] = info
                constant_pool._backward_entries[info] = offset
            else:
                uncomputed.append((offset, constant, info))

            offset += 1
            if constant.wide:
                offset += 1

        constant_pool._index = offset

        # FIXME: Could cause an infinite loop, check for this
        while uncomputed:
            offset, constant, info = uncomputed.pop(0)
            value = constant.dereference(constant_pool._forward_entries, info)
            if value is None:
                uncomputed.append((offset, constant, info))
                continue

            constant_pool._forward_entries[offset] = value
            constant_pool._backward_entries[value] = offset

        return constant_pool

    @property
    def entries(self) -> dict[int, ConstantInfo]:
        """
        :return: A dictionary containing the forward entries in the pool.
        """

        return self._forward_entries.copy()

    def __init__(self) -> None:
        self.min_deref = False
        self._index = 1

        self._forward_entries: dict[int, ConstantInfo] = {}
        self._backward_entries: dict[ConstantInfo, int] = {}

    def __repr__(self) -> str:
        return "<ConstantPool(size=%i) at %x>" % (len(self), id(self))

    def __iter__(self) -> Iterable[tuple[int, ConstantInfo]]:
        return iter(self._forward_entries.items())

    def __getitem__(self, item: Any) -> ConstantInfo | int:
        if type(item) is int:
            if self.min_deref:
                return Index(item)
            constant = self._forward_entries.get(item)
            if constant is not None:
                return constant
            return Index(item)

        elif isinstance(item, ConstantInfo):
            if type(item) is Index:
                return item.value
            return self._backward_entries[item]

        raise TypeError("Type %r is not a valid index for %r." % (type(item), self))

    def __setitem__(self, index: int, item: Any) -> None:
        if isinstance(item, ConstantInfo):
            if type(item) is Index:
                return  # Nothing to do here

            self._forward_entries[index] = item
            self._backward_entries[item] = index

            if index >= self._index:
                self._index = index + 1
                if item.wide:
                    self._index += 1

            return

        raise TypeError("Type %r is not a valid constant for %r." % (type(item), self))

    def __contains__(self, item: Any) -> bool:
        if type(item) is int:
            return item in self._forward_entries
        elif isinstance(item, ConstantInfo):
            return item in self._backward_entries

        return False

    def __len__(self) -> int:
        return len(self._forward_entries)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Writes this constant pool to a buffer.

        :param class_file: The class file that this constant pool belongs to.
        :param buffer: The binary buffer to write to.
        """

        start = buffer.tell()
        buffer.write(b"\x00\x00")  # Placeholder bytes so we can seek back to them

        offset = 1
        while offset < self._index:
            constant = self._forward_entries[offset]
            buffer.write(bytes((constant.tag,)))
            constant.write(class_file, buffer)

            offset += 1
            if constant.wide:
                offset += 1

        # Now overwrite the old placeholder bytes with the max offset
        current = buffer.tell()

        buffer.seek(start)
        buffer.write(pack_H(offset))
        buffer.seek(current)

    # ------------------------------ Public API ------------------------------ #

    def get(self, index: int, default: ConstantInfo | None = None, do_raise: bool = False) -> ConstantInfo:
        """
        Gets the constant at a given index.

        :param index: The index of the constant.
        :param default: The default value to get if the constant doesn't exist.
        :param do_raise: Raises an error if the index is invalid.
        :return: The constant at that index.
        """

        if self.min_deref:
            return Index(index)

        constant = self._forward_entries.get(index)
        if constant is not None:
            return constant
        if default is not None:
            return default

        if do_raise:
            raise IndexError("Constant pool index %i is not defined." % index)

        return Index(index)

    def get_utf8(self, index: int, default: str | None = None, *, do_raise: bool = True) -> str:
        """
        Gets a UTF-8 value at the given index.

        :param index: The index of the constant.
        :param default: The value to default to if not found.
        :param do_raise: Should we raise an exception if the index is invalid?
        :return: The UTF-8 value of the constant.
        """

        constant = self._forward_entries.get(index)
        if constant is None:
            if not do_raise or default is not None:
                return default
            raise ValueError("Index %i not in constant pool." % index)
        elif type(constant) is not UTF8:
            if not do_raise or default is not None:
                return default
            raise TypeError("Index %i is not a valid UTF-8 constant." % index)

        return constant.value

    def clear(self) -> None:
        """
        Clears this constant pool.
        """

        self._index = 1
        self._forward_entries.clear()
        self._backward_entries.clear()

    def add(self, constant: ConstantInfo | str) -> int:
        """
        Adds a constant to this constant pool.

        :param constant: The constant to add, could also be a string (in this case it'll be added as a UTF8 constant).
        :return: The index of the added constant.
        """

        if type(constant) is str:
            constant = UTF8(constant)
        elif type(constant) is Index:
            return constant.value

        index = self._backward_entries.get(constant)
        if index is not None:
            return index

        self._forward_entries[self._index] = constant
        self._backward_entries[constant] = self._index

        index = self._index
        self._index += 1
        if constant.wide:
            self._index += 1

        return index

    def add_utf8(self, value: str) -> int:
        """
        Adds a UTF8 constant to this constant pool.

        :param value: The value of the UTF8 constant.
        :return: The index of the added constant.
        """

        return self.add(value)

    def add_class(self, name: str) -> int:
        """
        Adds a class constant to this constant pool.

        :param name: The name of the class.
        :return: The index of the added constant.
        """

        return self.add(Class(name))

    def add_string(self, value: str) -> int:
        """
        Adds a string constant to this constant pool.

        :param value: The value of the string constant.
        :return: The index of the added constant.
        """

        return self.add(String(value))

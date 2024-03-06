#!/usr/bin/env python3

__all__ = (
    "Code", "Exceptions",
)

"""
Attributes that are only found in method info structures.
"""

import logging
import typing
from io import BytesIO
from typing import IO, Iterable, Optional

from . import AttributeInfo
from .code import LineNumberTable, LocalVariableTable, LocalVariableTypeTable, StackMapTable
from .. import _instructions, attributes
from ..._struct import *
from ...constants import Class
from ...version import Version

if typing.TYPE_CHECKING:
    from .. import ClassFile, MethodInfo
    from ...instructions import Instruction

logger = logging.getLogger("kirjava.classfile.attributes.method")


class Code(AttributeInfo):
    """
    Contains the bytecode of the method, as well as other pieces of metadata.
    """

    __slots__ = ("__weakref__", "max_stack", "max_locals", "instructions", "exception_table", "attributes")

    name_ = "Code"
    since = Version(45, 0)
    locations = ("MethodInfo",)

    _LEGACY_VERSION = Version(45, 3)

    @property
    def stackmap_table(self) -> Optional["StackMapTable"]:
        """
        :return: The stackmap table in this code, or None if there isn't one.
        """

        stackmap_table, *_ = self.attributes.get(StackMapTable.name_, (None,))
        return stackmap_table

    @stackmap_table.setter
    def stackmap_table(self, value: Optional["StackMapTable"]) -> None:
        if value is None:
            self.attributes.pop(StackMapTable.name_, None)
        else:
            self.attributes[value.name] = (value,)

    @property
    def line_number_table(self) -> Optional["LineNumberTable"]:
        """
        :return: The line number table in this code, or None if there isn't one.
        """

        line_number_table, *_ = self.attributes.get(LineNumberTable.name_, (None,))
        return line_number_table

    @line_number_table.setter
    def line_number_table(self, value: Optional["LineNumberTable"]) -> None:
        if value is None:
            self.attributes.pop(LineNumberTable.name_, None)
        else:
            self.attributes[value.name] = (value,)

    @property
    def local_variable_table(self) -> Optional["LocalVariableTable"]:
        """
        :return: The local variable table in this code, or None if there isn't one.
        """

        local_variable_table, *_ = self.attributes.get(LocalVariableTable.name_, (None,))
        return local_variable_table

    @local_variable_table.setter
    def local_variable_table(self, value: Optional["LocalVariableTable"]) -> None:
        if value is None:
            self.attributes.pop(LocalVariableTable.name_, None)
        else:
            self.attributes[value.name] = (value,)

    @property
    def local_variable_type_table(self) -> Optional["LocalVariableTypeTable"]:
        """
        :return: The local variable type table in this code, or None if there isn't one.
        """

        local_variable_type_table, *_ = self.attributes.get(LocalVariableTypeTable.name_, (None,))
        return local_variable_type_table

    @local_variable_type_table.setter
    def local_variable_type_table(self, value: Optional["LocalVariableTypeTable"]) -> None:
        if value is None:
            self.attributes.pop(LocalVariableTypeTable.name_, None)
        else:
            self.attributes[value.name] = (value,)

    def __init__(self, parent: "MethodInfo", max_stack: int = 0, max_locals: int = 0) -> None:
        """
        :param max_stack: The maximum stack depth the code will reach.
        :param max_locals: The maximum number of locals.
        """

        super().__init__(parent, Code.name_)

        self.max_stack = max_stack
        self.max_locals = max_locals

        self.instructions: dict[int, "Instruction"] = {}
        self.exception_table: list[Code.ExceptionHandler] = []
        self.attributes: dict[str, tuple[AttributeInfo, ...]] = {}

    def __repr__(self) -> str:
        return "<Code(max_stack=%i, max_locals=%i, exception_table=%r) at %x>" % (
            self.max_stack, self.max_locals, self.exception_table, id(self),
        )

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        # Legacy code attribute for versions <= 45.2.
        # https://github.com/Storyyeller/Krakatau/blob/master/tests/decompiler/source/OldVersionTest.j
        if class_file.version < self._LEGACY_VERSION:
            self.max_stack, self.max_locals, code_length = unpack_BBH(buffer.read(4))
        else:
            self.max_stack, self.max_locals, code_length = unpack_HHI(buffer.read(8))

        self.instructions.clear()
        # Copy to a new BytesIO object as some instructions are byte-aligned to the start of the code
        self.instructions.update(_instructions.read_instructions(
            class_file, BytesIO(buffer.read(code_length)), code_length,
        ))

        self.exception_table.clear()
        exception_table_length, = unpack_H(buffer.read(2))
        for index in range(exception_table_length):
            self.exception_table.append(Code.ExceptionHandler.read(class_file, buffer))

        self.attributes.clear()
        attributes_count, = unpack_H(buffer.read(2))
        for index in range(attributes_count):
            attribute_info = attributes.read_attribute(self, class_file, buffer, fail_fast)
            self.attributes[attribute_info.name] = self.attributes.setdefault(attribute_info.name, ()) + (attribute_info,)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        code = BytesIO()
        _instructions.write_instructions(self.instructions, class_file, code)
        code = code.getvalue()

        if class_file.version < self._LEGACY_VERSION:
            buffer.write(pack_BBH(self.max_stack, self.max_locals, len(code)))
        else:
            buffer.write(pack_HHI(self.max_stack, self.max_locals, len(code)))

        buffer.write(code)

        buffer.write(pack_H(len(self.exception_table)))
        for exception in self.exception_table:
            exception.write(class_file, buffer)

        attributes_ = []
        for attributes__ in self.attributes.values():
            attributes_.extend(attributes__)

        buffer.write(pack_H(len(attributes_)))
        for attribute in attributes_:
            attributes.write_attribute(attribute, class_file, buffer)

    class ExceptionHandler:
        """
        An entry in the exception table.
        """

        __slots__ = ("start_pc", "end_pc", "handler_pc", "catch_type")

        @classmethod
        def read(cls, class_file: "ClassFile", buffer: IO[bytes]) -> "Code.ExceptionHandler":
            """
            Reads an exception handler from the buffer.

            :param class_file: The class file that the exception handler belongs to.
            :param buffer: The binary buffer to read from.
            :return: The exception handler that was read.
            """

            handler = cls.__new__(cls)

            (
                handler.start_pc,
                handler.end_pc,
                handler.handler_pc,
                catch_type_index,
            ) = unpack_HHHH(buffer.read(8))

            handler.catch_type = class_file.constant_pool[catch_type_index] if catch_type_index else None

            return handler

        def __init__(self, start_pc: int, end_pc: int, handler_pc: int, catch_type: Class | None) -> None:
            """
            :param start_pc: The starting bytecode offset of the exception handler.
            :param end_pc The ending bytecode offset of the exception handler.
            :param handler_pc: The bytecode offset of the handler jump start.
            :param catch_type: The type of exception being caught.
            """

            self.start_pc = start_pc
            self.end_pc = end_pc
            self.handler_pc = handler_pc
            self.catch_type = catch_type

        def __repr__(self) -> str:
            return "<ExceptionHandler(start=%i, end=%i, handler=%i, catch_type=%s) at %x>" % (
                self.start_pc, self.end_pc, self.handler_pc, self.catch_type, id(self),
            )

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            """
            Writes this exception handler to the buffer.

            :param class_file: The class file that this handler belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(pack_HHHH(
                self.start_pc,
                self.end_pc,
                self.handler_pc,
                0 if self.catch_type is None else class_file.constant_pool.add(self.catch_type),
            ))


class Exceptions(AttributeInfo):
    """
    Records checked exceptions that the method may throw.
    """

    __slots__ = ("exceptions",)

    name_ = "Exceptions"
    since = Version(45, 0)
    locations = ("MethodInfo",)

    def __init__(self, parent: "MethodInfo", exceptions: Iterable[Class] | None = None) -> None:
        super().__init__(parent, Exceptions.name_)

        self.exceptions: list[Class] = []
        if exceptions is not None:
            self.exceptions.extend(exceptions)

    def __repr__(self) -> str:
        return "<Exceptions(exceptions=%r) at %x>" % (self.exceptions, id(self))

    def __iter__(self) -> Iterable[Class]:
        return iter(self.exceptions)

    def __getitem__(self, index: int) -> Class:
        return self.exceptions[index]

    def __setitem__(self, index: int, value: Class) -> None:
        self.exceptions[index] = value

    def __contains__(self, item: Class) -> bool:
        return item in self.exceptions

    def __len__(self) -> int:
        return len(self.exceptions)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.exceptions.clear()
        exceptions_count, = unpack_H(buffer.read(2))
        for index in range(exceptions_count):
            class_index, = unpack_H(buffer.read(2))
            self.exceptions.append(class_file.constant_pool.get(class_index, do_raise=fail_fast))

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(len(self.exceptions)))
        for exception in self.exceptions:
            buffer.write(pack_H(class_file.constant_pool.add(exception)))

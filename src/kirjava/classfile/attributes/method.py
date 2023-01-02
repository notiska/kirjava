#!/usr/bin/env python3

__all__ = (
    "Code", "Exceptions",
)

"""
Attributes that are only found in method info structures.
"""

import logging
import struct
from io import BytesIO
from typing import Dict, IO, Iterable, List, Tuple, Union

from . import AttributeInfo
from .code import StackMapTable
from .. import attributes, ClassFile
from ..constants import Class
from ..members import MethodInfo
from ...version import Version

logger = logging.getLogger("kirjava.classfile.attributes.method")


class Code(AttributeInfo):
    """
    Contains the bytecode of the method, as well as other pieces of metadata.
    """

    __slots__ = ("max_stack", "max_locals", "instructions", "exception_table", "attributes")

    name_ = "Code"
    since = Version(45, 0)
    locations = (MethodInfo,)

    _LEGACY_VERSION = Version(45, 3)

    @property
    def stackmap_table(self) -> Union["StackMapTable", None]:
        """
        :return: The stackmap table in this code, or None if there isn't one.
        """

        stackmap_table, *_ = self.attributes.get(StackMapTable.name_, (None,))
        return stackmap_table

    @stackmap_table.setter
    def stackmap_table(self, value: Union["StackMapTable", None]) -> None:
        """
        Sets the stackmap table attribute in this code.
        """

        if value is None:
            del self.attributes[StackMapTable.name_]
        else:
            self.attributes[value.name] = (value,)

    def __init__(self, parent: MethodInfo, max_stack: int = 0, max_locals: int = 0) -> None:
        """
        :param max_stack: The maximum stack depth the code will reach.
        :param max_locals: The maximum number of locals.
        """

        super().__init__(parent, Code.name_)

        self.max_stack = max_stack
        self.max_locals = max_locals

        self.instructions: Dict[int, Instruction] = {}
        self.exception_table: List[Code.ExceptionHandler] = []
        self.attributes: Dict[str, Tuple[AttributeInfo, ...]] = {}

    def __repr__(self) -> str:
        return "<Code(max_stack=%i, max_locals=%i, exception_table=%r) at %x>" % (
            self.max_stack, self.max_locals, self.exception_table, id(self),
        )

    def read(self, class_file: ClassFile, buffer: IO[bytes], fail_fast: bool = True) -> None:
        # Legacy code attribute for versions <= 45.2.
        # https://github.com/Storyyeller/Krakatau/blob/master/tests/decompiler/source/OldVersionTest.j
        if class_file.version < self._LEGACY_VERSION:
            self.max_stack, self.max_locals, code_length = struct.unpack(">BBH", buffer.read(4))
        else:
            self.max_stack, self.max_locals, code_length = struct.unpack(">HHI", buffer.read(8))

        self.instructions.clear()
        # Copy to a new BytesIO object as some instructions are byte-aligned to the start of the code
        self.instructions.update(instructions.read_instructions(
            class_file, BytesIO(buffer.read(code_length)), code_length,
        ))

        self.exception_table.clear()
        exception_table_length, = struct.unpack(">H", buffer.read(2))
        for index in range(exception_table_length):
            self.exception_table.append(Code.ExceptionHandler.read(class_file, buffer))

        self.attributes.clear()
        attributes_count, = struct.unpack(">H", buffer.read(2))
        for index in range(attributes_count):
            attribute_info = attributes.read_attribute(self, class_file, buffer, fail_fast)
            self.attributes[attribute_info.name] = self.attributes.setdefault(attribute_info.name, ()) + (attribute_info,)

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        code = BytesIO()
        instructions.write_instructions(self.instructions, class_file, code)
        code = code.getvalue()

        if class_file.version < self._LEGACY_VERSION:
            buffer.write(struct.pack(">BBH", self.max_stack, self.max_locals, len(code)))
        else:
            buffer.write(struct.pack(">HHI", self.max_stack, self.max_locals, len(code)))

        buffer.write(code)

        buffer.write(struct.pack(">H", len(self.exception_table)))
        for exception in self.exception_table:
            exception.write(class_file, buffer)

        buffer.write(struct.pack(">H", len(self.attributes)))
        for attributes_ in self.attributes.values():
            for attribute in attributes_:
                attributes.write_attribute(attribute, class_file, buffer)

    class ExceptionHandler:
        """
        An entry in the exception table.
        """

        __slots__ = ("start_pc", "end_pc", "handler_pc", "catch_type")

        @classmethod
        def read(cls, class_file: ClassFile, buffer: IO[bytes]) -> "Code.ExceptionHandler":
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
            ) = struct.unpack(">HHHH", buffer.read(8))

            handler.catch_type = class_file.constant_pool[catch_type_index] if catch_type_index else None

            return handler

        def __init__(self, start_pc: int, end_pc: int, handler_pc: int, catch_type: Class) -> None:
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

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            """
            Writes this exception handler to the buffer.

            :param class_file: The class file that this handler belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(struct.pack(
                ">HHHH",
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
    locations = (MethodInfo,)

    def __init__(self, parent: MethodInfo, exceptions: Union[Iterable[Class], None] = None) -> None:
        super().__init__(parent, Exceptions.name_)

        self.exceptions: List[Class] = []
        if exceptions is not None:
            self.exceptions.extend(exceptions)

    def __repr__(self) -> str:
        return "<Exceptions(%r) at %x>" % (self.exceptions, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.exceptions.clear()
        exceptions_count, = struct.unpack(">H", buffer.read(2))
        for index in range(exceptions_count):
            class_index, = struct.unpack(">H", buffer.read(2))
            self.exceptions.append(class_file.constant_pool.get(class_index, fail_fast))

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", len(self.exceptions)))
        for exception in self.exceptions:
            buffer.write(struct.pack(">H", class_file.constant_pool.add(exception)))


from .. import instructions
from ..instructions import Instruction

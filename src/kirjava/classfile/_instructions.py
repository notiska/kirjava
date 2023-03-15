#!/usr/bin/env python3

__all__ = (
    "read_instructions", "write_instructions",
)

"""
Reads instructions from binary data.
"""

import operator
import typing
from typing import Dict, IO

from . import ClassFile
from ..instructions import jvm as instructions

if typing.TYPE_CHECKING:
    from ..instructions.jvm import Instruction


def read_instructions(class_file: ClassFile, buffer: IO[bytes], length: int) -> Dict[int, "Instruction"]:
    """
    Reads a list of instructions from the provided buffer.

    :param class_file: The classfile that the instructions belong to.
    :param buffer: The binary buffer to read from.
    :param length: The number of bytes to read.
    :return: The list of instructions (and their offsets) that were read.
    """

    instructions_ = {}

    offset = buffer.tell()
    wide = False

    while offset < length:
        opcode, = buffer.read(1)
        instruction = instructions._opcode_map.get(opcode, None)
        if instruction is None:
            raise ValueError("Unknown opcode: 0x%x." % opcode)
        instruction = instruction.__new__(instruction)
        instruction.read(class_file, buffer, wide)

        instructions_[offset] = instruction
        # print(offset, "\t", instruction)

        offset = buffer.tell()
        wide = instruction == instructions.wide

    return instructions_


def write_instructions(instructions_: Dict[int, "Instruction"], class_file: ClassFile, buffer: IO[bytes]) -> None:
    """
    Writes a list of instructions to the buffer.

    :param instructions_: The instructions to write.
    :param class_file: The classfile that the instructions belong to.
    :param buffer: The binary buffer to write to.
    """

    wide = False
    for offset, instruction in sorted(instructions_.items(), key=operator.itemgetter(0)):
        buffer.write(bytes((instruction.opcode,)))
        instruction.write(class_file, buffer, wide)

        wide = instruction == instructions.wide

#!/usr/bin/env python3

__all__ = (
    "read_instructions", "write_instructions",
)

"""
Reads instructions from binary data.
"""

import operator
import typing
from typing import IO

from ..instructions import wide, INSTRUCTIONS, Instruction

if typing.TYPE_CHECKING:
    from . import ClassFile

# Some hacky stuff to make reading instructions faster follows!!! Beware!!!
_immutable_opcode_map = {}
_mutable_opcode_map = {}
wide = wide()

for instruction in INSTRUCTIONS:
    if not instruction.operands:
        _immutable_opcode_map[instruction.opcode] = instruction()
    else:
        _mutable_opcode_map[instruction.opcode] = instruction


def read_instructions(class_file: "ClassFile", buffer: IO[bytes], length: int) -> dict[int, Instruction]:
    """
    Reads a list of instructions from the provided buffer.

    :param class_file: The classfile that the instructions belong to.
    :param buffer: The binary buffer to read from.
    :param length: The number of bytes to read.
    :return: The list of instructions (and their offsets) that were read.
    """

    instructions_ = {}

    offset = buffer.tell()
    is_wide = False

    while offset < length:
        opcode, = buffer.read(1)

        instruction = _immutable_opcode_map.get(opcode)
        if instruction is None:
            instruction = _mutable_opcode_map.get(opcode)
            if instruction is None:
               raise ValueError("Unknown opcode: 0x%x at offset %i." % (opcode, offset))
            instruction = instruction.__new__(instruction)
            instruction.read(class_file, buffer, is_wide)
        else:  # We only do this here as we know that the wide instruction is immutable.
            is_wide = instruction is wide

        instructions_[offset] = instruction
        # print(offset, "\t", instruction)

        offset = buffer.tell()

    return instructions_


def write_instructions(instructions_: dict[int, Instruction], class_file: "ClassFile", buffer: IO[bytes]) -> None:
    """
    Writes a list of instructions to the buffer.

    :param instructions_: The instructions to write.
    :param class_file: The classfile that the instructions belong to.
    :param buffer: The binary buffer to write to.
    """

    is_wide = False  # FIXME: Speed up
    for offset, instruction in sorted(instructions_.items(), key=operator.itemgetter(0)):
        buffer.write(bytes((instruction.opcode,)))
        instruction.write(class_file, buffer, is_wide)

        is_wide = instruction is wide

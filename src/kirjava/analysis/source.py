#!/usr/bin/env python3

__all__ = (
    "InstructionAtOffset", "InstructionInBlock",
)

"""
Different sources for this package.
"""

import typing
from typing import Any

from ..abc import Source

if typing.TYPE_CHECKING:
    from ._block import InsnBlock
    from ..classfile.attributes.method import Code
    from ..instructions.jvm import Instruction


class InstructionAtOffset(Source):
    """
    A source that contains the exact location of an instruction via its code attribute and the bytecode offset it's at.
    """

    __slots__ = ("code", "instruction", "offset")

    def __init__(self, code: "Code", instruction: "Instruction", offset: int) -> None:
        self.code = code
        self.instruction = instruction
        self.offset = offset

    def __repr__(self) -> str:
        return "<InstructionAtOffset(code=%r, instruction=%s, offset=%i) at %x>" % (
            self.code, self.instruction, self.offset, id(self),
        )

    def __str__(self) -> str:
        return "%s @ %i:%s" % (self.instruction, self.offset, self.code.parent)

    def __eq__(self, other: Any) -> bool:
        return type(other) is InstructionAtOffset and other.code == self.code and other.offset == self.offset

    def __hash__(self) -> int:
        return hash((self.instruction.opcode, self.offset))


class InstructionInBlock(Source):
    """
    A source that contains the exact location of an instruction via the block it's in and the index it's at in the block.
    """

    __slots__ = ("block", "instruction", "index")

    def __init__(self, block: "InsnBlock", instruction: "Instruction", index: int) -> None:
        self.block = block
        self.instruction = instruction
        self.index = index

    def __repr__(self) -> str:
        return "<InstructionInBlock(block=%r, instruction=%s, index=%i) at %x>" % (
            self.block, self.instruction, self.index, id(self),
        )

    def __str__(self) -> str:
        return "%s @ %i:%s" % (self.instruction, self.index, self.block)

    def __eq__(self, other: Any) -> bool:
        return type(other) is InstructionInBlock and other.block == self.block and other.index == self.index

    def __hash__(self) -> int:
        return hash((self.block.label, self.instruction.opcode, self.index))

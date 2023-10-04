#!/usr/bin/env python3

__all__ = (
    "InstructionAtOffset", "InstructionInBlock",
)

"""
Different sources for this package.
"""

import typing
from typing import Any

from .abc import Offset, Source

if typing.TYPE_CHECKING:
    from .analysis import InsnBlock
    from .instructions import Instruction


class InstructionAtOffset(Offset):
    """
    A source that contains the exact location of an instruction via the bytecode offset it's at.
    """

    __slots__ = ("code", "instruction", "_hash")

    def __init__(self, offset: int, instruction: "Instruction") -> None:
        super().__init__(offset)
        self.instruction = instruction

        self._hash = hash((offset, instruction.opcode))

    def __repr__(self) -> str:
        return "<InstructionAtOffset(offset=%i, instruction=%s)>" % (self.offset, self.instruction)

    def __str__(self) -> str:
        return "%s @ %i" % (self.instruction, self.offset)

    def __eq__(self, other: Any) -> bool:
        return type(other) is InstructionAtOffset and other.offset == self.offset and other.instruction == self.instruction

    def __hash__(self) -> int:
        return self._hash


class InstructionInBlock(Source):
    """
    A source that contains the exact location of an instruction via the block it's in and the index it's at in the block.
    """

    __slots__ = ("index", "block", "instruction", "_hash")

    def __init__(self, index: int, block: "InsnBlock", instruction: "Instruction") -> None:
        self.index = index
        self.block = block
        self.instruction = instruction

        self._hash = hash((index, block.label, instruction.opcode))

    def __repr__(self) -> str:
        return "<InstructionInBlock(index=%i, block=%s, instruction=%s)>" % (self.index, self.block, self.instruction)

    def __str__(self) -> str:
        return "%s @ %s[%i]" % (self.instruction, self.block, self.index)

    def __eq__(self, other: Any) -> bool:
        return type(other) is InstructionInBlock and other.index == self.index and other.block == self.block

    def __hash__(self) -> int:
        return self._hash

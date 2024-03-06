#!/usr/bin/env python3

__all__ = (
    "InsnBlock", "InsnReturnBlock", "InsnRethrowBlock",
)

import typing
from typing import Any, Iterable, Iterator

from .debug import *
from ... import instructions
from ...abc import Block, RethrowBlock, ReturnBlock
from ...instructions import Instruction, JumpInstruction, ReturnInstruction
from ...source import InstructionInBlock

if typing.TYPE_CHECKING:
    from .. import Context


class InsnBlock(Block):
    """
    A block containing Java instructions.
    """

    __slots__ = ("_instructions", "inline", "_hash")

    @property
    def instructions(self) -> tuple[Instruction, ...]:
        """
        :return: A tuple of the instructions in this block, cos I keep forgetting this is iterable.
        """

        return tuple(self._instructions)

    def __init__(self, label: int, instructions_: Iterable[Instruction] | None = None) -> None:
        """
        :param label: The label of this block.
        :param instructions_: JVM instructions to initialise this block with.
        """

        super().__init__(label)

        self._instructions: list[Instruction] = []
        self.inline = False  # Can this block be inlined?

        if instructions_ is not None:
            self._instructions.extend(instructions_)

        self._hash = id(self)

    def __repr__(self) -> str:
        # TODO: Pretty printing compatibility?
        return "<InsnBlock(label=%s, instructions=[%s]) at %x>" % (
            self.label, ", ".join(map(str, self._instructions)), id(self),
        )

    def __eq__(self, other: Any) -> bool:
        return other is self

    def __hash__(self) -> int:
        # 42.9ns -> 14.5ns
        # 209ms (5.8%) -> 71ms (2.1%)
        # Funnily enough this is faster than the default behaviour, lol. I'll take an extra 2.7%.
        # TODO: Need to be checking for future versions of Python to see if they improve this behaviour.
        return self._hash  # id(self)

    def __iter__(self) -> Iterator[Instruction]:
        return iter(self._instructions)

    def __getitem__(self, item: Any) -> tuple[Instruction, ...] | Instruction:
        return self._instructions[item]

    def __setitem__(self, key: Any, value: Any) -> None:
        if type(key) is int or type(key) is slice:
            if type(value) is type:
                value = value()
            if not isinstance(value, Instruction):
                raise ValueError("Expected an instruction, got %r." % value)

            self._check_instruction(value)
            self._instructions[key] = value
        else:
            raise TypeError("Expected int, got %r." % type(key))

    def __delitem__(self, item: Any) -> None:
        if type(item) is int or type(item) is slice:
            del self._instructions[item]

    def __contains__(self, item: Any) -> bool:
        return item in self._instructions

    def __len__(self) -> int:
        return len(self._instructions)

    def __bool__(self) -> bool:
        return bool(self._instructions)

    def copy(self, label: int | None = None, deep: bool = True) -> "InsnBlock":
        block = InsnBlock(label or self.label)
        block.inline = self.inline

        if not deep:
            block._instructions.extend(self._instructions)
        else:
            block._instructions.extend([instruction.copy() for instruction in self._instructions])

        return block

    def trace(self, context: "Context") -> None:
        for index, instruction in enumerate(self._instructions):
            context.source = InstructionInBlock(index, self, instruction)
            instruction.trace(context)

    # ------------------------------ Utility ------------------------------ #

    def _check_instruction(self, instruction: Instruction) -> None:
        """
        Checks that an instruction can be added to this block. Throws if not the case.
        """

        if isinstance(instruction, JumpInstruction):
            raise ValueError(
                "Cannot add a jump instruction directly, use graph.jump() instead, or use do_raise=False to ignore this.",
            )
        elif isinstance(instruction, ReturnInstruction):
            raise ValueError(
                "Cannot add a return instruction directly, use graph.return_() instead, or use do_raise=False to ignore this.",
            )
        elif instruction == instructions.athrow:
            raise ValueError(
                "Cannot add an athrow instruction directly, use graph.throw() instead, or use do_raise=False to ignore this.",
            )

    # ------------------------------ Public API ------------------------------ #

    def append(self, instruction: type[Instruction] | Instruction, do_raise: bool = True) -> Instruction:
        """
        Adds an instruction to this block.

        :param instruction: The instruction to add.
        :param do_raise: Raises if the instruction cannot be added to this block.
        :return: The same instruction.
        """

        if type(instruction) is type:
            instruction = instruction()  # Should throw at this point, if invalid
        if not isinstance(instruction, Instruction):
            raise ValueError("Expected an instruction, got %r." % instruction)

        if do_raise:
            self._check_instruction(instruction)
        self._instructions.append(instruction)

        return instruction

    def insert(self, index: int, instruction: type[Instruction] | Instruction, do_raise: bool = True) -> Instruction:
        """
        Inserts an instruction at the given index.

        :param index: The index to insert the instruction at.
        :param instruction: The instruction to insert.
        :param do_raise: Raises if the instruction cannot be added to this block.
        :return: The same instruction.
        """

        if type(instruction) is type:
            instruction = instruction()
        if not isinstance(instruction, Instruction):
            raise ValueError("Expected an instruction, got %r." % instruction)

        if do_raise:
            self._check_instruction(instruction)
        self._instructions.insert(index, instruction)

        return instruction

    def remove(self, instruction: Instruction) -> Instruction:
        """
        Removes an instruction from this block.

        :param instruction: The instruction to remove.
        :return: The same instruction.
        """

        self._instructions.remove(instruction)
        return instruction

    def pop(self, index: int) -> Instruction:
        """
        Pops an instruction from this block.

        :param index: The index of the instruction to remove.
        :return: The removed instruction.
        """

        return self._instructions.pop(index)

    def clear(self) -> None:
        """
        Clears all instructions from this block.
        """

        self._instructions.clear()

    def strip(self, line_numbers: bool = True, local_variables: bool = True) -> None:
        """
        Strips debug information from this block.

        :param line_numbers: Should we strip line number markers?
        :param local_variables: Should we strip local variable info?
        """

        to_remove = []

        for instruction in self._instructions:
            if line_numbers and type(instruction) is LineNumber:
                to_remove.append(instruction)
            elif local_variables and type(instruction) is LocalVariable:
                to_remove.append(instruction)

        for instruction in to_remove:
            self._instructions.remove(instruction)


class InsnReturnBlock(ReturnBlock, InsnBlock):
    """
    The return block for a method. Should contain no instructions.
    """

    def __repr__(self) -> str:
        return "<InsnReturnBlock() at %x>" % id(self)

    def copy(self, label: int | None = None, deep: bool = True) -> "InsnReturnBlock":
        return InsnReturnBlock()


class InsnRethrowBlock(RethrowBlock, InsnBlock):
    """
    The rethrow block for a method. Should contain no instructions.
    """

    def __repr__(self) -> str:
        return "<InsnRethrowBlock() at %x>" % id(self)

    def copy(self, label: int | None = None, deep: bool = True) -> "InsnRethrowBlock":
        return InsnRethrowBlock()

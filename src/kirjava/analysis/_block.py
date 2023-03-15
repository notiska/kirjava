#!/usr/bin/env python3

__all__ = (
    "InsnBlock", "InsnReturnBlock", "InsnRethrowBlock",
)

from typing import Any, Iterable, Iterator, List, Optional, Tuple, Type, Union

from ..abc.graph import Block, RethrowBlock, ReturnBlock
from ..instructions import jvm as instructions
from ..instructions.jvm import Instruction, JumpInstruction, ReturnInstruction


class InsnBlock(Block):
    """
    A block containing Java instructions.
    """

    __slots__ = ("_instructions", "inline")

    @property
    def instructions(self) -> Tuple[Instruction, ...]:
        """
        :return: A tuple of the instructions in this block, cos I keep forgetting this is iterable.
        """

        return tuple(self._instructions)

    def __init__(self, label: int, instructions_: Optional[Iterable[Instruction]] = None) -> None:
        """
        :param label: The label of this block.
        :param instructions_: JVM instructions to initialise this block with.
        """

        super().__init__(label)

        self._instructions: List[Instruction] = []
        self.inline = False  # Can this block be inlined?

        if instructions_ is not None:
            self._instructions.extend(instructions_)

    def __repr__(self) -> str:
        # TODO: Pretty printing compatibility?
        return "<InsnBlock(label=%s, instructions=[%s]) at %x>" % (
            self.label, ", ".join(map(str, self._instructions)), id(self),
        )

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return (
            isinstance(other, InsnBlock) and
            other.label == self.label and
            other._instructions == self._instructions
        )

    def __hash__(self) -> int:
        return id(self)

    def __len__(self) -> int:
        return len(self._instructions)

    def __bool__(self) -> bool:
        return bool(self._instructions)

    def __iter__(self) -> Iterator[Instruction]:
        return iter(self._instructions)

    def __contains__(self, item: Any) -> bool:
        return item in self._instructions

    def __getitem__(self, item: Any) -> Union[Tuple[Instruction, ...], Instruction]:
        if type(item) is int or type(item) is slice:
            return self._instructions[item]
        raise TypeError("Expected int or slice, got %r." % type(item))

    def __setitem__(self, key: Any, value: Any) -> None:
        if type(key) is int:
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

    def copy(self, label: Optional[int] = None, deep: bool = True) -> "InsnBlock":
        new_block = self.__class__.__new__(self.__class__)
        new_block.label = self.label if label is None else label
        new_block._instructions = []

        if not deep:
            new_block._instructions.extend(self._instructions)
        else:
            new_block._instructions.extend([instruction.copy() for instruction in self._instructions])

        return new_block

    # ------------------------------ Utility ------------------------------ #

    def _check_instruction(self, instruction: Instruction) -> None:
        """
        Checks that an instruction can be added to this block. Throws if not the case.
        """

        if isinstance(instruction, JumpInstruction):
            raise ValueError("Cannot add a jump instruction directly, use graph.jump() instead, or do_raise=False.")
        elif isinstance(instruction, ReturnInstruction):
            raise ValueError("Cannot add a return instruction directly, use graph.return_() instead, or do_raise=False.")
        elif instruction == instructions.athrow:
            raise ValueError("Cannot add an athrow instruction directly, use graph.throw() instead, or do_raise=False.")

    # ------------------------------ Public API ------------------------------ #

    def append(self, instruction: Union[Type[Instruction], Instruction], do_raise: bool = True) -> Instruction:
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

    def insert(self, index: int, instruction: Union[Type[Instruction], Instruction], do_raise: bool = True) -> Instruction:
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


class InsnReturnBlock(ReturnBlock, InsnBlock):
    """
    The return block for a method. Should contain no instructions.
    """

    def __repr__(self) -> str:
        return "<InsnReturnBlock() at %x>" % id(self)


class InsnRethrowBlock(RethrowBlock, InsnBlock):
    """
    The rethrow block for a method. Should contain no instructions.
    """

    def __repr__(self) -> str:
        return "<InsnRethrowBlock() at %x>" % id(self)

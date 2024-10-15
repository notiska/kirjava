#!/usr/bin/env python3

__all__ = (
    "Block",
)

import typing
from typing import Iterable

from ..insns import Instruction
from ..insns.flow import Jump, Switch

if typing.TYPE_CHECKING:
    from ...model.types import Class


class Block:
    """
    An extended basic block containing JVM instructions.

    Attributes
    ----------
    LABEL_ENTRY: int
        The label of all entry blocks.
    LABEL_RETURN: int
        The label of all return blocks.
    LABEL_RETHROW: int
        The label of all rethrow blocks.
    LABEL_OPAQUE: int
        The label of all opaque blocks.

    throws: frozenset[Class]
        A set of exceptions that could be thrown by instructions in this block.
    label: int
        A unique label for this block.
    insns: list[Instruction]
        An ordered list of the instructions in this block.

    Methods
    -------
    add(self, instruction: Instruction | type[Instruction], *, do_raise: bool = True) -> None
        Adds an instruction to the end of this block.
    extend(self, instructions: Iterable[Instruction | type[Instruction]]) -> None
        Extends this block with a sequence of instructions.
    insert(self, index: int, instruction: Instruction | type[Instruction]) -> None
        Inserts an instruction at the given index.
    remove(self, instruction: Instruction | type[Instruction]) -> Instruction
        Removes and returns the first occurrence of an instruction from this block.
    pop(self, index: int = -1) -> Instruction | None
        Removes and returns the instruction at the given index.
    trace(frame: Frame) -> list[Trace.Step]
        Traces the execution of this block.
    """

    __slots__ = ("label", "insns")

    LABEL_ENTRY   = 0
    LABEL_RETURN  = -1
    LABEL_RETHROW = -2
    LABEL_OPAQUE  = -3

    @property
    def throws(self) -> frozenset["Class"]:
        throws: set["Class"] = set()
        for instruction in self.insns:
            throws.update(instruction.lt_throws)
            throws.update(instruction.rt_throws)
        return frozenset(throws)

    def __init__(self, label: int, insns: Iterable["Instruction"] | None = None) -> None:
        self.label = label
        self.insns: list["Instruction"] = []
        if insns is not None:
            self.insns.extend(insns)

    def __repr__(self) -> str:
        return f"<Block(label={self.label}, insns=[{", ".join(map(str, self.insns))}])>"

    def __str__(self) -> str:
        if self.label == self.LABEL_ENTRY:
            return "block_entry"
        elif self.label == self.LABEL_RETURN:
            return "block_return"
        elif self.label == self.LABEL_RETHROW:
            return "block_rethrow"
        elif self.label == self.LABEL_OPAQUE:
            return "block_opaque"
        return f"block_{self.label}"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Block) and self.label == other.label and self.insns == other.insns

    def __getitem__(self, index: int) -> Instruction:
        return self.insns[index]

    def __setitem__(self, index: int, value: Instruction | type[Instruction]) -> None:
        if not isinstance(value, Instruction):
            value = value()
        self.insns[index] = value

    def __delitem__(self, index: int) -> None:
        del self.insns[index]

    def __len__(self) -> int:
        return len(self.insns)

    def add(self, instruction: Instruction | type[Instruction], *, do_raise: bool = True) -> None:
        """
        Adds an instruction to the end of this block.

        Parameters
        ----------
        instruction: Instruction | type[Instruction]
            The instruction to add.
        do_raise: bool
            Raises an exception if the instruction cannot be added to the block.

        Raises
        -------
        TypeError
            If `do_raise=True` and the instruction cannot exist in the block.
        """

        if not isinstance(instruction, Instruction):
            instruction = instruction()
        if do_raise and isinstance(instruction, (Jump, Switch)):
            raise TypeError("cannot add jump instruction to block")

        self.insns.append(instruction)

    def extend(self, instructions: Iterable[Instruction | type[Instruction]]) -> None:
        """
        Extends this block with a sequence of instructions.

        Parameters
        ----------
        instructions: Iterable[Instruction | type[Instruction]]
            The instructions to add.
        """

        for instruction in instructions:
            self.add(instruction)

    def insert(self, index: int, instruction: Instruction | type[Instruction]) -> None:
        """
        Inserts an instruction at the given index.

        Parameters
        ----------
        index: int
            The index to insert the instruction at.
        instruction: Instruction | type[Instruction]
            The instruction to insert.
        """

        if not isinstance(instruction, Instruction):
            instruction = instruction()
        self.insns.insert(index, instruction)

    def remove(self, instruction: Instruction | type[Instruction]) -> Instruction | None:
        """
        Removes and returns the first occurrence of an instruction from this block.

        Parameters
        ----------
        instruction: Instruction | type[Instruction]
            The instruction to remove.

        Returns
        -------
        Instruction | None
            The removed instruction, or `None` if not found.
        """

        if isinstance(instruction, Instruction):
            for index, instruction_ in enumerate(self.insns):
                if instruction == instruction_:
                    return self.insns.pop(index)
        else:
            for index, instruction_ in enumerate(self.insns):
                if isinstance(instruction_, instruction):
                    return self.insns.pop(index)

        return None

    def pop(self, index: int = -1) -> Instruction | None:
        """
        Removes and returns the instruction at the given index.

        Parameters
        ----------
        index: int
            The index of the instruction to remove.
        """

        try:
            return self.insns.pop(index)
        except IndexError:
            return None

    def clear(self) -> None:
        """
        Removes all instructions from this block.
        """

        self.insns.clear()

    def index(self, instruction: Instruction | type[Instruction]) -> int:
        """
        Returns the index of the first occurrence of an instruction in this block.

        Parameters
        ----------
        instruction: Instruction | type[Instruction]
            The instruction to find.

        Returns
        -------
        int
            The index of the instruction.
        """

        if not isinstance(instruction, Instruction):
            instruction = instruction()
        return self.insns.index(instruction)

    def count(self, instruction: Instruction | type[Instruction]) -> int:
        """
        Returns the number of occurrences of an instruction in this block.

        Parameters
        ----------
        instruction: Instruction | type[Instruction]
            The instruction to count.

        Returns
        -------
        int
            The number of occurrences of the instruction.
        """

        if not isinstance(instruction, Instruction):
            instruction = instruction()
        return self.insns.count(instruction)

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     """
    #     Traces the execution of this block.
    #
    #     Parameters
    #     ----------
    #     frame: Frame
    #         The current frame.
    #     state: State
    #         The state to add trace information to.
    #     """
    #
    #     steps = 0
    #     for instruction in self.insns:
    #         if instruction.trace(frame, state) is not None:
    #             steps += 1
    #         if frame.thrown is not None:
    #             break
    #
    #     logger.debug("Traced %s (%i insns) in %i step(s).", self, len(self.insns), steps)

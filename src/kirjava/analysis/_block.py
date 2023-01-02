#!/usr/bin/env python3

__all__ = (
    "InsnBlock", "InsnReturnBlock", "InsnRethrowBlock",
)

import typing
from typing import Any, Iterable, List, Union

from .. import types
from ..abc import Class, Block, RethrowBlock, ReturnBlock
from ..classfile import instructions
from ..classfile.constants import Class as Class_
from ..classfile.instructions import MetaInstruction, Instruction, JumpInstruction, ReturnInstruction
from ..types import ReferenceType

if typing.TYPE_CHECKING:
    from ._edge import ExceptionEdge, FallthroughEdge, JumpEdge
    from .graph import InsnGraph


class InsnBlock(Block):
    """
    A block containing Java instructions.
    """

    __slots__ = ("instructions", "inline")

    def __init__(
            self,
            graph: "InsnGraph",
            label: Union[int, None] = None,
            instructions_: Union[Iterable[Instruction], None] = None,
            add: bool = True,
    ) -> None:
        """
        :param instructions_: JVM instructions to initialise this block with.
        """

        super().__init__(graph, label, add)

        self.instructions: List[Instruction] = []
        self.inline = False  # Can this block be inlined?

        if instructions_ is not None:
            self.instructions.extend(instructions_)

    def __repr__(self) -> str:
        # TODO: Pretty printing compatibility?
        return "<InsnBlock(label=%s, instructions=[%s]) at %x>" % (
            self.label, ", ".join(map(str, self.instructions)), id(self),
        )

    def __len__(self) -> int:
        return len(self.instructions)

    def __contains__(self, item: Any) -> bool:
        return item in self.instructions

    def __getitem__(self, index: int) -> Instruction:
        return self.instructions[index]

    def __setitem__(self, index: int, item: Any) -> None:
        if isinstance(item, MetaInstruction):
            item = item()
        elif not isinstance(item, Instruction):
            raise ValueError("Expected an instruction, got %r." % item)

        # TODO: Specific instruction handling
        self.instructions[index] = item

    def copy(self, deep: bool = False) -> "InsnBlock":
        new_block = self.__class__.__new__(self.__class__)
        new_block.graph = self.graph
        new_block.label = self.label
        new_block.instructions = []

        if not deep:
            new_block.instructions.extend(self.instructions)
        else:
            new_block.instructions.extend([instruction.copy() for instruction in self.instructions])

        return new_block

    def add(
            self,
            instruction: Union[MetaInstruction, Instruction],
            to: Union["InsnBlock", None] = None,
            fix_edges: bool = True,
    ) -> Instruction:
        """
        Adds an instruction to this block.

        :param instruction: The instruction to add.
        :param to: The block to jump to, if adding a jump instruction.
        :param fix_edges: Should the correct edges be added when certain instructions are added (jump, return and athrow)?
        :return: The same instruction.
        """

        if isinstance(instruction, MetaInstruction):
            instruction = instruction()  # Should throw at this point, if invalid
        elif not isinstance(instruction, Instruction):
            raise ValueError("Expected an instruction, got %r." % instruction)

        if fix_edges:
            if isinstance(instruction, JumpInstruction):
                for edge in self.out_edges:
                    # The required jump edge already exists, so nothing to do.
                    if isinstance(edge, JumpEdge) and (to is None or edge.to == to) and edge.jump == instructions:
                        if self.instructions[-1] != instruction:
                            self.instructions.append(instruction)
                        return instruction
                if to is None:
                    raise ValueError("Expected a value for parameter 'block' if adding a jump instruction.")
                self.jump(to, instruction)
                return instruction
            elif isinstance(instruction, ReturnInstruction):
                self.return_()
                return self.instructions[-1]
            elif instruction == instructions.athrow:
                self.throw()
                return self.instructions[-1]

        self.instructions.append(instruction)  # Otherwise, just add directly to the instructions
        return instruction

    # TODO
    # def insert(
    #         self,
    #         index: int,
    #         instruction: Union[MetaInstruction, Instruction]
    #         to: Union["InsnBlock", None] = None,
    #         fix_edges: bool = True,
    # ) -> Instruction:
    #     ...

    def clear(self) -> None:
        """
        Completely clears this block, including all edges.
        """

        self.instructions.clear()
        for edge in self.out_edges:
            self.graph.disconnect(edge)

    def fallthrough(self, to: "InsnBlock", fix: bool = True) -> "FallthroughEdge":
        """
        Creates a fallthrough edge from this block to another block.

        :param to: The block to fall through to.
        :param fix: Removes any already existing fallthrough edges.
        :return: The fallthrough edge that was created.
        """

        return self.graph.fallthrough(self, to, fix)

    def jump(
            self,
            to: "InsnBlock",
            jump: Union[MetaInstruction, Instruction] = instructions.goto,
            fix: bool = True,
    ) -> "JumpEdge":
        """
        Creates a jump edge from this block to another block.

        :param to: The block to jump to.
        :param jump: The jump instruction to use.
        :param fix: Automatically fixes jumps by removing their offsets and adding them to the end of the block.
        :return: The created jump edge.
        """

        return self.graph.jump(self, to, jump, fix)

    def catch(
            self,
            to: "InsnBlock",
            priority: Union[int, None] = None,
            exception: Union[ReferenceType, Class, Class_, str] = types.throwable_t,
    ) -> "ExceptionEdge":
        """
        Creates an exception edge from this block to another block.

        :param to: The block that will act as the exception handler.
        :param priority: The priority of this exception handler, lower values mean higher priority.
        :param exception: The type of exception being caught.
        :return: The exception edge that was created.
        """

        return self.graph.catch(self, to, priority, exception)

    def return_(self, fix: bool = True) -> "FallthroughEdge":
        """
        Creates a fallthrough edge to the return block, and adds the return instruction if necessary.

        :param fix: Removes any already existing fallthrough edges and adds the return instruction if not already present.
        :return: The fallthrough edge to the return block that was created.
        """

        return self.graph.return_(self, fix)

    def throw(self, fix: bool = True) -> "FallthroughEdge":
        """
        Creates a fallthrough edge to the rethrow block, and adds the athrow instruction if necessary.

        :parma fix: Removes already existing fallthrough edges and adds the athrow instruction if not already present.
        :return: The fallthrough edge to the athrow block that was created.
        """

        return self.graph.throw(self, fix)


class InsnReturnBlock(ReturnBlock, InsnBlock):
    """
    The return block for a method. Should contain no instructions.
    """

    def __init__(self, graph: "InsnGraph") -> None:
        super().__init__(graph)

    def __repr__(self) -> str:
        return "<InsnReturnBlock() at %x>" % id(self)


class InsnRethrowBlock(RethrowBlock, InsnBlock):
    """
    The rethrow block for a method. Should contain no instructions.
    """

    def __init__(self, graph: "InsnGraph") -> None:
        super().__init__(graph)

    def __repr__(self) -> str:
        return "<InsnRethrowBlock() at %x>" % id(self)

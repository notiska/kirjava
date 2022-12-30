#!/usr/bin/env python3

__all__ = (
    "InsnBlock", "InsnReturnBlock", "InsnRethrowBlock",
)

import typing
from typing import Iterable, List, Union

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
        :param instructions_: Java instructions to initialise this block with.
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
            handle_jumps: bool = True,
    ) -> Instruction:
        """
        Adds an instruction to this block.

        :param instruction: The instruction to add.
        :param to: The block to jump to, if adding a jump instruction.
        :param handle_jumps: Should jump edges be added when a jump instruction is added?
        :return: The same instruction.
        """

        if isinstance(instruction, MetaInstruction):
            instruction = instruction()  # Should throw at this point, if invalid

        if handle_jumps and isinstance(instruction, JumpInstruction):
            if to is None:
                raise ValueError("Expected a value for parameter 'block' if adding a jump instruction.")
            self.jump(to, instruction)
            return instruction

        self.instructions.append(instruction)  # Otherwise, just add directly to the instructions
        return instruction

    def fallthrough(self, to: "InsnBlock") -> "FallthroughEdge":
        """
        Creates a fallthrough edge from this block to another block.

        :param to: The block to fall through to.
        :return: The fallthrough edge that was created.
        """

        return self.graph.fallthrough(self, to)

    def jump(self, to: "InsnBlock", jump: Union[MetaInstruction, Instruction] = instructions.goto) -> "JumpEdge":
        """
        Creates a jump edge from this block to another block.

        :param to: The block to jump to.
        :param jump: The jump instruction to use.
        :return: The created jump edge.
        """

        return self.graph.jump(self, to, jump)

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


class InsnReturnBlock(ReturnBlock, InsnBlock):
    """
    The return block for a method. Contains only the return instruction.
    """

    @property
    def return_(self) -> ReturnInstruction:
        """
        :return: The return instruction in this block.
        """

        return self.instructions[0]

    @return_.setter
    def return_(self, value: ReturnInstruction) -> None:
        self.instructions[0] = value

    def __init__(self, graph: "InsnGraph", return_: Union[ReturnInstruction, None] = None) -> None:
        """
        :param return_: The return instruction for the method, if None, this is determined automatically.
        """

        super().__init__(graph)

        self.inline = True  # We obviously want to inline return instructions rather than generating gotos

        if return_ is None:
            type_ = graph.method.return_type
            if type_ != types.void_t:
                type_ = type_.to_verification_type()

                if type_ == types.int_t:
                    return_ = instructions.ireturn()
                elif type_ == types.long_t:
                    return_ = instructions.lreturn()
                elif type_ == types.float_t:
                    return_ = instructions.freturn()
                elif type_ == types.double_t:
                    return_ = instructions.dreturn()
                else:
                    return_ = instructions.areturn()

            else:
                return_ = instructions.return_()

        self.instructions.append(return_)

    def __repr__(self) -> str:
        return "<InsnReturnBlock(return=%s) at %x>" % (self.instructions[0], id(self))


class InsnRethrowBlock(RethrowBlock, InsnBlock):
    """
    The rethrow block for a method. Should contain no instructions.
    """

    def __init__(self, graph: "InsnGraph") -> None:
        super().__init__(graph)

        self.inline = True
        self.instructions.append(instructions.athrow())

    def __repr__(self) -> str:
        return "<InsnRethrowBlock() at %x>" % id(self)

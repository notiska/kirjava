#!/usr/bin/env python3

__all__ = (
    "block", "edge",
    "InsnBlock", "InsnReturnBlock", "InsnRethrowBlock",
    "InsnEdge", "FallthroughEdge", "JumpEdge",
    "JsrJumpEdge", "JsrFallthroughEdge", "RetEdge",
    "ExceptionEdge",
    "InsnGraph",
)

"""
A control flow graph containing JVM instructions.
"""

import logging
import typing

from . import block, edge
from ._asm import assemble
from ._dis import disassemble
from .block import *
from .edge import *
from ... import _argument, instructions, types
from ...abc import Graph
from ...instructions import Instruction, JsrInstruction
from ...source import *

if typing.TYPE_CHECKING:
    from ...classfile import MethodInfo
    from ...classfile.attributes import Code

logger = logging.getLogger("kirjava.analysis.graph")


class InsnGraph(Graph):
    """
    A control flow graph that contains Java instructions.
    """

    __slots__ = ("source_map",)

    # Type hints for the fancy IDEs

    method: "MethodInfo"

    entry_block: InsnBlock
    return_block: InsnReturnBlock
    rethrow_block: InsnRethrowBlock

    _blocks: dict[int, InsnBlock]
    _forward_edges: dict[InsnBlock, set[InsnEdge]]
    _backward_edges: dict[InsnBlock, set[InsnEdge]]
    _opaque_edges: set[InsnEdge]

    @classmethod
    def disassemble(
            cls,
            method: "MethodInfo",
            *,
            do_raise: bool = True,
            keep_lnt: bool = True,
            keep_lvt: bool = True,
            keep_lvtt: bool = True,
            gen_source_map: bool = True,
    ) -> "InsnGraph":
        """
        Disassembles a method into a control flow graph.

        :param method: The method to disassemble.
        :param do_raise: Raise an exception if any errors occurred during disassembling.
        :param keep_lnt: Should we keep the line number table?
        :param keep_lvt: Should we keep the local variable table?
        :param keep_lvtt: Should we keep the local variable type table?
        :param gen_source_map: Should we generate a mapping of bytecode offset to block index?
        :return: The control flow graph.
        """

        self = cls(method)
        disassemble(self, method, do_raise, keep_lnt, keep_lvt, keep_lvtt, gen_source_map)
        return self

    def __init__(self, method: "MethodInfo") -> None:
        super().__init__(method, InsnBlock(0), InsnReturnBlock(), InsnRethrowBlock())

        self.source_map: dict[int, InstructionInBlock | InsnEdge] = {}

    def __repr__(self) -> str:
        return "<InsnGraph(blocks=%i, edges=%i)> at %x" % (len(self._blocks), len(self._forward_edges), id(self))

    def copy(self, *, deep: bool = True) -> "InsnGraph":
        """
        Creates a copy of this instruction graph.

        :param deep: Should we copy the instructions?
        :return: The copied graph.
        """

        # Ugly but performant.
        graph = InsnGraph.__new__(InsnGraph)
        Graph.__init__(
            graph, self.method,
            self.entry_block.copy(deep=deep),
            InsnReturnBlock(),
            InsnRethrowBlock(),
        )

        blocks = graph._blocks
        forward_edges = graph._forward_edges
        backward_edges = graph._backward_edges
        opaque_edges = graph._opaque_edges

        for label, block in self._blocks.items():
            if block is self.entry_block or block is self.return_block or block is self.rethrow_block:
                continue
            block = block.copy(deep=deep)
            blocks[label] = block

        for block, edges in self._forward_edges.items():
            block = blocks[block.label]
            new_edges = forward_edges[block]

            for edge in edges:
                if edge.to is not None:
                    edge = edge.copy(from_=block, to=blocks[edge.to.label], deep=deep)
                    new_edges.add(edge)
                    backward_edges[edge.to].add(edge)

                else:
                    edge = edge.copy(from_=block, deep=deep)
                    new_edges.add(edge)
                    opaque_edges.add(edge)

        # TODO: Copy the source map too.

        return graph

    def assemble(
            self,
            *,
            do_raise: bool = True,
            in_place: bool = False,
            adjust_wides: bool = True,
            adjust_ldcs: bool = True,
            adjust_jumps: bool = True,
            adjust_fallthroughs: bool = True,
            simplify_exception_ranges: bool = True,
            compute_maxes: bool = True,
            compute_frames: bool = True,
            compress_frames: bool = True,
            add_lnt: bool = True,
            add_lvt: bool = True,
            add_lvtt: bool = True,
            remove_dead_blocks: bool = True,
    ) -> "Code":
        """
        Assembles this graph into the method's code attribute.

        :param do_raise: Raise an exception if any errors occurred during assembling.
        :param in_place: Modifies this graph in-place while assembling. Can improve performance.
        :param adjust_wides: Adds/removes wide instructions if necessary.
        :param adjust_ldcs: Substitutes ldc instructions for ldc_w instructions if necessary.
        :param adjust_jumps: Adjusts certain impossible jumps by generating new blocks if necessary.
        :param adjust_fallthroughs: Generates gotos if certain fallthroughs are impossible.
        :param simplify_exception_ranges: Merges exception edges with the same priority in the exception table.
        :param compute_maxes: Computes the maximum stack size and maximum local.
        :param compute_frames: Computes stack map frames and adds the attribute to the code.
        :param compress_frames: Compresses the stack map frames. Only for compute_frames.
        :param add_lnt: Adds the line number table debug attribute.
        :param add_lvt: Adds the local variable table debug attribute.
        :param add_lvtt: Adds the local variable type table debug attribute.
        :param remove_dead_blocks: Removes blocks that will never be reached in execution.
        :return: The assembled Code attribute.
        """

        return assemble(
            self, self.method, self.method.class_,
            do_raise, in_place,
            adjust_wides, adjust_ldcs,
            adjust_jumps, adjust_fallthroughs,
            simplify_exception_ranges,
            compute_maxes, compute_frames, compress_frames,
            add_lnt, add_lvt, add_lvtt,
            remove_dead_blocks,
        )

    def strip(self, line_numbers: bool = True, local_variables: bool = True) -> None:
        """
        Strips debug information from this graph.

        :param line_numbers: Should we strip line number markers?
        :param local_variables: Should we strip local variable info?
        """

        for block in self._blocks.values():
            block.strip(line_numbers, local_variables)

    # ------------------------------ Blocks ------------------------------ #

    def new(self) -> InsnBlock:
        block = InsnBlock(max(self._blocks, default=0) + 1)
        self.add(block, check=False)
        return block

    def instructions(self, block_or_label: InsnBlock | int) -> tuple[Instruction, ...]:
        """
        Iterates over all the instructions in a block (including any instructions in its out edges).

        :param block_or_label: A block or a label for a block in this graph.
        :return: A copy of the instructions, note that the instructions themselves are not copied and are still mutable.
        """

        if type(block_or_label) is int:
            block_or_label = self._blocks.get(block_or_label)
        if block_or_label is None or not block_or_label in self._blocks.values():
            raise ValueError("Provided block or label %r is not a valid block in this graph." % block_or_label)

        instructions_ = list(block_or_label._instructions)
        edge_instruction = False
        for out_edge in self._forward_edges.get(block_or_label, ()):
            if not edge_instruction and out_edge.instruction is not None:
                instructions_.append(out_edge.instruction)
                edge_instruction = True
        return tuple(instructions_)

    # ------------------------------ Edges ------------------------------ #

    def fallthrough(self, from_: InsnBlock, to: InsnBlock, overwrite: bool = False) -> FallthroughEdge:
        """
        Creates and connects a fallthrough edge between two blocks.

        :param from_: The block we're coming from.
        :param to: The block we're going to.
        :param overwrite: Removes already existing fallthrough edges.
        :return: The created fallthrough edge.
        """

        edge = FallthroughEdge(from_, to)
        self.connect(edge, overwrite)
        return edge

    def jump(
            self,
            from_: InsnBlock,
            to: InsnBlock,
            jump: type[Instruction] | Instruction | None = None,
            overwrite: bool = True,
    ) -> JumpEdge:
        """
        Creates a jump edge between two blocks.

        :param from_: The block we're jumping from.
        :param to: The block we're jumping to.
        :param jump: The jump instruction.
        :param overwrite: Overwrites already existing jump edges.
        :return: The jump edge that was created.
        """

        if type(jump) is type:
            jump = jump()

        if isinstance(jump, JsrInstruction) or jump == instructions.ret:
            raise TypeError("Cannot add jsr/ret instructions with jump() method.")
        elif jump in (instructions.tableswitch, instructions.lookupswitch):
            raise TypeError("Cannot add switch instructions with jump() method.")

        edge = JumpEdge(from_, to, jump)
        self.connect(edge, overwrite)
        return edge

    def catch(
            self,
            from_: InsnBlock,
            to: InsnBlock,
            priority: int | None = None,
            exception: _argument.ReferenceType = types.throwable_t,
    ) -> ExceptionEdge:
        """
        Creates an exception edge between two blocks.

        :param from_: The block we're coming from.
        :param to: The block that will act as the exception handler.
        :param priority: The priority of this exception handler, lower values mean higher priority.
        :param exception: The exception type being caught.
        :return: The exception edge that was created.
        """

        exception = _argument.get_reference_type(exception)
        if priority is None:  # Determine this automatically
            priority = 0
            for edge in self._forward_edges.get(from_, ()):
                if isinstance(edge, ExceptionEdge) and edge.priority >= priority:
                    priority = edge.priority + 1

        edge = ExceptionEdge(from_, to, priority, exception)
        self.connect(edge)
        return edge

    def return_(self, from_: InsnBlock, overwrite: bool = False) -> JumpEdge:
        """
        Creates a fallthrough edge from the given block to the return block.

        :param from_: The block we're coming from.
        :param overwrite: Overwrites any existing fallthrough edges.
        :return: The fallthrough edge that was created.
        """

        return_type = self.method.return_type

        if return_type != types.void_t:
            return_type = return_type.to_verification_type()

            if return_type == types.int_t:
                instruction = instructions.ireturn()
            elif return_type == types.long_t:
                instruction = instructions.lreturn()
            elif return_type == types.float_t:
                instruction = instructions.freturn()
            elif return_type == types.double_t:
                instruction = instructions.dreturn()
            else:
                instruction = instructions.areturn()
        else:
            instruction = instructions.return_()

        edge = JumpEdge(from_, self.return_block, instruction)
        self.connect(edge, overwrite)
        return edge

    def throw(self, from_: InsnBlock, overwrite: bool = False) -> JumpEdge:
        """
        Creates a fallthrough edge from the given block to the rethrow block.

        :param from_: The block we're coming from.
        :param overwrite: Overwrites any existing fallthrough edges.
        :return: The fallthrough edge that was created.
        """

        edge = JumpEdge(from_, self.rethrow_block, instructions.athrow())
        self.connect(edge, overwrite)
        return edge

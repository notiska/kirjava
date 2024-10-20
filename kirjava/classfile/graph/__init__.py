#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "block", "edge",
    "Block", "Edge",
    "Graph",
)

import sys
import typing
from collections import defaultdict

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from . import block, edge
from ._dis import disassemble
from .block import Block
from .edge import Catch, Edge, Fallthrough, Jump as JumpEdge
from ..insns import goto, Instruction
from ..insns.flow import Jump as JumpInsn
from ...backend import Result

if typing.TYPE_CHECKING:
    from ..fmt import ClassFile
    from ..fmt.method import MethodInfo


# FIXME: Make the graph structure more/less expressive? Want to maximise usability, analysis can have a separate data
#        structure to store more complex relations such as rethrow, direct links, resolved subroutines, etc...
class Graph:
    """
    A JVM control flow graph.

    Attributes
    ----------
    blocks: list[Block]
        A list of all blocks in this graph.
    edges_out: dict[Block, set[Edge]]
        A mapping of all blocks to the edges leading out of them.
    edges_in: dict[Block, set[Edge]]
        A mapping of all blocks to the edges leading into them.
    entry: Block
        The entry block of the graph.
    return_: Block
        The return block of the graph.
    rethrow: Block
        The rethrow block of the graph, throws any uncaught exceptions.
    opaque: Block
        The opaque block of the graph, used for unresolved jumps.

    Methods
    -------
    disassemble(method: MethodInfo, cf: ClassFile) -> Result[Self]
        Disassembled a method into a JVM control flow graph.

    block(self) -> Block
        Creates a new block in this graph.
    fallthrough(self, source: int | Block, target: int | Block, *, do_raise: bool = True) -> Fallthrough
        Creates a fallthrough edge between two blocks.
    """

    __slots__ = (
        "blocks", "edges_out", "edges_in",
        "entry", "return_", "rethrow", "opaque",
        "_label",
    )

    @classmethod
    def disassemble(cls, method: "MethodInfo", cf: "ClassFile") -> Result[Self]:
        """
        Disassembles a method into a JVM control flow graph.

        Parameters
        ----------
        method: MethodInfo
            The method to disassemble.
        cf: ClassFile
            The class file containing the method.
        """

        return disassemble(cls(), method, cf)

    def __init__(self) -> None:
        self.blocks: list[Block] = []
        self.edges_out: dict[Block, set[Edge]] = defaultdict(set)
        self.edges_in:  dict[Block, set[Edge]] = defaultdict(set)

        self.entry   = self.block(Block.LABEL_ENTRY)
        self.return_ = self.block(Block.LABEL_RETURN)
        self.rethrow = self.block(Block.LABEL_RETHROW)
        self.opaque  = self.block(Block.LABEL_OPAQUE)

        self._label = 0

    def block(self, label: int | None = None) -> Block:
        """
        Creates a new block in this graph.

        Parameters
        ----------
        label: int | None
            The label of the block, or None to generate a unique one.

        Returns
        -------
        Block
            The new block with a valid label for this graph.
        """

        if label is None:
            # Faster to do it this way, might need to change later if I add better external API support.
            # ^^ to clarify, I mean by checking the maximum label already in the graph to avoid collisions.
            self._label += 1
            label = self._label

        block = Block(label)
        self.blocks.append(block)
        return block

    def fallthrough(self, source: int | Block, target: int | Block, *, do_raise: bool = True) -> Fallthrough:
        """
        Creates a fallthrough edge between two blocks.

        Parameters
        ----------
        source: int | Block
            The label or block to fall through from.
        target: int | Block
            The label or block to fall through to.
        do_raise: bool
            Raises an exception if the edge puts the graph in an invalid state.

        Returns
        -------
        Fallthrough
            The fallthrough edge created.

        Raises
        ------
        ValueError
            If `do_raise=True` and the edge would be invalid in the graph.
        """

        if not isinstance(source, Block):
            source = self.blocks[source]
        if not isinstance(target, Block):
            target = self.blocks[target]

        edge = Fallthrough(source, target)  # TODO: Checks for duplicate edges, etc.
        self.edges_out[source].add(edge)
        self.edges_in[target].add(edge)

        return edge

    def jump(
            self, source: int | Block, target: int | Block | None = None,
            instruction: Instruction | type[Instruction] = goto,
            *, do_raise: bool = True,
    ) -> JumpEdge:
        """
        Creates a jump edge between two blocks.

        Parameters
        ----------
        source: int | Block
            The label or block to jump from.
        target: int | Block | None
            The label or block to jump to, or `None` for certain instructions (i.e.
            return, athrow).
        instruction: Instruction | type[Instruction]
            The instruction to use for the jump.
        do_raise: bool
            Raises an exception if the edge puts the graph in an invalid state.

        Returns
        -------
        JumpEdge
            The jump edge created.

        Raises
        ------
        TypeError
            If `do_raise=True` and the instruction is not a jump instruction.
        ValueError
            If `do_raise=True` and the edge would be invalid in the graph.
        """

        if not isinstance(source, Block):
            source = self.blocks[source]
        if target is not None and not isinstance(target, Block):
            target = self.blocks[target]

        if not isinstance(instruction, Instruction):
            instruction = instruction(0)  # type: ignore[call-arg]
        if do_raise and not isinstance(instruction, JumpInsn):
            raise TypeError("expected jump instruction")

        # FIXME
        # edge = JumpEdge(source, target, instruction)
        # self.edges_out[source].add(edge)
        # self.edges_in[target].add(edge)

        # return edge

        raise NotImplementedError(f"jump() is not implemented for {type(self)!r}")

    # def catch(self) -> Catch:

    # def merge_single_successors(self) -> None:
    #     ...

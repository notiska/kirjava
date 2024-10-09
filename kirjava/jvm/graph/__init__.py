#!/usr/bin/env python3

__all__ = (
    "block", "edge",
    "Block", "Edge",
    "Graph",
)

import typing
from collections import defaultdict

from . import block, edge
from ._dis import disassemble
from .block import Block
from .edge import *
from ...meta import Metadata

if typing.TYPE_CHECKING:
    from ..fmt import ClassFile
    from ..fmt.method import MethodInfo


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
    block(self) -> Block
        Creates a new block in this graph.
    """

    __slots__ = (
        "blocks", "edges_out", "edges_in",
        "entry", "return_", "rethrow", "opaque",
        "_label",
    )

    @classmethod
    def disassemble(cls, method: "MethodInfo", cf: "ClassFile") -> tuple["Graph", Metadata]:
        """
        Disassembles a method into a JVM control flow graph.

        Parameters
        ----------
        method: MethodInfo
            The method to disassemble.
        cf: ClassFile
            The class file containing the method.

        Returns
        -------
        Graph
            The disassembled JVM control flow graph.
        Metadata
            Any metadata generated during disassembly.
        """

        self = cls()
        meta = disassemble(self, method, cf)
        return self, meta

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

    def fallthrough(self, source: int | Block, target: int | Block) -> Fallthrough:
        """
        Creates a fallthrough edge between two blocks.

        Parameters
        ----------
        source: int | Block
            The label or block to fall through from.
        target: int | Block
            The label or block to fall through to.

        Returns
        -------
        Fallthrough
            The fallthrough edge created.
        """

        if not isinstance(source, Block):
            source = self.blocks[source]
        if not isinstance(target, Block):
            target = self.blocks[target]

        edge = Fallthrough(source, target)  # TODO: Checks for duplicate edges, etc.
        self.edges_out[source].add(edge)
        self.edges_in[target].add(edge)

        return edge

    # def merge_single_successors(self) -> None:
    #     ...

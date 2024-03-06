#!/usr/bin/env python3

__all__ = (
    "Block", "Edge", "Graph", "RethrowBlock", "ReturnBlock",
)

"""
Abstract base classes for graph representations of methods.
"""

import logging
import typing
from collections import defaultdict
from typing import Any, Iterator

from .source import Source

if typing.TYPE_CHECKING:
    from .method import Method

logger = logging.getLogger("kirjava.abc.graph")


class Block(Source):
    """
    An (extended) basic block.
    """

    __slots__ = ("label",)

    def __init__(self, label: int) -> None:
        """
        :param label: The label of this block.
        """

        self.label = label

    def __repr__(self) -> str:
        return "<Block(label=%s) at %x>" % (self.label, id(self))

    def __str__(self) -> str:
        return "block %i" % self.label

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return isinstance(other, Block) and other.label == self.label

    def __hash__(self) -> int:
        return id(self)

    def copy(self, label: int | None = None, deep: bool = False) -> "Block":
        """
        Creates a copy of this block.

        :param label: The new label to use, if None, uses the current label.
        :param deep: Create a deep copy?
        :return: The copy of this block.
        """

        return Block(self.label if label is None else label)


class ReturnBlock(Block):
    """
    The return block for a graph.
    All blocks returning from the method should have an edge to this one.
    """

    LABEL = -1

    def __init__(self) -> None:
        super().__init__(self.LABEL)

    def __repr__(self) -> str:
        return "<ReturnBlock() at %x>" % id(self)

    def __str__(self) -> str:
        return "return block"


class RethrowBlock(Block):
    """
    The rethrow block for a graph.
    All blocks with explicit throws or uncaught exceptions should have an edge to this one.
    """

    LABEL = -2

    def __init__(self) -> None:
        super().__init__(self.LABEL)

    def __repr__(self) -> str:
        return "<RethrowBlock() at %x>" % (id(self))

    def __str__(self) -> str:
        return "rethrow block"


class Edge(Source):
    """
    An edge connects to vertices (blocks) in a control flow graph.
    """

    __slots__ = ("from_", "to", "_hash")

    # Limits how many of this certain type of edge can occur at a block. If None, there is no limit.
    limit: int | None = None

    def __init__(self, from_: Block, to: Block) -> None:
        """
        :param from_: The block we're coming from.
        :param to: The block we're going to.
        """

        self.from_ = from_
        self.to = to

        self._hash = hash((self.from_, self.to))

    def __repr__(self) -> str:
        return "<%s(from=%s, to=%s)>" % (type(self).__name__, self.from_, self.to)

    def __str__(self) -> str:
        return "%s -> %s" % (self.from_, self.to)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return isinstance(other, Edge) and other.from_ == self.from_ and other.to == self.to

    def __hash__(self) -> int:
        return self._hash

    def copy(self, from_: Block | None = None, to: Block | None = None, deep: bool = True) -> "Edge":
        """
        Creates a copy of this edge with the new to/from blocks.

        :param from_: The new from block, if None, uses the original.
        :param to: The new to block, if None, uses the original.
        :param deep: Should we copy any data inside the edge?
        :return: The copied edge.
        """

        return Edge(self.from_ if from_ is None else from_, self.to if to is None else to)


class Graph:
    """
    A control flow graph representing a method.
    """

    __slots__ = (
        "method",
        "entry_block", "return_block", "rethrow_block",
        "_blocks", "_forward_edges", "_backward_edges", "_opaque_edges",
    )

    @property
    def blocks(self) -> tuple[Block, ...]:
        return tuple(self._blocks.values())

    @property
    def edges(self) -> tuple[Edge, ...]:
        edges: list[Edge] = []
        for edges_ in self._forward_edges.values():
            edges.extend(edges_)
        return tuple(edges)

    @property
    def opaque_edges(self) -> tuple[Edge, ...]:
        return tuple(self._opaque_edges)

    def __init__(
            self, method: "Method", entry_block: Block, return_block: ReturnBlock, rethrow_block: RethrowBlock,
    ) -> None:
        """
        :param method: The method that this graph represents.
        :param entry_block: The entry block in this graph.
        :param return_block: The return block for this graph.
        :param rethrow_block: The rethrow block for this graph.
        """

        self.method = method

        # Special kinds of blocks
        self.entry_block = entry_block
        self.return_block = return_block
        self.rethrow_block = rethrow_block

        self._blocks: dict[int, Block] = {
            entry_block.label: entry_block,
            return_block.label: return_block,
            rethrow_block.label: rethrow_block,
        }
        self._forward_edges: dict[Block, set[Edge]] = defaultdict(set)  # Blocks to their out edges (faster lookup)
        self._backward_edges: dict[Block, set[Edge]] = defaultdict(set)  # Blocks to their in edges
        self._opaque_edges: set[Edge] = set()  # Edges whose jump targets we don't know yet

    def __iter__(self) -> Iterator[Block]:
        return iter(self._blocks.values())

    def __getitem__(self, item: Any) -> Block:
        if type(item) is int:
            return self._blocks[item]
        raise TypeError("Expected int, got %r." % type(item))

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, Block):
            return item.label in self._blocks and self._blocks[item.label] == item
        return False

    def __len__(self) -> int:
        return len(self._blocks)

    # ------------------------------ Public API ------------------------------ #

    def new(self) -> Block:
        """
        Creates a new block with the correct label.
        """

        ...

    def get(self, label: int) -> Block:
        """
        Gets a block in this graph given its label.

        :param label: The label of the block.
        :return: The block, if it was found.
        """

        try:
            return self._blocks[label]
        except KeyError:
            raise LookupError("Couldn't find block with label %i." % label)

    def add(self, block: Block, *, check: bool = True) -> None:
        """
        Adds a block to this graph.

        :param block: The block to add.
        """

        if check:
            if block.label in self._blocks:
                if self._blocks[block.label] != block:
                    raise ValueError("Block with label %i already exists in this graph." % block.label)
                return  # Already exists
            elif isinstance(block, ReturnBlock):
                raise ValueError("Cannot add return block %r to this graph." % block)
            elif isinstance(block, RethrowBlock):
                raise ValueError("Cannot add rethrow block %r to this graph." % block)

        self._blocks[block.label] = block
        # self._forward_edges[block] = set()
        # self._backward_edges[block] = set()

    def remove(self, block: Block, *, check: bool = True) -> None:
        """
        Removes a block from this graph. Any edges that connect this block to other blocks will be removed too.

        :param block: The block to remove.
        """

        # These blocks cannot be removed, for obvious reasons.
        if check and (block is self.return_block or block is self.rethrow_block):
            raise ValueError("Cannot remove block %r." % block)

        try:
            del self._blocks[block.label]
        except KeyError:  # Not in the graph
            raise ValueError("Block %r is not in the graph." % block)

        if block is self.entry_block:
            self.entry_block = None

        try:
            for edge in self._backward_edges.pop(block):
                self.disconnect(edge)
        except KeyError:
            ...
        try:
            for edge in self._forward_edges.pop(block):
                self.disconnect(edge)
        except KeyError:
            ...

    def connect(self, edge: Edge, overwrite: bool = False, *, check: bool = True) -> None:
        """
        Adds an edge to this graph (connecting two blocks).
        It's called connect cos I wanna keep this class clean lol, and not have "add_block" or "add_edge".

        :param edge: The edge to add to this graph.
        :param overwrite: Overwrites existing edges, if the given edge is limited.
        """

        if check:
            if edge.to == self.entry_block:
                raise ValueError("Cannot create an edge to the entry block.")
            elif edge.from_ == self.return_block:
                raise ValueError("Cannot create an edge from the return block.")
            elif edge.from_ == self.rethrow_block:
                raise ValueError("Cannot create an edge from the rethrow block.")

            if not edge.from_.label in self._blocks:
                self.add(edge.from_)
            if not edge.to.label in self._blocks:
                self.add(edge.to)

        if check:
            forward = self._forward_edges[edge.from_]
            conflicts = set()

            if edge.limit is None:
                forward.add(edge)
            else:
                for edge_ in forward:
                    if type(edge_) is type(edge):
                        conflicts.add(edge_)

                if len(conflicts) >= edge.limit:
                    if overwrite:
                        for edge_ in conflicts:
                            self.disconnect(edge_)
                    else:
                        raise ValueError("Cannot add edge %r, limit of %i reached. Use overwrite=True." % (edge, edge.limit))
                forward.add(edge)
        else:
            self._forward_edges[edge.from_].add(edge)

        if edge.to is not None:
            self._backward_edges[edge.to].add(edge)
        else:
            self._opaque_edges.add(edge)

    def disconnect(self, edge: Edge) -> None:
        """
        Removes an edge from this graph.

        :param edge: The edge to remove.
        """

        # self._blocks.setdefault(edge.from_.label, edge.from_)
        # self._blocks.setdefault(edge.to.label, edge.to)

        try:
            self._forward_edges[edge.from_].remove(edge)
        except KeyError:
            raise ValueError("Edge %r is not in the graph." % edge)

        if edge.to is not None:
            self._backward_edges[edge.to].discard(edge)
        else:
            self._opaque_edges.discard(edge)

    def is_opaque(self, edge: Edge) -> bool:
        """
        Checks if the given edge is opaque.

        :param edge: The edge to check.
        :return: Is this edge opaque?
        """

        return edge in self._opaque_edges

    def successors(self, block: Block) -> tuple[Block, ...]:
        """
        Gets the successors for a given block.

        :param block: The block in question.
        :return: The block's successors.
        """

        return tuple(edge.to for edge in self._forward_edges[block])

    def successors_iter(self, block: Block) -> Iterator[Block]:
        """
        Gest the successors for a given block, as an iterator.

        :param block: The block in question.
        """

        for edge in self._forward_edges[block]:
            yield edge.to

    def predecessors(self, block: Block) -> tuple[Block, ...]:
        """
        Gets the predecessors for a given block.

        :param block: The block in question.
        :return: The block's predecessors.
        """

        return tuple(edge.from_ for edge in self._backward_edges[block])

    def predecessors_iter(self, block: Block) -> Iterator[Block]:
        """
        Gets the predecessors for a given block, as an iterator.

        :param block: The block in question.
        """

        for edge in self._backward_edges[block]:
            yield edge.from_

    def out_edges(self, block: Block) -> tuple[Edge, ...]:
        """
        Gets the out edges for a given block.

        :param block: The block in question.
        :return: The out edges for that block.
        """

        return tuple(self._forward_edges[block])

    def out_edges_iter(self, block: Block) -> Iterator[Edge]:
        """
        Gets the out edges for a given block, as an iterator.

        :param block: The block in question.
        """

        for edge in self._forward_edges[block]:
            yield edge

    def in_edges(self, block: Block) -> tuple[Edge, ...]:
        """
        Gets the in edges for a given block.

        :param block: The block in question.
        :return: The in edges for that block.
        """

        return tuple(self._backward_edges[block])

    def in_edges_iter(self, block: Block) -> Iterator[Edge]:
        """
        Gets the in edges for a given block, as an iterator.

        :param block: The block in question.
        """

        for edge in self._backward_edges[block]:
            yield edge

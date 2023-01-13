# cython: language=c
# cython: language_level=3

__all__ = (
    "Block", "Edge", "Graph", "RethrowBlock", "ReturnBlock",
)

"""
Abstract base classes for graph representations of methods.
"""

import logging
from typing import Any, Dict, Iterator, Set, Tuple, Union

from .method import Method

logger = logging.getLogger("kirjava.abc.graph")


cdef class Block(Source):
    """
    An (extended) basic block.
    """

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
        return isinstance(other, Block) and (<Block>other).label == self.label

    def __hash__(self) -> int:
        return id(self)

    def copy(self, label: Union[int, None] = None, deep: bool = False) -> "Block":
        """
        Creates a copy of this block.

        :param label: The new label to use, if None, uses the current label.
        :param deep: Create a deep copy?
        :return: The copy of this block.
        """

        return Block(self.label if label is None else label)


cdef class ReturnBlock(Block):
    """
    The return block for a graph.
    All blocks returning from the method should have an edge to this one.
    """

    LABEL = -1

    def __init__(self) -> None:
        super().__init__(ReturnBlock.LABEL)

    def __repr__(self) -> str:
        return "<ReturnBlock() at %x>" % id(self)

    def __str__(self) -> str:
        return "return block"


cdef class RethrowBlock(Block):
    """
    The rethrow block for a graph.
    All blocks with explicit throws or uncaught exceptions should have an edge to this one.
    """

    LABEL = -2

    def __init__(self) -> None:
        super().__init__(RethrowBlock.LABEL)

    def __repr__(self) -> str:
        return "<RethrowBlock() at %x>" % (id(self))

    def __str__(self) -> str:
        return "rethrow block"


cdef class Edge(Source):
    """
    An edge connects to vertices (blocks) in a control flow graph.
    """

    # Limits how many of this certain type of edge can occur at a block. If None, there is no limit.
    limit: Union[int, None] = None

    def __init__(self, from_: Block, to: Block) -> None:
        """
        :param from_: The block we're coming from.
        :param to: The block we're going to.
        """

        self.from_ = from_
        self.to = to

    def __repr__(self) -> str:
        return "<%s(from=%s, to=%s) at %x>" % (self.__class__.__name__, self.from_, self.to, id(self))

    def __str__(self) -> str:
        return "%s -> %s" % (self.from_, self.to)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return isinstance(other, Edge) and (<Edge>other).from_ == self.from_ and (<Edge>other).to == self.to

    def __hash__(self) -> int:
        return hash((self.from_, self.to))

    def copy(self, from_: Union[Block, None] = None, to: Union[Block, None] = None) -> "Edge":
        """
        Creates a copy of this edge with the new to/from blocks.

        :param from_: The new from block, if None, uses the original.
        :param to: The new to block, if None, uses the original.
        :return: The copied edge.
        """

        return Edge(self.from_ if from_ is None else from_, self.to if to is None else to)


cdef class Graph:
    """
    A control flow graph representing a method.
    """

    property blocks:
        def __get__(self) -> Tuple[Block, ...]:
            return tuple(self._blocks.values())

    property edges:
        def __get__(self) -> Tuple[Edge, ...]:
            cdef list edges = []
            for edges_ in self._forward_edges.values():
                edges.extend(edges_)
            return tuple(edges)

    property opaque_edges:
        def __get__(self) -> Tuple[Edge, ...]:
            return tuple(self._opaque_edges)

    def __init__(
            self, method: Method, entry_block: Block, return_block: ReturnBlock, rethrow_block: RethrowBlock,
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

        self._blocks: Dict[int, Block] = {}
        self._forward_edges: Dict[Block, Set[Edge]] = {}  # Blocks to their out edges (faster lookup)
        self._backward_edges: Dict[Block, Set[Edge]] = {}  # Blocks to their in edges
        self._opaque_edges: Set[Edge] = set()  # Edges whose jump targets we don't know yet

        self._add(entry_block, check=False)
        self._add(return_block, check=False)
        self._add(rethrow_block, check=False)

    def __len__(self) -> int:
        return len(self._blocks)

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, Block):
            return (<Block>item).label in self._blocks and self._blocks[(<Block>item).label] == item
        return False

    def __iter__(self) -> Iterator[Block]:
        return iter(self._blocks.values())

    def __getitem__(self, item: Any) -> Block:
        if item.__class__ is int:
            return self._blocks[item]
        raise TypeError("Expected int, got %r." % item.__class__)

    # ------------------------------ Internal API ------------------------------ #

    cdef void _add(self, Block block, bint check = True) except *:
        """
        Internal call for adding a block to this graph.

        :param check: Should if this block is valid?
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
        self._forward_edges[block] = set()
        self._backward_edges[block] = set()

    cdef void _remove(self, Block block, bint check = True) except *:
        """
        Internal call for removing a block from this graph.

        :param check: Should we check if the block can be removed?
        """

        # These blocks cannot be removed, for obvious reasons.
        if check and (block == self.return_block or block == self.rethrow_block):
            raise ValueError("Cannot remove block %r." % block)

        try:
            del self._blocks[block.label]
        except KeyError:  # Not in the graph
            raise ValueError("Block %r is not in the graph." % block)

        if block == self.entry_block:
            self.entry_block = None

        cdef set edges = self._forward_edges.pop(block)
        for edge in edges:
            self.disconnect(edge)

    cdef void _connect(self, Edge edge, bint overwrite = False, bint check = True) except *:
        """
        Internal call for connecting an edge between two blocks in this graph.

        :param check: Should we check if the edge is valid (and add the blocks if they don't exist)?
        """

        if check:
            if edge.to == self.entry_block:
                raise ValueError("Cannot create an edge to the entry block.")
            elif edge.from_ == self.return_block:
                raise ValueError("Cannot create an edge from the return block.")
            elif edge.from_ == self.rethrow_block:
                raise ValueError("Cannot create an edge from the rethrow block.")

            if not edge.from_.label in self._blocks:
                self._add(edge.from_)
            if not edge.to.label in self._blocks:
                self._add(edge.to)

        cdef set forward = self._forward_edges[edge.from_]
        cdef set backward
        cdef set conflicts

        if check:
            conflicts = set()

            if edge.limit is None:
                forward.add(edge)
            else:
                for edge_ in forward:
                    if edge_.__class__ is edge.__class__:
                        conflicts.add(edge_)

                if len(conflicts) >= edge.limit:
                    if overwrite:
                        for edge_ in conflicts:
                            self.disconnect(edge_)
                    else:
                        raise ValueError("Cannot add edge %r, limit of %i reached. Use overwrite=True." % (edge, edge.limit))
                forward.add(edge)
        else:
            forward.add(edge)

        if edge.to is not None:
            backward = self._backward_edges[edge.to]
            backward.add(edge)
        else:
            self._opaque_edges.add(edge)

    cdef void _disconnect(self, Edge edge) except *:
        """
        Internal call for disconnecting an edge from this graph.
        """

        self._blocks.setdefault(edge.from_.label, edge.from_)
        self._blocks.setdefault(edge.to.label, edge.to)

        cdef set forward = self._forward_edges.get(edge.from_, None)
        cdef set backward

        if forward is not None and edge in forward:
            forward.remove(edge)

        if edge.to is not None:
            backward = self._backward_edges.get(edge.to, None)
            if backward is not None and edge in backward:
                backward.remove(edge)
        else:
            self._opaque_edges.remove(edge)

    # ------------------------------ Public API ------------------------------ #

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

    def add(self, block: Block) -> None:
        """
        Adds a block to this graph.

        :param block: The block to add.
        """

        self._add(<Block?>block)

    def remove(self, block: Block) -> None:
        """
        Removes a block from this graph. Any edges that connect this block to other blocks will be removed too.

        :param block: The block to remove.
        """

        self._remove(<Block?>block)

    def connect(self, edge: Edge, overwrite: bool = False) -> None:
        """
        Adds an edge to this graph (connecting two blocks).
        It's called connect cos I wanna keep this class clean lol, and not have "add_block" or "add_edge".

        :param edge: The edge to add to this graph.
        :param overwrite: Overwrites existing edges, if the given edge is limited.
        """

        self._connect(<Edge?>edge, overwrite)

    def disconnect(self, edge: Edge) -> None:
        """
        Removes an edge from this graph.

        :param edge: The edge to remove.
        """

        self._disconnect(<Edge?>edge)

    def is_opaque(self, edge: Edge) -> bool:
        """
        Checks if the given edge is opaque.

        :param edge: The edge to check.
        :return: Is this edge opaque?
        """

        return edge in self._opaque_edges

    def successors(self, block: Block) -> Tuple[Block, ...]:
        """
        Gets the successors for a given block.

        :param block: The block in question.
        :return: The block's successors.
        """

        return tuple((<Edge>edge).to for edge in self._forward_edges.get(block, ()))

    def successors_iter(self, block: Block) -> Iterator[Block]:
        """
        Gest the successors for a given block, as an iterator.

        :param block: The block in question.
        """

        for edge in self._forward_edges[block]:
            yield (<Edge>edge).to

    def predecessors(self, block: Block) -> Tuple[Block, ...]:
        """
        Gets the predecessors for a given block.

        :param block: The block in question.
        :return: The block's predecessors.
        """

        return tuple((<Edge?>edge).from_ for edge in self._backward_edges.get(block, ()))

    def predecessors_iter(self, block: Block) -> Iterator[Block]:
        """
        Gets the predecessors for a given block, as an iterator.

        :param block: The block in question.
        """

        for edge in self._backward_edges[block]:
            yield (<Edge>edge).from_

    def out_edges(self, block: Block) -> Tuple[Edge, ...]:
        """
        Gets the out edges for a given block.

        :param block: The block in question.
        :return: The out edges for that block.
        """

        return tuple(self._forward_edges.get(block, ()))

    def out_edges_iter(self, block: Block) -> Iterator[Edge]:
        """
        Gets the out edges for a given block, as an iterator.

        :param block: The block in question.
        """

        for edge in self._forward_edges[block]:
            yield edge

    def in_edges(self, block: Block) -> Tuple[Edge, ...]:
        """
        Gets the in edges for a given block.

        :param block: The block in question.
        :return: The in edges for that block.
        """

        return tuple(self._backward_edges.get(block, ()))

    def in_edges_iter(self, block: Block) -> Iterator[Edge]:
        """
        Gets the in edges for a given block, as an iterator.

        :param block: The block in question.
        """

        for edge in self._backward_edges[block]:
            yield edge

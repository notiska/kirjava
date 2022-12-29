#!/usr/bin/env python3

__all__ = (
    "Block", "Edge", "Graph", "RethrowBlock", "ReturnBlock",
)

"""
Abstract base classes for graph representations of methods.
"""

import logging
from abc import abstractmethod, ABC
from typing import Any, Dict, List, Set, Tuple, Union

from . import Source
from .method import Method

logger = logging.getLogger("kirjava.abc.graph")


class Block(Source, ABC):
    """
    An (extended) basic block.
    """

    __slots__ = ("graph", "label")

    @property
    def successors(self) -> Tuple["Block", ...]:
        """
        :return: This block's successors.
        """

        # Faster to just access it directly instead of making another function call.
        return tuple(edge.to for edge in self.graph._forward_edges.get(self, ()))

    @property
    def predecessors(self) -> Tuple["Block", ...]:
        """
        :return: This block's predecessors.
        """

        return tuple(edge.from_ for edge in self.graph._backward_edges.get(self, ()))

    @property
    def out_edges(self) -> Tuple["Edge", ...]:
        """
        :return: This block's out edges.
        """

        return tuple(self.graph._forward_edges.get(self, ()))

    @property
    def in_edges(self) -> Tuple["Edge", ...]:
        """
        :return: This block's in edges.
        """

        return tuple(self.graph._backward_edges.get(self, ()))

    def __init__(self, graph: "Graph", label: Union[int, None] = None, add: bool = True) -> None:
        """
        :param graph: The graph that this block belongs to.
        :param label: The label of this block, if None, it is determined automatically by the graph.
        :param add: Adds this block to the graph.
        """

        self.graph = graph
        self.label = label  # Define this before adding to the graph

        if add:
            self.label = graph.add(self)

    def __repr__(self) -> str:
        return "<Block(label=%s) at %x>" % (self.label, id(self))

    def __str__(self) -> str:
        if self.label is None:
            return "block (unidentified)"
        return "block %i" % self.label

    def __eq__(self, other: Any) -> bool:
        return other.__class__ == self.__class__ and other.graph == self.graph and other.label == self.label

    def __hash__(self) -> int:
        return hash(self.label)

    @abstractmethod
    def copy(self, deep: bool = False) -> "Block":
        """
        Creates a copy of this block.

        :param deep: Create a deep copy?
        :return: The copy of this block.
        """

        ...


class ReturnBlock(Block, ABC):
    """
    The return block for a graph. All blocks returning from the method should have an edge to this one.
    """

    LABEL = -1

    def __init__(self, graph: "Graph") -> None:
        super().__init__(graph, self.__class__.LABEL, add=False)

    def __repr__(self) -> str:
        return "<ReturnBlock() at %x>" % id(self)

    def __str__(self) -> str:
        return "return block"


class RethrowBlock(Block, ABC):
    """
    The rethrow block for a graph. If an exception is uncaught, the block that threw the exception (or one of its
    handlers) should have an edge to this block.
    """

    LABEL = -2

    def __init__(self, graph: "Graph") -> None:
        super().__init__(graph, self.__class__.LABEL, add=False)

    def __repr__(self) -> str:
        return "<RethrowBlock() at %x>" % (id(self))

    def __str__(self) -> str:
        return "rethrow block"


class Edge(Source, ABC):
    """
    An edge connects to vertices (blocks) in a control flow graph.
    """

    __slots__ = ("from_", "to")

    def __init__(self, from_: Block, to: Block) -> None:
        """
        :param from_: The block we're coming from.
        :param to: The block we're going to.
        """

        self.from_ = from_
        self.to = to

    def __repr__(self) -> str:
        return "<%s(from=%r, to=%r) at %x>" % (self.__class__.__name__, self.from_, self.to, id(self))

    def __str__(self) -> str:
        return "%s -> %s" % (self.from_, self.to)

    def __eq__(self, other: Any) -> bool:
        return other.__class__ == self.__class__ and other.from_ == self.from_ and other.to == self.to

    def __hash__(self) -> int:
        return hash((self.from_, self.to))


class Graph(ABC):
    """
    A control flow graph representing a method.
    """

    __slots__ = (
        "method",
        "_entry_block", "_return_block", "_rethrow_block",
        "_blocks",
        "_forward_edges", "_backward_edges", "_opaque_edges",
    )

    @property
    def blocks(self) -> Tuple[Block, ...]:
        """
        :return: All the blocks in this graph.
        """

        return tuple(self._blocks)

    @property
    def edges(self) -> Tuple[Edge, ...]:
        """
        :return: All the edges in this graph.
        """

        edges = []
        for edges_ in self._forward_edges.values():
            edges.extend(edges_)
        return tuple(edges)

    @property
    def opaque_edges(self) -> Tuple[Edge, ...]:
        """
        :return: All the opaque edges (edges whose to blocks we don't yet know).
        """

        return tuple(self._opaque_edges)

    # @property
    # def leaves(self) -> Tuple[Block, ...]:
    #     """
    #     :return: All the leaves in this graph (blocks with no out edges).
    #     """

    #     leaves = []
    #     for block in self._blocks:
    #         if not self._forward_edges.get(block, False):
    #             leaves.append(block)
    #     return tuple(leaves)

    @property
    def return_block(self) -> ReturnBlock:
        """
        :return: This graph's return block.
        """

        return self._return_block

    @property
    def rethrow_block(self) -> RethrowBlock:
        """
        :return: This graph's rethrow block.
        """

        return self._rethrow_block

    def __init__(self, method: Method, return_block: ReturnBlock, rethrow_block: RethrowBlock) -> None:
        """
        :param method: The method that this graph represents.
        :param return_block: The return block for this graph.
        :param rethrow_block: The rethrow block for this graph.
        """

        self.method = method

        # Special kinds of blocks
        self.entry_block: Union[Block, None] = None
        self._return_block = return_block
        self._rethrow_block = rethrow_block

        self._blocks: List[Block] = [return_block, rethrow_block]
        self._forward_edges: Dict[Block, Set[Edge]] = {}  # Blocks to their out edges (faster lookup)
        self._backward_edges: Dict[Block, Set[Edge]] = {}  # Blocks to their in edges
        self._opaque_edges: Set[Edge] = set()  # Edges whose jump targets we don't know yet

    def __len__(self) -> int:
        return len(self._blocks)

    def __getitem__(self, label: int) -> Block:
        return self.get(label)

    def fix_labels(self, zero_entry_block: bool = True) -> None:
        """
        Fixes any gaps in label ordering and fixes duplicate labels too.

        :param zero_entry_block: Zeroes the entry block's label if necessary.
        """

        labels: Dict[int, Block] = {}
        # We need to keep track of any changed blocks with their old edges, as the hashes depend on the labels.
        forward_edges: List[Tuple[Block, List[Edge]]] = []
        backward_edges: List[Tuple[Block, List[Edge]]] = []

        max_label = 0

        if zero_entry_block and self.entry_block.label:
            if self.entry_block in self._forward_edges:
                forward_edges.append((self.entry_block, list(self._forward_edges[self.entry_block])))
                del self._forward_edges[self.entry_block]
            if self.entry_block in self._backward_edges:
                backward_edges.append((self.entry_block, list(self._backward_edges[self.entry_block])))
                del self._backward_edges[self.entry_block]

            self.entry_block.label = 0

        if self._return_block.label != ReturnBlock.LABEL:
            if self._return_block in self._forward_edges:
                forward_edges.append((self._return_block, list(self._forward_edges[self._return_block])))
                del self._forward_edges[self._return_block]
            if self._return_block in self._backward_edges:
                backward_edges.append((self._return_block, list(self._backward_edges[self._return_block])))
                del self._backward_edges[self._return_block]
            self._return_block.label = ReturnBlock.LABEL

        if self._rethrow_block.label != RethrowBlock.LABEL:
            if self._rethrow_block in self._forward_edges:
                forward_edges.append((self._rethrow_block, list(self._forward_edges[self._rethrow_block])))
                del self._forward_edges[self._rethrow_block]
            if self._rethrow_block in self._backward_edges:
                backward_edges.append((self._rethrow_block, list(self._backward_edges[self._rethrow_block])))
                del self._backward_edges[self._rethrow_block]
            self._rethrow_block.label = RethrowBlock.LABEL

        for block in self._blocks:
            if block.label > max_label:
                max_label = block.label

            if not block.label in labels:
                labels[block.label] = block
                continue

            if block in self._forward_edges:
                forward_edges.append((block, list(self._forward_edges[block])))
                del self._forward_edges[block]
            if block in self._backward_edges:
                backward_edges.append((block, list(self._backward_edges[block])))
                del self._backward_edges[block]

            label = max_label + 1  # Find the next best label for this block, this will be adjusted later
            while label in labels:
                label += 1
            block.label = label
            labels[label] = block

        for index in range(len(self._blocks) - 2):  # Ignore return and rethrow blocks
            if index in labels:  # This index is fine, so skip over it
                del labels[index]
                continue

            # We need to find the next greatest label from the index and set it to the index, this will be the minimum
            # label in the labels dict as we're deleting old ones.
            min_label = min(labels)
            block = labels[min_label]

            if block in self._forward_edges:
                forward_edges.append((block, list(self._forward_edges[block])))
                del self._forward_edges[block]
            if block in self._backward_edges:
                backward_edges.append((block, list(self._backward_edges[block])))
                del self._backward_edges[block]

            block.label = index
            del labels[min_label]

        # Finally, add back all the edges that we removed

        for block, edges in forward_edges:
            self._forward_edges[block] = set(edges)
        for block, edges in backward_edges:
            self._backward_edges[block] = set(edges)

    def get(self, label: int) -> Block:
        """
        Gets a block in this graph given its label.

        :param label: The label of the block.
        :return: The block, if it was found.
        """

        for block in self._blocks:
            if block.label == label:
                return block

        raise LookupError("Couldn't find block with label %i." % label)

    def add(self, block: Block, fix_labels: bool = True) -> int:
        """
        Adds a block to this graph.

        :param block: The block to add.
        :param fix_labels: Should label conflicts be fixed?
        :return: The block's label.
        """

        if block in self._blocks:  # Already added
            return block.label

        if fix_labels or block.label is None:
            conflict = False
            max_label = 0

            for block_ in self._blocks:
                label = block_.label
                if label > max_label:
                    max_label = label
                if label == block.label:
                    conflict = True

            if conflict or block.label is None:
                max_label += 1
                logger.debug("Adjusted label for %s to %i." % (block, max_label))
                block.label = max_label

        self._blocks.append(block)

        # VV this probably just wastes performance
        # if isinstance(block, ReturnBlock):
        #     self._return_block = block
        # elif isinstance(block, RethrowBlock):
        #     self._rethrow_block = block

        return block.label

    def remove(self, block: Block) -> bool:
        """
        Removes a block from this graph. Any edges that connect this block to other blocks will be removed too.

        :param block: The block to remove.
        :return: Was the block removed successfully?
        """

        if block in (self._return_block, self._rethrow_block):  # These blocks cannot be removed, for obvious reasons
            return False

        try:
            self._blocks.remove(block)
        except ValueError:  # Not in the graph
            return False

        if block == self.entry_block:
            self.entry_block = None

        if block in self._forward_edges:
            edges = self._forward_edges[block]
            del self._forward_edges[block]

            for edge in edges:
                self.disconnect(edge)

        return True

    def connect(self, edge: Edge) -> None:
        """
        Adds an edge to this graph (connecting two blocks).
        It's called connect cos I wanna keep this class clean lol, and not have "add_block" or "add_edge".

        :param edge: The edge to add to this graph.
        """

        forward = self._forward_edges.setdefault(edge.from_, set()).add(edge)

        if edge.to is not None:
            self._backward_edges.setdefault(edge.to, set()).add(edge)
        else:
            self._opaque_edges.add(edge)

    def disconnect(self, edge: Edge) -> None:
        """
        Removes an edge from this graph.

        :param edge: The edge to remove.
        """

        forward = self._forward_edges.get(edge.from_, None)
        if forward is not None and edge in forward:
            forward.remove(edge)

        if edge.to is not None:
            backward = self._backward_edges.get(edge.to, None)
            if backward is not None and edge in backward:
                backward.remove(edge)
        else:
            self._opaque_edges.remove(edge)

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

        return tuple(edge.to for edge in self._forward_edges.get(block, ()))

    def predecessors(self, block: Block) -> Tuple[Block, ...]:
        """
        Gets the predecessors for a given block.

        :param block: The block in question.
        :return: The block's predecessors.
        """

        return tuple(edge.from_ for edge in self._backward_edges.get(block, ()))

    def out_edges(self, block: Block) -> Tuple[Edge, ...]:
        """
        Gets the out edges for a given block.

        :param block: The block in question.
        :return: The out edges for that block.
        """

        return tuple(self._forward_edges.get(block, ()))

    def in_edges(self, block: Block) -> Tuple[Edge, ...]:
        """
        Gets the in edges for a given block.

        :param block: The block in question.
        :return: The in edges for that block.
        """

        return tuple(self._backward_edges.get(block, ()))

    # def walk(self, top_down: bool = True) -> Tuple[Block, Union[Edge, None], Tuple[Edge, ...]]:
    #     """
    #     Walks this control flow graph.

    #     :param top_down: Walk the graph from the entry block down?
    #     :return: The current block, the current edge, and the out/in edges from the current block (depending on top_down).
    #     """

    #     if self.entry_block is None and top_down:
    #         raise ValueError("No entry block, cannot walk graph top down.")

    #     edges = self._forward_edges if top_down else self._backward_edges
    #     block = self.entry_block if top_down else self._return_block
    #     edge = None

    #     # Edges we've visited already, (note that we're not recording blocks here). 
    #     visited: Set[Edge] = set()
    #     next_: List[Edge] = []

    #     while True:
    #         edges_ = edges.get(block, ())
    #         yield block, edge, tuple(edges_)

    #         if edge is None or not edge in visited:  # Might have duplicates
    #             visited.add(edge)

    #             for edge in edges_:
    #                 if not edge in visited:
    #                     next_.append(edge)

    #         while next_:
    #             edge = next_.pop(0)
    #             block = edge.to
    #             if block is not None:  # Some edges are opaque, we don't know their target until we work it out
    #                 break
    #         else:
    #             break

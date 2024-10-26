#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "block", "edge",
    "Block", "MutableBlock", "ImmutableBlock", "Return",
    "Edge", "Fallthrough", "Jump", "Ret", "Switch", "Catch",
    "Graph",
)

from collections import defaultdict
from copy import copy, deepcopy
from typing import Iterable, Iterator

from . import block, edge
from ._dis import disassemble
from .block import *
from .edge import *
from .edge import Jump as JumpEdge
from ..fmt import ClassFile, MethodInfo
from ..insns import goto, Instruction
from ..insns.flow import Jump as JumpInsn
from ..._compat import Self
from ...backend import Result


# FIXME: Make the graph structure more/less expressive? Want to maximise usability, analysis can have a separate data
#        structure to store more complex relations such as rethrow, direct links, resolved subroutines, etc...
class Graph:
    """
    A JVM control flow graph.

    Attributes
    ----------
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
    disassemble(method: MethodInfo, cf: ClassFile | None = None) -> Result[Self]
        Disassembled a method into a JVM control flow graph.

    predecessors(self, block: int | Block) -> tuple[Edge, ...]
        Returns all the predecessor edges of a block.
    successors(self, block: int | Block) -> tuple[Edge, ...]
        Returns all the successor edges of a block.
    get(self, key: int | Block) -> Block | tuple[Edge, ...] | None
        Gets either a block or the out edges of a block.
    add(self, block_or_edge: Block | Edge) -> None
        Adds a block or an edge to this graph.
    remove(self, value: Block | Edge) -> None
        Removes a block or an edge from this graph.
    fallthrough(self, source: int | Block, target: int | Block, *, doraise: bool = True) -> Fallthrough
        Creates a fallthrough edge between two blocks.
    """

    __slots__ = (
        "entry", "return_", "rethrow", "opaque",
        "_blocks", "_edges_out", "_edges_in",
    )

    @classmethod
    def disassemble(cls, method: "MethodInfo", cf: ClassFile | None = None) -> Result[Self]:
        """
        Disassembles a method into a JVM control flow graph.

        Parameters
        ----------
        method: MethodInfo
            The method to disassemble.
        cf: ClassFile | None
            The class file containing the method.
        """

        return disassemble(cls(), method, cf)

    def __init__(self) -> None:
        self.entry   = MutableBlock(0)
        self.return_ = Return()
        self.rethrow = Rethrow()
        self.opaque  = Opaque()

        self._blocks = {
            self.opaque.label: self.opaque,
            self.rethrow.label: self.rethrow,
            self.return_.label: self.return_,
            self.entry.label: self.entry,
        }
        # Using dicts instead of sets here to preserve order.
        self._edges_out: dict[Block, dict[Edge, None]] = defaultdict(dict)
        self._edges_in:  dict[Block, dict[Edge, None]] = defaultdict(dict)

    # def __repr__(self) -> str:
    #     return f"<Graph(blocks=)>"

    def __iter__(self) -> Iterator[Block]:
        return iter(self._blocks.values())

    def __getitem__(self, key: int | Block) -> Block | tuple[Edge, ...]:
        if isinstance(key, int):
            return self._blocks[key]

        if self._blocks[key.label] != key:
            raise KeyError(key)
        return tuple(self._edges_out[key])

    def __setitem__(self, key: int, value: Block) -> None:
        if isinstance(value, Opaque):
            raise TypeError("cannot replace opaque block directly")
        elif isinstance(value, Rethrow):
            raise TypeError("cannot replace rethrow block directly")
        elif isinstance(value, Return):
            raise TypeError("cannot replace return block directly")

        old = self._blocks.get(key)
        if isinstance(old, Opaque):
            raise TypeError("cannot replace opaque block directly")
        elif isinstance(old, Rethrow):
            raise TypeError("cannot replace rethrow block directly")
        elif isinstance(old, Return):
            raise TypeError("cannot replace return block directly")

        if key != value.label:
            value = value.replace(label=key)
        self._blocks[key] = value

        if old is None or old is value:  # Nothing further to do.
            return

        for edge in self._edges_out.pop(old, ()):
            self._edges_out[value][edge.replace(source=value)] = None
        for edge in self._edges_in.pop(old, ()):
            self._edges_in[value][edge.replace(target=value)] = None

    def __delitem__(self, key: int | Block | Edge) -> None:
        if isinstance(key, Edge):
            if not key.source in self._edges_out:
                raise KeyError(key.source)
            if not key.target in self._edges_in:
                raise KeyError(key.target)
            self._edges_out[key.source].pop(key)
            self._edges_in[key.target].pop(key)
            return

        if isinstance(key, int):
            key = self._blocks[key]
        elif isinstance(key, Block):
            if self._blocks[key.label] != block:
                raise KeyError(key)

        if isinstance(key, Opaque):
            raise TypeError("cannot remove opaque block directly from graph")
        elif isinstance(key, Rethrow):
            raise TypeError("cannot remove rethrow block directly from graph")
        elif isinstance(key, Return):
            raise TypeError("cannot remove return block directly from graph")
        elif key == self.entry:
            raise ValueError("cannot remove entry block directly from graph")

        del self._blocks[key.label]
        for edge in self._edges_out.pop(key, ()):
            self._edges_in[edge.target].pop(edge)

    def __len__(self) -> int:
        return len(self._blocks)

    def predecessors(self, block: int | Block) -> tuple[Edge, ...]:
        """
        Returns all the predecessor edges of a block.

        Parameters
        ----------
        block: int | Block
            The label or block to get the predecessors of.

        Raises
        ------
        KeyError
            If the block doesn't exist in this graph.
        """

        if isinstance(block, int):
            block = self._blocks[block]
        elif self._blocks.get(block.label) != block:
            raise KeyError(block)
        return tuple(self._edges_in[block])

    def successors(self, block: int | Block) -> tuple[Edge, ...]:
        """
        Returns all the successor edges of a block.

        Parameters
        ----------
        block: int | Block
            The label or block to get the successors of.

        Raises
        ------
        KeyError
            If the block doesn't exist in this graph.
        """

        if isinstance(block, int):
            block = self._blocks[block]
        elif self._blocks.get(block.label) != block:
            raise KeyError(block)
        return tuple(self._edges_out[block])

    def get(self, key: int | Block) -> Block | tuple[Edge, ...] | None:
        """
        Returns either a block or the successor edges of a block.

        Parameters
        ----------
        key: int | Block
            Either the label of a block, to get the block, or a block itself, to get
            its successor edges.

        Returns
        -------
        Block | tuple[Edge, ...] | None
            If a label was provided, the block, or `None` if not found.
            If a block was provided, the successor edges of the block, or `None` if
            the block does not exist in this graph.
        """

        if isinstance(key, int):
            return self._blocks.get(key)
        if self._blocks.get(key.label) != key:
            return None
        return tuple(self._edges_out[key])

    def add(self, block_or_edge: Block | Edge) -> None:
        """
        Adds a block or an edge to this graph.

        Raises
        ------
        KeyError
            If adding a block, and a block with the same label already exists.
            If adding an edge, and either the source or target block does not exist
            in this graph.
        TypeError
            If adding a block, and the block type cannot be directly added to this
            graph.
        """

        if isinstance(block_or_edge, Block):
            if isinstance(block_or_edge, Opaque):
                raise TypeError("cannot add opaque block directly to graph")
            elif isinstance(block_or_edge, Rethrow):
                raise TypeError("cannot add rethrow block directly to graph")
            elif isinstance(block_or_edge, Return):
                raise TypeError("cannot add return block directly to graph")

            if block_or_edge.label in self._blocks:
                raise KeyError(block_or_edge.label)

            self._blocks[block_or_edge.label] = block_or_edge

        else:
            if self._blocks[block_or_edge.source.label] != block_or_edge.source:
                raise KeyError(block_or_edge.source)
            if self._blocks[block_or_edge.target.label] != block_or_edge.target:
                raise KeyError(block_or_edge.target)

            self._edges_out[block_or_edge.source][block_or_edge] = None
            self._edges_in[block_or_edge.target][block_or_edge] = None

    # def update(self) -> None:
    #     raise NotImplementedError()  # TODO

    def remove(self, value: Block | Edge) -> None:
        """
        Removes a block or an edge from this graph.

        No error is raised if the block or edge does not exist in this graph.
        """

        if isinstance(value, Edge):
            self._edges_out[value.source].pop(value, None)
            self._edges_in[value.target].pop(value, None)
            return

        if isinstance(value, (Opaque, Rethrow, Return)):
            return
        elif value == self.entry:
            return
        elif self._blocks.get(value.label) != value:
            return

        del self._blocks[value.label]
        for edge in self._edges_out.pop(value, ()):
            self._edges_in[edge.target].pop(edge, None)

    # def pop(self, key: int | Block) -> Block | set[Edge] | None:
    #     """
    #     Removes a block from this graph and returns it.

    #     Parameters
    #     ----------
    #     key: int | Block
    #         Either the label of a block, to pop the block, or a block itself, to pop
    #         its out edges.

    #     Returns
    #     -------
    #     Block | set[Edge] | None
    #         If a label was provided, the block, or `None` if not found.
    #         If a block was provided, the out edges of the block, or `None` if the
    #         block does not exist in this graph.
    #     """

    #     if isinstance(key, int):
    #         return self._blocks.pop(key, None)

    #     if self._blocks.get(key.label) != key:
    #         return None
    #     edges_out = self._edges_out.pop(key, None)
    #     if edges_out is None:
    #         return None
    #     for edge in edges_out:
    #         self._edges_in[edge.target].discard(edge)
    #     return edges_out

    def fallthrough(self, source: int | Block, target: int | Block, *, doraise: bool = True) -> Fallthrough:
        """
        Creates a fallthrough edge between two blocks.

        Parameters
        ----------
        source: int | Block
            The label or block to fall through from.
        target: int | Block
            The label or block to fall through to.
        doraise: bool
            Raises an exception if the edge puts the graph in an invalid state.

        Returns
        -------
        Fallthrough
            The fallthrough edge created.

        Raises
        ------
        ValueError
            If `doraise=True` and the edge would be invalid in the graph.
        """

        if not isinstance(source, Block):
            source = self._blocks[source]
        if not isinstance(target, Block):
            target = self._blocks[target]

        edge = Fallthrough(source, target)  # TODO: Checks for duplicate edges, etc.
        self._edges_out[source][edge] = None
        self._edges_in[target][edge] = None

        return edge

    def jump(
            self, source: int | Block, target: int | Block | None = None,
            instruction: JumpInsn | type[JumpInsn] = goto,
            *, doraise: bool = True,
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
        instruction: JumpInsn | type[JumpInsn]
            The instruction to use for the jump.
        doraise: bool
            Raises an exception if the edge puts the graph in an invalid state.

        Returns
        -------
        JumpEdge
            The jump edge created.

        Raises
        ------
        TypeError
            If `doraise=True` and the instruction is not a jump instruction.
        ValueError
            If `doraise=True` and the edge would be invalid in the graph.
        """

        if not isinstance(source, Block):
            source = self._blocks[source]
        if target is not None and not isinstance(target, Block):
            target = self._blocks[target]

        if not isinstance(instruction, JumpInsn):
            instruction = instruction(0)

        # FIXME
        # edge = JumpEdge(source, target, instruction)
        # self.edges_out[source].add(edge)
        # self.edges_in[target].add(edge)

        # return edge

        raise NotImplementedError(f"jump() is not implemented for {type(self)!r}")

    # def catch(self) -> Catch:

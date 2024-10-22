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
from .block import *
from .edge import Catch, Edge, Fallthrough, Jump as JumpEdge
from ..fmt import ClassFile, MethodInfo
from ..insns import goto, Instruction
from ..insns.flow import Jump as JumpInsn
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
        self._edges_out: dict[Block, set[Edge]] = defaultdict(set)
        self._edges_in:  dict[Block, set[Edge]] = defaultdict(set)

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
        self._edges_out[source].add(edge)
        self._edges_in[target].add(edge)

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

    # def merge_single_successors(self) -> None:
    #     ...

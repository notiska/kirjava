#!/usr/bin/env python3

__all__ = (
    "block", "edge",
    "Graph",
)

import typing
from collections import defaultdict
from typing import IO

from . import block, edge
from ._dis import *
from .block import Block
from .edge import Edge
from ..fmt.method import Code, MethodInfo

if typing.TYPE_CHECKING:
    from ..fmt import ClassFile


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
    disassemble(method_info: MethodInfo, class_file: ClassFile, stream: IO[bytes] | None = None) -> Graph
        Disassembles a method into a control flow graph.
    block(self) -> Block
        Creates a new block in this graph.
    """

    __slots__ = (
        "blocks", "edges_out", "edges_in",
        "entry", "return_", "rethrow", "opaque",
        "_label",
    )

    @classmethod
    def disassemble(cls, method: MethodInfo, cf: "ClassFile", stream: IO[bytes] | None) -> "Graph":
        """
        Disassembles a method into a JVM control flow graph.

        Parameters
        ----------
        method: MethodInfo
            The method to disassemble.
        cf: ClassFile
            The class file containing the method.
        stream: IO[bytes] | None
            An optional class file stream to disassemble from.
            Using this may result in more accurate disassembly, but is not required.

        Returns
        -------
        Graph
            The disassembled JVM control flow graph.

        Raises
        ------
        ValueError
            If the method has no code attribute.
        """

        assert not method.is_native, "cannot disassemble native methods"
        assert not method.is_abstract, "cannot disassemble abstract methods"

        code = None
        for attribute in method.attributes:
            if not isinstance(attribute, Code):
                continue
            elif code is not None:
                # Not even allowed by the JVM with `-Xverify:none`.
                raise ValueError("multiple code attributes in method")
            code = attribute
            # if context.skip_multiple_code_attrs:
            #     break
        if code is None:
            raise ValueError("no code attribute in method")

        self = cls()
        disassemble(self, code, cf, stream)
        return self

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

    def merge_single_successors(self) -> None:
        ...

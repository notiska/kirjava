#!/usr/bin/env python3

__all__ = (
    "IRGraph",
)

"""
A control flow graph containing the IR instructions.
"""

import typing
from typing import Iterable, List, Union

from ..trace import Trace
from ...abc import Block, Graph, Statement

if typing.TYPE_CHECKING:
    from ..graph import InsnGraph


class IRBlock(Block):
    """
    A block containing IR statements.
    """

    __slots__ = ("statements",)

    def __init__(
            self,
            label: Union[int, None] = None,
            statements: Union[Iterable[Statement], None] = None,
    ) -> None:
        """
        :param statements: The IR statements.
        """

        super().__init__(label)

        self.statements: List[Statement] = []
        if statements is not None:
            self.statements.extend(statements)

    def __repr__(self) -> str:
        return "<IRBlock(label=%i, statements=%r) at %x>" % (self.label, self.statements, id(self))


class IRGraph(Graph):
    """
    A control flow graph containing IR instructions.
    """

    @classmethod
    def lift(cls, graph: "InsnGraph") -> "IRGraph":
        """
        Lifts the provided instruction graph into IR.

        :param graph: The instruction graph.
        :return: The generated IR graph.
        """

        trace = Trace.from_graph(graph, exact=True)

        for block in graph.blocks:
            constraints = trace.states.get(block, None)
            if constraints is None:
                continue  # Block is not visited, so we don't need to worry about it

            # TODO: Check if we can actually merge the constraints

    def lower(self) -> "InsnGraph":
        """
        Lowers this IR graph into an instruction graph.

        :return: The generated instruction graph.
        """

        ...

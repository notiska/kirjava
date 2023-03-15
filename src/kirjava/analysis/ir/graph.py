#!/usr/bin/env python3

__all__ = (
    "IRGraph",
)

"""
A control flow graph containing the IR instructions.
"""

import typing
from typing import Iterable, List, Optional

from .variable import Parameter, Scope, Super, This
from .._edge import InsnEdge
from ..source import InstructionInBlock
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
            label: Optional[int] = None,
            statements: Optional[Iterable[Statement]] = None,
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

        trace = Trace.from_graph(graph)
        (initial, _), = trace.frames[graph.entry_block]

        scope = Scope()
        associations = {}

        # Declare this and super variables
        if not graph.method.is_static:
            this = This(initial.locals[0].type.class_)
            super_ = Super(initial.locals[0].type.class_)
            scope.declare(this)
            scope.declare(super_)
            associations[initial.locals[0]] = this

        # Declare any parameters
        for index, entry in initial.locals.items():
            param = Parameter(scope.variable_id, index, entry.type)
            scope.declare(param)
            associations[entry] = param

        for block in graph.blocks:
            states = trace.deltas.get(block)
            if states is None:
                continue  # Block is not visited, so we don't need to worry about it

            if len(states) == 1:  # We don't have to create any phis
                for delta in states[0]:
                    statement = None
                    if type(delta.source) is InstructionInBlock:
                        statement = delta.source.instruction.lift(delta, scope, associations)
                    elif isinstance(delta.source, InsnEdge):
                        statement = delta.source.instruction.lift(delta, scope, associations)

                    if statement is not None:
                        print(statement)

                continue

            raise NotImplementedError("Multiple states for block %s." % block)

            # TODO: Check if we can actually merge the constraints

    def lower(self) -> "InsnGraph":
        """
        Lowers this IR graph into an instruction graph.

        :return: The generated instruction graph.
        """

        ...

#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "state", "steps",
    "State",
    "Step",
    "Analysis",
)

"""
Various analysis functionality for JVM bytecode.
"""

import typing
from collections import defaultdict
from typing import Optional

from . import state, steps
from ._trace import *
from .state import *
from .steps import *
from ..._compat import Self
from ...backend import Result

if typing.TYPE_CHECKING:
    from ..graph import Block, Graph
    from ..fmt import ClassFile, MethodInfo


class Analysis:
    """
    Method JVM bytecode analysis information.

    Attributes
    ----------
    live_states: dict[Block, list[State]]
        All computed live states at all live blocks.
    all_states: list[State]
        All computed states (live or dead).
    prelive: dict[Block, set[int]]
        The live locals at the entry to each block.
    postlive: dict[Block, set[int]]
        The live locals at the exit of each block.

    Methods
    -------
    trace(graph: Graph, method: MethodInfo, cf: ClassFile | None) -> Result[Self]
        Traces through the provided graph.
    """

    __slots__ = ("live_states", "all_states", "prelive", "postlive")

    @classmethod
    def trace(cls, graph: "Graph", method: "MethodInfo", cf: Optional["ClassFile"]) -> Result[Self]:
        """
        Traces through the provided graph.

        Parameters
        ----------
        graph: Graph
            The graph to trace through.
        method: MethodInfo
            The method info represented in the provided graph.
        cf: ClassFile | None
            The classfile that the method belongs to.
        """

        return trace(cls(), graph, method, cf)

    def __init__(self) -> None:
        # FIXME: One shot for now, so these can stay public, but may want to make them private in the future.
        self.live_states: dict["Block", list[State]] = defaultdict(list)
        self.all_states: list[State] = []

        self.prelive: dict["Block", set[int]] = defaultdict(set)
        self.postlive: dict["Block", set[int]] = defaultdict(set)

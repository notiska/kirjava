#!/usr/bin/env python3

__all__ = (
    "Liveness",
)

"""
Local variable liveness analysis.
"""

import itertools
import typing
from frozendict import frozendict
from typing import Dict, FrozenSet, Iterator, List, Set

from ._edge import ExceptionEdge
from .trace import Trace
from .verifier import BasicTypeChecker
from ..abc import Edge

if typing.TYPE_CHECKING:
    from ._block import InsnBlock
    from .graph import InsnGraph


class Liveness:
    """
    Liveness analysis information.
    """

    __slots__ = ("graph", "trace", "entries", "exits")

    @classmethod
    def from_graph(cls, graph: "InsnGraph") -> "Liveness":
        """
        Computes liveness analysis for the given graph.

        :param graph: The graph.
        :return: The computed liveness information.
        """

        # We only need a basic type checker for liveness information
        return cls.from_trace(Trace.from_graph(graph, BasicTypeChecker()))

    @classmethod
    def from_trace(cls, trace: Trace) -> "Liveness":
        """
        Computes liveness analysis from the given trace information.

        :param trace: The trace information to use.
        :return: The computed liveness information.
        """

        entries: Dict[InsnBlock, Set[int]] = {}
        exits: Dict[InsnBlock, Set[int]] = {}

        for start in itertools.chain(trace.leaf_edges, trace.back_edges):
            live = entries.setdefault(start.to, set())
            overwritten: Set[int] = set()
            for exit in trace.states[start.to].values():
                for index, _, _, read in exit.local_accesses:
                    if index in overwritten:
                        continue
                    elif read:
                        live.add(index)
                    else:
                        overwritten.add(index)
                break

            to_visit: List[Iterator[Edge]] = [iter(trace.graph.in_edges(start.to))]

            while to_visit:
                try:
                    edge = next(to_visit[0])
                    block = edge.from_
                    previous = edge.to

                except StopIteration:
                    to_visit.pop(0)
                    continue

                live = exits.setdefault(block, set())
                live.update(entries.get(previous, ()))

                before = entries.get(block, None)
                live = live.copy()

                # Check if the block was visited, if not, we don't need to worry about the liveness for it
                if block in trace.states:
                    for exit in trace.states[block].values():
                        for index, _, _, read in reversed(exit.local_accesses):
                            if read:
                                live.add(index)
                            elif index in live:
                                live.remove(index)
                        break  # Local accesses do not vary in different states, so this only needs to be done once

                # Exception edges assume that the exception might have been thrown anywhere in the block, and
                # therefore we also need to copy the liveness state from the handler's entry to the current block's
                # entry.

                if isinstance(edge, ExceptionEdge):
                    live.update(entries.get(previous, ()))

                # print(block, before, live)
                if live != before:
                    entries.setdefault(block, set()).update(live)
                    to_visit.append(iter(trace.graph.in_edges(block)))

        for block, live in entries.items():
            entries[block] = frozenset(live)
        for block, live in exits.items():
            exits[block] = frozenset(live)

        return cls(trace.graph, trace, frozendict(entries), frozendict(exits))

    def __init__(
            self,
            graph: "InsnGraph",
            trace: Trace,
            entries: Dict["InsnBlock", FrozenSet[int]],
            exits: Dict["InsnBlock", FrozenSet[int]],
    ) -> None:
        self.graph = graph
        self.trace = trace

        self.entries = entries
        self.exits = exits

    def __repr__(self) -> str:
        return "<Liveness() at %x>" % id(self)

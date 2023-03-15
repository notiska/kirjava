#!/usr/bin/env python3

__all__ = (
    "Liveness",
)

"""
Local variable liveness analysis.
"""

import itertools
import typing
from typing import Dict, FrozenSet, Iterator, List, Set

from ._edge import ExceptionEdge, InsnEdge
from .trace import Frame, Trace
from ..verifier import BasicTypeChecker

if typing.TYPE_CHECKING:
    from ._block import InsnBlock
    from .graph import InsnGraph


class Liveness:
    """
    Liveness analysis information.
    """

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

        graph = trace.graph

        entries: Dict["InsnBlock", Set[int]] = {}
        exits:   Dict["InsnBlock", Set[int]] = {}

        overwritten: Set[int] = set()

        for start in itertools.chain(trace.leaf_edges, trace.back_edges):
            live = entries.setdefault(start.to, set())
            overwritten.clear()
            for _, exit_constraint in trace.frames[start.to]:
                for read, index, _ in reversed(exit_constraint.accesses):
                    if index in live or index in overwritten:
                        continue
                    elif read:
                        live.add(index)
                    else:
                        overwritten.add(index)
                break

            to_visit = [iter(graph._backward_edges[start.to])]

            while to_visit:
                try:
                    edge = next(to_visit[-1])
                    block = edge.from_
                    previous = edge.to

                except StopIteration:
                    # Optimisations: was pop(0) (BFS), this is much slower, so is now pop() (DFS), no difference to
                    # functionality AFAIK.
                    to_visit.pop()
                    continue

                live = exits.setdefault(block, set())
                live.update(entries.get(previous, ()))

                before = entries.get(block, None)
                if before is None:
                    entries[block] = set()
                live = live.copy()

                # Check if the block was visited, if not, we don't need to worry about the liveness for it
                if block in trace.frames:
                    for _, exit_constraint in trace.frames[block]:
                        for read, index, _ in reversed(exit_constraint.accesses):
                            if read:
                                live.add(index)
                            elif index in live:
                                live.remove(index)
                        break  # Local accesses do not vary in different states, so this only needs to be done once
                        # FIXME: ^ not true, will not record non-overwritten entries

                # Exception edges assume that the exception might have been thrown anywhere in the block, and
                # therefore we also need to copy the liveness state from the handler's entry to the current block's
                # entry.

                if isinstance(edge, ExceptionEdge):
                    live.update(entries.get(previous, ()))

                live.update(entries[block])
                if live != before and (before is None or len(live) > len(before)):
                    entries[block] = live
                    to_visit.append(iter(graph._backward_edges[block]))

        return cls(graph, trace, entries, exits)

    def __init__(
            self,
            graph: "InsnGraph",
            trace: Trace,
            entries: Dict["InsnBlock", Set[int]],
            exits: Dict["InsnBlock", Set[int]],
    ) -> None:
        self.graph = graph
        self.trace = trace

        self.entries = entries
        self.exits = exits

    def __repr__(self) -> str:
        return "<Liveness() at %x>" % id(self)

#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "trace",
)

import operator
import typing
from collections import defaultdict
from typing import Optional

from .frame import Frame
from .state import State
from ..graph import Catch, Graph, Jump
from ..._compat import TypeVar
from ...backend import Result

if typing.TYPE_CHECKING:
    from . import Analysis
    from ..fmt import ClassFile, MethodInfo

T = TypeVar("T", bound="Analysis")


def trace(analysis: T, graph: Graph, method: "MethodInfo", cf: Optional["ClassFile"]) -> Result[T]:
    """
    Traces through the provided graph.
    """

    with Result[T].meta(__name__) as result:
        # You may not like it, but this is what peak performance looks like.
        live_states = analysis.live_states
        all_states = analysis.all_states
        prelive = analysis.prelive
        postlive = analysis.postlive

        # edges_out = graph.edges_out
        # edges_in = graph.edges_in

        uses = defaultdict(set)
        defs = defaultdict(set)

        dont_trace = {graph.return_, graph.rethrow, graph.opaque}

        state = State.initial(graph, method, cf).unwrap_into(result)
        # live_states[graph.entry].append(state)

        stack = [state]
        visited = set()

        # TODO: Although it may not be performant, tracing edges that we may otherwise consider "dead" due to constant
        #       propagation could be beneficial to providing more code insight.

        pass_ = 0
        for pass_ in range(100):
            branches = []
            traced = 0
            retraced = 0

    # ------------------------------------------------------------ #
    #                           DFS trace                          #
    # ------------------------------------------------------------ #

            while stack:
                state = stack.pop()
                block = state.block

                if live_states[block]:
                    if not state.retrace(live_states[block], prelive[block]):
                        branches.append(state)
                        continue
                    retraced += 1
                traced += 1

                # assert retraced < 100000, "possible infinite loop"
                # assert traced < 100000, "possible infinite loop"

                block.trace(state).unwrap_into(result)
                seen_exceptions = set()  # FIXME: Move inside Catch edge.
                for edge in sorted(graph.successors(block), key=lambda edge: edge.precedence):
                    # Simple optimisation we can do at this stage, catch edges with the exact same type should not be
                    # traced when they are consecutive, so one catch edge has a higher priority than the other.
                    if isinstance(edge, Catch):
                        if edge.type in seen_exceptions:
                            continue
                        seen_exceptions.add(edge.type)
                    edge.trace(state)

                live_states[block].append(state)

                uses[block].update(state.uses)
                defs[block].update(state.defs)

                # This is valid to do as uses is a subset of the pre liveness, by definition. We want to do this because we
                # use the pre liveness when merging frames.
                # Although the pre liveness is updated properly later on, this may save us some computation as it may allow
                # us to recognise when we need to retrace a block earlier.
                prelive[block].update(uses[block])

                original = state.copy(False)
                # original.thrown = None
                # original.returned = None
                multiple_successors = len([edge for edge in edges_out[block] if not edge in state.dead]) > 1

                for target in state.targets:
                    successor = target.successor
                    if successor is None or successor in dont_trace:
                        continue
                    frame = target.frame or original

                    predecessors = edges_in[successor]
                    ignore = len([edge for edge in predecessors if edge in state.dead])

                    if len(predecessors) - ignore > 1:
                        frame = frame.generify()
                    elif multiple_successors and frame is original:
                        frame = frame.copy()
                    else:
                        # For performance reasons, we don't need to copy the frame as there's no risk of entries being
                        # modified in the wrong order, as there is only one successor.
                        # Also, catch edges already copy the frame so there's no need to do so again.
                        frame.uses.clear()
                        frame.defs.clear()

                    branched = state.branch(successor, frame)
                    all_states.append(branched)
                    stack.append(branched)

            result.debug("Pass %i: traced %i block(s), %i of which were retraced.", pass_ + 1, traced, retraced)

    # ------------------------------------------------------------ #
    #                    Block pre/post liveness                   #
    # ------------------------------------------------------------ #

            for base in all_states:
                successor = base.block
                for state in reversed(base.traversed):
                    block = state.block

                    old_postlive = postlive[block]
                    old_prelive = prelive[block]

                    new_postlive = old_postlive.union(prelive[successor])
                    new_prelive = old_prelive.union(uses[block])

                    for target in state.targets:
                        if successor == target.successor:
                            break
                    else:
                        # assert False, "successor not found in state targets"
                        raise ValueError(f"successor not found in state {state!r} targets")

                    # The assumption that the exception could have been thrown at any point in the block means that we don't
                    # know if any redefinitions occurred before the potential throw (or at least computing this would not be
                    # worth it at the current moment). Consequently, we will just have to copy the pre liveness state from
                    # the handler's entry as a "best guess".
                    if isinstance(target.edge, Catch):
                        new_prelive.update(prelive[successor])
                    else:
                        new_prelive.update(new_postlive.difference(defs[block]))

                    postlive_changed = old_postlive != new_postlive
                    prelive_changed = old_prelive != new_prelive

                    if postlive_changed:
                        postlive[block] = new_postlive
                    if prelive_changed:
                        prelive[block] = new_prelive

                    if postlive_changed or prelive_changed or not state in visited:
                        visited.add(state)
                    else:
                        break

                    successor = block

    # ------------------------------------------------------------ #
    #                  Branch constraints checking                 #
    # ------------------------------------------------------------ #

            retrace = False
            for state in branches:
                if state.retrace(live_states[state.block], prelive[state.block], pedantic=True) and not retrace:
                    retrace = True
                    stack.append(state)

            if not stack:
                result.debug("Trace done in %i pass(es).", pass_ + 1)
                break

            result.debug("Pass %i: constraints check failed for %i block(s).", pass_ + 1, len(stack))

        else:
            raise ValueError(f"failed to trace graph after {pass_ + 1} passes")

        return result.ok(analysis)
    return result

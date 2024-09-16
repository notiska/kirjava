#!/usr/bin/env python3

__all__ = (
    "trace",
)

import logging
import operator
import typing
from collections import defaultdict

from .frame import Frame
from .state import State
from ...jvm.graph.edge import Catch

if typing.TYPE_CHECKING:
    from . import Trace
    from ...context import Context
    from ...jvm.graph import Graph
    from ...model.class_ import *

logger = logging.getLogger("ijd.analysis.stack")


def trace(trace: "Trace", graph: "Graph", method: "Method", class_: "Class", context: "Context") -> None:
    # TODO: Description.

    # You may not like it, but this is what peak performance looks like.
    states = trace.states
    all_states = trace.all_states
    pre_live = trace.pre_live
    post_live = trace.post_live

    edges_out = graph.edges_out
    edges_in = graph.edges_in

    uses = defaultdict(set)
    defs = defaultdict(set)

    dont_trace = {graph.return_, graph.rethrow, graph.opaque}

    state = State(graph, graph.entry, Frame.initial(method, class_, context))
    all_states.append(state)

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

            if states[block]:
                if not state.retrace(states[block], pre_live[block]):
                    branches.append(state)
                    continue
                retraced += 1
            traced += 1

            # assert retraced < 100000, "possible infinite loop"
            # assert traced < 100000, "possible infinite loop"

            block.trace(state.frame, state)
            seen_exceptions = set()
            for edge in sorted(edges_out[block], key=operator.attrgetter("precedence")):
                # Simple optimisation we can do at this stage, catch edges with the exact same type should not be traced
                # when they are consecutive, so one catch edge has a higher priority than the other.
                if isinstance(edge, Catch):
                    if edge.type in seen_exceptions:
                        continue
                    seen_exceptions.add(edge.type)
                edge.trace(state.frame, state)

            states[block].append(state)

            uses[block].update(state.frame.uses)
            defs[block].update(state.frame.defs)

            # This is valid to do as uses is a subset of the pre liveness, by definition. We want to do this because we
            # use the pre liveness when merging frames.
            # Although the pre liveness is updated properly later on, this may save us some computation as it may allow
            # us to recognise when we need to retrace a block earlier.
            pre_live[block].update(uses[block])

            original = state.frame.copy(False)
            original.thrown = None
            original.returned = None
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

        logger.debug("Pass %i: traced %i block(s), %i of which were retraced.", pass_ + 1, traced, retraced)

    # ------------------------------------------------------------ #
    #                    Block pre/post liveness                   #
    # ------------------------------------------------------------ #

        for base in all_states:
            successor = base.block
            for state in reversed(base.traversed):
                block = state.block

                old_post_live = post_live[block]
                old_pre_live = pre_live[block]

                new_post_live = old_post_live.union(pre_live[successor])
                new_pre_live = old_pre_live.union(uses[block])

                for target in state.targets:
                    if target.successor == successor:
                        break
                else:
                    assert False, "successor not found in state targets"

                # The assumption that the exception could have been thrown at any point in the block means that we don't
                # know if any redefinitions occurred before the potential throw (or at least computing this would not be
                # worth it at the current moment). Consequently, we will just have to copy the pre liveness state from
                # the handler's entry as a "best guess".
                if isinstance(target.edge, Catch):
                    new_pre_live.update(pre_live[successor])
                else:
                    new_pre_live.update(new_post_live.difference(defs[block]))

                post_live_changed = old_post_live != new_post_live
                pre_live_changed = old_pre_live != new_pre_live

                if post_live_changed:
                    post_live[block] = new_post_live
                if pre_live_changed:
                    pre_live[block] = new_pre_live

                if post_live_changed or pre_live_changed or not state in visited:
                    visited.add(state)
                else:
                    break

                successor = block

    # ------------------------------------------------------------ #
    #                  Branch constraints checking                 #
    # ------------------------------------------------------------ #

        retrace = False
        for state in branches:
            if state.retrace(states[state.block], pre_live[state.block], pedantic=True) and not retrace:
                retrace = True
                stack.append(state)

        if not stack:
            logger.debug("Trace done in %i pass(es).", pass_ + 1)
            break

        logger.debug("Pass %i: constraints check failed for %i block(s).", pass_ + 1, len(stack))

    else:
        context.report_exception(
            class_, method, (graph,), Exception("failed to trace graph after %i passes" % (pass_ + 1)),
        )

    # for block in graph.blocks:
    #     if block in dont_trace:
    #         continue
    #     print(block, pre_live[block], post_live[block])

    # FIXME
    # if context.stack_strict_typing:
    #     conflicts = 0
    #     for block in graph.blocks:
    #         conflicts += len(block.conflicts)
    #     if conflicts:
    #         raise ValueError("%i type conflict(s) during tracing" % conflicts)

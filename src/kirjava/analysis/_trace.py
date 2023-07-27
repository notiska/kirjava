#!/usr/bin/env python3

__all__ = (
    "trace",
)

"""
The actual code that computes trace information.
"""

import logging
from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional, Set, Tuple

from . import Context, Trace
from .frame import Frame
from .graph import *
from ..error import MergeError
from ..verifier import TypeChecker

logger = logging.getLogger("kirjava.analysis._trace")


def trace(
        trace_: Trace,  # Great naming, Iska....
        graph: InsnGraph,
        do_raise: bool,
        # This function will be recursive as I don't want to write the tracing code twice.
        retraces: Optional[List[Tuple[Frame, InsnBlock, InsnEdge]]] = None,
        prev_defs: Optional[Dict[InsnBlock, Set[int]]] = None,
        retrace_pass: int = 0,
) -> None:
    if not retraces:
        logger.debug("Computing trace information for %s:" % graph.method)

    context = Context(graph.method, graph, do_raise)
    retraces = retraces or []

    entries = trace_.entries
    exits = trace_.exits

    subroutines = trace_.subroutines

    pre_liveness = trace_.pre_liveness
    post_liveness = trace_.post_liveness

    trace_stack: Deque[Tuple[Frame, InsnBlock, InsnEdge]] = deque()
    liveness_stack: Deque[InsnEdge] = deque()
    branches: Deque[Tuple[Frame, InsnBlock, InsnEdge]] = deque()

    # If we are retracing (recursive call), we already know the liveness (from the upper call) so we can substitute the
    # local uses for the full liveness. This is safe to do as we know that the uses set is a subset of the pre liveness.
    # Defs on the other hand need to be passed down as I don't believe it's possible to efficiently work out defs from
    # the liveness?
    # Additionally, the only purpose the use-def chains serve are to:
    #  1. compute liveness (already done if this is a retrace call)
    #  2. determine if a block retrace is required (which we will be doing if this is a retrace call)
    uses: Dict[InsnBlock, Set[int]] = pre_liveness.copy() if retraces else defaultdict(set)
    defs: Dict[InsnBlock, Set[int]] = prev_defs if retraces else defaultdict(set)

    if not retraces:
        trace_stack.append((Frame.initial(graph.method), graph.entry_block, None))
    else:
        trace_stack.extendleft(retraces)
        retraces.clear()

    # ------------------------------------------------------------ #
    #                           DFS trace                          #
    # ------------------------------------------------------------ #

    traced = 0
    retraced = 0

    while trace_stack:
        frame, block, edge = trace_stack.pop()
        constraints = entries[block]

        # Special check for subroutines too because we want to record those.
        if type(edge) is RetEdge:
            for in_edge in graph.in_edges(block):
                if type(in_edge) is JsrFallthroughEdge:
                    jsr_fallthrough = in_edge
                    break
            else:
                raise RuntimeError("Could not find JSR fallthrough edge for subroutine return.")  # Shouldn't happen.

            for in_edge in graph.out_edges(jsr_fallthrough.from_):
                if type(in_edge) is JsrJumpEdge:
                    subroutines.append(Trace.Subroutine(in_edge, edge, block, frame.copy(deep=False)))
                    break

        if constraints:
            # Although we only intend to visit each block once, some paths may need to be retraced due to invalid merges
            # and in some cases, we can work out if this needs to be done immediately when certain conditions are met.
            # This does not cover all invalid entry merges as we do not yet know all liveness information, which is why
            # some retraces are done later.

            can_merge = False
            live_locals = uses[block]

            for constraint in constraints:
                try:
                    if frame.merge(constraint, edge, live_locals):
                        can_merge = True
                        # We'll break early for performance reasons. Any further entry merges will be done later in the
                        # recursive retrace stage.
                        break
                except MergeError as error:
                    if do_raise:
                        raise error

            if can_merge:  # If we can merge this frame, add it to the branches and we'll check constraints again later.
                branches.append((frame, block, edge))
                continue
            retraced += 1

        traced += 1

        frame = frame.copy(deep=True)
        initial = frame.copy(deep=False)
        entries[block].append(initial)

        context.frame = frame
        context.local_uses.clear()
        context.local_defs.clear()
        context.retrace = False
        block.trace(context)

        for out_edge in graph.out_edges(block):
            frame, to = out_edge.trace(context)
            if frame is None or to is None:
                continue
            trace_stack.append((frame, to, out_edge))

            if frame.max_stack > trace_.max_stack:
                trace_.max_stack = frame.max_stack
            if frame.max_locals > trace_.max_locals:
                trace_.max_locals = frame.max_locals

        if context.retrace:  # AKA a type conflict has occurred during the trace, we will add this to be retraced.
            retraces.append((initial, block, edge))

        uses[block].update(context.local_uses)
        defs[block].update(context.local_defs)
        exits[block].append(context.frame)

    if not traced:  # Nothing more to do at this point.
        return

    logger.debug(" - (pass %i) initial trace for %i block(s) (%i retraced)." % (retrace_pass, len(entries), retraced))
    if branches:
        logger.debug(" - (pass %i) found %i branch(es) to check." % (retrace_pass, len(branches)))
    if subroutines:
        logger.debug(" - (pass %i) found %i subroutine(s)." % (retrace_pass, len(subroutines)))

    # ------------------------------------------------------------ #
    #                    Block pre/post liveness                   #
    # ------------------------------------------------------------ #

    # FIXME: Might be somewhat wasteful to attempt to recalculate liveness again, though I'm not sure if it would change
    #        if a retrace did occur, I would have to think about it before deciding fully. For now, I'll let it compute 
    #        liveness again.

    # Since the return/rethrow blocks cannot access locals, we know that their pre-liveness is empty.
    pre_liveness[graph.return_block] = set()
    pre_liveness[graph.rethrow_block] = set()

    liveness_stack.extendleft(graph.in_edges(graph.return_block))
    liveness_stack.extendleft(graph.in_edges(graph.rethrow_block))

    # The graph doesn't know about any resolved subroutines, and we need these for the liveness stack, so we'll record
    # the exit blocks in a dictionary for fast lookup.
    subroutine_exits: Dict[InsnBlock, Set[RetEdge]] = defaultdict(set)

    for subroutine in subroutines:
        ret_edge = subroutine.ret_edge.copy(to=subroutine.exit_block, deep=False)

        subroutine_exits[subroutine.exit_block].add(ret_edge)
        liveness_stack.append(ret_edge)

    # On top of having edges to the return and rethrow blocks on the liveness stack, we also need to account for things
    # like infinite loops, a contrived example:
    # entry:
    #  aload_0
    #  arraylength
    #  ifeq exit
    #
    #  iconst_0
    #  istore_1
    #
    # loop:
    #  iinc 1 1
    #  goto loop
    #
    # exit:
    #  return
    # In this case we won't trace backwards from the loop block as it never reaches the return or rethrow block,
    # as it is itself still a leaf node. The solution to this is adding the "to-visit" branches to the liveness
    # stack. This works as the DFS will visit the loop entry, but not the cyclic edge, which is excellent as we
    # can just trace backwards from the cyclic edge and end up having visited the entire loop.
    for frame, to, edge in branches:
        if frame is None or to is None:
            continue
        liveness_stack.append(edge)

    while liveness_stack:
        edge = liveness_stack.popleft()
        if edge.to is None:  # Opaque edge, ignore.
            continue

        # Yes, the naming isn't the best but oh well.
        prev_pre = pre_liveness.get(edge.to) or set()

        old_post = post_liveness.get(edge.from_)
        old_pre = pre_liveness.get(edge.from_)

        new_post = (old_post or set()).union(prev_pre)
        new_pre = (old_pre or set()).union(uses[edge.from_])

        # Exception edges assume that the exception could have been thrown from anywhere within the block, so we can't
        # assume that any redefinitions occurred and we'll instead just copy the liveness state at the handler's entry
        # to the entry of this block.
        if type(edge) is ExceptionEdge:
            new_pre.update(prev_pre)
        else:
            new_pre.update(new_post.difference(defs[edge.from_]))

        post_changed = old_post != new_post
        pre_changed = old_pre != new_pre

        if post_changed:
            post_liveness[edge.from_] = new_post
        if pre_changed:
            pre_liveness[edge.from_] = new_pre

        if post_changed or pre_changed:
            liveness_stack.extendleft(graph.in_edges(edge.from_))
            ret_edges = subroutine_exits.get(edge.from_)
            if ret_edges is not None:
                liveness_stack.extendleft(ret_edges)

    # for block in graph:
    #     print(block, pre_liveness.get(block), post_liveness.get(block))

    # ------------------------------------------------------------ #
    #                 Recursive retrace if required                #
    # ------------------------------------------------------------ #

    for frame, block, edge in branches:
        constraints = entries[block]
        if constraints is None:
            continue

        can_merge = False
        live_locals = pre_liveness[block]

        # Here we're finding at least one constraint that does merge, we know that if this does exist, then we have
        # already traced said path and do not need to retrace. We'll continue through all constraints to make sure that
        # we merge all entries that can be merged.
        for constraint in constraints:
            try:
                if frame.merge(constraint, edge, live_locals):
                    can_merge = True
            except MergeError as error:
                if do_raise:
                    raise error

        if not can_merge:
            retraces.append((frame, block, edge))

    if retraces:
        logger.debug(" - (pass %i) %i branch(es) need to be retraced." % (retrace_pass, len(retraces)))
        trace(trace_, graph, do_raise, retraces, defs, retrace_pass + 1)

    # Yay!!! The code is valid up until this point (minus the type checking).

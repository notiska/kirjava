#!/usr/bin/env python3

__all__ = (
    "trace",
)

"""
The actual code that computes trace information.
"""

import logging
from collections import defaultdict, deque

from . import Context, Trace
from .frame import Frame
from .graph import *
from ..error import MergeError

logger = logging.getLogger("kirjava.analysis._trace")


def trace(trace: Trace, graph: InsnGraph, do_raise: bool, merge_non_live: bool, make_params_live: bool) -> None:
    logger.debug("Computing trace information for %s:" % graph.method)

    context = Context(graph.method, graph, do_raise)

    entries = trace.entries
    exits = trace.exits

    conflicts = trace.conflicts
    subroutines = trace.subroutines

    pre_liveness = trace.pre_liveness
    post_liveness = trace.post_liveness

    trace_stack: deque[tuple[Frame, InsnBlock, InsnEdge | None]] = deque()
    liveness_stack: deque[InsnEdge] = deque()
    branches: deque[tuple[Frame, InsnBlock, InsnEdge]] = []
    retraces: list[tuple[Frame, InsnBlock, InsnEdge]] = []

    uses: dict[InsnBlock, set[int]] = defaultdict(set)
    defs: dict[InsnBlock, set[int]] = defaultdict(set)

    initial = Frame.initial(graph.method)
    trace.max_locals = initial.max_locals
    trace_stack.append((initial, graph.entry_block, None))

    if make_params_live:
        uses[graph.entry_block] = set(initial.locals.keys())

    # Not actually sure how many passes are needed for some methods, most tend to be 1 to 2 and some cleverly crafted
    # methods (mainly using subroutines) cause up to 5, but I'll put this to a max of 100 to be on the safe side.
    for pass_ in range(100):

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
                # Although we only intend to visit each block once, some paths may need to be retraced due to invalid 
                # merges and in some cases, we can work out if this needs to be done immediately when certain conditions
                # are met. This does not cover all invalid entry merges as we do not yet know all liveness information,
                # which is why some retraces are done later.

                can_merge = False
                live_locals = uses[block]
                # We can return with multiple stack depths so we can ignore checking that.
                check_depth = (
                    edge is not None and
                    edge.to is not graph.return_block and
                    edge.to is not graph.rethrow_block
                )

                for constraint in constraints:
                    try:
                        # Note: probably due to a retrace(?) so won't merge non-live locals on this pass.
                        # FIXME: Verify this is actually the correct way of doing things.
                        if frame.merge(constraint, edge, live_locals, check_depth, False):
                            can_merge = True
                            # We'll break early for performance reasons. Any further entry merges will be done later in
                            # the retrace stage.
                            break
                    except MergeError as error:
                        if do_raise:
                            raise error

                if can_merge:  # If we can merge this frame, add it to the branches and we'll check constraints again later.
                    branches.append((frame, block, edge))
                    continue
                retraced += 1

            traced += 1

            initial = frame

            # Small optimisation to avoid unnecessary copying of frames. We know that this path can only be taken once
            # and therefore the entries don't need to be copied (as we won't be needing to merge others into them). This
            # can save a lot of time on massive methods.
            if edge is None or len(graph.in_edges(block)) == 1:
                frame = frame.copy(deep=False)
                frame.max_stack = 0  # These are copied with shallow copies, so we need to reset them.
                frame.max_locals = 0
            else:
                frame = frame.copy(deep=True)

            entries[block].append(frame.copy(deep=False))
            context.frame = frame
            # Note: performance is similar to ` = set()`.
            context.conflicts.clear()
            context.local_uses.clear()
            context.local_defs.clear()

            block.trace(context)

            for out_edge in graph.out_edges(block):
                frame, to = out_edge.trace(context)
                if frame is None or to is None:
                    continue
                trace_stack.append((frame, to, out_edge))

                if frame.max_stack > trace.max_stack:
                    trace.max_stack = frame.max_stack
                if frame.max_locals > trace.max_locals:
                    trace.max_locals = frame.max_locals

            if context.conflicts:
                retraces.append((initial, block, edge))
                conflicts.update(context.conflicts)

            uses[block].update(context.local_uses)
            defs[block].update(context.local_defs)
            exits[block].append(context.frame)

        if not traced:  # Nothing more to do at this point.
            return

        trace.returned.update(context.returned)

        logger.debug(" - (pass %i) traced %i block(s), %i were retraced." % (pass_ + 1, traced, retraced))
        if branches:
            logger.debug("    - found %i branch(es) to check." % len(branches))
        if subroutines:
            logger.debug("    - found %i subroutine(s)." % len(subroutines))

    # ------------------------------------------------------------ #
    #                    Block pre/post liveness                   #
    # ------------------------------------------------------------ #

        # Since the return/rethrow blocks cannot access locals, we know that their pre-liveness is empty.
        pre_liveness[graph.return_block] = set()
        pre_liveness[graph.rethrow_block] = set()

        liveness_stack.extendleft(graph.in_edges(graph.return_block))
        liveness_stack.extendleft(graph.in_edges(graph.rethrow_block))

        # The graph doesn't know about any resolved subroutines, and we need these for the liveness stack, so we'll record
        # the exit blocks in a dictionary for fast lookup.
        subroutine_exits: dict[InsnBlock, set[RetEdge]] = defaultdict(set)

        for subroutine in subroutines:
            ret_edge = subroutine.ret_edge.copy(to=subroutine.exit_block, deep=False)

            subroutine_exits[subroutine.exit_block].add(ret_edge)
            liveness_stack.append(ret_edge)

        # On top of having edges to the return and rethrow blocks on the liveness stack, we also need to account for things
        # like infinite loops, a contrived example:
        # entry:
        #   aload_0
        #   arraylength
        #   ifeq exit
        #   iconst_0
        #   istore_1
        # loop:
        #   iinc 1 1
        #   goto loop
        # exit:
        #   return
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

            # Exception edges assume that the exception could have been thrown from anywhere within the block, so we
            # can't assume that any redefinitions occurred and we'll instead just copy the liveness state at the
            # handler's entry to the entry of this block.
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
    #                      Retrace if required                     #
    # ------------------------------------------------------------ #

        for frame, block, edge in branches:
            constraints = entries[block]
            if constraints is None:
                continue

            can_merge = False
            live_locals = pre_liveness[block]
            check_depth = edge.to is not graph.return_block and edge.to is not graph.rethrow_block

            # Here we're finding at least one constraint that does merge, we know that if this does exist, then we have
            # already traced said path and do not need to retrace. We'll continue through all constraints to make sure that
            # we merge all entries that can be merged.
            for constraint in constraints:
                try:
                    if frame.merge(constraint, edge, live_locals, check_depth, merge_non_live):
                        can_merge = True
                except MergeError as error:
                    if do_raise:
                        raise error

            if not can_merge:
                retraces.append((frame, block, edge))

        if not retraces:
            logger.debug("Trace for %s done in %i pass(es)." % (graph.method, pass_ + 1))
            return  # Yay!!! The code is valid up until this point (minus the type checking).

        logger.debug(" - %i branch(es) need to be retraced." % len(retraces))

        trace_stack.extendleft(retraces)
        branches.clear()
        retraces.clear()

        # This is valid to do as the uses is a subset of the pre liveness by definition. The extra liveness information
        # allows us to detect more merge conflicts.
        for block, liveness in pre_liveness.items():
            uses[block].update(liveness)

    else:
        raise ValueError("Failed to trace %s after 100 passes." % graph.method)

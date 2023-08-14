#!/usr/bin/env python3

__all__ = (
    "assemble",
)

"""
The assembler.
"""

import logging
import operator
import typing
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from .block import *
from .debug import *
from .edge import *
from .. import Frame, Trace
from ... import instructions
from ...classfile import ConstantPool
from ...classfile.attributes import Code, LineNumberTable, StackMapTable
from ...constants import Class
from ...error import TypeConflictError
from ...instructions.jvm import (
    Instruction,
    ConditionalJumpInstruction, JumpInstruction, SwitchInstruction,
    LoadLocalInstruction, StoreLocalInstruction,
)
from ...types import reserved_t, top_t, uninitialized_this_t, Reference

if typing.TYPE_CHECKING:
    from . import InsnGraph
    from ...classfile import ClassFile, MethodInfo

logger = logging.getLogger("kirjava.analysis.graph._asm")


def assemble(
        graph: "InsnGraph", method: "MethodInfo", classfile: "ClassFile",
        do_raise: bool, in_place: bool,
        adjust_wides: bool, adjust_ldcs: bool,
        adjust_jumps: bool, adjust_fallthroughs: bool,
        simplify_exception_ranges: bool,
        compute_maxes: bool, compute_frames: bool, compress_frames: bool,
        add_lnt: bool, add_lvt: bool, add_lvtt: bool,
        remove_dead_blocks: bool,
) -> Code:
    logger.debug("Assembling method %r:" % str(method))

    if not in_place:
        graph = graph.copy(deep=True)

    code = Code(method)
    code.max_locals = len(method.argument_types)
    if not method.is_static:
        code.max_locals += 1
    # method.code = code

    has_max_locals = False

    if classfile.version < StackMapTable.since:
        logger.debug(" - skipping stackmap table generation as class version is %s." % classfile.version)
        compute_frames = False

    trace: Optional[Trace] = None
    if compute_maxes or compute_frames:
        trace = Trace.from_graph(graph, do_raise=do_raise)
        if do_raise and trace.conflicts:
            raise TypeConflictError(trace.conflicts)
        code.max_stack = trace.max_stack
        code.max_locals = trace.max_locals

        has_max_locals = True

    # ------------------------------------------------------------ #
    #          Compute block order and remove dead blocks          #
    # ------------------------------------------------------------ #

    blocks = graph._blocks  # Faster access
    forward_edges = graph._forward_edges
    backward_edges = graph._backward_edges

    order: List[InsnBlock] = []
    skipped: Set[InsnBlock] = set()

    for label, block in sorted(blocks.items(), key=operator.itemgetter(0)):
        is_entry_block = block is graph.entry_block
        if remove_dead_blocks and not is_entry_block:
            # If we have computed a trace then we will already know if the block is dead or not. Otherwise, we'll need
            # to guess via how many in edges the block has.
            # TODO: For dead blocks, a proper dominance-based approach, if there are no subroutines present? Though I'm 
            #       guessing error verification will be on most of the time anyway.
            is_dead_block = not backward_edges[block] if trace is None else not block in trace.entries
            if is_dead_block:
                skipped.add(block)
                continue
        # Check if we need to order the block. There are special conditions that need to be addressed, namely the entry
        # block need to always be ordered first, and we need to check if inline blocks have certain in edges that means
        # they would need to be ordered normally (otherwise, they are written as required).
        if not is_entry_block and block.inline:
            order_block = False
            for edge in backward_edges[block]:
                if isinstance(edge, FallthroughEdge):
                    continue
                elif isinstance(edge, JumpEdge) and edge.instruction in (instructions.goto, instructions.goto_w):
                    continue
                # We only inline blocks to fallthrough and goto edges, so if we have any other edge, we need to order
                # the block, so that they can jump to it.
                order_block = True
                break
        else:
            order_block = block is not graph.return_block and block is not graph.rethrow_block

        if order_block:
            order.append(block)

    # FIXME
    # if trace is None:
    #     # We also need to remove any blocks dominated by skipped blocks if we haven't computed a trace.
    #     dominance = graph.dominance()
    #     for block in skipped:
    #         for dominated in dominance[block]:
    #             dominated = blocks.pop(dominated.label, None)
    #             if dominated is None:  # Wasn't added? Could be the same block?
    #                 continue
    #             skipped.add(dominated)
    #             order.remove(dominated)
    #             for edge in forward_edges[dominated]:
    #                 backward_edges[edge.to].remove(edge)
    #             for edge in backward_edges[dominated]:
    #                 forward_edges[edge.from_].remove(edge)

    if skipped:
        logger.debug(" - skipped %i dead block(s)." % len(skipped))

    # ------------------------------------------------------------ #
    #             Fix/adjust wide and ldc instructions             #
    # ------------------------------------------------------------ #

    adjusted_ldcs = 0
    added_wides = 0
    removed_wides = 0

    if adjust_wides or adjust_ldcs:
        if adjust_ldcs and classfile.constant_pool is None:
            classfile.constant_pool = ConstantPool()

        for block in blocks.values():
            index = 0
            while index < len(block._instructions):  # We'll be modifying the list in place
                instruction = block._instructions[index]
                index += 1

                if adjust_ldcs and instruction == instructions.ldc:
                    cp_index = classfile.constant_pool.add(instruction.constant)
                    if cp_index > 255:
                        block._instructions[index] = instructions.ldc_w(instruction.constant)
                        adjusted_ldcs += 1
                    continue

                if not adjust_wides:
                    continue

                # Check if we need to remove a stray wide instruction
                if instruction == instructions.wide:
                    next_instruction = block._instructions[index] if index < len(block._instructions) else None
                    if (
                        not isinstance(next_instruction, LoadLocalInstruction) and
                        not isinstance(next_instruction, StoreLocalInstruction) and
                        not next_instruction in (instructions.iinc, instructions.ret)
                    ):
                        index -= 1
                        block._instructions.pop(index)
                        removed_wides += 1
                    continue

                # Check if we need to add/remove a wide instruction before this instruction
                if (
                    isinstance(instruction, LoadLocalInstruction) or
                    isinstance(instruction, StoreLocalInstruction) or
                    instruction in (instructions.iinc, instructions.ret)
                ):
                    local_index = instruction.index
                    index_valid = local_index <= 255
                    value_valid = instruction != instructions.iinc or -128 <= instruction.value <= 127

                    # We basically get this for free, so might as well compute it here.
                    if not has_max_locals and local_index > code.max_locals:
                        code.max_locals = local_index

                    previous_instruction = block._instructions[index - 2] if index > 1 else None
                    if previous_instruction == instructions.wide and index_valid and value_valid:
                        index -= 1
                        block._instructions.pop(index)
                        removed_wides += 1
                    elif previous_instruction != instructions.wide and (not index_valid or not value_valid):
                        index += 1  # Skip the wide instruction we're about to add
                        block._instructions.insert(index, instructions.wide())
                        added_wides += 1

            if not adjust_wides:
                continue

            for edge in forward_edges[block]:
                if edge.instruction == instructions.ret:
                    local_index = edge.instruction.index

                    if not has_max_locals and local_index > code.max_locals:
                        code.max_locals = local_index

                    # Basically the same deal as above
                    previous_instruction = block._instructions[-1] if block._instructions else None
                    if previous_instruction == instructions.wide and local_index <= 255:
                        block._instructions.pop(-1)
                        removed_wides += 1
                    elif local_index > 255:
                        block._instructions.append(instructions.wide())
                        added_wides += 1

        has_max_locals = has_max_locals or adjust_wides

    if adjusted_ldcs:
        logger.debug(" - adjusted %i ldc instruction(s)." % adjusted_ldcs)
    if added_wides or removed_wides:
        logger.debug(" - added %i wide instruction(s), removed %i." % (added_wides, removed_wides))

    # ------------------------------------------------------------ #
    #                Adjust impossible fallthroughs                #
    # ------------------------------------------------------------ #

    transformed_fallthroughs = 0
    generated_blocks = 0

    if adjust_fallthroughs:
        for index, block in enumerate(order):  # block, out_edges in forward_edges.items():
            # Find all the jump and fallthrough edges
            out_edges = forward_edges[block]
            jump_edges = []
            fallthrough_edges = []

            for edge in out_edges:
                if isinstance(edge, JumpEdge):
                    jump_edges.append(edge)
                elif isinstance(edge, FallthroughEdge):
                    fallthrough_edges.append(edge)

            if not fallthrough_edges:  # Nothing to adjust
                continue
            elif len(fallthrough_edges) > 1:
                # This means that the graph is in an invalid state, so there's not much we can really do to fix it.
                logger.debug(" - unable to adjust %s due to multiple fallthrough edges." % block)
                continue

            fallthrough_edge, = fallthrough_edges
            target = fallthrough_edge.to
            in_edges = backward_edges[target]  # A slight misnomer, but whatever

            # Fallthrough target is a dead block, can occur with jsr fallthroughs where a subroutine does not return.
            if target in skipped:
                continue

            # Check if the fallthrough target will be written immediately after this block. This occurs if either the
            # label is the next one, or the target can be inlined.
            elif target is not block and (target.inline or (index + 1 < len(order) and order[index + 1] is target)):
                continue

            elif isinstance(target, InsnReturnBlock) or isinstance(target, InsnRethrowBlock):
                continue

            # Check if we can turn this fallthrough directly into a goto.
            elif not jump_edges:
                new_edge = JumpEdge(block, target)

                out_edges.remove(fallthrough_edge)
                in_edges.remove(fallthrough_edge)
                out_edges.add(new_edge)
                in_edges.add(new_edge)

                transformed_fallthroughs += 1

            # If all else fails, we probably have a conditional jump (check that anyway though) and therefore we need to
            # generate an intermediary block to fallthrough to, which will contain a goto directly to the target.
            elif len(jump_edges) == 1:
                # jump_edge, = jump_edges
                # # Not sure why this would happen, might as well have a check for it though?
                # if not isinstance(jump_edge.instruction, ConditionalJumpInstruction):
                #     continue

                out_edges.remove(fallthrough_edge)
                in_edges.remove(fallthrough_edge)

                intermediary_block = graph.new()
                intermediary_block.inline = True

                new_fallthrough_edge = FallthroughEdge(block, intermediary_block)
                new_jump_edge = JumpEdge(intermediary_block, target)

                out_edges.add(new_fallthrough_edge)
                in_edges.add(new_fallthrough_edge)

                blocks[intermediary_block.label] = intermediary_block
                forward_edges[intermediary_block] = {new_jump_edge}
                backward_edges[target] = {new_jump_edge}

                generated_blocks += 1

            else:
                # If any other case occurs, the graph is in a completely invalid state, and we can't really do much more
                # at this point. This should've been caught by the verifier, but obviously that can be disabled.
                logger.debug(" - unable to adjust edge %s due to multiple jump edges." % fallthrough_edge)

    if transformed_fallthroughs:
        logger.debug(" - transformed %i fallthrough edge(s) into gotos." % transformed_fallthroughs)
    if generated_blocks:
        logger.debug(" - generated %i intermediary block(s)." % generated_blocks)

    # ------------------------------------------------------------ #
    #                        Code generation                       #
    # ------------------------------------------------------------ #

    # We may need to do multiple passes, depending on if we need to substitute any jumps with wide ones. Note that
    # substituting jumps with wide jumps may actually cause other jump offsets to become too large, and in that case we
    # would need to do ANOTHER pass, we'll limit it to max 5 passes though.
    for pass_ in range(5):
        code.instructions.clear()

        written:  List[Tuple[InsnBlock, int]] = []  # The order and offset of written blocks.
        starting: Dict[InsnBlock, int] = {}
        ending:   Dict[InsnBlock, int] = {}
        inlined:  Dict[InsnBlock, Tuple[List[int], List[int]]] = defaultdict(lambda: ([], []))

        # This will save us time at the jump adjustment stage
        switches:            Dict[int, List[SwitchEdge]] = {}
        unconditional_jumps: Dict[int, JumpEdge] = {}
        conditional_jumps:   Dict[int, JumpEdge] = {}

        line_numbers: Dict[int, int] = {}

        inline_stack: List[InsnBlock] = []

        index = 0
        offset = 0
        wide = False

        while index < len(order):  # Not a for loop as order can change during iteration.
            block = order[index]
            index += 1

            record_offsets = not inline_stack or not block.inline   # Don't record offsets of inlined blocks
            if record_offsets:
                starting[block] = offset
                inline_stack.clear()
            else:
                inlined[block][0].append(offset)

            written.append((block, offset))

            for instruction in block:
                if type(instruction) is LineNumber:
                    line_numbers[offset] = instruction.line_number
                    continue
                code.instructions[offset] = instruction
                offset += instruction.get_size(offset, wide)
                wide = instruction == instructions.wide

            switch_edges: List[SwitchEdge] = []
            inline_edges: List[InsnEdge] = []

            jump_edge:        Optional[JumpEdge] = None
            jump_instruction: Optional[Instruction] = None

            for edge in forward_edges[block]:
                if type(edge) is SwitchEdge:
                    switch_edges.append(edge)
                elif type(edge) is not ExceptionEdge and edge.to is not None and edge.to.inline:
                    inline_edges.append(edge)

                if isinstance(edge, JumpEdge):
                    jump_edge = edge

                # We'll only write the first instruction we find in the edges. Obviously, having multiple jump
                # instructions is invalid, and should've been caught by the verifier.
                if jump_instruction is None and edge.instruction is not None:
                    jump_instruction = edge.instruction

            if switch_edges:
                inline_stack.clear()  # Housekeeping

                if not isinstance(jump_instruction, SwitchInstruction):
                    logger.debug(" - found a switch and jump edge on %s?" % block)
                    jump_instruction = switch_edges[0].instruction

                # So this is an interesting case. Earlier we copied the edges, which in turn copied the instructions
                # inside them. Which is generally fine, except for switch instructions, as all the edges refer to the
                # same instruction. So what we have to do is replace the switch instructions in these edges with a
                # single one, and then modify that one.

                if not pass_:  # We only need to add the placeholders on the first pass
                    for edge in switch_edges:
                        edge.instruction = jump_instruction  # We shouldn't really be doing this tbh
                        if edge.value is None:
                            # 0 is a placeholder value for now, we just need to know the size of the instruction.
                            jump_instruction.default = 0
                        else:
                            jump_instruction.offsets[edge.value] = 0

            elif len(inline_edges) > 1:
                logger.debug(" - skipping inline edges for %s due to multiple (%i) edges." % (block, len(inline_edges)))

            elif len(inline_edges) == 1:
                edge, = inline_edges
                if not edge.instruction in (None, instructions.goto, instructions.goto_w):
                    logger.debug(" - skipping inline edge %s for %s, don't know how to inline %s." % (edge, block, jump_instruction))
                else:
                    inline_stack.append(block)
                    if not edge.to in inline_stack:
                        order.insert(index, edge.to)
                        if edge.instruction == jump_instruction:
                            jump_instruction = None  # Don't write the goto
                    else:
                        inline_stack.clear()

            else:
                inline_stack.clear()

            if jump_instruction is not None:
                if switch_edges:
                    switches[offset] = switch_edges
                elif isinstance(jump_instruction, ConditionalJumpInstruction):
                    conditional_jumps[offset] = jump_edge
                # Unconditional jumps may include "jumps" without offsets (returns, athrows and rets), so filter those
                # out.
                elif isinstance(jump_instruction, JumpInstruction) and jump_instruction != instructions.ret:
                    unconditional_jumps[offset] = jump_edge

                # Need to copy as inline blocks might be written multiple times, meaning the offsets would all be weird.
                code.instructions[offset] = jump_instruction.copy()
                offset += jump_instruction.get_size(offset, wide)
                wide = False

            if record_offsets:
                ending[block] = offset
            else:
                inlined[block][1].append(offset)

        logger.debug(" - code generation pass %i (%i instructions written, max offset %i)" % (
            pass_ + 1, len(code.instructions), offset,
        ))
        if switches:
            logger.debug("   - %i switch(es)." % len(switches))
        if unconditional_jumps:
            logger.debug("   - %i unconditional jump(s)." % len(unconditional_jumps))
        if conditional_jumps:
            logger.debug("   - %i conditional jump(s)." % len(conditional_jumps))

    # ------------------------------------------------------------ #
    #                    Jump offset calculation                   #
    # ------------------------------------------------------------ #

        for offset, edges in switches.items():
            instruction = code.instructions[offset]
            for edge in edges:
                if edge.value is None:
                    instruction.default = starting[edge.to] - offset
                else:
                    instruction.offsets[edge.value] = starting[edge.to] - offset
        for offset, edge in unconditional_jumps.items():
            code.instructions[offset].offset = starting[edge.to] - offset
        for offset, edge in conditional_jumps.items():
            code.instructions[offset].offset = starting[edge.to] - offset

        # We'll only need to substitute jumps for wide jumps if the code is large enough.
        if not adjust_jumps or max(code.instructions) <= 32767:
            break

        substituted_jumps = 0
        generated_blocks = 0

        # Unconditional jumps are relatively easy to substitute
        for offset, edge in unconditional_jumps.items():
            instruction = code.instructions[offset]
            if abs(instruction.offset) <= 32767 or instruction in (instructions.goto_w, instructions.jsr_w):
                continue

            if instruction == instructions.goto:
                edge.instruction = instructions.goto_w()
            elif instruction == instructions.jsr:
                edge.instruction = instructions.jsr_w()
            else:
                raise ValueError("Unknown jump instruction: %s" % instruction)

            substituted_jumps += 1

        # Conditional jumps are more interesting. We'll generate intermediary blocks for the conditional to jump to, and
        # the intermediary block will jump to the actual target, with a wide jump.
        for offset, edge in conditional_jumps.items():
            instruction = code.instructions[offset]
            if abs(instruction.offset) <= 32767:
                continue

            forward_edges[edge.from_].remove(edge)
            backward_edges[edge.to].remove(edge)

            intermediary_block = graph.new()
            # block.inline = True
            order.insert(order.index(edge.to) + 1, intermediary_block)  # We want to write it immediately after

            # FIXME
            conditional_edge = edge.copy(to=intermediary_block, deep=False)
            direct_edge = JumpEdge(intermediary_block, edge.to, instructions.goto_w())

            forward_edges[edge.from_].add(conditional_edge)
            backward_edges[intermediary_block].add(conditional_edge)
            forward_edges[intermediary_block].add(direct_edge)
            backward_edges[edge.to].add(direct_edge)

            substituted_jumps += 1

        if not substituted_jumps:
            logger.debug("   - no jumps substituted.")
            break
        logger.debug("   - substituted %i jump(s) with wide jumps." % substituted_jumps)
        if generated_blocks:
            logger.debug("   - generated %i intermediary block(s)." % generated_blocks)

        # We'll also remove the inline flag from all blocks, as we've already inserted them into the order, so we don't
        # have to spend effort calculating that twice. We only need to do this on the first pass.
        if not pass_:
            for block in blocks.values():
                block.inline = False

    else:
        raise ValueError("Code generation failed after 5 passes.")

    # ------------------------------------------------------------ #
    #                  Exception table generation                  #
    # ------------------------------------------------------------ #

    code.exception_table.clear()

    split_handlers = 0
    merged_edges = 0

    handlers: Dict[int, List[Code.ExceptionHandler]] = defaultdict(list)  # Handlers and their priority

    # We'll iterate through the backward edges as it allows us to easily group and merge exception ranges that may span
    # multiple blocks.
    for block, in_edges in backward_edges.items():
        if not simplify_exception_ranges:
            # Generate an exception handler for every exception edge we find, it's wasteful but faster to compute.
            for edge in in_edges:
                if type(edge) is ExceptionEdge and not edge.from_ in skipped:
                    handlers[edge.priority].append(Code.ExceptionHandler(
                        starting[edge.from_], ending[edge.from_], starting[edge.to], Class(edge.throwable.name),
                    ))
            continue

        # Otherwise, we will attempt to merge the ranges of exception edges which have the same priority and throwable.
        exception_edges: Dict[Tuple[int, Optional[Reference]], Dict[int, Tuple[int, ExceptionEdge]]] = defaultdict(dict)

        for edge in in_edges:
            if type(edge) is ExceptionEdge and not edge.from_ in skipped:
                handler = (edge.priority, edge.throwable)
                # We might have written this block at multiple places, and if so, we will need to generate an exception
                # handler for each.
                if edge.from_.inline:
                    offsets = inlined.get(edge.from_)
                    if offsets is not None:
                        for _, end in zip(*offsets):
                            exception_edges[handler][offset] = (end, edge)
                    if not edge.from_ in starting:  # Since it's inlined, it may not have been written normally
                        continue
                exception_edges[handler][starting[edge.from_]] = (ending[edge.from_], edge)

        # We need to check if the blocks in between the minimum and maximum range all lie within the actual exception
        # range. Otherwise, we'll just have to split the exception range into multiple handlers.
        for (priority, throwable), edges in exception_edges.items():
            current_handlers = handlers[priority]
            current_range: Optional[Tuple[int, int]] = None

            for start, (end, edge) in sorted(edges.items(), key=operator.itemgetter(0)):
                in_range = False

                if current_range is None:
                    current_range = (start, end)
                    in_range = True
                elif start == current_range[1]:
                    current_range = (current_range[0], end)
                    in_range = True

                if not in_range:
                    current_handlers.append(Code.ExceptionHandler(*current_range, starting[edge.to], Class(throwable.name)))
                    current_range = (start, end)
                    split_handlers += 1
                    continue

                # Might need to extend the current range if the edge has inline coverage.
                if edge.inline_coverage:
                    for edge_ in forward_edges[edge.from_]:
                        if edge_.to.inline:
                            break
                    else:
                        continue

                    for inline_block, (starts, ends) in inlined.items():
                        index = starts.index(start)
                        if index >= 0:  # Extend the range to the end of the inline block
                            current_range = (current_range[0], ends[index])
                            break

                merged_edges += 1

            if current_range is not None:
                current_handlers.append(Code.ExceptionHandler(*current_range, starting[edge.to], Class(throwable.name)))

    for priority, handlers_ in sorted(handlers.items(), key=operator.itemgetter(0)):
        code.exception_table.extend(handlers_)

    if split_handlers:
        logger.debug(" - split %i exception handler(s)." % split_handlers)
    if code.exception_table:
        if merged_edges:
            logger.debug(" - generated %i exception handler(s) from %i merged edge(s)." % (
                len(code.exception_table), merged_edges,
            ))
        else:
            logger.debug(" - generated %i exception handler(s)." % len(code.exception_table))

    # ------------------------------------------------------------ #
    #                    Generate stackmap table                   #
    # ------------------------------------------------------------ #

    if compute_frames and len(written) > 1:
        stackmap_table = StackMapTable(code)
        code.stackmap_table = stackmap_table

        dead_blocks: Set[InsnBlock] = set()

        prev_offset = -1
        prev_locals = None

        for block, offset in written:
            offset_delta = offset - prev_offset

            if block is not graph.entry_block:
                # If this block is not jumped to then there's no need to write a stackmap frame for it. This is simply a
                # measure to save space.
                # FIXME: Test with inline blocks too?
                for edge in graph.in_edges(block):
                    if not isinstance(edge, FallthroughEdge):
                        break
                else:
                    continue

                # AKA a block with no instructions. We do have to be careful though as it may be the entry block, which we
                # do want to have a frame for (though we don't need to write it as the first frame is implicit).
                if not offset_delta:
                    continue

            prev_offset = offset
            offset_delta -= 1  # Another space saving measure by the JVM.

            entries = trace.entries.get(block)
            if not entries:  # FIXME: Determine entry constraints or nop instructions (probably will do the latter).
                dead_blocks.add(block)
                continue

            skip = False
            live = trace.pre_liveness[block]

            frame, *_ = entries

            # If there is an uninitialized this type in the locals, no matter if it's live, we still need to declare it.
            # Info obtained from ProGuard so credit to them.
            # https://github.com/Guardsquare/proguard-core/blob/master/base/src/main/java/proguard/preverify/CodePreverifier.java#L296C1-L300C80
            for index, entry in frame.locals.items():
                if entry._type is uninitialized_this_t:  # Use of ._type is for performance and accuracy.
                    live.add(index)

            stack_depth = len(frame.stack)
            max_local = max(live) + 1 if live else 0  # TODO: uninit_this_t needs to be accounted for no matter what

            stack = []
            locals_ = []

            for entry in frame.stack:
                stack.append(entry.inference())
            for index in range(max_local):
                if not index in live:
                    locals_.append({top_t})
                    continue
                entry = frame.locals.get(index)
                # This is invalid yes, but if do_raise=True then the error will have been raised prior to this, so the
                # best we can do at this point is guess.
                if entry is None:
                    locals_.append({top_t})
                    continue
                locals_.append(entry.inference())

            for frame in entries[1:]:
                if len(frame.stack) != stack_depth:
                    # Again, another case where do_raise=True would've caught this earlier. We will have to skip over
                    # this frame fully though if we encounter this.
                    skip = True
                    break

                # FIXME: Are merges between uninitialized_this_ts actually valid? Might have to substitute for a top_t.
                for index, entry in frame.locals.items():
                    if entry._type is uninitialized_this_t:
                        live.add(index)

                for index, entry in enumerate(frame.stack):
                    stack[index].update(entry.inference())

                for index in range(max_local):
                    if not index in live:
                        continue
                    entry = frame.locals.get(index)
                    if entry is None:
                        continue
                    locals_[index].update(entry.inference())

            if skip:
                continue

            for index, types in enumerate(stack):
                valid = []
                invalid = False

                types = list(types)
                while types:
                    vtype = types.pop().as_vtype()
                    for type_ in types:
                        if not vtype.mergeable(type_) and not type_.mergeable(vtype):
                            invalid = True
                            break
                    else:
                        valid.append(vtype)

                # This may appear to be a somewhat cheap way of handling these situations, but in actuality it's more
                # nuanced. To demonstrate this, here's an example (this is based off information xxDark gave me, so
                # credits to him):
                #  entry:
                #   aconst_null
                #   ifnull push_ints
                # push_double:
                #  dconst_0
                #  goto combine
                # push_ints:
                #  iconst_0
                #  iconst_0
                # combine:
                #  pop2
                #  return
                # In this case, the merge conflict would be at the combine label, however note that the pop2 instruction
                # does not care what type is on the stack, so you can somewhat trick the verifier into thinking that this
                # is valid bytecode. If any other usage that didn't fit this criteria was used then we previously
                # would've reported the error as a type conflict (if do_raise=True).
                # As a sidenote: jdk11 doesn't seem to fall for this trick.
                if invalid:
                    stack[index] = top_t
                    continue
                elif len(valid) == 1:
                    stack[index], = valid
                    continue

                ...  # TODO: Merge common supertypes?
                raise NotImplementedError("Cannot merge common supertypes yet.")

            for index, types in enumerate(locals_):
                valid = []
                invalid = False

                types = list(types)
                while types:
                    vtype = types.pop().as_vtype()
                    for type_ in types:
                        if not vtype.mergeable(type_) and not type_.mergeable(vtype):
                            invalid = True
                            break
                    else:
                        valid.append(vtype)

                # Unfortunately the same logic about invalid types on the stack cannot really be applied to the
                # locals as they are read to and written from via typed instructions, but we'll still try our best.
                if invalid:
                    locals_[index] = top_t
                    continue
                elif len(valid) == 1:
                    locals_[index], = valid
                    continue

                ...  # TODO: Merge common supertypes
                raise NotImplementedError("Cannot merge common supertypes yet.")

            # Reserved types are implicit when dealing with the stack map table, so we need to remove all of them.
            stack = [type_ for type_ in stack if type_ is not reserved_t]
            locals_ = [type_ for type_ in locals_ if type_ is not reserved_t]
            # while reserved_t in stack:
            #     stack.remove(reserved_t)
            # while reserved_t in locals_:
            #     locals_.remove(reserved_t)

            if block is graph.entry_block:  # As stated above, no need to write this frame.
                prev_offset = -1
                prev_locals = locals_
                continue

            # print(offset, offset_delta, block)
            # print("[", ", ".join(map(str, stack)), "]")
            # print("[", ", ".join(map(str, locals_)), "]")

            stackmap_frame = StackMapTable.FullFrame(offset_delta, locals_, stack)

            if not compress_frames:
                stackmap_table.frames.append(stackmap_frame)
                continue

            locals_delta = len(locals_) - len(prev_locals)
            same_locals = not locals_delta and locals_ == prev_locals

            if same_locals:
                if not stack:
                    stackmap_frame = (
                        StackMapTable.SameFrame(offset_delta)
                        if offset_delta < 64 else
                        StackMapTable.SameFrameExtended(offset_delta)
                    )
                elif len(stack) == 1:
                    stackmap_frame = (
                        StackMapTable.SameLocals1StackItemFrame(offset_delta, stack[0])
                        if offset_delta < 64 else
                        StackMapTable.SameLocals1StackItemFrameExtended(offset_delta, stack[0])
                    )

            elif locals_delta in range(-3, 1) and locals_ == prev_locals[:locals_delta]:
                stackmap_frame = StackMapTable.ChopFrame(offset_delta, -locals_delta)

            elif locals_delta in range(0, 4) and locals_[:-locals_delta] == prev_locals:
                stackmap_frame = StackMapTable.AppendFrame(offset_delta, tuple(locals_[-locals_delta:]))

            prev_locals = locals_

            stackmap_table.frames.append(stackmap_frame)

        if not stackmap_table:
            code.stackmap_table = None

    # ------------------------------------------------------------ #
    #                        Add debug info                        #
    # ------------------------------------------------------------ #

    if add_lnt and line_numbers:
        line_number_table = LineNumberTable(code)
        code.line_number_table = line_number_table

        for offset, line_number in line_numbers.items():
            line_number_table.entries.append(LineNumberTable.LineNumberEntry(offset, line_number))

    # TODO: LVT and LVTT

    return code

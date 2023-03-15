#!/usr/bin/env python3

__all__ = (
    "_write_block",
    "_adjust_jumps_and_add_exception_handlers",
    "_simplify_exception_ranges",
    "_nop_out_dead_blocks_and_compute_frames",
)

"""
Functions that make up Kirjava's assembler.
Kept in a separate file because graph.py was previously 1500+ lines, which was unmanageable.
The assembler is quite complex, so it's split into multiple functions. The basic stages of the assembler are:
 - Write the instructions from the blocks (and jump edges, etc). This automatically fixes any edge conflicts.
 - Adjust jump offsets to be absolute and add exception handlers to the code.
 - Simplify exception ranges if applicable.
 - "nop out" dead blocks and compute stackmap frames, if necessary.
"""

import itertools
import logging
import typing
from typing import Dict, List, Optional, Set, Tuple, Union

from ._edge import *
from .liveness import *
from .source import InstructionInBlock
from .trace import *
from .. import types
from ..classfile.attributes.code import StackMapTable
from ..classfile.attributes.method import Code
from ..classfile.constants import Class
from ..instructions import jvm as instructions
from ..instructions.jvm import (
    ConditionalJumpInstruction, JumpInstruction, LookupSwitchInstruction, ReturnInstruction, TableSwitchInstruction,
)
from ..types.verification import Uninitialized
from ..verifier import Error, Verifier

if typing.TYPE_CHECKING:
    from ._block import InsnBlock
    from .graph import InsnGraph

logger = logging.getLogger("kirjava.analysis._assembler")


def _write_block(
        graph: "InsnGraph",
        verifier: Verifier,
        offset: int,
        block: "InsnBlock",
        code: "Code",
        offsets: Dict["InsnBlock", List[Tuple[int, int, int]]],
        jumps: Dict[int, JumpEdge],
        switches: Dict[int, List[SwitchEdge]],
        exceptions: List[ExceptionEdge],
        temporary: Set["InsnBlock"],
        inlined: Dict[InsnEdge, List[Tuple[int, int]]],  # FIXME: Dict["InsnBlock", Tuple[int, int]] ?
        inline: bool = False,
) -> int:
    """
    A helper method for writing individual blocks to the code's instructions.
    """

    inline = inline and block.inline
    if block in offsets and not inline:  # The block is already written, so nothing to do here
        return offset
    # No instructions means nothing to write, so skip this block. Keep in mind if we do have out edges though, we may
    # need to add jumps to account for impossible fallthroughs.
    elif not block and not graph._forward_edges.get(block):
        return offset

    if offsets:  # Have we actually written any yet?
        previous = next(reversed(offsets))
        fallthrough_edge = None

        for edge in graph._forward_edges[previous]:
            if isinstance(edge, FallthroughEdge):  # FIXME: See below
                fallthrough_edge = edge
                break

        # Check to see if this block won't fallthrough to its target
        if (
            fallthrough_edge is not None and
            not fallthrough_edge.to in (block, graph.return_block, graph.rethrow_block) and
            not fallthrough_edge.to in offsets
        ):
            # Currently using a goto_w to mitigate any issues with large methods, as we don't know the target offset
            # yet.
            instruction = instructions.goto_w()

            code.instructions[offset] = instruction
            jumps[offset] = JumpEdge(previous, fallthrough_edge.to, instruction)
            offset += instruction.get_size(offset, False)

            logger.debug("    - Generated jump %s to account for edge %s." % (instruction, fallthrough_edge))

    start = offset

    # Stuff for keeping track of instructions
    instructions_ = {}
    news = {}

    unbound_jumps = False
    unbound_returns = False
    unbound_athrows = False

    shifted = False
    
    while not shifted:
        offset = start

        instructions_.clear()
        news.clear()

        wide = False
        for index, instruction in enumerate(block._instructions):
            instructions_[offset] = instruction.copy()  # Copy, so we don't modify the original

            if instruction == instructions.new:
                news[index] = offset
            elif not unbound_jumps and isinstance(instruction, JumpInstruction):
                unbound_jumps = True
            elif not unbound_returns and isinstance(instruction, ReturnInstruction):
                unbound_returns = True
            elif not unbound_athrows and instruction == instructions.athrow:
                unbound_athrows = True

            offset += instruction.get_size(offset, wide)
            wide = instruction == instructions.wide

        # Is the method is large enough that we may need to consider generating intermediary blocks to account for
        # jumps around this block?
        if offset < 32768:
            break

        for offset_, edge in jumps.items():
            # If either the offset delta is valid for a 2 byte jump, the target of the jump has already been
            # written, or the jump instruction is a wide goto, we don't need to handle anything here.
            if offset - offset_ <= 32767 or edge.to in offsets or edge.instruction == instructions.goto_w:
                continue
            shifted = True

            intermediary = InsnBlock(65336 - len(temporary))  # FIXME: Better to just figure out the max label
            temporary.add(intermediary)
            graph.jump(intermediary, edge.to, instructions.goto_w)

            # Overwrite the old edge with a new one where the jump target is the intermediary block.
            jumps[offset_] = JumpEdge(edge.from_, intermediary, edge.instruction)

            # Write the block immediately, adjusting the offset too
            offset = _write_block(
                graph, verifier, offset, intermediary, code, offsets, jumps, switches, exceptions, temporary, inlined,
            )
            logger.debug("    - Generated %s to account for edge %s." % (intermediary, edge))

        if not shifted:
            break

        logger.debug("    - Shifted %s by %+i byte(s)." % (block, offset - start))
        start = offset

    code.instructions.update(instructions_)  # Add the new instructions to the code

    if unbound_jumps:
        verifier.report(Error(Error.Type.INVALID_BLOCK, block, "block has unbound jumps"))
    if unbound_returns:
        verifier.report(Error(Error.Type.INVALID_BLOCK, block, "block has unbound returns"))
    if unbound_athrows:
        verifier.report(Error(Error.Type.INVALID_BLOCK, block, "block has unbound athrows"))

    # if multiple_returns:
    #     errors.append(Error(Error.Type.INVALID_BLOCK, block, "block has multiple return instructions"))
    # if multiple_athrows:
    #     errors.append(Error(Error.Type.INVALID_BLOCK, block, "block has multiple athrow instructions"))

    offsets.setdefault(block, []).append((start, offset, news))  # Update with the new bounds of this block

    # Validate that the out edges from this block are valid, and get the required ones.

    multiple_fallthroughs = False
    multiple_jumps = False
    has_out_edges = False

    fallthrough_edge: Optional[FallthroughEdge] = None
    jump_edge:        Optional[JumpEdge] = None
    switch_edge:      Optional[SwitchEdge] = None
    switch_edges: List[SwitchEdge] = []

    for edge in graph._forward_edges[block]:
        if isinstance(edge, FallthroughEdge):  # FIXME: JsrFallthroughEdge subclasses this in the future?
            if fallthrough_edge is not None:
                multiple_fallthroughs = True
            fallthrough_edge = edge
            has_out_edges = True

        elif type(edge) is JsrFallthroughEdge:
            if fallthrough_edge is not None:
                multiple_fallthroughs = True
            fallthrough_edge = edge  # Not technically a fallthrough, but I don't want to add more complexity
            has_out_edges = True

        elif type(edge) is SwitchEdge:
            switch_edges.append(edge)
            has_out_edges = True

        elif type(edge) is ExceptionEdge:
            exceptions.append(edge)

        elif isinstance(edge, JumpEdge):
            if jump_edge is not None:
                multiple_jumps = True
            jump_edge = edge
            has_out_edges = True

    # Check that all the edges are valid

    if multiple_fallthroughs:
        verifier.report(Error(Error.Type.INVALID_BLOCK, block, "multiple fallthrough edges on block"))

    if jump_edge is not None:
        if multiple_jumps:
            verifier.report(Error(Error.Type.INVALID_BLOCK, block, "multiple jumps on block"))

        jump_instruction = jump_edge.instruction.copy()
        is_conditional = isinstance(jump_instruction, ConditionalJumpInstruction)

        offsets_ = offsets.get(jump_edge.to)
        if offsets_ is not None:  # If we have written the block already, we may need to add intermediary jumps
            start_ = min(map(lambda item: item[0], offsets_), key=lambda offset_: offset - offset_)
            delta = start_ - offset

        # Check if we can remove the jump altogether (due to inline blocks)
        if (
            not is_conditional and
            jump_edge.to is not None and
            jump_edge.to.inline and
            len(graph._forward_edges[jump_edge.to]) <= 1
        ):
            offset = _write_block(
                graph, verifier, offset, jump_edge.to, code,
                offsets, jumps, switches, exceptions,
                temporary, inlined, inline=True,
            )
            inlined[jump_edge] = offsets[jump_edge.to][-1][:-1]

            # Jump is inlined and therefore doesn't need to be written
            jump_edge = None
            jump_instruction = None

        # Now check if we need to adjust the jump in some way. This can be through substituting the jump with its wide
        # variant, or creating temporary blocks as intermediaries.
        elif offsets_ is not None and delta <= -32768 and jump_instruction != instructions.goto_w:
            if is_conditional:
                raise NotImplementedError("Wide conditional substitution is not yet implemented.")

            # Otherwise we can just generate the wide variants of the jumps and it won't change much
            elif jump_edge.to is not None:
                if jump_instruction == instructions.jsr:
                    jump_instruction = instructions.jsr_w(delta)
                else:
                    jump_instruction = instructions.goto_w(delta)
                logger.debug("    - Adjusted edge %s to wide jump %s." % (jump_edge, jump_instruction))

                # Also create a new jump edge, we don't need to add it, but we do need to represent the new jump in
                # jumps with and edge.
                jump_edge = JumpEdge(block, jump_edge.to, jump_instruction)

        if jump_edge is not None and jump_instruction is not None:
            code.instructions[offset] = jump_instruction
            jumps[offset] = jump_edge
            offset += jump_instruction.get_size(offset, wide)
            # We also need to adjust the offset and bounds of the block
            offsets[block][-1] = (start, offset, news)

        if type(jump_edge) is JsrJumpEdge:
            if type(fallthrough_edge) is not JsrFallthroughEdge:
                verifier.report(Error(
                    Error.Type.INVALID_BLOCK, block, "jsr jump edge with no jsr fallthrough edge on block",
                ))
        elif is_conditional and fallthrough_edge is None:
            verifier.report(Error(
                Error.Type.INVALID_BLOCK, block, "conditional jump edge with no fallthrough edge on block",
            ))
        elif not is_conditional and fallthrough_edge is not None:
            verifier.report(Error(
                Error.Type.INVALID_BLOCK, block, "unconditional jump edge with a fallthrough edge on block",
            ))

        if switch_edges:
            verifier.report(Error(Error.Type.INVALID_BLOCK, block, "jump and switch edges on block"))

    elif switch_edges:
        switch_instruction: Union[TableSwitchInstruction, LookupSwitchInstruction, None] = None
        multiple = False

        for switch_edge in switch_edges:
            if switch_instruction is not None and switch_instruction != switch_edge.instruction:
                multiple = True
            switch_instruction = switch_edge.instruction

        switch_instruction = switch_instruction.copy()

        if multiple:
            verifier.report(Error(
                Error.Type.INVALID_BLOCK, block,
                "block has multiple switch edges which reference different switch instructions",
            ))

            # Remove any edges whose instruction we aren't writing
            for switch_edge in switch_edges.copy():
                if switch_edge.instruction != switch_instruction:
                    switch_edges.remove(switch_edge)

        switch_instruction.offsets.clear()  # FIXME: Don't clear explicit offsets maybe?

        # We need to fix the switch instruction's size because as far as it is concerned, it won't have any offsets
        # and therefore it won't compute the size correctly, so dummy values are added as offsets here.
        if switch_instruction == instructions.tableswitch:
            for switch_edge in switch_edges:
                if switch_edge.value is not None:  # Ignore the default switch edge
                    switch_instruction.offsets.append(0)
        elif switch_instruction == instructions.lookupswitch:
            for switch_edge in switch_edges:
                if switch_edge.value is not None:
                    switch_instruction.offsets[switch_edge.value] = 0  # As a temporary offset
        else:
            # Internal error, raise.
            raise Exception("Internal error, got invalid switch instruction: %s" % switch_instruction)

        # Write the instruction, recompute the offset and readjust the block's bounds
        code.instructions[offset] = switch_instruction
        switches[offset] = switch_edges
        offset += switch_instruction.get_size(offset, wide)
        offsets[block][-1] = (start, offset, news)

    if not has_out_edges and block != graph.return_block and block != graph.rethrow_block:
        verifier.report(Error(Error.Type.INVALID_BLOCK, block, "block has no out edges"))

    if fallthrough_edge is not None:
        offsets_ = offsets.get(fallthrough_edge.to)

        if fallthrough_edge.to == graph.return_block or fallthrough_edge.to == graph.rethrow_block:
            # We need to add a return/athrow instruction and adjust the block's bounds
            instruction = fallthrough_edge.instruction.copy()
            code.instructions[offset] = instruction
            offset += instruction.get_size(offset, wide)
            offsets[block][-1] = (start, offset, news)

        else:
            # Try to inline the fallthrough block if we can, taking into account if a blocks fallthrough is itself. This
            # could create an infinite loop, which is not good lol.
            if fallthrough_edge.to.inline and fallthrough_edge.to != block:
                offset = _write_block(
                    graph, verifier, offset, fallthrough_edge.to, code,
                    offsets, jumps, switches, exceptions,
                    temporary, inlined, inline=True,
                )
                # Note down where we inlined the block at
                inlined[fallthrough_edge] = offsets[fallthrough_edge.to][-1][:-1]

            # Have we already written the fallthrough block? Bear in mind that if the block can be inlined, we
            # don't need to worry about it as we can just write it directly after this one, hence the elif.
            elif offsets_ is not None:
                # Find the closest starting offset for the fallthrough block, as we want to avoid using wide jumps as
                # much as possible.
                start = min(map(lambda item: item[0], offsets_), key=lambda offset_: offset - offset_)
                delta = start - offset

                if delta >= -32767:
                    goto_instruction = instructions.goto(delta)
                else:
                    goto_instruction = instructions.goto_w(delta)

                # Another temporary jump edge, also don't need to add it to the graph.
                jumps[offset] = JumpEdge(block, fallthrough_edge.to, goto_instruction)
                code.instructions[offset] = goto_instruction
                offset += goto_instruction.get_size(offset, wide)

                logger.debug("    - Generated jump %s to account for edge %s." % (goto_instruction, fallthrough_edge))

    return offset


def _adjust_jumps_and_add_exception_handlers(
        verifier: Verifier,
        code: "Code",
        jumps: Dict[int, JumpEdge],
        switches: Dict[int, List[SwitchEdge]],
        exceptions: List[ExceptionEdge],
        offsets: Dict["InsnBlock", List[Tuple[int, int, int]]],
        inlined: Dict[InsnEdge, List[Tuple[int, int]]],
) -> None:
    """
    Adjusts jump offsets to be absolute, given their corresponding edges and adds exception handlers to the code from
    the exception edges.
    """

    for offset, jump_edge in jumps.items():
        instruction = code.instructions[offset]

        if instruction.offset is not None:  # Already computed the jump offset, or it's explicit
            continue
        elif jump_edge.to is None:  # Opaque edge, can't compute offset
            continue

        if not jump_edge.to in offsets:
            # if not jump_edge.to:
            #     errors.append(Error(Error.Type.INVALID_EDGE, jump_edge, "jump edge to block with no instructions"))
            #     continue
            # raise Exception("Internal error while adjusting offset for jump edge %r." % jump_edge)
            verifier.report(Error(
                Error.Type.INVALID_EDGE, jump_edge,
                "jump edge to unknown block", "use graph.add() to add it to the graph",
            ))
            continue

        start = min(map(lambda item: item[0], offsets[jump_edge.to]), key=lambda offset_: abs(offset - offset_))
        instruction.offset = start - offset

    if jumps:
        logger.debug(" - Adjusted %i jump(s)." % len(jumps))

    for offset, switch_edges in switches.items():
        instruction = code.instructions[offset]

        for switch_edge in switch_edges:
            if not switch_edge.to in offsets:
                # if not switch_edge.to:
                #     errors.append(Error(
                #         Error.Type.INVALID_EDGE, switch_edge, "switch edge to block with no instructions",
                #     ))
                #     continue
                # raise Exception("Internal error while adjusting offset for switch edge %r." % switch_edge)
                verifier.report(Error(
                    Error.Type.INVALID_EDGE, switch_edge,
                    "switch edge to unknown block", "use graph.add() to add it to the graph",
                ))
                continue

            start = min(map(lambda item: item[0], offsets[switch_edge.to]), key=lambda offset_: abs(offset - offset_))
            value = switch_edge.value
            if value is None:
                instruction.default = start - offset
            else:
                instruction.offsets[value] = start - offset

    if switches:
        logger.debug(" - Adjusted %i switch(es)." % len(switches))

    # Add exception handlers and set their offsets to the correct positions to, then simplify any overlapping ones
    # if required (simplify_exception_ranges=True).

    for exception_edge in sorted(exceptions, key=lambda edge: edge.priority):
        for start, end, _ in offsets[exception_edge.from_]:
            # If there are multiple offsets for the exception handler, simply just pick the first one.
            (handler, _, _), *extra = offsets[exception_edge.to]
            if extra:
                verifier.report(Error(
                    Error.Type.INVALID_EDGE, exception_edge,
                    "multiple exception handler targets", "is the handler inlined?",
                ))

            if exception_edge.inline_coverage:  # FIXME: Inlined blocks on inlined blocks
                for edge_, (_, end_) in inlined.items():
                    if edge_.from_ == exception_edge.from_ and end_ > end:
                        end = end_  # Adjust the end offset for this exception handler

            code.exception_table.append(Code.ExceptionHandler(
                start, end, handler, Class(exception_edge.throwable.name),
            ))

    if code.exception_table:
        logger.debug(" - Generated %i exception handler(s)." % len(code.exception_table))


def _simplify_exception_ranges(
        code: "Code", exceptions: List[ExceptionEdge], offsets: Dict["InsnBlock", List[Tuple[int, int, int]]],
) -> None:
    """
    Simplifies exception ranges by combining handlers that can be merged.
    """

    ...  # TODO


def _nop_out_dead_blocks_and_compute_frames(
        graph: "InsnGraph",
        verifier: Verifier,
        trace: Trace,
        code: "Code",
        jumps: Dict[int, JumpEdge],
        switches: Dict[int, List[SwitchEdge]],
        exceptions: List[ExceptionEdge],
        dead: Set["InsnBlock"],
        offsets: Dict["InsnBlock", List[Tuple[int, int, int]]],
        inlined: Dict[InsnEdge, List[Tuple[int, int]]],
        compress_frames: bool,
) -> None:
    """
    Nops out any dead blocks and computes stackmap frames, adding a StackMapTable attribute if necessary.
    """

    write_frames = dead or jumps or switches or exceptions
    dead_frames: Dict["InsnBlock", Frame] = {}

    if dead:
        # The standard state we'll use for these dead blocks' stackmap frames, since these are never actually visited,
        # the only proof we need that the athrow is valid is from the stackmap frame, so we can just say that there's a
        # throwable on the stack lol.
        # Might be cool in the future to be able to work out the entry constraints for such blocks with some form of
        # stack delta analysis, but that's a bit too much work for now.
        frame = Frame(verifier)
        frame.push(types.throwable_t)

        logger.debug(" - %i dead block(s):" % len(dead))
        for block in dead:
            if not block in offsets:
                logger.debug("    - %s (unwritten)" % block)
                continue

            logger.debug("    - %s (written at %s)" % (
                block, ", ".join(map(str, (start for start, _, _ in offsets[block]))),
            ))
            dead_frames[block] = frame

            for start, end, _ in offsets[block]:
                last = end - 1
                offset = start
                while offset < last:
                    jumps.pop(offset, None)
                    switches.pop(offset, None)
                    code.instructions[offset] = instructions.nop()
                    offset += 1
                code.instructions[last] = instructions.athrow()

    if not write_frames:  # Nothing more to do
        return

    for edge in jumps.values():
        if type(edge) is JsrJumpEdge:
            # We can't compute frames if we find any live jsr edge at all, even if it's not part of a
            # subroutine. This is because at the jump target, the stackmap frame will contain the return address
            # in the stack, which isn't valid. We still need to write the stackmap table attribute though.
            write_frames = False
            break

    if not write_frames:
        logger.debug(" - Not computing frames as live jsr edges were found.")
        return

    stackmap_table = StackMapTable(code)
    stackmap_frames: Dict[int, Tuple["InsnBlock", Frame]] = {
        # Create the bootstrap (implicit) frame
        -1: (graph.entry_block, trace.frames[graph.entry_block][0][0]),
    }
    visited: Set["InsnBlock"] = set()
    liveness = Liveness.from_trace(trace)

    # Add the dead stackmap frames first.
    for block, frame in dead_frames.items():
        for start, _, _ in offsets[block]:
            stackmap_frames[start] = (block, frame)

    # Add all the blocks that are jump targets in some sense (this includes exception handler targets), as we
    # don't actually need to write all the states basic blocks, contrary to what the JVM spec says, instead we
    # only need to write the states at basic blocks that are jumped to. At this stage, we'll also combine the
    # states from different paths.

    for edge in itertools.chain(jumps.values(), *switches.values(), exceptions):
        if edge is None:
            continue
        block = edge.to
        if not block in offsets:  # Error will have already been reported above
            continue
        base = None

        # We can split constraints on inlined blocks
        if block.inline and edge in inlined:
            frames = trace.frames[edge.from_]
            offsets_ = (inlined[edge],)
        elif block in visited:  # Don't check this for inline edges, obviously
            continue
        else:
            visited.add(block)
            frames = trace.frames[block]
            offsets_ = offsets[block]

        # print(edge)
        for frame, _ in frames:
            # print("[", ", ".join(map(str, frozen.stack)), "]")
            if base is None:
                base = frame
                continue

            # Check that the stack is merge-able
            if len(frame.stack) > len(base.stack):
                verifier.report(Error(
                    Error.Type.INVALID_STACK_MERGE, edge,
                    "stack overrun, expected stack size %i for edge, got size %i" % (
                        len(base.stack), len(frame.stack),
                    ),
                ))
            elif len(frame.stack) < len(base.stack):
                verifier.report(Error(
                    Error.Type.INVALID_STACK_MERGE, edge,
                    "stack underrun, expected stack size %i for edge, got size %i" % (
                        len(base.stack), len(frame.stack),
                    ),
                ))

            for index, (entry_a, entry_b) in enumerate(zip(base.stack, frame.stack)):
                if not verifier.checker.check_merge(entry_a.type, entry_b.type):
                    verifier.report(Error(
                        Error.Type.INVALID_STACK_MERGE, edge,
                        "invalid stack type merge at index %i (%s, via %s and %s, via %s)" % (
                            index, entry_a.type, entry_a.source, entry_b.type, entry_b.source,
                        ),
                    ))

                # FIXME: Multiple sources for uninitialised type? Need to improve how offsets are calculated.

                merged = verifier.checker.merge(entry_a.type, entry_b.type)
                if merged != entry_a.type or merged != entry_b.type:  # Has the merge changed the entry?
                    base.stack[index] = entry_a.cast(None, merged)

            for index in liveness.entries[block]:
                entry_a = base.locals.get(index)
                entry_b = frame.locals.get(index)

                if entry_a is None and entry_b is None:
                    verifier.report(Error(
                        Error.Type.INVALID_LOCALS_MERGE, edge,
                        "illegal locals type merge at index %i, expected live local" % index,
                    ))
                    continue
                elif entry_a is None:
                    verifier.report(Error(
                        Error.Type.INVALID_LOCALS_MERGE, edge,
                        "invalid locals type merge at index %i, expected live local (have %s via %s)" % (
                            index, entry_b.type, entry_b.source,
                        ),
                    ))
                    base.set(index, entry_b)
                    continue
                elif entry_b is None:
                    verifier.report(Error(
                        Error.Type.INVALID_LOCALS_MERGE, edge,
                        "invalid locals type merge at index %i, expected live local (have %s via %s)" % (
                            index, entry_a.type, entry_a.source,
                        ),
                    ))
                    continue

                if not verifier.checker.check_merge(entry_a.type, entry_b.type):
                    verifier.report(Error(
                        Error.Type.INVALID_LOCALS_MERGE, edge,
                        "invalid locals type merge at index %i (%s via %s and %s via %s)" % (
                            index, entry_a.type, entry_a.source, entry_b.type, entry_b.source,
                        ),
                    ))

                merged = verifier.checker.merge(entry_a.type, entry_b.type)
                if merged != entry_a.type or merged != entry_b.type:
                    base.locals[index] = entry_a.cast(None, merged)

        for start, _, _ in offsets_:
            stackmap_frames[start] = (block, base)

    for offset in sorted(stackmap_frames):
        block, frame = stackmap_frames[offset]
        # The bootstrap (implicit) frame requires that all types are explicit and there are no tops, so we don't
        # take the liveness for the entry block, instead we just use the local indices to indicate that all the
        # locals are "live".
        live = liveness.entries[block] if offset >= 0 else set(frame.locals.keys())

        locals_ = []
        stack = []

        max_local = 0  # We can truncate trailing tops from the locals
        max_actual = max((0,) + tuple(live))

        if frame.locals:
            wide = False
            for index in range(max(frame.locals) + 1):
                if wide:
                    wide = False
                    continue

                entry = frame.locals.get(index, frame.top)

                # Note: uninitializedThis must be specified, live or not.
                if not index in live and entry.type != types.uninit_this_t:
                    locals_.append(types.top_t)
                else:
                    # Special handling for uninitialised types, we need to add the offset in
                    if (
                        isinstance(entry.type, Uninitialized) and
                        entry.type != types.uninit_this_t and
                        type(entry.source) is InstructionInBlock
                    ):
                        done = False
                        for _, _, news in offsets[entry.source.block]:
                            if done:
                                verifier.report(Error(
                                    Error.Type.INVALID_TYPE, entry.source,
                                    "unable to determine source of uninitialised type as block is written multiple times",
                                ))
                                break
                            locals_.append(Uninitialized(news[entry.source.index]))
                            done = True
                        continue

                    locals_.append(entry.type)
                    max_local = len(locals_)
                    wide = entry.type.internal_size > 1

            locals_ = locals_[:max_local]

        for entry in frame.stack:
            if entry == frame.top:
                continue
            elif (
                isinstance(entry.type, Uninitialized) and
                entry.type != types.uninit_this_t and
                type(entry.source) is InstructionInBlock
            ):
                done = False
                for _, _, news in offsets[entry.source.block]:
                    if done:
                        verifier.report(Error(
                            Error.Type.INVALID_TYPE, entry.source,
                            "unable to determine source of uninitialised type as block is written multiple times",
                        ))
                        break
                    stack.append(Uninitialized(news[entry.source.index]))
                    done = True
                continue

            stack.append(entry.type)

        # print(offset, block, live, liveness.exits.get(block, None))
        # print("locals: [", ", ".join(map(str, locals_)), "]")
        # print("stack:  [", ", ".join(map(str, stack)), "]")

        if offset >= 0:  # Don't write the bootstrap frame (offset -1)
            stackmap_frame: Optional[StackMapTable.StackMapFrame] = None
            offset_delta = offset - (prev_offset + 1)

            if compress_frames:
                locals_delta = max_local - prev_max_local
                same_locals = not locals_delta and locals_ == prev_locals

                # if locals_ and locals_[-1].internal_size > 1:
                #     locals_delta -= 1

                if same_locals:
                    if not stack:
                        stackmap_frame = (
                            StackMapTable.SameFrame(offset_delta) if offset_delta < 64 else
                            StackMapTable.SameFrameExtended(offset_delta)
                        )
                    elif len(stack) == 1:
                        stackmap_frame = (
                            StackMapTable.SameLocals1StackItemFrame(offset_delta, stack[0])
                            if offset_delta < 64 else
                            StackMapTable.SameLocals1StackItemFrameExtended(offset_delta, stack[0])
                        )
                elif not stack and max_actual != prev_max_actual:
                    if -3 <= locals_delta < 0 and locals_ == prev_locals[:locals_delta]:
                        stackmap_frame = StackMapTable.ChopFrame(offset_delta, -locals_delta)
                    elif 3 >= locals_delta > 0 and locals_[:-locals_delta] == prev_locals:
                        stackmap_frame = StackMapTable.AppendFrame(offset_delta, tuple(locals_[-locals_delta:]))

            if stackmap_frame is None:  # Resort to a full frame if we haven't worked out what it should be
                stackmap_frame = StackMapTable.FullFrame(offset_delta, tuple(locals_), tuple(stack))

            stackmap_table.frames.append(stackmap_frame)

        prev_offset = offset
        prev_locals = locals_
        prev_max_local = max_local
        prev_max_actual = max_actual

    if stackmap_table.frames:
        code.stackmap_table = stackmap_table
        logger.debug(" - Generated %i stackmap frame(s)." % len(stackmap_table.frames))

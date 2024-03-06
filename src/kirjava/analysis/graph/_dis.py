#!/usr/bin/env python3

__all__ = (
    "disassemble",
)

"""
The disassembler.
"""

import logging
import typing
from collections import defaultdict

from .block import InsnBlock
from .debug import *
from .edge import *
from ... import instructions
from ...instructions import (
    AThrowInstruction, ConditionalJumpInstruction, JsrInstruction, JumpInstruction, RetInstruction, ReturnInstruction, SwitchInstruction,
)
from ...source import *

if typing.TYPE_CHECKING:
    from . import InsnGraph
    from ...classfile import MethodInfo

logger = logging.getLogger("kirjava.analysis.graph._dis")


def disassemble(
        graph: "InsnGraph", method: "MethodInfo", do_raise: bool,
        keep_lnt: bool, keep_lvt: bool, keep_lvtt: bool,
        gen_source_map: bool,
) -> None:
    code = method.code
    if code is None:
        raise ValueError("Cannot disassemble a method without code.")

    logger.debug("Disassembling method %r:" % str(method))

    # ------------------------------------------------------------ #
    #        Find jump/handler targets and exception bounds        #
    # ------------------------------------------------------------ #

    instructions_ = code.instructions
    source_map = graph.source_map

    flow_splits: set[int] = set()

    for offset, instruction in instructions_.items():
        if isinstance(instruction, JumpInstruction):
            try:
                if instruction.offset is not None:
                    flow_splits.add(offset + instruction.offset)
            except AttributeError:
                ...  # ret instruction doesn't have an offset and catching this error is simply faster than checking

        elif isinstance(instruction, SwitchInstruction):
            flow_splits.add(offset + instruction.default)
            for offset_ in instruction.offsets.values():
                flow_splits.add(offset + offset_)

    for handler in code.exception_table:
        flow_splits.add(handler.handler_pc)
        flow_splits.add(handler.start_pc)
        flow_splits.add(handler.end_pc)

    # logger.debug(" - found %i jump target(s), %i exception handler target(s) and %i exception bound(s)." % (
    #     len(jump_targets), len(handler_targets), len(exception_bounds),
    # ))

    # ------------------------------------------------------------ #
    #        Prepare line number and local variable tables         #
    # ------------------------------------------------------------ #

    lnt = {}
    lvt = {}

    if keep_lnt:
        line_number_table = code.line_number_table
        if line_number_table is not None:
            for entry in line_number_table:
                lnt[entry.start_pc] = LineNumber(entry.line_number)

    if keep_lvt:
        ...  # TODO
        # local_variable_table = code.local_variable_table
        # if local_variable_table is not None:
        #     skipped = 0
        #     for entry in local_variable_table:
        #         if type(entry.name) is not UTF8 or type(entry.descriptor) is not UTF8:
        #             skipped += 1
        #             continue
        #         local_variable = LocalVariable(entry.index, entry.name.value, entry.descriptor.value)
        #         entries = lvt.setdefault(entry.start_pc, set())
        #         entries.add((entry.start_pc + entry.length, local_variable))
        #     if skipped:
        #         logger.debug(" - %i LVT entries with non-UTF8 name or descriptor." % skipped)

    if keep_lvtt:
        ...  # TODO

    # ------------------------------------------------------------ #
    #              Create basic blocks and jump edges              #
    # ------------------------------------------------------------ #

    starting: dict[int, InsnBlock] = {}
    ending:   dict[InsnBlock, int] = {}
    forward_jumps: dict[int, list[InsnEdge]] = defaultdict(list)  # Forward reference jump targets

    previous: InsnBlock | None = None
    block = graph.entry_block

    # We do this so that we always create a new block if offset 0 is a jump target because by definition the entry block
    # should dominate all other blocks. (The nop is removed later.)
    block.append(instructions.nop(), do_raise=False)

    # https://stackoverflow.com/questions/50493838/fastest-way-to-sort-a-python-3-7-dictionary
    for offset in sorted(instructions_):
        # Don't want to modify the original as some instructions are not immutable (due to their operands).
        instruction = instructions_[offset].copy()

        is_new_block = previous is not None
        is_forward_offset = offset in forward_jumps

        # Is this block jumped to at any point?
        if not is_new_block and (is_forward_offset or offset in flow_splits):
            # If the current block has instructions, we need to create a new one.
            if block:  # or block is graph.entry_block:
                previous = block
                is_new_block = True
                block = InsnBlock(block.label + 1)
                graph.add(block, check=False)
                graph.connect(FallthroughEdge(previous, block), False, check=False)

        line_number = lnt.get(offset)
        if line_number is not None:
            block._instructions.append(line_number)

        if is_new_block:
            ending[previous] = offset
            starting[offset] = block

            previous = None

            # Check if any previous jumps reference this starting offset
            if is_forward_offset:
                for edge in forward_jumps.pop(offset):
                    # Since this is a bound edge, remove any absolute jump offsets from it.
                    if type(edge) is SwitchEdge:
                        if edge.value is None:
                            edge.instruction.default = None
                        else:
                            edge.instruction.offsets.pop(edge.value)

                    elif isinstance(edge, JumpEdge):
                        edge.instruction.offset = None

                    graph.connect(edge.copy(to=block, deep=False), False, check=False)

        # Check if it's an instruction that breaks the control flow and create a new block (adding edges if necessary).
        if isinstance(instruction, JumpInstruction):
            is_jsr = isinstance(instruction, JsrInstruction)

            if not is_jsr:  # jsr instructions are handled more specifically
                if isinstance(instruction, RetInstruction):  # instruction == instructions.ret:
                    edge = RetEdge(block, None, instruction)
                    graph.connect(edge, False, check=False)
                    if gen_source_map:
                        source_map[offset] = edge
                else:
                    to = starting.get(offset + instruction.offset)
                    edge = JumpEdge(block, to, instruction)
                    if to is not None:
                        instruction.offset = None
                        graph.connect(edge, False, check=False)
                    else:  # Mark the offset as a forward jump edge
                        forward_jumps[offset + instruction.offset].append(edge)

                    if gen_source_map:
                        source_map[offset] = edge

            previous = block
            block = InsnBlock(block.label + 1)
            graph.add(block, check=False)

            if isinstance(instruction, ConditionalJumpInstruction):
                graph.connect(FallthroughEdge(previous, block), False, check=False)
            elif is_jsr:
                to = starting.get(offset + instruction.offset)
                edge = JsrJumpEdge(previous, to, instruction)
                if to is not None:
                    instruction.offset = None
                    graph.connect(edge, False, check=False)
                else:
                    forward_jumps[offset + instruction.offset].append(edge)

                if gen_source_map:
                    source_map[offset] = edge

                # block.inline = True  # We need to inline jsr fallthrough targets no matter what.
                graph.connect(JsrFallthroughEdge(previous, block, instruction), False, check=False)

        elif isinstance(instruction, SwitchInstruction):
            to = starting.get(offset + instruction.default)
            edge = SwitchEdge(block, to, instruction, None)
            if to is not None:
                instruction.default = None
                graph.connect(edge, False, check=False)
            else:
                forward_jumps[offset + instruction.default].append(edge)

            offsets_ = instruction.offsets
            for value, offset_ in offsets_.copy().items():
                to = starting.get(offset + offset_)
                edge = SwitchEdge(block, to, instruction, value)
                if to is not None:
                    offsets_.pop(value)
                    graph.connect(edge, False, check=False)
                else:
                    forward_jumps[offset + offset_].append(edge)

            if gen_source_map:
                source_map[offset] = edge

            previous = block
            block = InsnBlock(block.label + 1)
            graph.add(block, check=False)

        elif isinstance(instruction, ReturnInstruction):
            edge = JumpEdge(block, graph.return_block, instruction)
            graph.connect(edge, False, check=False)
            previous = block
            block = InsnBlock(block.label + 1)
            graph.add(block, check=False)

            if gen_source_map:
                source_map[offset] = edge

        elif isinstance(instruction, AThrowInstruction):  # instruction == instructions.athrow:
            edge = JumpEdge(block, graph.rethrow_block, instruction)
            graph.connect(edge, False, check=False)
            previous = block
            block = InsnBlock(block.label + 1)
            graph.add(block, check=False)

            if gen_source_map:
                source_map[offset] = edge

        else:
            if gen_source_map:
                source_map[offset] = InstructionInBlock(len(block), block, instruction)
            # "So Iska, how did you get the disassembler so fast?" :doom:
            block._instructions.append(instruction)

    # Note down the ending offset of the final block(s), note that this is not actually a valid offset inside the code,
    # but it acts as a marker which is used when determining the exception handlers. It is important that we don't use a
    # real offset as sometimes the ending block is empty, meaning its starting offset could be equal to its actual
    # ending offset, which would otherwise result in an infinite loop.
    ending[block] = -1
    if previous is not None:
        ending[previous] = -1

    graph.entry_block.pop(0)  # Remove the nop that we added

    if forward_jumps:
        unbound = 0
        for edges in forward_jumps.values():
            for edge in edges:
                if not isinstance(edge, SwitchEdge):
                    edge.from_._instructions.append(edge.instruction)

                # Now generate a fallthrough edge to the next block, if it exists. This is done to maintain the original
                # order of the instructions in the code. This code is invalid as it is, so it doesn't matter if this is
                # not an accurate representation of what would happen, instead we want to maintain the correctness of
                # the actual instructions.
                # An example:
                #   goto +32767
                #   return
                # In this case, we want to maintain that the return instruction comes directly after the invalid goto.

                to = graph._blocks.get(edge.from_.label + 1)
                if to is not None:
                    # If the jump is conditional, this will already exist, but the _connect method should ensure that we
                    # don't get duplicates.
                    graph.connect(FallthroughEdge(edge.from_, to), True, check=True)

                unbound += 1
        if unbound:
            if do_raise:
                # TODO: Specific exception types?
                raise ValueError("Found %i unbound jump(s)! Use do_raise=False to ignore this." % unbound)
            logger.debug(" - %i unbound forward jump(s)!" % unbound)

    # Remove the final block if it is empty and has no out edges. There might be cases where the final instruction in a
    # method is not one that breaks control flow, and due to that we want to check if we can remove it first.
    if not block and not graph._forward_edges[block]:  # and not graph._backward_edges[block]:
        graph.remove(block, check=False)

    logger.debug(" - found %i basic block(s)." % (len(graph._blocks) - 2))  # - 2 for the return and rethrow blocks

    # ------------------------------------------------------------ #
    #                    Create exception edges                    #
    # ------------------------------------------------------------ #

    # for start, block in starting.items():
    #     for index, handler in enumerate(code.exception_table):
    #         if handler.start_pc <= start < handler.end_pc:
    #             target = starting.get(handler.handler_pc)
    #             if target is not None:
    #                 type_ = handler.catch_type.type if handler.catch_type is not None else None
    #                 graph.connect(ExceptionEdge(block, target, index, type_), overwrite=False, check=False)

    unbound_starts = 0
    unbound_ends = 0
    unbound_targets = 0

    # So why the rewrite? Well, with this new method we save 100ms on a 1900ms disassembly (on my laptop), which might
    # be worth the extra complexity.
    for index, handler in enumerate(code.exception_table):
        block = starting.get(handler.start_pc)
        if block is None:
            # Obviously this can't happen in valid bytecode, but we do want to be able to handle invalid bytecode
            # (somewhat?) correctly, so we'll just go through the blocks manually and check if they lie within the
            # bounds, which is less optimised, but this shouldn't occur too often (if at all) anyway.
            unbound_starts += 1
            for start, block in starting.items():  # Should be in the correct order?
                if start < handler.start_pc <= ending[block]:
                    break
            else:  # Couldn't find any block that lies within the bounds, weird?
                continue

        target = starting.get(handler.handler_pc)
        if target is None:
            unbound_targets += 1
            # We'll search for the handler target like above.
            for start, target in starting.items():
                if start < handler.handler_pc <= ending[target]:
                    break
            else:
                continue
        type_ = handler.catch_type.class_type if handler.catch_type is not None else None

        end = ending[block]
        while True:
            graph.connect(ExceptionEdge(block, target, index, type_), False, check=False)
            if end == handler.end_pc:
                break
            elif end > handler.end_pc:
                unbound_ends += 1
                break
            block = starting.get(end)
            if block is None:
                break
            end = ending[block]

    if unbound_starts:
        if do_raise:
            raise ValueError(
                "Found %i exception handler(s) with unbound start offsets! Use do_raise=False to ignore this." % unbound_starts,
            )
        logger.debug(" - %i exception handler(s) with unbound start offsets!" % unbound_starts)
    if unbound_ends:
        if do_raise:
            raise ValueError(
                "Found %i exception handler(s) with unbound end offsets! Use do_raise=False to ignore this." % unbound_ends,
            )
        logger.debug(" - %i exception handler(s) with unbound end offsets!" % unbound_ends)
    if unbound_targets:
        if do_raise:
            raise ValueError(
                "Found %i exception handler(s) with unbound target offsets! Use do_raise=False to ignore this." % unbound_targets,
            )
        logger.debug(" - %i exception handler(s) with unbound target offsets!" % unbound_targets)

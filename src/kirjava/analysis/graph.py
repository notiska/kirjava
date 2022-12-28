#!/usr/bin/env python3

__all__ = (
    "InsnBlock", "InsnReturnBlock", "InsnRethrowBlock",
    "JumpEdge", "FallthroughEdge", "ExceptionEdge",
    "InsnGraph",
)

"""
A control flow graph containing the Java instructions (with offsets removed, so somewhat abstracted).
"""

import itertools
import logging
import typing
from typing import Dict, List, Set, Tuple, Union

from ._block import *
from ._edge import *
from .liveness import Liveness
from .trace import BlockInstruction, Entry, State, Trace
from .verifier import FullTypeChecker
from .. import _argument, types
from ..abc import Class, Edge, Error, Graph, VerifyError
from ..classfile import instructions
from ..classfile.attributes.code import StackMapTable
from ..classfile.attributes.method import Code
from ..classfile.constants import Class as Class_
from ..classfile.instructions import (
    MetaInstruction, Instruction, ConditionalJumpInstruction,
    JumpInstruction, JsrInstruction, RetInstruction,
    ReturnInstruction,
)
from ..types import ReferenceType
from ..types.verification import Uninitialized

if typing.TYPE_CHECKING:
    from ..classfile.members import MethodInfo

logger = logging.getLogger("kirjava.analysis.graph")


class InsnGraph(Graph):
    """
    A control flow graph that contains Java instructions.
    """

    @classmethod
    def disassemble(cls, method_info: "MethodInfo") -> "InsnGraph":
        """
        Disassembles a method's code and returns the disassembled graph.

        :param method_info: The method to disassemble.
        :return: The created graph.
        """

        if method_info.is_abstract:
            raise ValueError("Method %s is abstract, cannot disassemble." % method_info)
        if method_info.is_native:
            raise ValueError("Method %s is native, cannot disassemble." % method_info)

        code, *_ = method_info.attributes.get(Code.name_, (None,))
        if code is None:
            raise ValueError("Method %s has no code, cannot disassemble." % method_info)

        logger.debug("Disassembling method %r:" % str(method_info))

        graph = cls(method_info)

        # Find jump and exception targets, copy instructions into temporary list

        # Different bytecode offsets that we'll use for splitting the code into blocks
        jump_targets: Set[int] = set()
        handler_targets: Set[int] = set()
        exception_bounds: Set[int] = set()

        # has_subroutines = False

        for offset, instruction in code.instructions.items():
            if isinstance(instruction, JumpInstruction):  # Add jump offsets for jump instructions
                if isinstance(instruction, RetInstruction):
                    ...  # has_subroutines = True
                else:
                    jump_targets.add(offset + instruction.offset)

            elif instruction == instructions.tableswitch:  # Add jump offsets for tableswitch instructions
                jump_targets.add(offset + instruction.default)
                for offset_ in instruction.offsets:
                    jump_targets.add(offset + offset_)

            elif instruction == instructions.lookupswitch:  # Add jump offsets for lookupswitch instructions
                jump_targets.add(offset + instruction.default)
                for offset_ in instruction.offsets.values():
                    jump_targets.add(offset + offset_)

        for handler in code.exception_table:  # Add exception handler targets and bounds
            handler_targets.add(handler.handler_pc)
            exception_bounds.add(handler.start_pc)
            exception_bounds.add(handler.end_pc)

        logger.debug(" - Found %i jump target(s), %i exception handler target(s) and %i exception bound(s)." % (
            len(jump_targets), len(handler_targets), len(exception_bounds),
        ))

        # Create basic blocks and edges

        starting: Dict[int, InsnBlock] = {}
        forward_jumps: Dict[int, List[JumpEdge]] = {}  # Forward reference jump targets

        graph.entry_block = InsnBlock(graph, 0)
        block = graph.entry_block

        for offset, instruction in sorted(code.instructions.items(), key=lambda item: item[0]):
            # Don't want to modify the original as some instructions are not immutable (due to their operands).
            instruction = instruction.copy()

            if offset in exception_bounds:
                # If the current block has instructions, we need to create a new one, otherwise, don't even if it is
                # the entry block as this block is not jumped to.
                if block.instructions:
                    previous = block
                    block = InsnBlock(graph, block.label + 1)

                    graph.connect(FallthroughEdge(previous, block))

            if offset in jump_targets or offset in handler_targets:  # Is this block jumped to at any point?
                # Don't create a new block if the current one isn't empty as that's wasteful. The exception to this
                # however is the entry block, as by definition, it must dominate all other blocks in the graph.
                if block.instructions or block == graph.entry_block:
                    previous = block
                    block = InsnBlock(graph, block.label + 1)

                    graph.connect(FallthroughEdge(previous, block))

            if not block.instructions:
                starting[offset] = block

                # Check if any previous jumps reference this starting offset
                if offset in forward_jumps:
                    for edge in forward_jumps[offset]:
                        # Technically we aren't allowed to set the edge's to, but we can get away with it here as we
                        # haven't yet added it to the graph, though generally, these should be immutable.
                        edge.to = block
                        graph.connect(edge)

                    del forward_jumps[offset]

            block.instructions.append(instruction)

            # Check if it's an instruction that breaks the control flow and create a new block (adding edges if 
            # necessary).
            if isinstance(instruction, JumpInstruction):
                if isinstance(instruction, RetInstruction):
                    graph.connect(RetEdge(block, None, instruction))

                elif not isinstance(instruction, JsrInstruction):  # jsr instructions are handled more specifically
                    to = starting.get(offset + instruction.offset, None)
                    if to is not None:
                        graph.connect(JumpEdge(block, to, instruction))
                    else:  # Mark the offset as a forward jump edge
                        forward_jumps.setdefault(offset + instruction.offset, []).append(
                            JumpEdge(block, None, instruction),
                        )

                previous = block
                block = InsnBlock(graph, block.label + 1)

                if isinstance(instruction, JsrInstruction):
                    to = starting.get(offset + instruction.offset, None)
                    if to is not None:
                        graph.connect(JsrEdge(previous, to, block, instruction))
                    else:
                        forward_jumps.setdefault(offset + instruction.offset, []).append(
                            JsrEdge(previous, None, block, instruction),
                        )

                elif isinstance(instruction, ConditionalJumpInstruction):
                    graph.connect(FallthroughEdge(previous, block))

                instruction.offset = None  # It doesn't make sense for a jump to have an offset at this point

            elif instruction == instructions.tableswitch:
                to = starting.get(offset + instruction.default, None)
                if to is not None:
                    graph.connect(SwitchEdge(block, to, instruction, None))
                else:
                    forward_jumps.setdefault(offset + instruction.default, []).append(
                        SwitchEdge(block, None, instruction, None),
                    )

                for index, offset_ in enumerate(instruction.offsets):
                    to = starting.get(offset + offset_, None)
                    if to is not None:
                        graph.connect(SwitchEdge(block, to, instruction, index))
                    else:
                        forward_jumps.setdefault(offset + offset_, []).append(
                            SwitchEdge(block, None, instruction, index),
                        )

                instruction.default = None
                instruction.offsets.clear()

                block = InsnBlock(graph, block.label + 1)

            elif instruction == instructions.lookupswitch:
                to = starting.get(offset + instruction.default, None)
                if to is not None:
                    graph.connect(SwitchEdge(block, to, instruction, None))
                else:
                    forward_jumps.setdefault(offset + instruction.default, []).append(
                        SwitchEdge(block, None, instruction, None),
                    )

                for value, offset_ in instruction.offsets.items():
                    to = starting.get(offset + offset_, None)
                    if to is not None:
                        graph.connect(SwitchEdge(block, to, instruction, value))
                    else:
                        forward_jumps.setdefault(offset + offset_, []).append(
                            SwitchEdge(block, None, instruction, value),
                        )

                instruction.default = None
                instruction.offsets.clear()

                block = InsnBlock(graph, block.label + 1)

            # FIXME: Exception coverage issues with empty blocks and the return + athrow instructions themselves
            elif isinstance(instruction, ReturnInstruction):
                block.instructions.pop()  # Don't include the return instruction
                graph.connect(FallthroughEdge(block, graph._return_block))

                block = InsnBlock(graph, block.label + 1)

            elif instruction == instructions.athrow:
                block.instructions.pop()
                graph.connect(FallthroughEdge(block, graph._rethrow_block))

                block = InsnBlock(graph, block.label + 1)

        if forward_jumps:
            unbound = sum(map(len, forward_jumps.values()))
            if unbound:
                logger.debug(" - %i unbound forward jump(s)!" % unbound)

        # Add exception edges via the code's exception table

        for start, block in starting.items():
            for index, handler in enumerate(code.exception_table):
                if handler.start_pc <= start < handler.end_pc:
                    type_ = handler.catch_type.get_actual_type() if handler.catch_type is not None else None
                    graph.connect(ExceptionEdge(block, starting[handler.handler_pc], index, type_))

        # Remove any empty blocks that might have been generated (due to return insns, etc...)

        to_remove: Set[InsnBlock] = set()
        removed = 0

        for block in graph._blocks:
            if not block.instructions and block != graph.entry_block:
                to_remove.add(block)

        while to_remove:
            for block in to_remove:
                target: Union[InsnBlock, None] = None
                cant_remove = False
                cant_remove_yet = False

                for edge in graph.out_edges(block):
                    if isinstance(edge, ExceptionEdge):
                        continue
                    elif edge.to != block and edge.to in to_remove:  
                        cant_remove_yet = True
                        break
                    elif target is not None:
                        cant_remove = True
                        break
                    target = edge.to

                if cant_remove:  # This block is an intermediary, so we can't remove it
                    to_remove.remove(block)
                    break  # FIXME: Some more analysis on the types of edges could be done however
                elif cant_remove_yet:
                    continue
                if not graph.remove(block):  # Might be removing key blocks (i.e. return/rethrow blocks), so don't.
                    to_remove.remove(block)
                    break

                # Reconnect the in edges with their new to block being the to block from the out edge (lol I should 
                # probably use better/correct terminology, I need to touch up on my graph theory I guess).
                for edge in graph.in_edges(block):
                    graph.disconnect(edge)
                    edge.to = target  # Kinda evil doing this, but it's faster than creating a new edge
                    graph.connect(edge)

                removed += 1
                break

        logger.debug(" - Removed %i empty block(s)." % removed)

        graph.fix_labels()
        logger.debug(" - Found %i basic block(s)." % len(graph._blocks))

        return graph

    def __init__(self, method: "MethodInfo") -> None:
        self.method = method

        super().__init__(method, InsnReturnBlock(self), InsnRethrowBlock(self))

    # ------------------------------ Internal methods ------------------------------ #

    def _write_block(
            self,
            offset: int,
            block: InsnBlock,
            code: Code,
            errors: List[Error],
            offsets: Dict[InsnBlock, List[Tuple[int, int, Dict[int, int]]]],
            jumps: Dict[int, JumpEdge],
            switches: Dict[int, List[SwitchEdge]],
            exceptions: List[ExceptionEdge],
            temporary: Set[InsnBlock],
            inlined: Dict[Edge, Tuple[int, int]],
            inline: bool = False,
    ) -> int:
        """
        A helper method for writing individual blocks to the code's instructions.
        """

        inline = inline and block.inline
        if block in offsets and not inline:  # The block is already written, so nothing to do here
            return offset
        elif not block.instructions:  # No instructions means nothing to write
            return offset

        if offsets:  # Have we actually written any yet?
            previous = next(reversed(offsets))
            fallthrough: Union[FallthroughEdge, None] = None

            for edge in self._forward_edges.get(previous, ()):
                if isinstance(edge, FallthroughEdge):
                    fallthrough = edge
                    break

            # Check to see if this block won't fallthrough to its target
            if fallthrough is not None and fallthrough.to != block and not fallthrough.to in offsets:
                # Currently using a goto_w to mitigate any issues with large methods, as we don't know the target offset
                # yet.
                instruction = instructions.goto_w()

                code.instructions[offset] = instruction
                jumps[offset] = JumpEdge(previous, fallthrough.to, instruction)
                offset += instruction.get_size(offset, False)

                logger.debug("    - Generated jump %s to account for edge %s." % (instruction, fallthrough))

        start = offset
        instructions_: Dict[int, Instruction] = {}
        new_offsets: Dict[int, int] = {}

        shifted = False
        while not shifted:
            offset = start
            instructions_.clear()
            new_offsets.clear()

            wide = False
            for index, instruction in enumerate(block.instructions):
                instructions_[offset] = instruction.copy()
                if instruction == instructions.new:
                    new_offsets[index] = offset
                offset += instruction.get_size(offset, wide)

                wide = instruction == instructions.wide

            # Is the method is large enough that we may need to consider generating intermediary blocks to account for
            # jumps around this block?
            if offset < 32768:
                break

            for offset_, edge in jumps.items():
                # If either the offset delta is valid for a 2 byte jump, the target of the jump has already been
                # written, or the jump instruction is a wide goto, we don't need to handle anything here.
                if offset - offset_ <= 32767 or edge.to in offsets or edge.jump == instructions.goto_w:
                    continue
                shifted = True

                intermediary = InsnBlock(self)
                temporary.add(intermediary)
                intermediary.jump(edge.to, instructions.goto_w)

                # Overwrite the old edge with a new one where the jump target is the intermediary block.
                jumps[offset_] = JumpEdge(edge.from_, intermediary, edge.jump)

                # Write the block immediately, adjusting the offset too
                offset = self._write_block(
                    offset, intermediary, code, errors, offsets, jumps, switches, exceptions, temporary, inlined,
                )
                logger.debug("    - Generated %s to account for edge %s." % (intermediary, edge))

            if not shifted:
                break

            logger.debug("    - Shifted %s by %+i bytes." % (block, offset - start))
            start = offset

        code.instructions.update(instructions_)  # Add the new instructions to the code
        max_offset = next(reversed(instructions_))

        offsets.setdefault(block, []).append((start, offset, new_offsets))  # Update with the new bounds of this block

        # Validate that the out edges from this block are valid, and get the required ones.
        
        multiple_fallthroughs = False
        multiple_jumps = False
        has_out_edges = False

        fallthrough: Union[FallthroughEdge, None] = None
        jump: Union[JumpEdge, None] = None
        switches_: List[SwitchEdge] = []

        for edge in self._forward_edges.get(block, ()):
            if isinstance(edge, FallthroughEdge):
                if fallthrough is not None:
                    multiple_fallthroughs = True
                fallthrough = edge
                has_out_edges = True

            elif isinstance(edge, SwitchEdge):
                switches_.append(edge)
                has_out_edges = True

            elif isinstance(edge, JumpEdge):
                if jump is not None:
                    multiple_jumps = True
                jump = edge
                has_out_edges = True

            elif isinstance(edge, ExceptionEdge):
                exceptions.append(edge)
                # Exceptions don't count as valid out edges, at least I wouldn't think so
                # FIXME: ^^^ true?

        # Check that all the edges are valid

        if multiple_fallthroughs:
            errors.append(Error(block, "multiple fallthrough edges on block"))

        if jump is not None:
            if multiple_jumps:
                errors.append(Error(block, "multiple jumps on block"))
            is_conditional = isinstance(jump.jump, ConditionalJumpInstruction)

            if jump.jump == instruction:  # Record the offset of the jump instruction on the jump edge, for adjustment
                offsets_ = offsets.get(jump.to, None)
                if offsets_ is not None:  # If we have written the block already, we may need to add intermediary jumps
                    start_ = min(map(lambda item: item[0], offsets_), key=lambda offset_: offset - offset_)
                    delta = start_ - offset

                # Check if we can remove the jump altogether (due to inline blocks)
                if not is_conditional and jump.to is not None and jump.to.inline:
                    del code.instructions[max_offset]
                    offset -= instruction.get_size(max_offset, False)
                    offsets[block][-1] = (start, offset, new_offsets)
                    offset = self._write_block(
                        offset, jump.to, code,
                        errors, offsets,
                        jumps, switches, exceptions,
                        temporary, inlined,
                        inline=True,
                    )
                    inlined[jump] = offsets[jump.to][-1][:-1]

                # We don't need to adjust the jump at all if any of these are the case
                elif offsets_ is None or delta > -32768 or jump.jump == instructions.goto_w:
                    jumps[max_offset] = jump

                elif is_conditional:
                    raise NotImplementedError("Wide conditional substitution is not yet implemented.")

                else:  # Otherwise we can just generate the wide variants of the jumps and it won't change much
                    if jump.jump == instructions.jsr:
                        instruction = instructions.jsr_w(delta)
                    else:
                        instruction = instructions.goto_w(delta)

                    jumps[max_offset] = JumpEdge(block, jump.to, instruction)
                    code.instructions[max_offset] = instruction
                    # We also need to adjust the offset and bounds of the block
                    offset = max_offset + instruction.get_size(max_offset, False)
                    offsets[block][-1] = (start, offset, new_offsets)

                    logger.debug("    - Adjusted edge %s to wide jump %s." % (jump, instruction))

            else:
                errors.append(Error(block, "expected jump instruction %s at end of block" % jump.jump))

            if is_conditional and fallthrough is None:
                errors.append(Error(block, "conditional jump edge with no fallthrough edge on block"))
            elif not is_conditional and fallthrough is not None:
                errors.append(Error(block, "unconditional jump edge with a fallthrough edge on block"))

            if switches_:
                errors.append(Error(block, "jump and switch edges on block"))

        elif switches_:
            multiple = False
            previous = None

            for edge in switches_:
                if previous is not None and previous.jump != edge.jump:
                    multiple = True
                previous = edge

            if multiple:
                errors.append(Error(block, "block has multiple switch edges which reference different switch instructions"))

            if edge.jump == instruction:
                if multiple:  # Remove any edges whose instruction we aren't writing
                    for edge in switches_.copy():
                        if edge.jump != instruction:
                            switches_.remove(edge)
                instruction = code.instructions[max_offset]  # Use the copied instruction from now on
                instruction.offsets.clear()

                switches[max_offset] = switches_
                # We need to fix the switch instruction's size because as far as it is concerned, it won't have any offsets
                # and therefore it won't compute the size correctly, so dummy values are added as offsets here.
                if instruction == instructions.tableswitch:
                    for edge in switches_:
                        if edge.value is not None:  # Ignore the default switch edge
                            instruction.offsets.append(0)
                elif instruction == instructions.lookupswitch:
                    for edge in switches_:
                        if edge.value is not None:
                            instruction.offsets[edge.value] = 0

                # Recompute the offset and readjust the block's bounds
                offset = max_offset + instruction.get_size(max_offset, False)
                offsets[block][-1] = (start, offset, new_offsets)

            else:
                errors.append(Error(block, "expected switch instruction %s at end of block" % edge.jump))

        if not has_out_edges and not block in (self._return_block, self._rethrow_block):
            errors.append(Error(block, "block has no out edges"))

        if fallthrough is not None:
            offsets_ = offsets.get(fallthrough.to, None)

            if fallthrough.to.inline and fallthrough.to != block:  # Try to inline the fallthrough block if we can
                offset = self._write_block(
                    offset, fallthrough.to, code,
                    errors, offsets,
                    jumps, switches, exceptions,
                    temporary, inlined,
                    inline=True,
                )
                inlined[fallthrough] = offsets[fallthrough.to][-1][:-1]  # Note down where we inlined the block at

            # Have we already written the fallthrough block? Bear in mind, that if the block can be inlined, we don't
            # need to worry about it as we can just write it directly after this one.
            elif offsets_ is not None:
                # Find the closest starting offset for the fallthrough block, as we want to avoid using wide jumps as
                # much as possible.
                start = min(map(lambda item: item[0], offsets_), key=lambda offset_: offset - offset_)
                delta = start - offset

                if delta < -32767:
                    instruction = instructions.goto(delta)
                else:
                    instruction = instructions.goto_w(delta)

                jumps[offset] = JumpEdge(block, fallthrough.to, instruction)
                code.instructions[offset] = instruction
                offset += instruction.get_size(offset, False)

                logger.debug("    - Generated jump %s to account for edge %s." % (instruction, fallthrough))

        return offset

    # ------------------------------ Assembly ------------------------------ #

    def assemble(
            self,
            do_raise: bool = True,
            simplify_exception_ranges: bool = True,
            compute_frames: bool = True,
            compress_frames: bool = True,
            remove_dead_blocks: bool = True,
    ) -> Code:
        """
        Assembles this graph into a Code attribute.

        :param do_raise: Raise an exception if there are verify errors.
        :param simplify_exception_ranges: Merges overlapping exception ranges, if possible.
        :param compute_frames: Computes stackmap frames and creates a StackMapTable attribute for the code.
        :param compress_frames: Uses compressed stackmap frames instead of just writing out FullFrames.
        :param remove_dead_blocks: Doesn't write dead blocks.
        """

        if self.entry_block is None:
            raise ValueError("Cannot assemble as the entry block is None.")
        if self._opaque_edges:
            raise NotImplementedError("Cannot yet assemble a method with opaque edges.")

        logger.debug("Assembling method %r:" % str(self.method))

        checker = FullTypeChecker()  # TODO: Allow specified type checker through verifier parameter
        errors: List[Error] = []

        trace = Trace.from_graph(self, checker)
        errors.extend(trace.errors)

        code = Code(self.method, trace.max_stack, trace.max_locals)
        logger.debug(" - Max stack: %i, max locals: %i." % (code.max_stack, code.max_locals))

        # Write blocks and record the offsets they were written at, as well as keeping track of jump, switch and
        # exception offsets for later adjustment, as we don't know all the offsets while we're writing.

        offset = 0
        # Record the blocks that have been written and their start/end offsets as well as new instruction mappings (this
        # for keeping track of uninitialised types, hacky, I know). Note that blocks can actually be written multiple 
        # times if they have inline=True, so take that into account.
        offsets: Dict[InsnBlock, List[Tuple[int, int, Dict[int, int]]]] = {}
        dead: Set[InsnBlock] = set()

        jumps: Dict[int, JumpEdge] = {}
        switches: Dict[int, List[SwitchEdge]] = {}
        exceptions: List[ExceptionEdge] = []
        inlined: Dict[FallthroughEdge, Tuple[int, int]] = {}

        logger.debug(" - Writing %i block(s):" % len(self._blocks))

        # We'll record blocks that we've created for the purpose of assembling so that we can remove them later, as we
        # don't want to alter the state of the graph.
        temporary: Set[InsnBlock] = set()

        for block in sorted(self._blocks, key=lambda block_: block_.label):
            if remove_dead_blocks and not block in trace.states:
                dead.add(block)
                continue
            if block in (self._return_block, self._rethrow_block):
                continue

            offset = self._write_block(
                offset, block, code, errors, offsets, jumps, switches, exceptions, temporary, inlined,
            )

        # We may need to write the return and rethrow blocks if we have direct jumps to them that weren't, this can
        # occur, for example, when the only exit path from a method is via a conditional directly to the return block.
        for block in (self._return_block, self._rethrow_block):
            if block in offsets:  # Has already been written, so we don't need to worry about it
                continue
            for edge in itertools.chain(jumps.values(), *switches.values(), exceptions):
                if edge.to == block:
                    offset = self._write_block(
                        offset, block, code, errors, offsets, jumps, switches, exceptions, temporary, inlined,
                    )
                    logger.debug(" - Force write %s due to non-inlined edge reference." % block)
                    break

        # Also check for if we haven't written anything lol, cos we need to add a return for the method to be valid.
        if not offsets:
            self._write_block(
                offset, self._return_block, code, errors, offsets, jumps, switches, exceptions, temporary, inlined,
            )

        if temporary:
            logger.debug(" - Generated %i temporary block(s) while writing." % len(temporary))
            for block in temporary:
                self.remove(block)
        if inlined:
            logger.debug(" - Inlined %i block(s)." % len(inlined))

        dead_frames: Dict[InsnBlock, State] = {}

        # Fix dead blocks by replacing them with nops and an athrow at the end, to break control flow.

        if dead:
            if compute_frames:
                # The standard state we'll use for these dead blocks' stackmap frames, since these are never actually
                # visited, the only proof we need that the athrow is valid is from the stackmap frame, so we can just
                # say that there's a throwable on the stack lol.
                state = State(0)
                state.push(None, types.throwable_t)

            logger.debug(" - %i dead block(s):")
            for block in dead:
                if not block in offsets:
                    logger.debug("    - %s (unwritten)" % block)
                    continue

                logger.debug("    - %s (written at %s)" % (
                    block, ", ".join(map(str, (start for start, _, _ in offsets[block]))),
                ))
                if compute_frames:  # We'll only do this if we're computing frames, as otherwise there's no point
                    dead_frames[block] = state

                    for start, end, _ in offsets[block]:
                        last = end - 1
                        offset = start
                        while offset < last:
                            code.instructions[offset] = instructions.nop()
                            offset += 1
                        code.instructions[last] = instructions.athrow()

        # Adjust jumps and switches to the correct positions, if needs be.

        for offset, edge in jumps.items():
            if edge.jump.offset is not None:  # Already computed the jump offset
                continue
            start = min(map(lambda item: item[0], offsets[edge.to]), key=lambda offset_: abs(offset - offset_))
            code.instructions[offset].offset = start - offset
        if jumps:
            logger.debug(" - Adjusted %i jump(s)." % len(jumps))

        for offset, edges in switches.items():
            instruction = code.instructions[offset]
            for edge in edges:
                start = min(map(lambda item: item[0], offsets[edge.to]), key=lambda offset_: abs(offset - offset_))
                value = edge.value
                if value is None:
                    instruction.default = start - offset
                else:
                    instruction.offsets[value] = start - offset

        if switches:
            logger.debug(" - Adjusted %i switch(es)." % len(switches))

        # Add exception handlers and set their offsets to the correct positions to, then simplify any overlapping ones
        # if required (simplify_exception_ranges=True).

        for edge in sorted(exceptions, key=lambda edge_: edge_.priority):
            for start, end, _ in offsets[edge.from_]:
                (handler, _, _), *extra = offsets[edge.to]
                if extra:
                    errors.append(Error(edge, "multiple exception handler targets (is the handler inlined?)"))
                # If there are multiple offsets for the exception handler, simply just pick the first one.
                code.exception_table.append(Code.ExceptionHandler(
                    start, end, handler, Class_(edge.throwable.name),
                ))
        if simplify_exception_ranges:
            ...  # TODO
        if code.exception_table:
            logger.debug(" - Generated %i exception handler(s)." % len(code.exception_table))

        # Compute stackmap frames

        if compute_frames and (dead_frames or jumps or switches or exceptions):
            stackmap_table = StackMapTable(code)
            stackmap_frames: Dict[int, Tuple[Dict[int, int], InsnBlock, State]] = {
                # Create the bootstrap (implicit) frame
                -1: (self.entry_block, tuple(trace.states[self.entry_block].keys())[0]),
            }
            visited: Set[InsnBlock] = set()
            liveness = Liveness.from_trace(trace)

            # Add the dead stackmap frames first

            for block, state in dead_frames.items():
                for start, _, _ in offsets[block]:
                    stackmap_frames[start] = (block, state)

            # Add all the blocks that are jump targets in some sense (this includes exception handler targts), as we
            # don't actually need to write all the states basic blocks, contrary to what the JVM spec says, instead we
            # only need to write the states at basic blocks that are jumped to. At this stage, we'll also combine the
            # states from different paths.

            for edge in itertools.chain(jumps.values(), *switches.values(), exceptions):
                block = edge.to
                base: Union[State, None] = None

                # We can split constraints on inlined blocks
                if block.inline and edge in inlined:
                    states = trace.states[edge.from_]
                    offsets_ = (inlined[edge],)
                elif block in visited:  # Don't check this for inline edges, obviously
                    continue
                else:
                    visited.add(block)
                    states = trace.states[block]
                    offsets_ = offsets[block]

                # print(edge)
                for state in states:
                    # print(", ".join(map(str, state.locals.values())))
                    if base is None:
                        base = state.unfreeze()
                        continue

                    # Check that the stack is mergeable
                    if len(state.stack) > len(base.stack):
                        errors.append(Error(
                            edge,
                            "stack overrun, expected stack size %i for edge, got size %i" % (
                                len(base.stack), len(state.stack),
                            ),
                        ))
                    elif len(state.stack) < len(base.stack):
                        errors.append(Error(
                            edge,
                            "stack underrun, expected stack size %i for edge, got size %i" % (
                                len(base.stack), len(state.stack),
                            ),
                        ))

                    for index, (entry_a, entry_b) in enumerate(zip(base.stack, state.stack)):
                        if not checker.check_merge(entry_a.type, entry_b.type):
                            errors.append(Error(
                                edge,
                                "illegal stack merge at index %i (%s, via %s and %s, via %s)" % (
                                    index, entry_a.type, entry_a.source, entry_b.type, entry_b.source,
                                ),
                            ))

                        merged = checker.merge(entry_a.type, entry_b.type)
                        if merged != entry_a.type:  # Has the merge changed the entry?
                            base.stack[index] = Entry(-base.id, None, merged, parents=(), merges=(entry_a, entry_b))

                    for index in liveness.entries[block]:
                        entry_a = base.locals.get(index, None)
                        entry_b = state.locals.get(index, None)

                        if entry_a is None and entry_b is None:
                            errors.append(Error(
                                edge, "illegal locals merge at index %i, expected live local" % index,
                            ))
                            continue
                        elif entry_a is None:
                            errors.append(Error(
                                edge,
                                "illegal locals merge at index %i, expected live local (have %s via %s)" % (
                                    index, entry_b.type, entry_b.source,
                                ),
                            ))
                            base.set(entry_b.source, index, entry_b)
                            continue
                        elif entry_b is None:
                            errors.append(Error(
                                edge,
                                "illegal locals merge at index %i, expected live local (have %s via %s)" % (
                                    index, entry_a.type, entry_a.source,
                                ),
                            ))
                            continue

                        if not checker.check_merge(entry_a.type, entry_b.type):
                            errors.append(Error(
                                edge,
                                "illegal locals merge at index %i (%s via %s and %s via %s)" % (
                                    index, entry_a.type, entry_a.source, entry_b.type, entry_b.source,
                                ),
                            ))

                        merged = checker.merge(entry_a.type, entry_b.type)
                        if merged != entry_a.type:
                            base.locals[index] = Entry(-base.id, None, merged, parents=(), merges=(entry_a, entry_b))

                for start, _, _ in offsets_:
                    stackmap_frames[start] = (block, base)

            for offset, (block, state) in sorted(stackmap_frames.items(), key=lambda item: item[0]):
                # The bootstrap (implicit) frame requires that all types are explicit and there are no tops, so we don't
                # take the liveness for the entry block, instead we just use the local indices to indicate that all the
                # locals are "live".
                live = liveness.entries[block] if offset >= 0 else set(state.locals.keys())

                locals_ = []
                stack = []

                max_local = 0  # We can truncate trailing tops from the locals
                max_actual = max((0, *live))

                if state.locals:
                    wide_skip = False
                    for index in range(max(state.locals) + 1):
                        if wide_skip:
                            wide_skip = False
                            continue

                        entry = state.locals.get(index, state._top)

                        # Note: uninitializedThis must be specified, live or not.
                        if not index in live and entry.type != types.uninit_this_t:
                            locals_.append(types.top_t)
                        else:
                            # Special handling for uninitialised types, we need to add the offset in
                            if (
                                isinstance(entry.type, Uninitialized) and
                                entry.type != types.uninit_this_t and
                                isinstance(entry.source, BlockInstruction)
                            ):
                                done = False
                                for _, _, new_offsets in offsets[entry.source.block]:
                                    if done:
                                        errors.append(Error(
                                            entry.source,
                                            "unable to determine source of uninitialised type as block is written multiple times",
                                        ))
                                        break
                                    locals_.append(Uninitialized(new_offsets[entry.source.index]))
                                    done = True
                                continue

                            locals_.append(entry.type)
                            max_local = len(locals_)
                            wide_skip = entry.type.internal_size > 1

                    locals_ = locals_[:max_local]

                for entry in state.stack:
                    if entry == state._top:
                        continue
                    elif (
                        isinstance(entry.type, Uninitialized) and
                        entry.type != types.uninit_this_t and
                        isinstance(entry.source, BlockInstruction)
                    ):
                        done = False
                        for _, _, new_offsets in offsets[entry.source.block]:
                            if done:
                                errors.append(Error(
                                    entry.source,
                                    "unable to determine source of uninitialised type as block is written multiple times",
                                ))
                                break
                            stack.append(Uninitialized(new_offsets[entry.source.index]))
                            done = True
                        continue

                    stack.append(entry.type)

                # print(offset, block, live, liveness.exits.get(block, None))
                # print("locals: [", ", ".join(map(str, locals_)), "]")
                # print("stack:  [", ", ".join(map(str, stack)), "]")

                if offset >= 0:  # Don't write the bootstrap frame (offset -1)
                    stackmap_frame: Union[StackMapTable.StackMapFrame, None] = None
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
                                    StackMapTable.SameLocals1StackItemFrame(offset_delta, stack[0]) if offset_delta < 64 else
                                    StackMapTable.SameLocals1StackItemFrameExtended(offset_delta, stack[0])
                                )
                        elif not stack and max_actual != prev_max_actual:
                            if -3 <= locals_delta < 0 and locals_ == prev_locals[:locals_delta]:
                                stackmap_frame = StackMapTable.ChopFrame(offset_delta, -locals_delta)
                            elif 3 >= locals_delta > 0 and locals_[:-locals_delta] == prev_locals:
                                stackmap_frame = StackMapTable.AppendFrame(offset_delta, locals_[-locals_delta:])

                    if stackmap_frame is None:  # Resort to a full frame if we haven't worked out what it should be
                        stackmap_frame = StackMapTable.FullFrame(offset_delta, tuple(locals_), stack)

                    stackmap_table.frames.append(stackmap_frame)

                prev_offset = offset
                prev_locals = locals_
                prev_stack = stack
                prev_max_local = max_local
                prev_max_actual = max_actual

            if stackmap_table.frames:
                code.attributes[stackmap_table.name] = (stackmap_table,)
                logger.debug(" - Generated %i stackmap frame(s)." % len(stackmap_table.frames))

        if errors:
            if do_raise:
                raise VerifyError(errors)

            logger.debug(" - %i error(s) during assembling:" % len(errors))
            for error in errors:
                logger.debug("    - %s" % error)

        return code

    # ------------------------------ Edges ------------------------------ #

    def connect(self, edge: Edge, handle_fallthroughs: bool = True, handle_jumps: bool = True) -> None:
        """
        :param handle_fallthroughs: Handle multiple fallthrough edges by removing already existing ones.
        :param handle_jumps: Handle jump edges by removing extra ones and adding the jump to the block if it isn't
                             already in it.
        """

        if isinstance(edge, FallthroughEdge) and handle_fallthroughs:
            # Ensure that blocks only have one fallthrough edge
            for edge_ in self._forward_edges.get(edge.from_, []).copy():
                if isinstance(edge_, FallthroughEdge):
                    self.disconnect(edge_)

        elif isinstance(edge, JumpEdge) and handle_jumps:
            for edge_ in self._forward_edges.get(edge.from_, []).copy():
                if isinstance(edge_, JumpEdge) and edge_.jump != edge.jump:
                    self.disconnect(edge_)

            if not edge.jump in edge.from_.instructions:  # Add to the instructions in the block we're jumping from
                edge.from_.instructions.append(edge.jump)

        super().connect(edge)

    def disconnect(self, edge: Edge, handle_jumps: bool = True) -> None:
        """
        :param handle_jumps: Removes jump instructions from the block if this edge is the last edge that references them.
        """

        if isinstance(edge, JumpEdge) and handle_jumps:
            # Remove the jump instruction if there are no more edges referencing the jump
            for edge_ in self._forward_edges.get(edge.from_, ()):
                if isinstance(edge_, JumpEdge):
                    break
            else:
                while edge.jump in edge.from_.instructions:
                    edge.from_.instructions.remove(edge.jump)

        super().disconnect(edge)

    def fallthrough(self, from_: InsnBlock, to: InsnBlock) -> FallthroughEdge:
        """
        Creates and connects a fallthrough edge between two blocks.

        :param from_: The block we're coming from.
        :param to: The block we're going to.
        :return: The created fallthrough edge.
        """

        edge = FallthroughEdge(from_, to)
        self.connect(edge)
        return edge

    def jump(
            self, from_: InsnBlock, to: InsnBlock, jump: Union[MetaInstruction, Instruction] = instructions.goto,
    ) -> JumpEdge:
        """
        Creates a jump edge between two blocks.

        :param from_: The block we're coming from.
        :param to: The block we're going to.
        :param jump: The jump instruction.
        :return: The jump edge that was created.
        """

        if isinstance(jump, MetaInstruction):
            jump = jump()

        if isinstance(jump, JsrInstruction) or isinstance(jump, RetInstruction):
            raise TypeError("Cannot add jsr/ret instructions with jump() method.")
        elif jump in (instructions.tableswitch, instructions.lookupswitch):
            raise TypeError("Cannot add switch instructions with jump() method.")

        jump.offset = None

        edge = JumpEdge(from_, to, jump)
        self.connect(edge)
        return edge

    def catch(
            self,
            from_: InsnBlock,
            to: InsnBlock,
            priority: Union[int, None] = None,
            exception: Union[ReferenceType, Class, Class_, str] = types.throwable_t,
    ) -> ExceptionEdge:
        """
        Creates an exception edge between two blocks.

        :param from_: The block we're coming from.
        :param to: The block that will act as the exception handler.
        :param priority: The priority of this exception handler, lower values mean higher priority.
        :param exception: The exception type being caught.
        :return: The exception edge that was created.
        """

        exception = _argument.get_reference_type(exception)
        if priority is None:  # Determine this automatically
            priority = 0
            for edge in self._forward_edges.get(from_, ()):
                if isinstance(edge, ExceptionEdge) and edge.priority >= priority:
                    priority = edge.priority + 1

        edge = ExceptionEdge(from_, to, priority, exception)
        self.connect(edge)
        return edge

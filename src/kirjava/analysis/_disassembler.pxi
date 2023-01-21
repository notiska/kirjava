"""
Functions that make up Kirjava's disassembler.
Similarly to the assembler: kept in a separate file because graph.py was previously 1500+ lines.
"""

import itertools
import logging

from ..classfile import instructions
from ..classfile.instructions import ConditionalJumpInstruction, JsrInstruction, JumpInstruction, ReturnInstruction

_disassembler_logger = logging.getLogger("kirjava.analysis._disassembler")


cdef inline tuple _find_targets_and_bounds(object code):  # -> Tuple[Set[int], Set[int], Set[int]]:
    """
    Finds jump targets, exception handler targets and exception bounds.
    """

    cdef set jump_targets = set()
    cdef set handler_targets = set()
    cdef set exception_bounds = set()

    for offset, instruction in (<dict>code.instructions).items():
        if isinstance(instruction, JumpInstruction):  # Add jump offsets for jump instructions
            try:
                if instruction.offset is not None:
                    jump_targets.add(offset + instruction.offset)
            except AttributeError:
                ...  # ret instruction doesn't have an offset and catching this error is simply faster than checking

        elif instruction == instructions.tableswitch:  # Add jump offsets for tableswitch instructions
            jump_targets.add(offset + instruction.default)
            for offset_ in instruction.offsets:
                jump_targets.add(offset + offset_)

        elif instruction == instructions.lookupswitch:  # Add jump offsets for lookupswitch instructions
            jump_targets.add(offset + instruction.default)
            for offset_ in instruction.offsets.values():
                jump_targets.add(offset + offset_)

    for handler in <list>code.exception_table:  # Add exception handler targets and bounds
        handler_targets.add(handler.handler_pc)
        exception_bounds.add(handler.start_pc)
        exception_bounds.add(handler.end_pc)

    return jump_targets, handler_targets, exception_bounds


cdef inline void _create_blocks_and_edges(
        InsnGraph graph, object code, set jump_targets, set handler_targets, set exception_bounds,
) except *:
    """
    Creates basic blocks and edges between them.
    """

    cdef dict starting = {}
    cdef dict forward_jumps = {}  # Forward reference jump targets

    # Variables that'll be used later
    cdef:
        dict instructions_ = code.instructions

        bint is_new_block = False
        bint is_forward_offset
        bint is_jsr

        list edges

        InsnEdge edge
        InsnBlock previous
        InsnBlock to

        dict offsets  # For switch instructions

        InsnBlock block = graph.entry_block

    for offset in sorted(instructions_):
        # Don't want to modify the original as some instructions are not immutable (due to their operands).
        instruction = instructions_[offset].copy()

        is_forward_offset = offset in forward_jumps

        # Is this block jumped to at any point?
        if not is_new_block and (is_forward_offset or offset in jump_targets or offset in exception_bounds or offset in handler_targets):
            # If the current block has instructions, we need to create a new one.
            if block._instructions or block is graph.entry_block:
                previous = block
                is_new_block = True
                block = InsnBlock(previous.label + 1)
                graph._add(block, check=False)
                graph._connect(FallthroughEdge(previous, block), overwrite=False, check=False)

        if is_new_block:
            is_new_block = False
            starting[offset] = block

            # Check if any previous jumps reference this starting offset
            if is_forward_offset:
                edges = forward_jumps.pop(offset)
                for edge in edges:
                    # Since this is a bound edge, remove any absolute jump offsets from it.
                    if isinstance(edge, SwitchEdge):
                        if edge.value is None:
                            edge.instruction.default = None
                        elif edge.instruction == instructions.tableswitch:
                            # FIXME: Remove individual offsets, might have unbound switch edges
                            edge.instruction.offsets.clear()
                        elif edge.instruction == instructions.lookupswitch:
                            edge.instruction.offsets.pop(edge.value, None)

                    elif isinstance(edge, JumpEdge):
                        edge.instruction.offset = None

                    # Technically we aren't allowed to set the edge's to, but we can get away with it here as we
                    # haven't yet added it to the graph, though generally, these should be immutable.
                    edge.to = block
                    graph._connect(edge, overwrite=False, check=False)

        # Check if it's an instruction that breaks the control flow and create a new block (adding edges if
        # necessary).
        if isinstance(instruction, JumpInstruction):
            is_jsr = isinstance(instruction, JsrInstruction)

            if instruction == instructions.ret:
                graph._connect(RetEdge(block, None, instruction), overwrite=False, check=False)

            elif not is_jsr:  # jsr instructions are handled more specifically
                to = starting.get(offset + instruction.offset, None)
                edge = JumpEdge(block, to, instruction)
                if to is not None:
                    instruction.offset = None
                    graph._connect(edge, overwrite=False, check=False)
                else:  # Mark the offset as a forward jump edge
                    edges = forward_jumps.setdefault(offset + instruction.offset, [])
                    edges.append(edge)

            previous = block
            is_new_block = True
            block = InsnBlock(previous.label + 1)
            graph._add(block, check=False)

            if isinstance(instruction, ConditionalJumpInstruction):
                graph._connect(FallthroughEdge(previous, block), overwrite=False, check=False)
            elif is_jsr:
                to = starting.get(offset + instruction.offset, None)
                edge = JsrJumpEdge(previous, to, instruction)
                if to is not None:
                    instruction.offset = None
                    graph._connect(edge, overwrite=False, check=False)
                else:
                    edges = forward_jumps.setdefault(offset + instruction.offset, [])
                    edges.append(edge)

                block.inline_ = True  # We need to inline jsr fallthrough targets no matter what.
                graph._connect(JsrFallthroughEdge(previous, block, instruction), overwrite=False, check=False)

        elif instruction == instructions.tableswitch:
            # Previously chained the default to the beginning of the offsets, this was slower so it's here now.
            to = starting.get(offset + instruction.default)
            edge = SwitchEdge(block, to, instruction, None)
            if to is not None:
                instruction.default = None
                graph._connect(edge, overwrite=False, check=False)
            else:
                edges = forward_jumps.setdefault(offset + instruction.default, [])
                edges.append(edge)

            for index, offset_ in enumerate(<list>instruction.offsets.copy()):
                to = starting.get(offset + offset_, None)
                edge = SwitchEdge(block, to, instruction, index)
                if to is not None:
                    # FIXME: Remove individual offsets, might have unbound switch edges
                    instruction.offsets.clear()
                    graph._connect(edge, overwrite=False, check=False)
                else:
                    edges = forward_jumps.setdefault(offset + offset_, [])
                    edges.append(edge)

            is_new_block = True
            block = InsnBlock(block.label + 1)
            graph._add(block, check=False)

        elif instruction == instructions.lookupswitch:
            to = starting.get(offset + instruction.default)
            edge = SwitchEdge(block, to, instruction, None)
            if to is not None:
                instruction.default = None
                graph._connect(edge, overwrite=False, check=False)
            else:
                edges = forward_jumps.setdefault(offset + instruction.default, [])
                edges.append(edge)

            offsets = instruction.offsets
            for value, offset_ in offsets.copy().items():
                to = starting.get(offset + offset_, None)
                edge = SwitchEdge(block, to, instruction, value)
                if to is not None:
                    offsets.pop(value)
                    graph._connect(edge, overwrite=False, check=False)
                else:
                    edges = forward_jumps.setdefault(offset + offset_, [])
                    edges.append(edge)

            is_new_block = True
            block = InsnBlock(block.label + 1)
            graph._add(block, check=False)

        elif isinstance(instruction, ReturnInstruction):
            graph._connect(FallthroughEdge(block, graph.return_block, instruction), overwrite=False, check=False)
            is_new_block = True
            block = InsnBlock(block.label + 1)
            graph._add(block, check=False)

        elif instruction == instructions.athrow:
            graph._connect(FallthroughEdge(block, graph.rethrow_block, instruction), overwrite=False, check=False)
            is_new_block = True
            block = InsnBlock(block.label + 1)
            graph._add(block, check=False)

        else:  # Otherwise, we can add the instruction to the block
            block._instructions.append(instruction)

    cdef int unbound
    if forward_jumps:
        unbound = 0
        for edges in forward_jumps.values():
            for edge in edges:
                edge.from_._instructions.append(edge.instruction)

                # Now generate a fallthrough edge to the next block, if it exists. This is done to maintain the original
                # order of the instructions in the code. This code is invalid as it is, so it doesn't matter if this is
                # not an accurate representation of what would happen, instead we want to maintain the correctness of
                # the actual instructions.
                # An example:
                # goto +32767
                # return
                # In this case, we want to maintain that the return instruction comes directly after the invalid goto.

                to = graph._blocks.get(edge.from_.label + 1, None)
                if block is not None:
                    # If the jump is conditional, this will already exist, but the _connect method should ensure that we
                    # don't get duplicates.
                    graph._connect(FallthroughEdge(edge.from_, to), overwrite=True, check=True)

                unbound += 1
        if unbound:
            _disassembler_logger.debug(" - %i unbound forward jump(s)!" % unbound)

    # Remove the final block if it is empty and has no out edges. There might be cases where the final instruction in a
    # method is not one that breaks control flow, and due to that we want to check if we can remove it first.
    if not block._instructions and not graph._forward_edges[block]:  # and not graph._backward_edges[block]:
        graph._remove(block, check=False)

    # Add exception edges via the code's exception table.

    for start, block in starting.items():
        for index, handler in enumerate(<list>code.exception_table):
            if handler.start_pc <= start < handler.end_pc:
                target = starting.get(handler.handler_pc, None)
                if target is not None:
                    type_ = handler.catch_type.type if handler.catch_type is not None else None
                    graph._connect(ExceptionEdge(block, target, index, type_), overwrite=False, check=False)

#!/usr/bin/env python3

__all__ = (
    "Block", "Edge", "Graph",
    "ExceptionEdge", "FallthroughEdge", "JumpEdge",
)

"""
Method control flow.
"""

import itertools
import logging
import operator
from abc import abstractmethod, ABC
from io import BytesIO
from typing import Any, Dict, List, Set, Tuple, Union

from . import Error, VerifyError
from .trace import Entry, State
from .. import types
from ..classfile import instructions, ClassFile
from ..classfile.attributes.code import StackMapTable
from ..classfile.attributes.method import Code
from ..classfile.constants import Class
from ..classfile.instructions import Instruction, MetaInstruction
from ..classfile.instructions.flow import ConditionalJumpInstruction, JumpInstruction
from ..classfile.instructions.other import ReturnInstruction
from ..classfile.members import MethodInfo
from ..environment import Environment
from ..types import ReferenceType, VerificationType
from ..types.reference import ClassOrInterfaceType

logger = logging.getLogger("kirjava.analysis.graph")


class Block:
    """
    An (extended) basic block, as technically any instruction could jump to an exception handler or the rethrow block.
    """

    def __init__(self, label: int, cfg: Union["Graph", None] = None) -> None:
        """
        :param label: The unique label of this block.
        :param cfg: The control flow graph that this block belongs to.
        """

        self.label = label
        if cfg is not None:
            cfg.add(self)

        self.instructions: List[Instruction] = []

        self.fallthrough_edge: Union[FallthroughEdge, None] = None
        self.jump_edges: List[JumpEdge] = []
        self.exception_edges: List[ExceptionEdge] = []

    def __repr__(self) -> str:
        return "<Block(label=%i) at %x>" % (self.label, id(self))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Block) and other.label == self.label and other.instructions == self.instructions

    def __hash__(self) -> int:
        return self.label

    def copy(self) -> "Block":
        """
        Creates a copy of this block.

        :return: The copied block.
        """

        block = Block(self.label)
        block.instructions.extend(self.instructions)    
        # It doesn't make sense to copy the edges here as they'll still reference the old blocks, so don't, as they'll
        # be copied later (at least in the assemble method) and copying them here would just be a waste of time.
        block.fallthrough_edge = self.fallthrough_edge
        block.jump_edges.extend(self.jump_edges)
        block.exception_edges.extend(self.exception_edges)

        return block

    # ------------------------------ Public API ------------------------------ #

    def add(self, instruction: Union[MetaInstruction, Instruction], block: Union["Block", None] = None) -> Instruction:
        """
        Adds an instruction to this block.

        :param instruction: The instruction to add.
        :param block: The block to jump to, if adding a jump instruction.
        :return: The same instruction.
        """

        if isinstance(instruction, MetaInstruction):
            instruction = instruction()  # Should throw at this point, if invalid

        if isinstance(instruction, JumpInstruction):
            if block is None:
                raise ValueError("Expected a value for parameter 'block' if adding a jump instruction.")
            self.jump(block, instruction)
            return instruction

        self.instructions.append(instruction)  # Otherwise, just add to insns

        return instruction

    def fallthrough(self, to: "Block") -> "FallthroughEdge":
        """
        Creates a fallthrough edge to the provided block and sets it to this block's fallthrough edge.

        :param to: The block to fallthrough to.
        :return: The fallthrough edge that was created.
        """

        self.fallthrough_edge = FallthroughEdge(self, to)
        return self.fallthrough_edge

    def jump(self, to: "Block", instruction: Union[Instruction, MetaInstruction, None] = None) -> "JumpEdge":
        """
        Creates a jump edge to the provided block and adds it to this block's jump edges.

        :param to: The block to jump to.
        :param instruction: The jump instruction to use.
        :return: The jump edge that was created.
        """

        if instruction is None:
            instruction = instructions.goto()
        if isinstance(instruction, MetaInstruction):
            instruction = instruction(0)
        jump_edge = JumpEdge(self, to, instruction)
        if not jump_edge in self.jump_edges:
            self.jump_edges.append(jump_edge)
        return jump_edge


class Edge(ABC):
    """
    An edge between two vertices (blocks) in the control flow graph.
    """

    def __init__(self, from_: Block, to: Block) -> None:
        """
        :param from_: The block we're coming from.
        :param to: The block we're going to.
        """

        self.from_ = from_
        self.to = to

    def __repr__(self) -> str:
        return "<%s(from=%r, to=%r) at %x>" % (self.__class__.__name__, self.from_, self.to, id(self))

    def __eq__(self, other: Any) -> bool:
        return other.__class__ == self.__class__ and other.from_ == self.from_ and other.to == self.to

    def __hash__(self) -> int:
        return hash((self.from_, self.to))

    @abstractmethod
    def copy(self) -> "Edge":
        """
        Creates a copy of this edge.

        :return: The copied edge.
        """

        ...


class JumpEdge(Edge):
    """
    An edge caused by an explicit jump in the bytecode.
    """

    def __init__(self, from_: Block, to: Block, jump: JumpInstruction) -> None:
        """
        :param jump: The jump instruction responsible for the jump.
        """

        super().__init__(from_, to)

        self.jump = jump

    def __repr__(self) -> str:
        return "<JumpEdge(from=%r, to=%r, jump=%r) at %x>" % (self.from_, self.to, self.jump, id(self))

    def copy(self) -> "JumpEdge":
        return JumpEdge(self.from_, self.to, self.jump)


class SwitchEdge(JumpEdge):
    """
    A switch-specific jump edge.
    """

    def __init__(self, from_: Block, to: Block, jump: JumpInstruction, index: Union[int, None] = None) -> None:
        """
        :param index: The index/value in the switch statement, None for the default.
        """

        super().__init__(from_, to, jump)

        self.index = index

    def __repr__(self) -> str:
        if self.index is None:
            return "<SwitchEdge(from=%r, to=%r, jump=%r, index=<default>) at %x>" % (
                self.from_, self.to, self.jump, id(self),
            )
        return "<SwitchEdge(from=%r, to=%r, jump=%r, index=%i) at %x>" % (
            self.from_, self.to, self.jump, self.index, id(self),
        )

    def copy(self) -> "SwitchEdge":
        return SwitchEdge(self.from_, self.to, self.jump, self.index)


class FallthroughEdge(Edge):
    """
    An edge caused by a block fallthrough.
    """

    def copy(self) -> "FallthroughEdge":
        return FallthroughEdge(self.from_, self.to)


class ExceptionEdge(Edge):
    """
    An edge caused by an exception handler.
    """

    def __init__(self, from_: Block, to: Block, exception: Class, explicit: bool = False) -> None:
        """
        :param exception: The class of the exception being caught.
        :param explicit: Is it an explicit throw?
        """

        super().__init__(from_, to)

        self.exception = exception
        self.explicit = explicit

    def __repr__(self) -> str:
        return "<ExceptionEdge(from=%r, to=%r, exception=%s, explicit=%s) at %x>" % (
            self.from_, self.to, self.exception, self.explicit, id(self),
        )

    def copy(self) -> "ExceptionEdge":
        return ExceptionEdge(self.from_, self.to, self.exception, self.explicit)


class Graph:
    """
    A control flow graph used to represent methods' code.
    """

    @classmethod
    def disassemble(cls, method_info: MethodInfo) -> "Graph":  # TODO: Accept Code attribute, not MethodInfo
        """
        Creates a control flow graph from the given method and instructions.

        :param method_info: The method.
        :param instructions_: The instructions in the method.
        :return: The control flow graph.
        """

        if not Code.name_ in method_info.attributes:
            raise ValueError("Method %r has no code." % method_info)
        code, = method_info.attributes[Code.name_]

        instructions_ = sorted(code.instructions.items(), key=operator.itemgetter(0))

        graph = cls(method_info)
        logger.debug("Disassembling method %r:" % str(method_info))

        # Find jump targets

        targets: Set[int] = set()

        # Add the exception handlers to the jump targets to attempt to create separate blocks
        for exception_handler in code.exception_table:
            targets.add(exception_handler.start_pc)
            targets.add(exception_handler.end_pc)
            targets.add(exception_handler.handler_pc)

        for offset, instruction in instructions_:
            if isinstance(instruction, JumpInstruction):
                targets.add(offset + instruction.offset)

            elif instruction == instructions.tableswitch:
                targets.add(offset + instruction.default)
                for offset_ in instruction.offsets:
                    targets.add(offset + offset_)

            elif instruction == instructions.lookupswitch:
                targets.add(offset + instruction.default)
                for offset_ in instruction.offsets.values():
                    targets.add(offset + offset_)

        logger.debug(" - Found %i jump target(s)." % len(targets))

        # Create the basic blocks

        current = Block(0)
        # Starting bytecode offset to block mapping (and the reverse too, because I'm lazy)
        starting: Dict[Union[int, Block], Union[Block, int]] = {0: current, current: 0}
        ending: Dict[Block, int] = {}  # Block to their (inclusive) ending offsets, only if they have a jump
        fallthroughs: Dict[Block, Block] = {}  # Blocks to their fallthrough blocks

        for offset, instruction in instructions_:
            if offset in targets:
                # Don't create a new block if the current one isn't empty as that's wasteful
                if current.instructions:
                    previous = current
                    current = Block(current.label + 1)

                    fallthroughs[previous] = current

            # This is the first instruction, so add the current block to the starting offsets with the current offset
            if not current.instructions:
                starting[offset] = current
                starting[current] = offset
            current.instructions.append(instruction)

            if (
                isinstance(instruction, JumpInstruction) or
                isinstance(instruction, ReturnInstruction) or
                instruction in (instructions.athrow, instructions.tableswitch, instructions.lookupswitch)
            ):
                ending[current] = offset

                previous = current
                current = Block(current.label + 1)

                fallthroughs[previous] = current

        logger.debug(" - Found %i basic block(s)." % (len(starting) // 2))

        # Remove the jumps and create edges

        for start_offset, block in starting.items():
            if not isinstance(block, Block):  # We also iterate the reverse mappings
                continue

            graph.blocks.append(block)
            last = block.instructions[-1]
            explicit_throw = False

            if isinstance(last, JumpInstruction):
                block.instructions.pop()

                block.jump_edges.append(JumpEdge(block, starting[ending[block] + last.offset], last))
                if isinstance(last, ConditionalJumpInstruction):  # Need to add the fallthrough edge too
                    block.fallthrough_edge = FallthroughEdge(block, fallthroughs[block])

            elif last == instructions.tableswitch:
                block.instructions.pop()

                block.jump_edges.append(SwitchEdge(block, starting[ending[block] + last.default], last, None))
                for index, offset in enumerate(last.offsets):
                    block.jump_edges.append(SwitchEdge(block, starting[ending[block] + offset], last, index))

            elif last == instructions.lookupswitch:
                block.instructions.pop()

                block.jump_edges.append(SwitchEdge(block, starting[ending[block] + last.default], last, None))
                for value, offset in last.offsets.items():
                    block.jump_edges.append(SwitchEdge(block, starting[ending[block] + offset], last, value))

            elif last == instructions.athrow:
                ...  # FIXME: We can't actually know it's explicit until we check the type I guess :(
                # block.instructions.pop()
                # explicit_throw = True

            elif not isinstance(last, ReturnInstruction):  # Add a fallthrough edge to the next block, if it doesn't break the control flow
                block.fallthrough_edge = FallthroughEdge(block, fallthroughs[block])

            # Add exception edges
            found_handler = False
            if block in fallthroughs:
                end_offset = starting.get(fallthroughs[block], offset)
            else:  # If there's no fallthrough we'll use the final offset
                end_offset = offset
            for exception_handler in code.exception_table:
                if start_offset >= exception_handler.start_pc and end_offset <= exception_handler.end_pc:
                    found_handler = True
                    exception = exception_handler.catch_type
                    if exception is None:
                        exception = Class("java/lang/Throwable")

                    block.exception_edges.append(ExceptionEdge(
                        block, starting[exception_handler.handler_pc], exception,  # explicit_throw,
                    ))

        return graph

    def __init__(self, method_info: MethodInfo) -> None:
        """
        :param method_info: The method whose code this graph represents.
        :param blocks: A mapping of labels to their blocks in the method's code.
        """

        self.method_info = method_info

        # self.entry_block = EntryBlock(self)
        # self.return_block = ReturnBlock(self)
        # self.rethrow_block = RethrowBlock(self)

        self.blocks: List[Block] = []

    # ------------------------------ Utility ------------------------------ #

    def _write_block(
            self,
            block: Block,
            offset: int,
            max_label: int,
            code: Code,
            blocks: Dict[int, Block],
            offsets: Dict[Block, Tuple[int, int]],
            jumps: Dict[int, Tuple[Edge, ...]],
            errors: List[Error],
    ) -> Tuple[int, int]:
        """
        :param block: The block to write:
        :param offset: The current bytecode offset.
        :param max_label: The current maximum block label.
        :param code: The code we're writing to.
        :param blocks: A copy of all the blocks in this graph.
        :param offsets: Blocks to their start/end offsets.
        :param jumps: Jumps given their offsets and jump edges.
        :param errors: The list of errors that occurred when assembling.
        :return: The new bytecode offset and the new max label.
        """

        # Check if the previously written block has a fallthrough edge, and check if we need to generate a goto in its
        # place. We only need to generate a goto if we haven't already written the fallthrough block, as otherwise we'll
        # have already generated one.

        if offsets:  # Have we actually written any yet?
            previous = next(reversed(offsets.keys()))
            if (
                previous.fallthrough_edge is not None and
                previous.fallthrough_edge.to != block and
                not previous.fallthrough_edge.to in offsets and
                # Check that we also haven't already done this lol cos sometimes we can end up writing two gotos
                not previous.fallthrough_edge in jumps.get(offsets[previous][1], ())
            ):
                instruction = instructions.goto_w()  # FIXME: Work out if goto or goto_w is needed

                code.instructions[offset] = instruction
                jumps[offset] = (previous.fallthrough_edge,)

                logger.debug(" - Generated goto for fallthrough block %i to block %i." % (
                    previous.label, previous.fallthrough_edge.to.label,
                ))

                offset += instruction.get_size(offset, False)
                # offsets[previous] = (offsets[previous][0], offset)  # Adjust previous block bounds

        # Record the starting offset of the block and calculate the new offsets, given the instructions in the block.

        start_offset = offset
        start_shift = 0
        instructions_: Dict[int, Instruction] = {}

        wide = False  # TODO: Accounting for wide instructions across blocks?
        for instruction in block.instructions:
            instructions_[offset] = instruction

            offset += instruction.get_size(offset, wide)
            wide = instruction == instructions.wide

        # Account for wide forwards jump offsets in already written blocks.

        if offset > 32767:  # This case can't occur unless the method is large enough
            for block_, (_, end_offset) in list(offsets.items()):
                for jump_edge in block_.jump_edges:
                    if not jump_edge.to in offsets:
                        offset_delta = offset - end_offset
                        # Will this jump be valid? If not, we need to generate an intermediary one.
                        if offset_delta > 32767 and jump_edge.jump != instructions.goto_w:
                            intermediary_block = Block(max_label + 1)
                            intermediary_block.jump(jump_edge.to, instructions.goto_w())

                            max_label += 1
                            blocks[max_label] = intermediary_block

                            logger.debug(" - Generated new block %i to account for edge from block %i to block %i (%s)." % (
                                max_label, jump_edge.from_.label, jump_edge.to.label, jump_edge.jump,
                            ))

                            jump_edge.to = intermediary_block

                            offset_, max_label = self._write_block(
                                intermediary_block, start_offset, max_label, code, blocks, offsets, jumps, errors,
                            )
                            offset_delta = offset_ - start_offset

                            # Shift the starting offset up by the delta, we can do this as we can be sure that no 
                            # instructions inside the block are going to reference other bytecode offsets (jumps
                            # in particular) as we haven't written this block's jump instruction yet (if it even exists).
                            # This is equivalent to simply inserting the intermediary block right before the one we're writing 
                            # right now.
                            start_shift += offset_delta
                            offset += offset_delta

        if start_shift:
            logger.debug(" - Shifted block %i by %+i bytes." % (block.label, start_shift))

            code.instructions.update({offset + start_shift: instruction for offset, instruction in instructions_.items()})
            start_offset += start_shift

        else:
            code.instructions.update(instructions_)

        # We might be generating new blocks, so we need to add this block to the "already written blocks" to prevent
        # gotos being generated for fallthroughs. It doesn't matter if the offsets are incorrect, as we'll correct
        # them later.
        offsets[block] = (start_offset, offset)

        # Add the jump instruction to this offset too, check for invalid edges and account for wide backwards jump 
        # offsets.

        jump: Union[Instruction, None] = None
        jump_offset = 0
        modified_fallthrough = False  # bool(start_shift)

        for jump_edge in block.jump_edges:
            if jump is not None:
                if jump_edge.jump != jump:
                    errors.append(Error(offset, None, "block %i has multiple jump instructions" % block.label))
                else:
                    jumps[jump_offset] += (jump_edge,)

            elif jump is None:
                jump = jump_edge.jump
                jump_offset = offset

                if isinstance(jump, ConditionalJumpInstruction) and block.fallthrough_edge is None:
                    errors.append(Error(
                        offset, None, "block %i has a conditional jump edge but no fallthrough edge" % block.label,
                    ))

                # Check for backwards jump references that may need to be modified to account for wide jump offsets
                # (i.e. offsets > 32767). If this is the case, a temporarily modified copy of the block and jump
                # edge in question is created and written, and that is used through the rest of the assembly.

                jump_start, _ = offsets.get(jump_edge.to, (None, None))
                if jump_start is None:  # We haven't written the edge target block yet, so no need to do anything
                    code.instructions[offset] = jump
                    jumps[offset] = (jump_edge,)
                    offset += jump.get_size(offset, wide)
                    continue

                offset_delta = jump_start - offset

                # The jump is valid, so yet again, no need to do anything
                if offset_delta > -32768 or jump == instructions.goto_w:
                    code.instructions[offset] = jump
                    jumps[offset] = (jump_edge,)
                    offset += jump.get_size(offset, wide)
                    continue

                if isinstance(jump, ConditionalJumpInstruction):
                    # Create the block that contains the edge with the wide goto
                    jump_block = Block(max_label + 1)
                    jump_block.jump(jump_edge.to, instructions.goto_w(offset_delta))

                    max_label += 1
                    blocks[max_label] = jump_block

                    # Create a fallthrough block and replace this block's actual fallthrough with a fallthrough
                    # edge to the fallthrough block, confusing, I know, sorry :p.
                    # Note: we also need to check if there actually is a fallthrough edge as the code being
                    #       generated might be unverified.
                    if block.fallthrough_edge is not None:
                        fallthrough_block = Block(max_label + 1)
                        fallthrough_block.fallthrough(block.fallthrough_edge.to)

                        max_label += 1
                        blocks[max_label] = fallthrough_block

                        block.fallthrough(fallthrough_block)
                        modified_fallthrough = True

                        logger.debug(" - Generated new blocks %i and %i to account for edge from block %i to block %i (%s)." % (
                            jump_block.label, max_label, jump_edge.from_.label, jump_edge.to.label, 
                            jump_edge.jump,
                        ))

                    else:
                        logger.debug(" - Generated new block %i to account for edge from block %i to block %i (%s)." % (
                            max_label, jump_edge.from_.label, jump_edge.to.label,
                        ))

                    jump_edge.to = jump_block  # This is here cos we reference the old one in the logging calls
                    code.instructions[offset] = jump
                    jumps[offset] = (jump_edge,)
                    offset += jump.get_size(offset, wide)

                    # Now write the blocks that we've generated as we want them to immediately follow this block, for
                    # organisational reasons really.
                    if block.fallthrough_edge is not None:
                        offset, max_label = self._write_block(
                            block.fallthrough_edge.to, offset, max_label, code, blocks, offsets, jumps, errors,
                        )
                    offset, max_label = self._write_block(
                        jump_block, offset, max_label, code, blocks, offsets, jumps, errors,
                    )

                elif jump == instructions.tableswitch:  # TODO
                    raise NotImplemented("Widened tableswitch is not yet implemented.")

                elif jump == instructions.lookupswitch:  # TODO
                    raise NotImplemented("Widened lookupswitch is not yet implemented.")

                else:  # We can just generate a goto_w in its place and it won't change anything
                    jump_edge.jump = instructions.goto_w(offset_delta)
                    code.instructions[offset] = jump_edge.jump
                    jumps[offset] = (jump_edge,)
                    offset += jump_edge.jump.get_size(offset, wide)

        # Now check if we need to generate a goto for this block's fallthrough edge, in case the target has already been
        # written. We also need to check that we haven't modified the fallthrough edge, which can occur when accounting
        # for wide jumps.

        if not modified_fallthrough and block.fallthrough_edge is not None:
            fallthrough_offset, _ = offsets.get(block.fallthrough_edge.to, (None, None))
            if fallthrough_offset is not None:
                offset_delta = fallthrough_offset - offset

                if offset_delta < -32767:
                    instruction = instructions.goto_w(offset_delta)
                else:
                    instruction = instructions.goto(offset_delta)

                code.instructions[offset] = instruction
                jumps[offset] = (block.fallthrough_edge,)
                offset += instruction.get_size(offset, False)

                logger.debug(" - Generated goto for fallthrough block %i to block %i." % (
                    block.label, block.fallthrough_edge.to.label,
                ))

        # Check to see if this block has out edges
        if jump is None and block.fallthrough_edge is None and not block.exception_edges:
            last = instructions_[max(instructions_)]
            # Also check that it isn't an instruction that breaks the control flow
            if not isinstance(last, ReturnInstruction) and last != instructions.athrow:
                errors.append(Error(offset, None, "block %i has no out edges" % block.label))

        offsets[block] = (start_offset, offset)
        return offset, max_label

    def _combine_reference_types(self, entry_a: Entry, entry_b: Entry) -> Union[Entry, None]:
        """
        Combines two reference types, when merging the stack or locals for two blocks.

        :param entry_a: The entry that we're attempting to merge.
        :param entry_b: The entry that is in the entry constraints.
        :return: The new entry to replace it with, or None if no replacement is required.
        """

        if entry_a.type == entry_b.type:  # Nothing to do here
            return None
        elif entry_a.type == types.null_t:  # Trying to merge a null type, so no extra information
            return None
        elif entry_b.type == types.null_t:  # Trying to merge into a null type, so return the first type
            return entry_a
        elif isinstance(entry_a.type, ClassOrInterfaceType) and isinstance(entry_b.type, ClassOrInterfaceType):
            environ = Environment.INSTANCE

            common: Union[str, None] = None
            super_classes_a: Set[str] = set()

            try:
                class_a = environ.find_class(entry_a.type.name)
                class_b = environ.find_class(entry_b.type.name)

                while class_a is not None:
                    super_classes_a.add(class_a.name)
                    if class_a.name == class_b.name:
                        common = class_a.name
                        break
                    try:
                        class_a = class_a.super
                    except LookupError:
                        break

                while common is None and class_b is not None:
                    if class_b.name in super_classes_a:
                        common = class_b.name
                        break
                    class_b = class_b.super

            except LookupError:
                ...

            if common is not None:
                logger.debug(" - Combined common Java supertype for %r and %r, %r." % (
                    entry_a.type.name, entry_b.type.name, common,
                ))
                return Entry(entry_a.offset, ClassOrInterfaceType(class_b.name))

            logger.debug(" - Could not resolve common Java supertype for %r and %r." % (
                entry_a.type.name, entry_b.type.name,
            ))
            return Entry(entry_b.offset, types.object_t)  # java/lang/Object it is then :(

        # TODO: Array types

    # ------------------------------ Public API ------------------------------ #

    def add(self, block: Block, fix_label: bool = True) -> None:
        """
        Adds a block to this graph.

        :param block: The block to add.
        :param fix_label: Fixes the label of the block if a block with that label already exists.
        """

        if block in self.blocks:
            return

        if fix_label and block.label in self.blocks:
            conflict = False
            max_label = 0

            for block_ in self.blocks:
                if block_.label > max_label:
                    max_label = block_.label
                if block_.label == block.label:
                    conflict = True

            if conflict:
                block.label = max_label + 1

        self.blocks.append(block)

    def remove(self, block: Block) -> None:
        """
        Removes a block from this graph.
        Note: this does not remove the references to it in other blocks.

        :param block: The block to remove.
        """

        try:
            self.blocks.remove(block)
        except ValueError:
            ...

    def assemble(
            self,
            class_file: ClassFile,
            no_verify: bool = False,
            compute_frames: bool = True,
            compress_frames: bool = False,
            sort_blocks: bool = False,
    ) -> Code:
        """
        Creates writeable instructions with their given offsets.

        :param class_file: The classfile that the method belongs to.
        :param no_verify: Don't verify the instructions (may throw exceptions though).
        :param compute_frames: Computes the stackmap frames for the code, if verification fails, no frames are computed.
        :param compress_frames: Compresses the stackmap frames.
        :param sort_blocks: Writes the blocks in order based on their ID.
        :return: The instructions and generated stack frames.
        """

        logger.debug("Assembling method %r:" % str(self.method_info))

        state = State.make_initial(self.method_info)
        code = Code(self.method_info, len(state.stack), len(state.locals))

        if not self.blocks:  # Obviously
            return code

        errors: List[Error] = []

        jumps_to_adjust: Dict[int, Tuple[Edge, ...]] = {}  # Jumps that will be adjusted later
        exception_handlers_to_adjust: List[Tuple[ExceptionEdge, ...]] = []  # Exception handlers to adjust later

        # Visited blocks with their entry/exit constraints and the edges to the block
        visited: Dict[Block, Tuple[State, State, Set[Edge]]] = {}
        offsets: Dict[Block, Tuple[int, int]] = {}  # Blocks and their starting/ending offsets

        # Create a copy of the blocks in this graph as they may be modified when writing, if required.
        blocks: Dict[int, Block] = {block.label: block.copy() for block in self.blocks}

        # Copy and modify the block edges to fit the copied blocks
        for block in blocks.values():
            if block.fallthrough_edge is not None:
                block.fallthrough_edge = FallthroughEdge(block, blocks[block.fallthrough_edge.to.label])

            jump_edges = []
            for jump_edge in block.jump_edges:
                jump_edge = jump_edge.copy()
                jump_edge.from_ = block
                jump_edge.to = blocks[jump_edge.to.label]
                jump_edges.append(jump_edge)
            block.jump_edges = jump_edges

            exception_edges = []
            for exception_edge in block.exception_edges:
                exception_edge = exception_edge.copy()
                exception_edge.from_ = block
                exception_edge.to = blocks[exception_edge.to.label]
                exception_edges.append(exception_edge)
            block.exception_edges = exception_edges

        max_label = max(blocks)  # For when generating new blocks
        offset = 0  # Current bytecode offset

        if sort_blocks:
            for label in list(sorted(blocks)):
                offset, max_label = self._write_block(
                    blocks[label], offset, max_label, code, blocks, offsets, jumps_to_adjust, errors,
                )

        # Find the entry block, start from the block with the smallest label and follow its predecessors until we find
        # one with no more predecessors, this is the entry block. I'm sure something with dominators could be done to
        # better determine the entry block but I'm lazy.
        entry_block = blocks[min(blocks)]

        # The next edges to visit, in terms of priortiy
        fallthrough_edges: List[FallthroughEdge] = []
        jump_edges: List[JumpEdge] = []
        exception_edges: List[ExceptionEdge] = []

        edge: Union[Edge, None] = None  # Current edge
        block = entry_block  # Current block

        while True:
            if block in visited:
                entry_constraints, exit_constraints, edges = visited[block]
                _, end_offset = offsets[block]

                edges.add(edge)

                # Entries that need to be repropagated through the graph, normally due to merging of reference types.
                to_repropagate: Dict[Entry, Entry] = {}

                if len(state.stack) > len(entry_constraints.stack):
                    errors.append(Error(
                        end_offset, None,
                        "stack overrun, expected stack size %i for block %i to block %i transition, got size %i" % (
                            len(entry_constraints.stack), edge.from_.label, block.label, len(state.stack),
                        ),
                    ))
                    compute_frames = False
                elif len(state.stack) < len(entry_constraints.stack):
                    errors.append(Error(
                        end_offset, None,
                        "stack underrun, expected stack size %i for block %i to block %i transition, got size %i" % (
                            len(entry_constraints.stack), edge.from_.label, block.label, len(state.stack),
                        ),
                    ))
                    compute_frames = False

                for index, (entry_a, entry_b) in enumerate(zip(state.stack, entry_constraints.stack)):
                    if not entry_a.type.can_merge(entry_b.type):
                        errors.append(Error(
                            end_offset, None,
                            "illegal stack merge for block %i to block %i transition, (%s and %s)" % (
                                edge.from_.label, block.label, entry_a.type, entry_b.type,
                            ),
                        ))
                        compute_frames = False
                        break

                    combined = self._combine_reference_types(entry_a, entry_b)
                    if combined is not None:
                        to_repropagate[entry_b] = combined
                        # Replace the values here, for this block, to save time later
                        entry_constraints.replace(entry_b, combined)
                        exit_constraints.replace(entry_b, combined)

                # Locals that are "live" (note: we can't determine this fully yet) in this block, so we won't trust
                # this information fully.
                # live: Set[int] = set()
                # for index, read in exit_constraints.local_accesses:
                #     if read:
                #         live.add(index)
                #     elif index in live:
                #         live.remove(index)

                for index in set(state.locals).intersection(entry_constraints.locals):  # live:
                    if not index in entry_constraints.locals:  # No need to check it then
                        continue

                    entry_a = state.locals[index]
                    entry_b = entry_constraints.locals[index]

                    if not entry_a.type.can_merge(entry_b.type):
                        continue  # FIXME: Lazy solution for now, instead, calculate if overwritten, etc...

                        # if not index in live:  # Might not be needed, so don't worry about it right now
                        #     continue
                        # if not no_verify:
                        #     print(entry_a, entry_b)
                        #     raise Exception("Illegal locals merge.")
                        # compute_frames = False
                        # break

                    combined = self._combine_reference_types(entry_a, entry_b)
                    if combined is not None and combined != entry_b:
                        to_repropagate[entry_b] = combined
                        entry_constraints.replace(entry_b, combined)
                        exit_constraints.replace(entry_b, combined)

                if to_repropagate:
                    logger.debug(" - Repropagating %i entry(s) due to block %i to block %i merge." % (
                        len(to_repropagate), edge.from_.label, block.label,
                    ))
                    # for entry_a, entry_b in to_repropagate.items():
                    #     logger.debug("    - Entry %s (offset %i) merges with %s (offset %i)." % (
                    #         entry_a.type, entry_a.offset, entry_b.type, entry_b.offset,
                    #     ))

                    next_: List[Edge] = list(edges)
                    finished: Set[Edge] = {edge}

                    while next_:
                        edge = next_.pop(0)
                        if edge in finished:
                            continue

                        # If we haven't visited this block already, that's fine, as we've already adjusted the exit
                        # constraints for this block we're jumping from, so when it's run through it should have the
                        # adjusted types too.
                        if edge.to in visited:
                            entry_constraints, exit_constraints, edges = visited[edge.to]

                            for entry_a, entry_b in to_repropagate.items():
                                entry_constraints.replace(entry_a, entry_b)
                                exit_constraints.replace(entry_a, entry_b)

                            if edge.to.fallthrough_edge is not None:
                                next_.append(edge.to.fallthrough_edge)
                            next_.extend(edge.to.jump_edges)
                            next_.extend(edge.to.exception_edges)

                        finished.add(edge)

            else:
                # Find the start and end offsets for this block, and write it if necessary

                start_offset, end_offset = offsets.get(block, (None, None))
                if start_offset is None:  # Write the block
                    offset, max_label = self._write_block(
                        block, offset, max_label, code, blocks, offsets, jumps_to_adjust, errors,
                    )
                    start_offset, end_offset = offsets[block]

                # print("==================== block %i ====================" % block.label)

                # Update the future edges to visit (and handle exceptions)

                if block.fallthrough_edge is not None:
                    fallthrough_edges.append(block.fallthrough_edge)
                if block.jump_edges:
                    jump_edges.extend(block.jump_edges)
                if block.exception_edges:
                    # explicit = False
                    for exception_edge in block.exception_edges:
                        # if exception_edge.explicit and not explicit:
                        #     instructions_.append(instructions.athrow())  # Generate an athrow instruction
                        #     explicit = True
                        exception_edges.append(exception_edge)

                    exception_handlers_to_adjust.append(tuple(block.exception_edges))

                # Step through the instructions in the block

                start_state = state.copy()
                for offset_, instruction in code.instructions.items():
                    # Check that we are within the bounds of the current block
                    if offset_ < start_offset:
                        continue
                    if offset_ >= end_offset:
                        break

                    instruction.step(offset_, state, errors, True)

                    # print(offset_, "\t", instruction, "\t[ %s ]" % ", ".join(map(str, state.stack)))
                    # print("stack:  [ %s ]" % ", ".join(map(str, state.stack)))
                    # print("locals: { %s }" % ", ".join(["%i=%s" % local for local in state.locals.items()]))

                # Adjust the maximum stack and local depths for the method, if necessary

                if state.max_stack > code.max_stack:
                    code.max_stack = state.max_stack
                if state.max_locals > code.max_locals:
                    code.max_locals = state.max_locals

                visited[block] = (start_state, state, {edge})

            if fallthrough_edges:
                edge = fallthrough_edges.pop(0)
            elif jump_edges:
                edge = jump_edges.pop(0)
            elif exception_edges:
                edge = exception_edges.pop(0)
            else:  # No other edges to visit
                break

            # print(edge)

            block = edge.to
            entry_constraints, exit_constraints, _ = visited[edge.from_]
            if isinstance(edge, ExceptionEdge):
                state = exit_constraints.copy()  # exit_constraints.copy()
                if not edge.explicit:  # Stack should already be in a valid state otherwise
                    state.stack.clear()
                    state.push(Entry(-4, edge.exception.get_type()))
            else:
                state = exit_constraints.copy()

        logger.debug(" - Max stack: %i, max locals: %i." % (code.max_stack, code.max_locals))

        while None in errors:  # Shouldn't have been lazy earlier, oops
            errors.remove(None)

        if errors:
            if not no_verify:
                logger.debug(" - %i error(s) occurred during assembling:" % len(errors))
            else:
                logger.debug(" - Skipping %i error(s) during assembling:" % len(errors))
            for error in errors:
                logger.debug("    - At offset %i (%s): %r" % (error.offset, error.instruction, error.message))
            if not no_verify:
                raise VerifyError(errors)

        # For generating stackmap frames, if applicable, we also need to generate stackmap frames for the exception
        # handers, which is why this variable is defined here.
        frame_offsets: Dict[int, Tuple[Block, State, State]] = {}

        # Adjust exception handler offsets and add them

        if exception_handlers_to_adjust:
            for exception_edges in exception_handlers_to_adjust:
                for edge in exception_edges:
                    entry_constraints, exit_constraints, _ = visited[edge.to]

                    start_offset, end_offset = offsets[edge.from_]
                    handler_offset, _ = offsets[edge.to]

                    # FIXME: Simplify overlapping exception handlers
                    code.exception_table.append(Code.ExceptionHandler(
                        start_offset, end_offset, handler_offset, edge.exception,
                    ))

                    frame_offsets[handler_offset] = (edge.to, entry_constraints, exit_constraints)

            logger.debug(" - Generated %i exception handler(s)." % len(code.exception_table))

        # Adjust jump instruction offsets

        if jumps_to_adjust:
            for offset, edges in jumps_to_adjust.items():
                jump = code.instructions[offset]

                if isinstance(jump, JumpInstruction):
                    entry_constraints, exit_constraints, _ = visited[edges[0].to]
                    target_offset, _ = offsets[edges[0].to]
                    
                    jump.offset = target_offset - offset
                    # Record this for stackmap frame generation later
                    frame_offsets[target_offset] = (edges[0].to, entry_constraints, exit_constraints)

                    # logger.debug(" - Adjusted jump at offset %i to block %i (%s)." % (offset, edges[0].to.label, jump))

                    # if abs(jump.offset) > 32767:
                    #     print(self.method_info, jump)
                    #     input()

                elif jump in (instructions.tableswitch, instructions.lookupswitch):
                    # logger.debug(" - Adjusted switch at offset %i (%s)." % (offset, jump))
                    for edge in edges:
                        entry_constraints, exit_constraints, _ = visited[edge.to]
                        target_offset, _ = offsets[edge.to]

                        frame_offsets[target_offset] = (edge.to, entry_constraints, exit_constraints)
                        offset_delta = target_offset - offset

                        if edge.index is None:
                            jump.default = offset_delta
                            # logger.debug(" - Adjusted switch default at offset %i to block %i (%+i)." % (
                            #     offset, edge.to.label, offset_delta,
                            # ))

                        else:
                            jump.offsets[edge.index] = offset_delta
                            # logger.debug(" - Adjusted switch at offset %i to block %i (index/value %i -> %+i)." % (
                            #     offset, edge.to.label, edge.index, offset_delta,
                            # ))

            logger.debug(" - Adjusted %i jump(s)." % len(jumps_to_adjust))

        compute_frames = compute_frames and not errors

        # Check for dead blocks that were written (this can occur with sort_blocks=True) and fix them by replacing all
        # the instructions in them with nops and then adding an athrow at the end to break control flow. We also need
        # to generate stackmap frames for these.

        if len(visited) != len(blocks):
            # The standard state we'll use for these dead blocks' stackmap frames, since these are never actually 
            # visited, the only proof we need that the athrow is valid is from the stackmap frame, so we can just
            # say that there's a throwable on the stack lol.
            state = State(0)
            state.push(Entry(0, types.throwable_t))

            logger.debug(" - %i dead block(s):" % (len(blocks) - len(visited)))
            for block in blocks.values():
                if not block in visited:
                    start_offset, end_offset = offsets.get(block, (None, None))
                    if start_offset is None:
                        logger.debug("    - Block %i (not written)." % block.label)
                        continue

                    # We only need to be concerned about dead blocks that were actually written
                    logger.debug("    - Block %i (written at offset %i to %i)." % (
                        block.label, start_offset, end_offset,
                    ))

                    if compute_frames:  # We'll nop out the block only if we need to
                        frame_offsets[start_offset] = (block, state, None)

                        last_offset = end_offset - 1
                        offset = start_offset
                        while offset < last_offset:
                            code.instructions[offset] = instructions.nop()
                            offset += 1
                        code.instructions[last_offset] = instructions.athrow()

        # Generate the stackmap frames, if necessary

        if compute_frames and frame_offsets:
            liveness: Dict[Block, Set[int]] = {}  # TODO: Move into liveness.py

            # Compute the liveness of the locals
            exit_blocks = []
            for block in visited:
                if not block.jump_edges and block.fallthrough_edge is None:  # Don't count exception edges
                    exit_blocks.append(block)

            if not exit_blocks:
                # If there are no exits (i.e. infinite loops), just start from the back of the code
                exit_blocks.append(next(reversed(offsets.keys())))

            for exit_block in exit_blocks:
                _, exit_constraints, edges = visited[exit_block]
                next_: List[Edge] = list(edges)
                if None in next_:
                    next_.remove(None) 
                finished: Set[Edge] = set()

                # First compute the liveness for the exit block itself, it shouldn't have been calculated already as it
                # has no backwards edges, so there's no need to check that.
                variables = set()
                for index, read in reversed(exit_constraints.local_accesses):
                    if read:
                        variables.add(index)
                    elif index in variables:
                        variables.remove(index)
                liveness[exit_block] = variables

                while next_:
                    edge = next_.pop(0)
                    if edge is None:
                        continue

                    # print("block_%i -> block_%i %r" % (edge.to.label, edge.from_.label, liveness[edge.to]))

                    _, exit_constraints, edges = visited[edge.from_]

                    changed = False  # Has there been a change in the liveness for this edge?
                    if not edge.from_ in liveness:  # First time computing the liveness for this block
                        liveness[edge.from_] = set()
                        changed = True

                    variables = liveness[edge.from_]
                    variables_before = variables.copy()
                    variables.update(liveness[edge.to])

                    # Already computed liveness for this edge, check there hasn't been another change though
                    if edge in finished:
                        if variables_before == variables:
                            # print("...skipped")
                            continue

                    for index, read in reversed(exit_constraints.local_accesses):
                        if read:
                            variables.add(index)
                        elif index in variables:
                            variables.remove(index)

                    if not changed:
                        if variables_before == variables:  # Check this now, as it's more expensive
                            finished.add(edge)

                    next_.extend(edges)

            stack_map_table = StackMapTable(code)

            prev_offset = -1
            frame_offsets = sorted(frame_offsets.items(), key=operator.itemgetter(0))

            for base_offset, (block, entry_constraints, _) in frame_offsets:
                locals_ = []
                stack = []

                if entry_constraints.locals:
                    live = liveness[block]
                    max_local = 0  # The maxmimum local we'll write up to
                    index = 0

                    while index <= max(entry_constraints.locals):
                        entry = entry_constraints.locals.get(index, None)

                        if entry is not None:
                            # Still need to include uninitialised this types, even if they're unused
                            if index in live or entry.type == types.uninit_this_t:
                                if entry.type == types.this_t:  # Don't write this types, obviously
                                    locals_.append(entry.type.class_)
                                else:
                                    locals_.append(entry.type)
                                max_local = len(locals_)  # Update to the current size of the locals
                                index += entry.type.internal_size
                            else:
                                locals_.append(types.top_t)
                                index += 1

                        else:
                            locals_.append(types.top_t)
                            index += 1

                    locals_ = locals_[:max_local]  # Truncate locals to add implicit tops

                for entry in entry_constraints.stack:
                    if entry.type != types.top_t:
                        if entry.type == types.this_t:
                            stack.append(entry.type.class_)
                        else:
                            stack.append(entry.type)

                # print("offset", base_offset)
                # print(liveness[block])
                # print("stack:  [ %s ]" % ", ".join(map(str, stack)))
                # print("locals: [ %s ]" % ", ".join(map(str, locals_)))

                offset_delta = base_offset - (prev_offset + 1)
                # FIXME: Not full frames every time, cos that's wasteful
                if compress_frames:
                    ...
                else:
                    stack_map_table.stack_frames.append(StackMapTable.FullFrame(
                        offset_delta, tuple(locals_), tuple(stack),
                    ))
                prev_offset = base_offset

            logger.debug(" - Generated %i stackmap frame(s)." % len(stack_map_table.stack_frames))
            code.attributes[stack_map_table.name] = (stack_map_table,)

        return code

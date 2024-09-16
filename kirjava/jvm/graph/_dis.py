#!/usr/bin/env python3

__all__ = (
    "disassemble",
)

import logging
import typing
from io import BufferedIOBase, BytesIO
from os import SEEK_CUR, SEEK_SET
from typing import IO

from .edge import *
from ..fmt.constants import ClassInfo
from ..insns import Instruction
from ..insns.flow import Jsr, Jump as JumpInsn, Ret as RetInsn, Return, Switch as SwitchInsn
from ..insns.misc import Wide
from ...model.types import throwable_t

if typing.TYPE_CHECKING:
    from . import Graph
    from .block import Block
    from ..fmt import ClassFile
    from ..fmt.method import Code

logger = logging.getLogger("ijd.jvm.graph")

_insns: dict[int, type[Instruction]] = {}
_insns_wide: dict[int, type[Instruction]] = {}


def disassemble(
        graph: "Graph", code: "Code", class_file: "ClassFile", stream: IO[bytes] | None,
) -> None:
    """
    JVM bytecode disassembler with some degree of undefined behaviour handling.

    Parameters
    ----------
    graph: Graph
        The control flow graph to build.
    code: Code
        The method code to disassemble.
    class_file: ClassFile
        The class file containing the method.
    stream: IO[bytes] | None
        The binary data stream to disassemble instructions from.
    """

    # Setting up instruction lookup tables if they aren't already set up.
    if not _insns or not _insns_wide:
        subclasses = Instruction.__subclasses__().copy()
        while subclasses:
            subclass = subclasses.pop()
            subclasses.extend(subclass.__subclasses__())
            try:
                if subclass.opcode is not None:
                    if not subclass.mutate_w:
                        _insns[subclass.opcode] = subclass
                    else:
                        _insns_wide[subclass.opcode] = subclass
            except AttributeError:
                ...  # Some instructions don't have opcodes as they are considered "abstract".

    if stream is not None:
        stream.seek(code.offset, SEEK_SET)
        stream = CodeIOWrapper(stream)
    else:
        logger.debug("No CF stream provided, disassembly may be incomplete.")
        stream = BytesIO(code.code)

    blocks = graph.blocks
    edges_out = graph.edges_out
    edges_in  = graph.edges_in

    disassembled = 0  # Final number of bytes disassembled, for debug (also cos it sounds cool).

    pure: dict[int, Instruction] = {}  # "Pure" code section (valid bytecode area).
    data: dict[int, Instruction | None] = {}  # Data areas interpreted as instructions.
    oom:  dict[int, Instruction | None] = {}  # Out of method instructions.

    valid = range(0, len(code.code))  # Valid in-method code range.

    visited:  set[int] = set()
    splits:   set[int] = set()
    targets: list[int] = []

    for handler in code.exception_table:
        splits.add(handler.start_pc)
        splits.add(handler.end_pc)
        targets.append(handler.handler_pc)

    # Don't split at entry block. We'll only note down offset 0 as a split if it's a jump target.
    splits.discard(0)

    # ------------------------------------------------------------ #
    #                       Read instructions                      #
    # ------------------------------------------------------------ #

    offset = 0
    section = pure

    while True:
        visited.add(offset)
        opcode, = stream.read(1)

        insn_type = _insns.get(opcode)
        if insn_type is None:
            raise ValueError("unknown opcode 0x%x at offset %i" % (opcode, offset))
        instruction = insn_type.read(stream, class_file)

        if isinstance(instruction, Wide):
            # We'll check if the next instruction has a wide mutation in order to essentially "merge" the `wide`
            # instruction that prefixes it with itself. If it does not have a wide mutation, we'll just continue reading.
            # This may simply be because the bytecode has `wide` instructions randomly in it.
            opcode, = stream.read(1)
            insn_type = _insns_wide.get(opcode)
            if insn_type is not None:
                instruction = insn_type.read(stream, class_file)
            else:
                stream.seek(-1, SEEK_CUR)  # Move back one byte as we attempted to read an opcode.

        instruction.offset = offset
        section[offset] = instruction

        split = False
        fallthrough = True

        if isinstance(instruction, JumpInsn):
            split = True
            fallthrough = instruction.conditional or isinstance(instruction, Jsr)
            if instruction.delta is not None:
                targets.append(offset + instruction.delta)                
        elif isinstance(instruction, SwitchInsn):
            split = True
            fallthrough = False
            targets.append(offset + instruction.default)
            targets.extend(offset + offset_ for offset_ in instruction.offsets.values())

        offset = stream.tell()

        if split:
            splits.add(offset)

        # Continue disassembling if we're still in the "pure" code area.
        if section is pure:
            if offset in valid:
                continue
            disassembled += offset
        # Continue disassembling if we're not at an already disassembled offset AND the current instruction does not
        # break control flow. This is necessary so that non-"pure" code areas do not result in us disassembling data that
        # will never be interpreted as code.
        elif not offset in visited and fallthrough:
            continue
        else:
            # We've fallen back into the code, so we'll need to ensure there is a split at this offset.
            splits.add(offset)
            section[offset] = None

        # TODO: Add invalid jump bytes to disassembled.

        splits.update(targets)  # Ensuring that jump targets result in block generation at the target location.
        while targets:
            offset = targets.pop()
            # Really wishing for a do-while loop right now. How cruel that the only time I can actually find a use for it
            # is in Python code.
            if not offset in visited:
                break
        else:
            break
        stream.seek(offset, SEEK_SET)

        if offset in valid:
            section = data
            logger.debug("Jump into data section at offset %i.", offset)
        else:
            # section = oom
            logger.debug("Jump out of method at offset %i.", offset)
            raise NotImplementedError("disassembly from OOM offset %i" % offset)

    # ------------------------------------------------------------ #
    #              Create basic blocks and jump edges              #
    # ------------------------------------------------------------ #

    starts: dict[int, "Block"] = {0: graph.entry, **{offset: graph.block() for offset in sorted(splits)}}
    ends:   dict["Block", int] = {}  # Used for faster exception handler edge generation.
    can_throw: set["Block"] = set()

    for section in (pure, data, oom):
        if not section:
            continue
        block = starts[min(section)]
        fallthrough = True
        fallthrough_insn: Instruction | None = None

        for offset, instruction in section.items():
            new_block = starts.get(offset)
            if new_block is not None and block is not new_block:
                ends[block] = offset
                if fallthrough:
                    edge = Fallthrough(block, new_block, fallthrough_insn)
                    edges_out[block].add(edge)
                    edges_in[new_block].add(edge)
                    fallthrough_insn = None
                block = new_block

            if instruction is None:  # Essentially a note to add a fallthrough, namely for non-pure sections.
                continue

            if instruction.can_throw:
                can_throw.add(block)

            if isinstance(instruction, JumpInsn):
                fallthrough = instruction.conditional or isinstance(instruction, Jsr)
                if fallthrough:
                    fallthrough_insn = instruction

                if instruction.delta is not None:
                    target = starts.get(offset + instruction.delta, graph.opaque)
                elif isinstance(instruction, Return):
                    target = graph.return_
                # Interesting point is that we don't actually know where throws will jump right now, so we can call it
                # an opaque jump, alongside the `ret` and `ret_w` instructions of course.
                else:
                    target = graph.opaque

                if isinstance(instruction, RetInsn):
                    edge = Ret(block, target, instruction)
                else:
                    edge = Jump(block, target, instruction)
                edges_out[block].add(edge)
                edges_in[target].add(edge)

            elif isinstance(instruction, SwitchInsn):
                fallthrough = False
                target = starts.get(offset + instruction.default, graph.opaque)
                edge = Switch(block, target, instruction, None)
                edges_out[block].add(edge)
                edges_in[target].add(edge)
                for value, delta in instruction.offsets.items():
                    target = starts.get(offset + delta, graph.opaque)
                    edge = Switch(block, target, instruction, value)
                    edges_out[block].add(edge)
                    edges_in[target].add(edge)

            else:
                block.insns.append(instruction)
                # If a new block is suddenly created on the next iteration, we want a fallthrough to be generated too.
                fallthrough = True

    # Conserve the fact that the entry block should dominate all other blocks, and should also be the entry point of the
    # method. It will not have been populated with instructions if there was a jump back to offset 0.
    if not graph.entry.insns and not edges_out[graph.entry]:
        edge = Fallthrough(graph.entry, starts[0])
        edges_out[graph.entry].add(edge)
        edges_in[starts[0]].add(edge)

    for block in blocks.copy():
        if block.insns or edges_in[block] or edges_out[block]:
            continue
        elif block in {graph.return_, graph.rethrow, graph.opaque}:
            continue
        blocks.remove(block)

    # Sanity checks, I make mistakes quite often :p.
    assert graph.entry in graph.blocks, "entry block is not present in graph"
    assert not edges_in[graph.entry], "entry block has in edges"

    # ------------------------------------------------------------ #
    #                    Create exception edges                    #
    # ------------------------------------------------------------ #

    handles_throwable: set["Block"] = set()

    # TODO: Merge handlers with same catch types.

    # for start, source in starts.items():
    #     for index, handler in enumerate(code.exception_table):
    #         if handler.start_pc <= start < handler.end_pc:
    #             target = starts[handler.handler_pc]
    #             source.edges.append(Catch(source, target, throwable_t, index))
    # Much, much faster exception table handling algorithm compared to above.
    for index, handler in enumerate(code.handlers):
        source = starts[handler.start_pc]
        target = starts[handler.handler_pc]

        if handler.catch_type is None:
            catch_type = throwable_t
            is_throwable = True
        elif isinstance(handler.catch_type.info, ConstantClassInfo):  # Weird PyCharm bug?
            catch_type = handler.catch_type.info.unwrap().as_rtype()
            is_throwable = catch_type is throwable_t
        else:
            raise NotImplementedError("handler with catch type %r" % handler.catch_type)

        # FIXME: Disassembler edge case where the last block may not have a recorded end offset due to having only a
        #        jump in it. This check prevents a crash, but slows down the code. The offset should just be calculated
        #        above and added into the ends dictionary.
        end = ends.get(source, handler.end_pc)
        while end is not None and end <= handler.end_pc:
            if is_throwable:
                handles_throwable.add(source)

            if source in can_throw:
                edge = Catch(source, target, catch_type, index)
                edges_out[source].add(edge)
                edges_in[target].add(edge)

            source = starts[end]
            end = ends.get(source)

    # Finally, we'll add an edge from every block that doesn't handle java.lang.Throwable to the rethrow block.
    for block in blocks:
        if block in handles_throwable or not block in can_throw:
            continue
        # Last priority handler, 65536 is beyond the range of the exception table so will never be used.
        edge = Catch(block, graph.rethrow, throwable_t, 65536)
        edges_out[block].add(edge)
        edges_in[graph.rethrow].add(edge)

    # Mfw I realise that counting the edges in the graph is actually kinda hard.
    all_edges = set()
    for edges in graph.edges_out.values():
        all_edges.update(edges)
    logger.debug("Disassembled %i bytes to %i block(s) and %i edge(s).", disassembled, len(graph.blocks), len(all_edges))

    # for block in graph.blocks:
    #     print("========== %s ==========" % block)
    #     for ref in block.insns:
    #         print(ref)
    #     for edge in block.edges:
    #         print(edge)


class CodeIOWrapper(BufferedIOBase):
    """
    A stream wrapper for code in a method, so that the offset is correct as per the
    base of the code, rather than the base of the class file.

    Attributes
    ----------
    delegate: IO[bytes]
        The underlying stream to read from.
    start: int
        The start offset.
    """

    __slots__ = ("delegate", "start")

    def __init__(self, delegate: IO[bytes]) -> None:
        self.delegate = delegate
        self.start = delegate.tell()

    def tell(self) -> int:
        return self.delegate.tell() - self.start

    def seek(self, offset: int, whence: int = ...) -> int:
        if whence == SEEK_SET:
            offset += self.start
        return self.delegate.seek(offset, whence)

    def read(self, size: int | None = ...) -> bytes:
        return self.delegate.read(size)

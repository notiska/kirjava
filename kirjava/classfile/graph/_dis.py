#!/usr/bin/env python3

__all__ = (
    "disassemble",
)

from ..fmt.constants import UTF8Info

"""
The JVM bytecode disassembler.
"""

import typing
from io import BytesIO

from .edge import Catch, Edge, Fallthrough, Jump as JumpEdge, Ret as RetEdge, Switch as SwitchEdge
from ..fmt.attribute import RawInfo
from ..fmt.method import Code, MethodInfo
from ..insns import Instruction
from ..insns.flow import Jsr, Jump as JumpInsn, Ret as RetInsn, Return, Switch as SwitchInsn
from ...meta import Metadata

if typing.TYPE_CHECKING:
    from . import Graph
    from .block import Block
    from ..fmt import ClassFile


def disassemble(graph: "Graph", method: MethodInfo, cf: "ClassFile") -> Metadata:
    """
    JVM bytecode disassembler.

    Parameters
    ----------
    graph: Graph
        The graph to build.
    method: MethodInfo
        The method to disassemble.
    cf: ClassFile
        The class file that the method belongs to.

    Returns
    -------
    Metadata
        Any metadata generated during disassembly.
    """

    meta = Metadata(__name__, graph)

    if method.is_abstract or method.is_native:
        meta.info("access", "Method is abstract and/or native.")
        return meta

    code: Code | RawInfo | None = None

    for attribute in method.attributes:
        if isinstance(attribute, Code):
            code = attribute
            break
        elif (  # Otherwise, it could be an improperly parsed code attribute.
            isinstance(attribute, RawInfo) and
            isinstance(attribute.name, UTF8Info) and
            attribute.name.value == Code.tag
        ):
            code = attribute
            break

    if not isinstance(code, Code):  # code is None:
        meta.error("nocode", "Method has no code attribute.")
        return meta

    # blocks = graph.blocks
    edges_out = graph.edges_out
    edges_in = graph.edges_in

    # ------------------------------------------------------------ #
    #                       Find flow splits                       #
    # ------------------------------------------------------------ #

    edge: Edge  # To make mypy happy.

    stream = BytesIO()
    offset = 0

    insns: dict[int, "Instruction"] = {}
    splits:  set[int] = set()
    targets: set[int] = set()
    stops:   set[int] = set()

    for handler in code.handlers:
        splits.add(handler.start_pc)
        splits.add(handler.end_pc)
        targets.add(handler.handler_pc)
        # targets.append(handler.handler_pc)

    for instruction in code.instructions:
        # Unfortunately, we can't actually trust that instruction.offset will be correct as it's only really counted as
        # metadata, so we need to re-compute the instruction offsets ourselves, here.
        instruction.write(stream, cf.pool)
        insns[offset] = instruction

        split_ = False  # mypy scoping. Whatever.
        stop = False

        if isinstance(instruction, JumpInsn):
            split_ = True
            # jsrs are treated specially because we need to know where to return to, if a ret is encountered. So they
            # have a pseudo-fallthrough in the graph.
            # TODO: Mark fallthrough as symbolic.
            stop = not instruction.conditional and not isinstance(instruction, Jsr)
            if instruction.delta is not None:
                targets.add(offset + instruction.delta)
        elif isinstance(instruction, SwitchInsn):
            split_ = True
            stop = True
            targets.add(offset + instruction.default)
            targets.update(offset + branch for branch in instruction.offsets.values())

        offset = stream.tell()

        if split_:
            splits.add(offset)
        if stop:
            stops.add(offset)

    # TODO: Debug information such as LNT, LVT and LVTT.

    # ------------------------------------------------------------ #
    #                 Create blocks and jump edges                 #
    # ------------------------------------------------------------ #

    blocks: dict[int, tuple["Block", int]] = {}

    block = graph.entry
    prev = graph.entry
    last = 0

    # We'll only add the entry block if we know that there are no back edges to offset 0. If there are, this means that
    # the entry block would not dominate all other blocks, and therefore would not be the entry block.
    if not 0 in targets:
        blocks[0] = (graph.entry, 0)
    else:
        stops.discard(0)

    # Return instructions at the end will add the final offset to the splits, which isn't technically correct, so we'll
    # manually remove that.
    splits.discard(offset)
    splits.update(targets)

    for split in sorted(splits):
        if not split in insns:
            raise NotImplementedError(f"split at data/oom offset {split}")
        blocks[last] = (block, split)
        prev = block
        block = graph.block()
        last = split
        if not split in stops:
            edge = Fallthrough(prev, block)
            edges_out[prev].add(edge)
            edges_in[block].add(edge)

    if splits:  # The end offset of the last block is the offset we finished disassembling at.
        blocks[split] = (block, offset)

    prev = graph.entry

    for offset, instruction in insns.items():
        block, _ = blocks.get(offset) or (prev, 0)
        prev = block

        if isinstance(instruction, JumpInsn):
            if instruction.delta is not None:
                edge = JumpEdge(block, blocks[offset + instruction.delta][0], instruction)
            elif isinstance(instruction, Return):
                edge = JumpEdge(block, graph.return_, instruction)
            elif isinstance(instruction, RetInsn):
                edge = RetEdge(block, graph.opaque, instruction)
            else:
                edge = JumpEdge(block, graph.opaque, instruction)

            edges_out[edge.source].add(edge)
            edges_in[edge.target].add(edge)

        elif isinstance(instruction, SwitchInsn):
            edge = SwitchEdge(block, blocks[offset + instruction.default][0], instruction, None)
            edges_out[edge.source].add(edge)
            edges_in[edge.target].add(edge)
            for value, branch in instruction.offsets.items():
                edge = SwitchEdge(block, blocks[offset + branch][0], instruction, value)
                edges_out[edge.source].add(edge)
                edges_in[edge.target].add(edge)

        else:
            block.insns.append(instruction)

    # ------------------------------------------------------------ #
    #                    Create exception edges                    #
    # ------------------------------------------------------------ #

    for index, handler in enumerate(code.handlers):
        block, end = blocks[handler.start_pc]
        target, _ = blocks[handler.handler_pc]

        while True:  # Wishing for a do-while loop right now.
            edge = Catch(block, target, handler.class_, index)
            edges_out[block].add(edge)
            edges_in[target].add(edge)
            if end == handler.end_pc:
                break
            block, end = blocks[end]

    # for block, _ in blocks.values():
    #     print("%s:" % block)
    #     for instruction in block.insns:
    #         print("  %s" % instruction)
    #     for edge in edges_out[block]:
    #         print(" %s" % edge)

    return meta

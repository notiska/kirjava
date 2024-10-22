#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "disassemble",
)

from ..fmt.constants import UTF8Info

"""
The JVM bytecode disassembler.
"""

import sys
import typing
from io import BytesIO
from operator import itemgetter
from typing import TypeVar

from .block import MutableBlock
from .edge import Catch, Edge, Fallthrough, Jump as JumpEdge, Ret as RetEdge, Switch as SwitchEdge
from ..fmt import ClassFile, ConstPool, RawInfo
from ..fmt.method import Code, MethodInfo
from ..insns import Instruction
from ..insns.flow import Jsr, Jump as JumpInsn, Ret as RetInsn, Return, Switch as SwitchInsn
from ...backend import Result

if typing.TYPE_CHECKING:
    from . import Graph

T = TypeVar("T", bound="Graph")  # To "prove" to mypy that the type in is the same type out, as we can't use Self here.


def disassemble(graph: T, method: MethodInfo, cf: ClassFile | None) -> Result[T]:
    """
    JVM bytecode disassembler.

    Parameters
    ----------
    graph: T
        The graph to build.
    method: MethodInfo
        The method to disassemble.
    cf: ClassFile | None
        The class file that the method belongs to.
    """

    with Result[T].meta(__name__) as result:
        if method.is_abstract or method.is_native:
            return result.err(ValueError(f"method {method!s} is abstract and/or native"))

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
            return result.err(ValueError(f"method {method!s} has no code attribute"))

        blocks = graph._blocks
        edges_out = graph._edges_out
        edges_in = graph._edges_in

    # ------------------------------------------------------------ #
    #                       Find flow splits                       #
    # ------------------------------------------------------------ #

        edge: Edge  # To make mypy happy.

        # FIXME: Added indices won't be 100% accurate which could result in minor differences.
        pool = cf.pool if cf is not None else ConstPool()
        stream = BytesIO()
        offset = 0

        insns: dict[int, "Instruction"] = {}
        splits: dict[int, int | None] = {}
        targets: set[int] = set()
        stops:   set[int] = set()

        for handler in code.handlers:
            splits[handler.start_pc] = None
            splits[handler.end_pc] = None
            targets.add(handler.handler_pc)
            # targets.append(handler.handler_pc)

        for instruction in code.insns:
            # Unfortunately, we can't actually trust that instruction.offset will be correct as it's only really counted
            # as metadata, so we need to re-compute the instruction offsets ourselves, here.
            instruction.write(stream, pool)
            insns[offset] = instruction

            split_ = False  # mypy scoping. Whatever.
            prior: int | None = None

            if isinstance(instruction, JumpInsn):
                split_ = True
                # jsrs are treated specially because we need to know where to return to, if a ret is encountered. So
                # they have a pseudo-fallthrough in the graph.
                if instruction.conditional or isinstance(instruction, Jsr):
                    prior = offset
                if instruction.delta is not None:
                    targets.add(offset + instruction.delta)
            elif isinstance(instruction, SwitchInsn):
                split_ = True
                targets.add(offset + instruction.default)
                targets.update(offset + branch for branch in instruction.offsets.values())

            offset = stream.tell()

            if split_:
                splits[offset] = prior
                if prior is None:
                    stops.add(offset)

        # TODO: Debug information such as LNT, LVT and LVTT.

    # ------------------------------------------------------------ #
    #                 Create blocks and jump edges                 #
    # ------------------------------------------------------------ #

        bounds: dict[int, tuple[MutableBlock, int]] = {}

        block = graph.entry
        label = block.label + 1
        prev = graph.entry
        last = 0

        # We'll only add the entry block if we know that there are no back edges to offset 0. If there are, this means
        # that the entry block would not dominate all other blocks, and therefore would not be the entry block.
        if not 0 in targets:
            bounds[0] = (graph.entry, 0)
        else:
            stops.discard(0)

        # Return instructions at the end will add the final offset to the splits, which isn't technically correct, so
        # we'll manually remove that.
        splits.pop(offset, None)
        for split in targets:
            splits.setdefault(split, None)  # Be careful not to overwrite any existing split-fallthrough associations.

        for split, prior in sorted(splits.items(), key=itemgetter(0)):
            if not split in insns:
                raise NotImplementedError(f"split at data/oom offset {split}")
            bounds[last] = (block, split)
            prev = block

            block = MutableBlock(label)
            blocks[label] = block
            label += 1

            last = split
            if not split in stops:
                if prior is not None:
                    instruction = insns[prior]
                    assert isinstance(instruction, JumpInsn), "fallthrough with flow break at non-jump instruction"
                    edge = Fallthrough(prev, block, instruction)
                else:
                    edge = Fallthrough(prev, block)
                edges_out[prev].add(edge)
                edges_in[block].add(edge)

        if splits:  # The end offset of the last block is the offset we finished disassembling at.
            bounds[split] = (block, offset)

        prev = graph.entry

        for offset, instruction in insns.items():
            block, _ = bounds.get(offset) or (prev, 0)
            prev = block

            if isinstance(instruction, JumpInsn):
                if instruction.delta is not None:
                    edge = JumpEdge(block, bounds[offset + instruction.delta][0], instruction)
                elif isinstance(instruction, Return):
                    edge = JumpEdge(block, graph.return_, instruction)
                elif isinstance(instruction, RetInsn):
                    edge = RetEdge(block, graph.opaque, instruction)
                else:
                    edge = JumpEdge(block, graph.opaque, instruction)

                edges_out[edge.source].add(edge)
                edges_in[edge.target].add(edge)

            elif isinstance(instruction, SwitchInsn):
                edge = SwitchEdge(block, bounds[offset + instruction.default][0], instruction, None)
                edges_out[edge.source].add(edge)
                edges_in[edge.target].add(edge)
                for value, branch in instruction.offsets.items():
                    edge = SwitchEdge(block, bounds[offset + branch][0], instruction, value)
                    edges_out[edge.source].add(edge)
                    edges_in[edge.target].add(edge)

            else:
                block._insns.append(instruction)

    # ------------------------------------------------------------ #
    #                    Create exception edges                    #
    # ------------------------------------------------------------ #

        for index, handler in enumerate(code.handlers):
            block, end = bounds[handler.start_pc]
            target, _ = bounds[handler.handler_pc]

            while True:  # Wishing for a do-while loop right now.
                edge = Catch(block, target, handler.class_, index)
                edges_out[block].add(edge)
                edges_in[target].add(edge)
                if end == handler.end_pc:
                    break
                block, end = bounds[end]

        # for block, _ in bounds.values():
        #     print("%s:" % block)
        #     for instruction in block.insns:
        #         print("  %s" % instruction)
        #     for edge in edges_out[block]:
        #         print(" %s" % edge)

        return result.ok(graph)
    return result

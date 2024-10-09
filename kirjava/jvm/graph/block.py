#!/usr/bin/env python3

__all__ = (
    "Block",
)

import logging
import typing
from typing import Iterable

if typing.TYPE_CHECKING:
    from ..insns import Instruction

logger = logging.getLogger("ijd.jvm.graph.block")


class Block:
    """
    An extended basic block containing JVM instructions.

    Attributes
    ----------
    LABEL_ENTRY: int
        The label of all entry blocks.
    LABEL_RETURN: int
        The label of all return blocks.
    LABEL_RETHROW: int
        The label of all rethrow blocks.
    LABEL_OPAQUE: int
        The label of all opaque blocks.

    label: int
        A unique label for this block.
    insns: list[Instruction]
        An ordered list of the instructions in this block.

    Methods
    -------
    trace(frame: Frame) -> list[Trace.Step]
        Traces the execution of this block.
    """

    __slots__ = ("label", "insns")

    LABEL_ENTRY   = 0
    LABEL_RETURN  = -1
    LABEL_RETHROW = -2
    LABEL_OPAQUE  = -3

    def __init__(self, label: int, insns: Iterable["Instruction"] | None = None) -> None:
        self.label = label
        self.insns: list["Instruction"] = []
        if insns is not None:
            self.insns.extend(insns)

    def __repr__(self) -> str:
        return "<Block(label=%i, insns=[%s])>" % (self.label, ", ".join(map(str, self.insns)))

    def __str__(self) -> str:
        if self.label == self.LABEL_ENTRY:
            return "block_entry"
        elif self.label == self.LABEL_RETURN:
            return "block_return"
        elif self.label == self.LABEL_RETHROW:
            return "block_rethrow"
        elif self.label == self.LABEL_OPAQUE:
            return "block_opaque"
        return "block_%i" % self.label

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     """
    #     Traces the execution of this block.
    #
    #     Parameters
    #     ----------
    #     frame: Frame
    #         The current frame.
    #     state: State
    #         The state to add trace information to.
    #     """
    #
    #     steps = 0
    #     for instruction in self.insns:
    #         if instruction.trace(frame, state) is not None:
    #             steps += 1
    #         if frame.thrown is not None:
    #             break
    #
    #     logger.debug("Traced %s (%i insns) in %i step(s).", self, len(self.insns), steps)

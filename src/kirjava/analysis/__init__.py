#!/usr/bin/env python3

__all__ = (
    "graph", "ir", "reconstruct", "trace",
    "VerfiyError", "Error",
    "Block", "Edge", "Graph",
    "ExceptionEdge", "FallthroughEdge", "JumpEdge",
)

"""
Bytecode analysis stuff.
"""

from typing import List, Tuple

from ..classfile.instructions import Instruction


class VerifyError(Exception):
    """
    An exception to throw when verification fails.
    """

    def __init__(self, errors: List["Error"]) -> None:
        super().__init__("%i verification error(s)." % len(errors))

        self.errors = errors.copy()


class Error:
    """
    An error that has occurred during the bytecode analysis, typically due to invalid bytecode.
    """

    def __init__(self, offset: int, instruction: Instruction, *message: Tuple[object, ...]) -> None:
        """
        :param offset: The bytecode offset that the error occurred at.
        :param instruction: The instruction that caused the error.
        :param message: Information about the error that occurred.
        """

        self.offset = offset
        self.instruction = instruction
        self.message = " ".join(map(str, message))

    def __repr__(self) -> str:
        return "<Error(offset=%i, instruction=%r, message=%r) at %x>" % (self.offset, self.instruction, self.message)

    def __str__(self) -> str:
        return "error at offset %i (%s): %r" % (self.offset, self.instruction, self.message)


from . import graph, ir, trace, reconstruct
from .graph import *
from .ir import *

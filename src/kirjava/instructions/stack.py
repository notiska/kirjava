#!/usr/bin/env python3

__all__ = (
    "PopInstruction", "Pop2Instruction",
    "DupInstruction", "DupX1Instruction", "DupX2Instruction",
    "Dup2Instruction", "Dup2X1Instruction", "Dup2X2Instruction",
    "SwapInstruction",
)

"""
Instructions that manipulate values on the stack.
"""

import typing

from . import Instruction

if typing.TYPE_CHECKING:
    from ..analysis import Context


class PopInstruction(Instruction):
    """
    Pops a value off of the stack.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        context.pop()


class Pop2Instruction(Instruction):
    """
    Pops two values off of the stack.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        context.pop(2)


class DupInstruction(Instruction):
    """
    Duplicates a value on the stack.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        context.frame.dup()


class DupX1Instruction(DupInstruction):
    """
    Duplicates a value on the stack and places it two values down.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        context.frame.dup(1, 1)


class DupX2Instruction(DupInstruction):
    """
    Duplicates a value on the stack and places it three values down.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        context.frame.dup(1, 2)


class Dup2Instruction(Instruction):
    """
    Duplicates two values on the stack.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        context.frame.dup(2)


class Dup2X1Instruction(Dup2Instruction):
    """
    Duplicates two values on the stack and places them one value down.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        context.frame.dup(2, 1)


class Dup2X2Instruction(Dup2Instruction):
    """
    Duplicates two values on the stack and places them two values down.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        context.frame.dup(2, 2)


class SwapInstruction(Instruction):
    """
    Swaps the top two values on the stack.
    """

    __slots__ = ()

    def trace(self, context: "Context") -> None:
        context.frame.swap()

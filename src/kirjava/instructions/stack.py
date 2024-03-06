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

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> DeclareStatement | None:
    #     if not delta.dups:
    #         return None
    #
    #     entry = tuple(delta.dups.keys())[0]
    #     if entry.type == types.top_t:  # Don't accept these as valid types, and therefore don't lift them
    #         return None
    #
    #     value = associations[entry]
    #     variable = Variable(scope.variable_id, entry.type)
    #     scope.declare(variable)
    #     associations[entry] = variable
    #
    #     return DeclareStatement(variable, value)


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

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> CompoundStatement | DeclareStatement | None:
    #     if not delta.dups:
    #         return None
    #
    #     statements = []
    #     for entry in delta.dups.keys():
    #         if entry.type == types.top_t:
    #             continue
    #         value = associations[entry]
    #         variable = Variable(scope.variable_id, entry.type)
    #         scope.declare(variable)
    #         associations[entry] = variable
    #         statements.append(DeclareStatement(variable, value))
    #
    #     if len(statements) == 1:
    #         return statements[0]
    #     elif statements:
    #         return CompoundStatement(statements)
    #     return None


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

#!/usr/bin/env python3

"""
Instructions that manipulate values on the stack.
"""

from typing import Dict, Optional, Union

from . import Instruction
from ... import types
from ...abc import Value
from ...analysis.ir.variable import Scope, Variable
from ...analysis.trace import Entry, Frame, FrameDelta
from ...instructions.ir.other import CompoundStatement
from ...instructions.ir.variable import DeclareStatement


class PopInstruction(Instruction):
    """
    Pops a value off of the stack.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        frame.pop()


class Pop2Instruction(Instruction):
    """
    Pops two values off of the stack.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        frame.pop(2)


class DupInstruction(Instruction):
    """
    Duplicates a value on the stack.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        frame.dup()

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> Optional[DeclareStatement]:
        if not delta.dups:
            return None

        entry = tuple(delta.dups.keys())[0]
        if entry.type == types.top_t:  # Don't accept these as valid types, and therefore don't lift them
            return None

        value = associations[entry]
        variable = Variable(scope.variable_id, entry.type)
        scope.declare(variable)
        associations[entry] = variable

        return DeclareStatement(variable, value)


class DupX1Instruction(DupInstruction):
    """
    Duplicates a value on the stack and places it two values down.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        frame.dup(displace=1)


class DupX2Instruction(DupInstruction):
    """
    Duplicates a value on the stack and places it three values down.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        frame.dup(displace=2)


class Dup2Instruction(Instruction):
    """
    Duplicates two values on the stack.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        frame.dup2()

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> Union[CompoundStatement, DeclareStatement, None]:
        if not delta.dups:
            return None

        statements = []
        for entry in delta.dups.keys():
            if entry.type == types.top_t:
                continue
            value = associations[entry]
            variable = Variable(scope.variable_id, entry.type)
            scope.declare(variable)
            associations[entry] = variable
            statements.append(DeclareStatement(variable, value))

        if len(statements) == 1:
            return statements[0]
        elif statements:
            return CompoundStatement(statements)
        return None


class Dup2X1Instruction(Dup2Instruction):
    """
    Duplicates two values on the stack and places them three values down.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        frame.dup2(displace=1)


class Dup2X2Instruction(Dup2Instruction):
    """
    Duplicates two values on the stack and places them four values down.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        frame.dup2(displace=2)


class SwapInstruction(Instruction):
    """
    Swaps the top two values on the stack.
    """

    __slots__ = ()

    def trace(self, frame: Frame) -> None:
        frame.swap()

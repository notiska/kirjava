#!/usr/bin/env python3

"""
Instructions that manipulate values on the stack.
"""

from abc import ABC
from typing import List

from . import Instruction
from ...abc import Error, Source, TypeChecker
from ...analysis.trace import State


class PopInstruction(Instruction, ABC):
    """
    Pops a value off of the stack.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_category(entry.type, 1):
            errors.append(Error(
                source, "can't pop category 2 type %s (via %s)" % (entry.type, entry.source), "use pop2 instead",
            ))


class Pop2Instruction(Instruction, ABC):
    """
    Pops two values off of the stack.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        state.pop(source, 2)


class DupInstruction(Instruction, ABC):
    """
    Duplicates a value on the stack.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.stack[-1]
        if not checker.check_category(entry.type, 1):
            errors.append(Error(
                source, "can't dup category 2 type %s (via %s)" % (entry.type, entry.source), "use dup2 instead",
            ))
        state.stack.append(entry)


class DupX1Instruction(Instruction, ABC):
    """
    Duplicates a value on the stack and places it two values down.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.stack[-1]
        if not checker.check_category(entry.type, 1):
            errors.append(Error(source, "can't dup_x1 category 2 type %s (via %s)" % (entry.type, entry.source)))
        if not checker.check_category(state.stack[-2].type, 1):
            errors.append(Error(
                source,
                "can't dup_x1 around category 2 type %s (via %s)" % (state.stack[-2].type, state.stack[-2].source),
            ))
        state.stack.insert(-2, entry)


class DupX2Instruction(Instruction, ABC):
    """
    Duplicates a value on the stack and places it three values down.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.stack[-1]
        if not checker.check_category(entry.type, 1):
            errors.append(Error(source, "can't dup_x2 category 2 type %s (via %s)" % (entry.type, entry.source)))
        if not checker.check_category(state.stack[-3].type, 1):
            errors.append(Error(
                source, "can't dup_x2 around category 2 type %s (via %s)" % (state.stack[-3].type, state.stack[-1].source),
            ))
        state.stack.insert(-3, entry)


class Dup2Instruction(Instruction, ABC):
    """
    Duplicates two values on the stack.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        state.stack.append(state.stack[-2])
        state.stack.append(state.stack[-2])  # Equivalent to state.stack[-1] before the first push


class Dup2X1Instruction(Instruction, ABC):
    """
    Duplicates two values on the stack and places them three values down.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry_a, entry_b = state.stack[-2:]
        if not checker.check_category(entry_a.type, 1):
            errors.append(Error(source, "can't dup2_x1 category 2 type %s (via %s)" % (entry_a.type, entry_a.source)))
        if not checker.check_category(state.stack[-3].type, 1):
            errors.append(Error(
                source,
                "can't dup2_x1 around category 2 type %s (via %s)" % (state.stack[-3].type, state.stack[-3].source),
            ))
        state.stack.insert(-3, entry_a)
        state.stack.insert(-3, entry_b)


class Dup2X2Instruction(Instruction, ABC):
    """
    Duplicates two values on the stack and places them four values down.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry_a, entry_b = state.stack[-2:]
        if not checker.check_category(entry_a.type, 1):
            errors.append(Error(source, "can't dup2_x2 category 2 type %s (via %s)" % (entry_a.type, entry_a.source)))
        if not checker.check_category(state.stack[-4].type, 1):
            errors.append(Error(
                source,
                "can't dup2_x2 around category 2 type %s (via %s)" % (state.stack[-4].type, state.stack[-4].source),
            ))
        state.stack.insert(-4, entry_a)
        state.stack.insert(-4, entry_b)


class SwapInstruction(Instruction, ABC):
    """
    Swaps the top two values on the stack.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.stack[-1]
        if not checker.check_category(entry.type, 1):
            errors.append(Error(source, "can't swap category 2 type %s (via %s)" % (entry.type, entry.source)))
        if not checker.check_category(state.stack[-2].type, 1):
            errors.append(Error(
                source, "can't swap category 2 type %s (via %s)" % (state.stack[-2].type, state.stack[-2].source),
            ))
        state.stack[-1] = state.stack[-2]
        state.stack[-2] = entry

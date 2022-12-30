#!/usr/bin/env python3

"""
Arithmetic related instructions.
"""

from abc import ABC
from typing import List

from . import Instruction
from ... import types
from ...abc import Error, Source, TypeChecker
from ...analysis.trace import State
from ...types import BaseType


class UnaryOperationInstruction(Instruction, ABC):
    """
    A unary arithmetic operation.
    """

    type_: BaseType = ...

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry, *_ = state.pop(source, self.type_.internal_size, tuple_=True)
        if not checker.check_merge(self.type_, entry.type):
            errors.append(Error(
                source, "expected type %s" % self.type_, "got %s (via %s)" % (entry.type, entry.source),
            ))
        state.push(source, checker.merge(self.type_, entry.type), parents=(entry,))


class BinaryOperationInstruction(Instruction, ABC):
    """
    A binary arithmetic operation.
    """

    type_a: BaseType = ...
    type_b: BaseType = ...

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry_a, *_ = state.pop(source, self.type_a.internal_size, tuple_=True)
        entry_b, *_ = state.pop(source, self.type_b.internal_size, tuple_=True)

        valid = entry_b.type
        if not checker.check_merge(self.type_b, entry_b.type):
            errors.append(Error(
                source, "expected type %s" % self.type_b, "got %s (via %s)" % (entry_b.type, entry_b.source),
            ))
            valid = entry_a.type
        if not checker.check_merge(self.type_a, entry_a.type):
            errors.append(Error(
                source, "expected type %s" % self.type_a, "got %s (via %s)" % (entry_a.type, entry_a.source),
            ))
            valid = self.type_b  # Just resort to what we should expect it to be at this point

        state.push(source, checker.merge(self.type_b, valid), parents=(entry_a, entry_b))


class ComparisonInstruction(BinaryOperationInstruction, ABC):
    """
    Compares two values on the stack.
    """

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry_a, *_ = state.pop(source, self.type_.internal_size, tuple_=True)
        entry_b, *_ = state.pop(source, self.type_.internal_size, tuple_=True)

        if not checker.check_merge(self.type_, entry_a.type):
            errors.append(Error(
                source, "expected type %s" % self.type_, "got %s (via %s)" % (entry_a.type, entry_a.source),
            ))
        if not checker.check_merge(self.type_, entry_b.type):
            errors.append(Error(
                source, "expected type %s" % self.type_, "got %s (via %s)" % (entry_b.type, entry_b.source),
            ))

        state.push(source, types.int_t, parents=(entry_a, entry_b))

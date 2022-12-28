#!/usr/bin/env python3

"""
Arithmetic related instructions.
"""

from abc import ABC
from typing import List

from . import Instruction
from ... import types
from ...abc import Error, TypeChecker
from ...analysis.trace import BlockInstruction, State
from ...types import BaseType


class UnaryOperationInstruction(Instruction, ABC):
    """
    A unary arithmetic operation.
    """

    type_: BaseType = ...

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry, *_ = state.pop(source, self.type_.internal_size, tuple_=True)
        if not checker.check_merge(self.type_, entry.type):
            errors.append(Error(source, "expected type %s, got %s" % (self.type_, entry.type)))
        state.push(source, checker.merge(self.type_, entry.type), parents=(entry,))


class BinaryOperationInstruction(Instruction, ABC):
    """
    A binary arithmetic operation.
    """

    type_a: BaseType = ...
    type_b: BaseType = ...

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry_a, *_ = state.pop(source, self.type_a.internal_size, tuple_=True)
        entry_b, *_ = state.pop(source, self.type_b.internal_size, tuple_=True)

        valid = entry_b.type
        if not checker.check_merge(self.type_b, entry_b.type):
            errors.append(Error(source, "expected type %s, got %s" % (self.type_b, entry_b.type)))
            valid = entry_a.type
        if not checker.check_merge(self.type_a, entry_a.type):
            errors.append(Error(source, "expected type %s, got %s" % (self.type_a, entry_a.type)))
            valid = self.type_b  # Just resort to what we should expect it to be at this point

        state.push(source, checker.merge(self.type_b, valid), parents=(entry_a, entry_b))


class ComparisonInstruction(BinaryOperationInstruction, ABC):
    """
    Compares two values on the stack.
    """

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry_a, *_ = state.pop(source, self.type_.internal_size, tuple_=True)
        entry_b, *_ = state.pop(source, self.type_.internal_size, tuple_=True)

        if not checker.check_merge(self.type_, entry_a.type):
            errors.append(Error(source, "expected type %s, got %s" % (self.type_, entry_a.type)))
        if not checker.check_merge(self.type_, entry_b.type):
            errors.append(Error(source, "expected type %s, got %s" % (self.type_, entry_b.type)))

        state.push(source, types.int_t, parents=(entry_a, entry_b))

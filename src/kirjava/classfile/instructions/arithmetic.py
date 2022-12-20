#!/usr/bin/env python3

"""
Arithmetic related instructions.
"""

from abc import ABC
from typing import List

from . import Instruction
from ... import types
from ...analysis import Error
from ...analysis.trace import Entry, State
from ...types import BaseType


class UnaryOperationInstruction(Instruction, ABC):
    """
    A unary arithmetic operation.
    """

    type_: BaseType = ...

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry, *_ = state.pop(self.type_.internal_size, tuple_=True)
        if not self.type_.can_merge(entry.type):
            errors.append(Error(offset, self, "expected type %s, got %s" % (self.type_, entry.type)))
        state.push(Entry(offset, entry.type if no_verify else self.type_))


class BinaryOperationInstruction(Instruction, ABC):
    """
    A binary arithmetic operation.
    """

    type_a: BaseType = ...
    type_b: BaseType = ...

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry_a, *_ = state.pop(self.type_a.internal_size, tuple_=True)
        entry_b, *_ = state.pop(self.type_b.internal_size, tuple_=True)

        valid = entry_b.type
        if not self.type_b.can_merge(entry_b.type):
            errors.append(Error(offset, self, "expected type %s, got %s" % (self.type_b, entry_b.type)))
            valid = entry_a.type
        if not self.type_a.can_merge(entry_a.type):
            errors.append(Error(offset, self, "expected type %s, got %s" % (self.type_a, entry_a.type)))
            valid = None

        state.push(Entry(offset, valid if valid is not None and no_verify else self.type_b))


class ComparisonInstruction(BinaryOperationInstruction, ABC):
    """
    Compares two values on the stack.
    """

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry_a, *_ = state.pop(self.type_.internal_size, tuple_=True)
        entry_b, *_ = state.pop(self.type_.internal_size, tuple_=True)

        if not self.type_.can_merge(entry_a.type):
            errors.append(Error(offset, self, "expected type %s, got %s" % (self.type_, entry_a.type)))
        if not self.type_.can_merge(entry_b.type):
            errors.append(Error(offset, self, "expected type %s, got %s" % (self.type_, entry_b.type)))

        state.push(Entry(offset, types.int_t))

#!/usr/bin/env python3

"""
Other instructions that don't really fall into a category or don't have enough similar instructions for me to count it
as a valid category, because I'm lazy.
"""

from abc import ABC
from typing import List

from . import Instruction
from ... import types
from ...analysis import Error
from ...analysis.trace import _check_reference_type, Entry, State
from ...types import BaseType


class ReturnInstruction(Instruction, ABC):
    """
    An instruction that returns from the current method.
    """

    throws = (types.illegalmonitorstateexception_t,)

    type_: BaseType = ...

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        # TODO: Check method return type too?
        if self.type_ != types.void_t:  # Void returns accept no value
            if self.type_ is None:
                entry = state.pop()
                errors.append(_check_reference_type(offset, self, entry.type))
            else:
                entry, *_ = state.pop(self.type_.internal_size, tuple_=True)
                if not self.type_.can_merge(entry.type):
                    errors.append(Error(offset, self, "expected type %s, got %s" % (self.type_, entry.type)))

        # if state.stack:
        #     raise ValueError("Stack is not empty after return.")


class AThrowInstruction(Instruction, ABC):
    """
    An instruction that throws an exception.
    """

    throws = (
        types.illegalmonitorstateexception_t,
        types.nullpointerexception_t,
    )

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry = state.pop()
        errors.append(_check_reference_type(offset, self, entry.type))  # TODO: Check extends exception?
        state.stack.clear()
        state.push(entry)


class MonitorEnterInstruction(Instruction, ABC):
    """
    An instruction that enters a monitor for an object.
    """

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry = state.pop()
        errors.append(_check_reference_type(offset, self, entry.type))


class MonitorExitInstruction(Instruction, ABC):
    """
    An instruction that exits a monitor for an object.
    """

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry = state.pop()
        errors.append(_check_reference_type(offset, self, entry.type))

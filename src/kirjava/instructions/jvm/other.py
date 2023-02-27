#!/usr/bin/env python3

"""
Other instructions that don't really fall into a category or don't have enough similar instructions for me to count it
as a valid category, because I'm lazy.
"""

from typing import Dict

from . import Instruction
from ..ir.other import MonitorEnterStatement, MonitorExitStatement, ReturnStatement, ThrowStatement
from ... import types
from ...abc import Value
from ...analysis.ir.variable import Scope
from ...analysis.trace import Entry, Frame, FrameDelta
from ...types import BaseType


class ReturnInstruction(Instruction):
    """
    An instruction that returns from the current method.
    """

    throws = (types.illegalmonitorstateexception_t,)

    type_: BaseType = ...

    def trace(self, frame: Frame) -> None:
        # TODO: Check method return type too?
        if self.type_ != types.void_t:  # Void returns accept no value
            if self.type_ is not None:
                frame.pop(self.type_.internal_size, expect=self.type_)
            else:
                frame.pop(expect=self.type_)

        # if state.stack:
        #     raise ValueError("Stack is not empty after return.")

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> ReturnStatement:
        return ReturnStatement(associations[delta.pops[-1]] if self.type_ != types.void_t else None)


class AThrowInstruction(Instruction):
    """
    An instruction that throws an exception.
    """

    throws = (
        types.illegalmonitorstateexception_t,
        types.nullpointerexception_t,
    )

    def trace(self, frame: Frame) -> None:
        entry = frame.pop(expect=types.throwable_t)
        if frame.stack:
            frame.pop(len(frame.stack))

        # TODO: We might be able to work out the lower bound from the exception ranges?
        if entry.type == types.null_t:  # FIXME: This might throw things off the in the future?
            frame.push(types.nullpointerexception_t)
        else:
            frame.push(entry)

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> ThrowStatement:
        return ThrowStatement(associations[delta.pops[-1]])


class MonitorEnterInstruction(Instruction):
    """
    An instruction that enters a monitor for an object.
    """

    throws = (
        types.nullpointerexception_t,
    )

    def trace(self, frame: Frame) -> None:
        frame.pop(expect=None)

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> MonitorEnterStatement:
        return MonitorEnterStatement(associations[delta.pops[-1]])


class MonitorExitInstruction(Instruction):
    """
    An instruction that exits a monitor for an object.
    """

    throws = (
        types.illegalmonitorstateexception_t,
        types.nullpointerexception_t,
    )

    def trace(self, frame: Frame) -> None:
        frame.pop(expect=None)

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> MonitorExitStatement:
        return MonitorExitStatement(associations[delta.pops[-1]])

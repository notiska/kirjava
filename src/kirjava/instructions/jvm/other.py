#!/usr/bin/env python3

__all__ = (
    "ReturnInstruction", "AThrowInstruction",
    "MonitorEnterInstruction", "MonitorExitInstruction",
)

"""
Other instructions that don't really fall into a category or don't have enough similar instructions for me to count it
as a valid category, because I'm lazy.
"""

import typing
from typing import Dict

from . import Instruction
from ..ir.other import *
from ... import types
from ...abc import Value
from ...types import Class, Verification

if typing.TYPE_CHECKING:
    from ...analysis import Context


class ReturnInstruction(Instruction):
    """
    An instruction that returns from the current method.
    """

    __slots__ = ()

    throws = (Class("java/lang/IllegalMonitorStateException"),)

    type: Verification = ...

    def trace(self, context: "Context") -> None:
        if self.type is not types.void_t:
            *_, entry = context.pop(1 + self.type.wide, as_tuple=True)
            context.constrain(entry, self.type)

        # if state.stack:
        #     raise ValueError("Stack is not empty after return.")

    # def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> ReturnStatement:
    #     return ReturnStatement(associations[delta.pops[-1]] if self.type_ != types.void_t else None)


class AThrowInstruction(Instruction):
    """
    An instruction that throws an exception.
    """

    __slots__ = ()

    throws = (
        Class("java/lang/IllegalMonitorStateException"),
        Class("java/lang/NullPointerException"),
    )

    def trace(self, context: "Context") -> None:
        entry = context.pop()
        context.pop(len(context.frame.stack))

        if entry.type == types.null_t:  # FIXME: This might throw things off the in the future?
            context.push(Class("java/lang/NullPointerException"))
        else:
            context.push(entry, types.throwable_t)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> ThrowStatement:
    #     return ThrowStatement(associations[delta.pops[-1]])


class MonitorEnterInstruction(Instruction):
    """
    An instruction that enters a monitor for an object.
    """

    __slots__ = ()

    throws = (Class("java/lang/NullPointerException"),)

    def trace(self, context: "Context") -> None:
        context.constrain(context.pop(), types.object_t)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> MonitorEnterStatement:
    #     return MonitorEnterStatement(associations[delta.pops[-1]])


class MonitorExitInstruction(Instruction):
    """
    An instruction that exits a monitor for an object.
    """

    __slots__ = ()

    throws = (
        Class("java/lang/IllegalMonitorStateException"),
        Class("java/lang/NullPointerException"),
    )

    def trace(self, context: "Context") -> None:
        context.constrain(context.pop(), types.object_t)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> MonitorExitStatement:
    #     return MonitorExitStatement(associations[delta.pops[-1]])

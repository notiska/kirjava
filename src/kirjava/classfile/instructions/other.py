#!/usr/bin/env python3

"""
Other instructions that don't really fall into a category or don't have enough similar instructions for me to count it
as a valid category, because I'm lazy.
"""

from abc import ABC
from typing import Dict, List

from . import Instruction
from ... import types
from ...abc import Source, TypeChecker, Value
from ...analysis.ir.other import MonitorEnterStatement, MonitorExitStatement, ReturnStatement, ThrowStatement
from ...analysis.trace import Entry, State
from ...types import BaseType
from ...verifier import Error


class ReturnInstruction(Instruction, ABC):
    """
    An instruction that returns from the current method.
    """

    throws = (types.illegalmonitorstateexception_t,)

    type_: BaseType = ...

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        # TODO: Check method return type too?
        if self.type_ != types.void_t:  # Void returns accept no value
            if self.type_ is None:
                entry = state.pop(source)
                if not checker.check_reference(entry.type):
                    errors.append(Error(
                        Error.Type.INVALID_TYPE, source,
                        "expected reference type", "got %s (via %s)" % (entry.type, entry.source),
                    ))
            else:
                entry, *_ = state.pop(source, self.type_.internal_size, tuple_=True)
                if not checker.check_merge(self.type_, entry.type):
                    errors.append(Error(
                        Error.Type.INVALID_TYPE, source,
                        "expected type %s" % self.type_, "got %s (via %s)" % (entry.type, entry.source),
                    ))

        # if state.stack:
        #     raise ValueError("Stack is not empty after return.")

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> ReturnStatement:
        return ReturnStatement(associations[pre.stack[-1]] if self.type_ != types.void_t else None)


class AThrowInstruction(Instruction, ABC):
    """
    An instruction that throws an exception.
    """

    throws = (
        types.illegalmonitorstateexception_t,
        types.nullpointerexception_t,
    )

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        state.stack.clear()

        # TODO: We might be able to work out the lower bound from the exception ranges?
        if not checker.check_merge(types.throwable_t, entry.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected type java/lang/Throwable", "got %s (via %s)" % (entry.type, entry.source),
            ))
            state.push(source, checker.merge(types.throwable_t, entry.type), parents=entry.parents, merges=(entry,))
        elif entry.type == types.null_t:  # FIXME: This might throw things off the in the future?
            state.push(source, types.nullpointerexception_t, parents=(entry,))
        else:
            state.push(source, entry)

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> ThrowStatement:
        return ThrowStatement(associations[pre.stack[-1]])


class MonitorEnterInstruction(Instruction, ABC):
    """
    An instruction that enters a monitor for an object.
    """

    throws = (
        types.nullpointerexception_t,
    )

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_reference(entry.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected reference type", "got %s (via %s)" % (entry.type, entry.source),
            ))

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> MonitorEnterStatement:
        return MonitorEnterStatement(associations[pre.stack[-1]])


class MonitorExitInstruction(Instruction, ABC):
    """
    An instruction that exits a monitor for an object.
    """

    throws = (
        types.illegalmonitorstateexception_t,
        types.nullpointerexception_t,
    )

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_reference(entry.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected reference type", "got %s (via %s)" % (entry.type, entry.source),
            ))

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> MonitorExitStatement:
        return MonitorExitStatement(associations[pre.stack[-1]])

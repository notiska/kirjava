#!/usr/bin/env python3

"""
Instructions related to arrays.
"""

from typing import Dict, Optional

from . import Instruction
from ..ir.array import ArrayLoadExpression, ArrayLengthExpression, ArrayStoreStatement
from ... import types
from ...abc import Value
from ...analysis.ir.variable import Scope
from ...analysis.trace import Entry, Frame, FrameDelta
from ...types import BaseType
from ...types.reference import ArrayType


class ArrayLoadInstruction(Instruction):
    """
    Loads a value from an array.
    """

    __slots__ = ()

    throws = (
        types.arrayindexoutofboundsexception_t,
        types.nullpointerexception_t,
    )

    type_: Optional[BaseType] = ...

    def trace(self, frame: Frame) -> None:
        frame.pop(expect=types.int_t)
        array_entry = frame.pop(expect=ArrayType)

        # Create type from array, taking into account if it's multi-dimensional
        if type(array_entry.type) is ArrayType:
            type_ = array_entry.type.set_dimension(array_entry.type.dimension - 1).to_verification_type()
        else:
            type_ = array_entry.type  # Best we can do I guess

        if self.type_ is not None:
            type__ = self.type_.to_verification_type()  # Naming scheme <333
            if type_ != types.null_t and not frame.verifier.checker.check_merge(type__, type_):
                frame.verifier.report_invalid_type(frame.source, type__, type_, array_entry.source)
            frame.push(frame.verifier.checker.merge(type__, type_))

        else:
            if not frame.verifier.checker.check_reference(type_):
                frame.verifier.report_expected_reference_type(frame.source, type_, array_entry.source)
            frame.push(type_)

    def lift(self, delta: FrameDelta, scope: "Scope", associations: Dict[Entry, Value]) -> None:
        offset = self.type_.internal_size if self.type_ is not None else 1
        associations[delta.pushes[0]] = ArrayLoadExpression(
            array=associations[delta.pops[-(1 + offset)]],
            index=associations[delta.pops[-1]],
        )


class ArrayStoreInstruction(Instruction):
    """
    Stores a value in an array.
    """

    __slots__ = ()

    throws = (
        types.arrayindexoutofboundsexception_t,
        types.arraystoreexception_t,
        types.nullpointerexception_t,
    )

    type_: Optional[BaseType] = ...

    def trace(self, frame: Frame) -> None:
        # Check the array type matches what the instruction expects
        if self.type_ is not None:
            type_ = self.type_.to_verification_type()
            *_, entry = frame.pop(type_.internal_size, tuple_=True, expect=type_)
        else:
            entry = frame.pop(expect=None)

        frame.pop(expect=types.int_t)
        array_entry = frame.pop(expect=ArrayType)

        if type(array_entry.type) is ArrayType:
            type_ = array_entry.type.set_dimension(array_entry.type.dimension - 1).to_verification_type()
        else:
            type_ = array_entry.type

        # Check the value can merge with the array that we popped
        if type_ != types.null_t and not frame.verifier.checker.check_merge(type_, entry.type):
            frame.verifier.report_invalid_type(frame.source, type_, entry.type, entry.source)

    def lift(self, delta: FrameDelta, scope: "Scope", associations: Dict[Entry, Value]) -> ArrayStoreStatement:
        offset = self.type_.internal_size if self.type_ is not None else 1
        return ArrayStoreStatement(
            array=associations[delta.pops[-(2 + offset)]],
            index=associations[delta.pops[-(1 + offset)]],
            value=associations[delta.pops[-1]],
        )


class ArrayLengthInstruction(Instruction):
    """
    Gets the length of an array.
    """

    __slots__ = ()

    throws = (types.nullpointerexception_t,)

    def trace(self, frame: Frame) -> None:
        frame.pop(expect=ArrayType)
        frame.push(types.int_t)

    def lift(self, delta: FrameDelta, scope: "Scope", associations: Dict[Entry, Value]) -> None:
        associations[delta.pushes[0]] = ArrayLengthExpression(associations[delta.pops[-1]])

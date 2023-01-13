#!/usr/bin/env python3

"""
Instructions related to arrays.
"""

from abc import ABC
from typing import Dict, List, Union

from . import Instruction
from ... import types
from ...abc import Source, TypeChecker, Value
from ...analysis.ir.array import ArrayLoadExpression, ArrayLengthExpression, ArrayStoreStatement
from ...analysis.trace import Entry, State
from ...types import BaseType
from ...types.reference import ArrayType
from ...verifier import Error


class ArrayLoadInstruction(Instruction, ABC):
    """
    Loads a value from an array.
    """

    throws = (
        types.arrayindexoutofboundsexception_t,
        types.nullpointerexception_t,
    )

    type_: Union[BaseType, None] = ...

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        index_entry, array_entry = state.pop(source, 2)

        # Check initial types (array and int)
        if not checker.check_array(array_entry.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected array type", "got %s (via %s)" % (array_entry.type, array_entry.source),
            ))
        if not checker.check_merge(types.int_t, index_entry.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected type int", "got %s (via %s)" % (index_entry.type, index_entry.source),
            ))

        # Create type from array, taking into account if it's multi-dimensional
        if array_entry.type.__class__ is ArrayType:
            type_ = array_entry.type.set_dimension(array_entry.type.dimension - 1).to_verification_type()
        else:
            type_ = array_entry.type  # Best we can do I guess

        if self.type_ is not None:
            type__ = self.type_.to_verification_type()
            if type_ != types.null_t and not checker.check_merge(type__, type_):
                errors.append(Error(
                    Error.Type.INVALID_TYPE, source,
                    "expected type %s" % type__, "got %s (via %s)" % (type_, array_entry.source),
                ))
            state.push(source, checker.merge(type__, type_), parents=(index_entry, array_entry))

        else:
            if not checker.check_reference(type_):
                errors.append(Error(
                    Error.Type.INVALID_TYPE, source,
                    "expected reference type", "got %s (via %s)" % (type_, array_entry.source),
                ))
            state.push(source, type_, parents=(index_entry, array_entry))

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        offset = self.type_.internal_size if self.type_ is not None else 1
        associations[post.stack[-1]] = ArrayLoadExpression(
            associations[pre.stack[-(1 + offset)]], associations[pre.stack[-1]],
        )


class ArrayStoreInstruction(Instruction, ABC):
    """
    Stores a value in an array.
    """

    throws = (
        types.arrayindexoutofboundsexception_t,
        types.arraystoreexception_t,
        types.nullpointerexception_t,
    )

    type_: Union[BaseType, None] = ...

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        # Check the array type matches what the instruction expects
        if self.type_ is not None:
            type_ = self.type_.to_verification_type()
            entry, *_ = state.pop(source, type_.internal_size, tuple_=True)
            if not checker.check_merge(type_, entry.type):
                errors.append(Error(
                    Error.Type.INVALID_TYPE, source,
                    "expected type %s" % type_, "got %s (via %s)" % (entry.type, entry.source),
                ))
        else:
            entry = state.pop(source)
            if not checker.check_reference(entry.type):
                errors.append(Error(
                    Error.Type.INVALID_TYPE, source,
                    "expected reference type", "got %s (via %s)" % (entry.type, entry.source),
                ))

        index_entry, array_entry = state.pop(source, 2)

        # Check the array and index types are valid
        if not checker.check_array(array_entry.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected array type", "got %s (via %s)" % (array_entry.type, array_entry.source),
            ))
        if not checker.check_merge(types.int_t, index_entry.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected type int", "got %s (via %s)" % (index_entry.type, index_entry.source),
            ))

        if array_entry.type.__class__ is ArrayType:
            type_ = array_entry.type.set_dimension(array_entry.type.dimension - 1).to_verification_type()
        else:
            type_ = array_entry.type

        # Check the value can merge with the array that we popped
        if type_ != types.null_t and not checker.check_merge(type_, entry.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source,
                "expected type %s" % type_, "got %s (via %s)" % (entry.type, entry.source),
            ))

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> ArrayStoreStatement:
        offset = self.type_.internal_size if self.type_ is not None else 1
        return ArrayStoreStatement(
            associations[pre.stack[-(2 + offset)]], associations[pre.stack[-(1 + offset)]], associations[pre.stack[-1]],
        )


class ArrayLengthInstruction(Instruction, ABC):
    """
    Gets the length of an array.
    """

    throws = (types.nullpointerexception_t,)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_array(entry.type):
            errors.append(Error(
                Error.Type.INVALID_TYPE, source, "expected array type", "got %s (via %s)" % (entry.type, entry.source),
            ))
        state.push(source, types.int_t, parents=(entry,))

    def lift(self, pre: State, post: State, associations: Dict[Entry, Value]) -> None:
        associations[post.stack[-1]] = ArrayLengthExpression(associations[pre.stack[-1]])

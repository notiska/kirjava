#!/usr/bin/env python3

"""
Instructions related to arrays.
"""

from abc import ABC
from typing import List, Union

from . import Instruction
from ... import types
from ...analysis import Error
from ...analysis.trace import _check_reference_type, Entry, State
from ...types import BaseType
from ...types.reference import ArrayType


class ArrayLoadInstruction(Instruction, ABC):
    """
    Loads a value from an array.
    """

    throws = (
        types.arrayindexoutofboundsexception_t,
        types.nullpointerexception_t,
    )

    type_: Union[BaseType, None] = ...

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        index_entry, array_entry = state.pop(2)

        # Check initial types (array and int)
        if not isinstance(array_entry.type, ArrayType) and array_entry.type != types.null_t:
            errors.append(Error(offset, self, "expected array type, got %s" % array_entry.type))
        if not types.int_t.can_merge(index_entry.type):
            errors.append(Error(offset, self, "expected type int, got %s" % index_entry.type))

        # Create type from array, taking into account if it's multi-dimensional
        if isinstance(array_entry.type, ArrayType):
            if array_entry.type.dimension > 1:
                type_ = ArrayType(array_entry.type.element_type, array_entry.type.dimension - 1)
            else:
                type_ = array_entry.type.element_type.to_verification_type()
        else:
            type_ = array_entry.type  # Best we can do I guess

        if self.type_ is not None:
            type__ = self.type_.to_verification_type()
            if not type__.can_merge(type_):
                errors.append(Error(offset, self, "expected type %s, got %s" % (type__, type_)))
        else:
            errors.append(_check_reference_type(offset, self, type_))

        if no_verify:
            state.push(Entry(offset, type_))
        else:  # We may not be able to infer the correct type :(
            state.push(Entry(offset, type_ if self.type_ is None else self.type_.to_verification_type()))


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

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        # Check the array type matches what the instruction expects
        if self.type_ is not None:
            type_ = self.type_.to_verification_type()
            entry, *_ = state.pop(type_.internal_size, tuple_=True)
            if not type_.can_merge(entry.type):
                errors.append(Error(offset, self, "expected type %s, got %s" % (type_, entry.type)))
        else:
            entry = state.pop()
            errors.append(_check_reference_type(offset, self, entry.type))

        index_entry, array_entry = state.pop(2)

        # Check the array and index types are valid
        if not isinstance(array_entry.type, ArrayType) and array_entry.type != types.null_t:
            errors.append(Error(offset, self, "expected array type, got %s" % array_entry.type))
        if not types.int_t.can_merge(index_entry.type):
            errors.append(Error(offset, self, "expected type int, got %s" % index_entry.entry))

        if isinstance(array_entry.type, ArrayType):
            if array_entry.type.dimension > 1:
                type_ = ArrayType(array_entry.type.element_type, array_entry.type.dimension - 1)
            else:
                type_ = array_entry.type.element_type.to_verification_type()
        else:
            type_ = array_entry.type

        # Check the value can merge with the array that we popped
        if not type_.can_merge(entry.type):
            errors.append(Error(offset, self, "expected type %s, got %s" % (type_, entry.type)))


class ArrayLengthInstruction(Instruction, ABC):
    """
    Gets the length of an array.
    """

    throws = (types.nullpointerexception_t,)

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry = state.pop()
        if not isinstance(entry.type, ArrayType) and entry.type != types.null_t:
            errors.append(Error(offset, self, "expected array type, got %s" % entry.type))
        state.push(Entry(offset, types.int_t))

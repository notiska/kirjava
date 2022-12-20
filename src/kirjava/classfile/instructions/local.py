#!/usr/bin/env python3

"""
Local-related instructions.
"""

from abc import ABC
from typing import Any, IO, List, Union

from . import Instruction, MetaInstruction
from .. import ClassFile
from ... import types
from ...analysis import Error
from ...analysis.trace import _check_reference_type, Entry, State
from ...types import BaseType


class LoadLocalInstruction(Instruction, ABC):
    """
    Loads the value from a local variable and pushes it to the stack.
    """

    __slots__ = ("index",)

    operands = {"index": ">B"}
    operands_wide = {"index": ">H"}

    type_: Union[BaseType, None] = ...  # None means don't check the type

    def __init__(self, index: int) -> None:
        self.index = index

    def __repr__(self) -> str:
        return "<LoadLocalInstruction(opcode=0x%x, mnemonic=%s, index=%i) at %x>" % (
            self.opcode, self.mnemonic, self.index, id(self),
        )

    def __str__(self) -> str:
        return "%s %i" % (self.mnemonic, self.index)

    def __eq__(self, other: Any) -> bool:
        return (
            (isinstance(other, MetaInstruction) and other == self.__class__) or 
            (other.__class__ == self.__class__ and other.index == self.index)
        )

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry = state.get(self.index)

        error = None
        if self.type_ is None:
            error = _check_reference_type(offset, self, entry.type)
        elif not self.type_.can_merge(entry.type):
            error = Error(offset, self, "expected type %s, got %s" % (self.type_, entry.type))

        if error is not None:
            errors.append(error)
            state.push(Entry(offset, self.type_) if self.type_ is not None and no_verify else entry)
        else:
            state.push(entry)


class LoadLocalFixedInstruction(LoadLocalInstruction, ABC):
    """
    Loads the value from a fixed local variable and pushes it to the stack.
    """

    operands = {}
    operands_wide = {}

    index: int = ...

    def __init__(self) -> None:
        super().__init__(self.__class__.index)

    def __repr__(self) -> str:
        return "<LoadLocalFixedInstruction(opcode=0x%x, mnemonic=%s) at %x>" % (
            self.opcode, self.mnemonic, id(self),
        )

    def __str__(self) -> str:
        return self.mnemonic

    def __eq__(self, other: Any) -> bool:
        return other == self.__class__ or other.__class__ == self.__class__

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...


class StoreLocalInstruction(Instruction, ABC):
    """
    Stores the top value of the stack in the specified local index.
    """

    __slots__ = ("index",)

    operands = {"index": ">B"}
    operands_wide = {"index": ">H"}

    type_: Union[BaseType, None] = ...

    def __init__(self, index: int) -> None:
        self.index = index

    def __repr__(self) -> str:
        return "<StoreLocalInstruction(opcode=0x%x, mnemonic=%s, index=%i) at %x>" % (
            self.opcode, self.mnemonic, self.index, id(self),
        )

    def __str__(self) -> str:
        return "%s %i" % (self.mnemonic, self.index)

    def __eq__(self, other: Any) -> bool:
        return (
            (isinstance(other, MetaInstruction) and other == self.__class__) or 
            (other.__class__ == self.__class__ and other.index == self.index)
        )

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        error = None
        if self.type_ is not None:
            entry, *_ = state.pop(self.type_.internal_size, tuple_=True)
            if not self.type_.can_merge(entry.type):
                error = Error(offset, self, "expected type %s, got %s" % (self.type_, entry.type))
        else:
            entry = state.pop()
            if entry.type != types.return_address_t:  # Can also be used for returnAddresses
                error = _check_reference_type(offset, self, entry.type)

        if error is not None:
            state.set(self.index, Entry(offset, self.type_) if self.type_ is not None and no_verify else entry)
            errors.append(error)
        else:
            state.set(self.index, entry)


class StoreLocalFixedInstruction(StoreLocalInstruction, ABC):
    """
    Stores the top value of the stack in a fixed local index.
    """

    operands = {}
    operands_wide = {}

    index: int = ...

    def __init__(self) -> None:
        super().__init__(self.__class__.index)

    def __repr__(self) -> str:
        return "<StoreLocalFixedInstruction(opcode=0x%x, mnemonic=%s) at %x>" % (
            self.opcode, self.mnemonic, id(self),
        )

    def __str__(self) -> str:
        return self.mnemonic

    def __eq__(self, other: Any) -> bool:
        return other == self.__class__ or other.__class__ == self.__class__

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...


class IncrementLocalInstruction(Instruction, ABC):
    """
    Increments a local variable by a given amount.
    """

    __slots__ = ("index", "value")

    operands = {"index": ">B", "value": ">b"}
    operands_wide = {"index": ">H", "value": ">h"}

    def __init__(self, index: int, value: int) -> None:
        self.index = index
        self.value = value

    def __repr__(self) -> str:
        return "<IncrementLocalInstruction(opcode=0x%x, mnemonic=%s, index=%i, value=%i) at %x>" % (
            self.opcode, self.mnemonic, self.index, self.value,
        )

    def __str__(self) -> str:
        return "%s %i by %i" % (self.mnemonic, self.index, self.value)

    def __eq__(self, other: Any) -> bool:
        return (
            (isinstance(other, MetaInstruction) and other == self.__class__) or 
            (other.__class__ == self.__class__ and other.index == self.index and other.value == self.value)
        )

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry = state.get(self.index)
        if not types.int_t.can_merge(entry.type):
            errors.append(Error(offset, self, "expected type int, got %s" % entry.type))
        state.set(self.index, Entry(offset, types.int_t))

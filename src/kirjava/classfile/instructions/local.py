#!/usr/bin/env python3

"""
Local-related instructions.
"""

from abc import ABC
from typing import Any, IO, List, Union

from . import Instruction, MetaInstruction
from .. import ClassFile
from ... import types
from ...abc import Error, Source, TypeChecker
from ...analysis.trace import State
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

    def copy(self) -> "LoadLocalInstruction":
        return self.__class__(self.index)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.get(source, self.index)

        error = None
        if self.type_ is None:
            if not checker.check_reference(entry.type):
                error = Error(source, "expected reference type", "got %s (via %s)" % (entry.type, entry.source))
        elif not checker.check_merge(self.type_, entry.type):
            error = Error(source, "expected type %s" % self.type_, "got %s (via %s)" % (entry.type, entry.source))

        if error is not None:
            errors.append(error)
            state.push(source, checker.merge(self.type_, entry.type), parents=entry, merges=(entry,))
        else:
            state.push(source, entry)


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

    def copy(self) -> "LoadLocalFixedInstruction":
        return self

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

    def copy(self) -> "StoreLocalInstruction":
        return self.__class__(self.index)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        error = None
        if self.type_ is not None:
            entry, *_ = state.pop(source, self.type_.internal_size, tuple_=True)
            if not checker.check_merge(self.type_, entry.type):
                error = Error(source, "expected type %s" % self.type_, "got %s (via %s)" % (entry.type, entry.source))
        else:
            entry = state.pop(source)
            if not checker.check_merge(types.return_address_t, entry.type):  # Can also be used for returnAddresses
                if not checker.check_reference(entry.type):
                    error = Error(
                        source, "expected reference type or returnAddress type",
                        "got %s (via %s)" % (entry.type, entry.source),
                    )

        if error is not None:
            errors.append(error)
            state.set(source, self.index, checker.merge(self.type_, entry.type), parents=entry.parents, merges=(entry,))
        else:
            state.set(source, self.index, entry)


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

    def copy(self) -> "StoreLocalFixedInstruction":
        return self

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
            self.opcode, self.mnemonic, self.index, self.value, id(self),
        )

    def __str__(self) -> str:
        return "%s %i by %i" % (self.mnemonic, self.index, self.value)

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, MetaInstruction) and other == self.__class__) or (
            other.__class__ == self.__class__ and
            other.index == self.index and
            other.value == self.value
        )

    def copy(self) -> "IncrementLocalInstruction":
        return self.__class__(self.index, self.value)

    def trace(self, source: Source, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.get(source, self.index)
        if not checker.check_merge(types.int_t, entry.type):
            errors.append(Error(source, "expected type int", "got %s (via %s)" % (entry.type, entry.source)))
        state.set(source, self.index, types.int_t, parents=(entry,))

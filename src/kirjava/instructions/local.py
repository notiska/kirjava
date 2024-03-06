#!/usr/bin/env python3

__all__ = (
    "LoadLocalInstruction", "LoadLocalFixedInstruction",
    "StoreLocalInstruction", "StoreLocalFixedInstruction",
    "IncrementLocalInstruction",
)

"""
Local-related instructions.
"""

import typing
from typing import Any, IO

from . import Instruction
from ..constants import Integer
from ..types import int_t, Reference, ReturnAddress, Verification

if typing.TYPE_CHECKING:
    from ..analysis import Context
    from ..classfile import ClassFile


class LoadLocalInstruction(Instruction):
    """
    Loads the value from a local variable and pushes it to the stack.
    """

    __slots__ = ("index",)

    operands = {"index": ">B"}
    operands_wide = {"index": ">H"}

    type: Verification = ...

    def __init__(self, index: int) -> None:
        self.index = index

    def __repr__(self) -> str:
        return "<LoadLocalInstruction(opcode=0x%x, mnemonic=%s, index=%i) at %x>" % (
            self.opcode, self.mnemonic, self.index, id(self),
        )

    def __str__(self) -> str:
        return "%s %i" % (self.mnemonic, self.index)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.index == self.index) or other is type(self)

    def copy(self) -> "LoadLocalInstruction":
        return type(self)(self.index)

    def trace(self, context: "Context") -> None:
        context.push(context.get(self.index), self.type)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> None:
    #     entry = delta.pushes[0]
    #     value = associations[entry]
    #     if type(value) is Parameter:
    #         return
    #     associations[entry] = GetLocalExpression(self.index, associations[entry])


class LoadLocalFixedInstruction(LoadLocalInstruction):
    """
    Loads the value from a fixed local variable and pushes it to the stack.
    """

    __slots__ = ()

    operands = {}
    operands_wide = {}

    index: int = ...

    def __init__(self) -> None:
        ...  # super().__init__(self.__class__.index)

    def __repr__(self) -> str:
        return "<LoadLocalFixedInstruction(opcode=0x%x, mnemonic=%s) at %x>" % (
            self.opcode, self.mnemonic, id(self),
        )

    def __str__(self) -> str:
        return self.mnemonic

    def __eq__(self, other: Any) -> bool:
        return type(other) is type(self) or other is type(self)

    def copy(self) -> "LoadLocalFixedInstruction":
        return self

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        ...

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        ...


class StoreLocalInstruction(Instruction):
    """
    Stores the top value of the stack in the specified local index.
    """

    __slots__ = ("index",)

    operands = {"index": ">B"}
    operands_wide = {"index": ">H"}

    type: Verification = ...

    def __init__(self, index: int) -> None:
        self.index = index

    def __repr__(self) -> str:
        return "<StoreLocalInstruction(opcode=0x%x, mnemonic=%s, index=%i) at %x>" % (
            self.opcode, self.mnemonic, self.index, id(self),
        )

    def __str__(self) -> str:
        return "%s %i" % (self.mnemonic, self.index)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is type(self) and other.index == self.index) or other is type(self)

    def copy(self) -> "StoreLocalInstruction":
        return type(self)(self.index)

    def trace(self, context: "Context") -> None:
        *_, entry = context.pop(1 + self.type.wide, as_tuple=True)
        # The astore instruction has a special case for storing return addresses which we need to account for.
        if isinstance(self.type, Reference) and type(entry.generic) is ReturnAddress:
            context.set(self.index, entry)
        else:
            context.constrain(entry, self.type)
            context.set(self.index, entry, self.type)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> SetLocalStatement | None:
    #     if not self.index in delta.overwrites:
    #         return None
    #
    #     entry = delta.pops[-1]
    #     return SetLocalStatement(self.index, associations[entry])


class StoreLocalFixedInstruction(StoreLocalInstruction):
    """
    Stores the top value of the stack in a fixed local index.
    """

    __slots__ = ()

    operands = {}
    operands_wide = {}

    index: int = ...

    def __init__(self) -> None:
        ...  # super().__init__(self.__class__.index)

    def __repr__(self) -> str:
        return "<StoreLocalFixedInstruction(opcode=0x%x, mnemonic=%s) at %x>" % (
            self.opcode, self.mnemonic, id(self),
        )

    def __str__(self) -> str:
        return self.mnemonic

    def __eq__(self, other: Any) -> bool:
        return type(other) is type(self) or other is type(self)

    def copy(self) -> "StoreLocalFixedInstruction":
        return self

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        ...

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        ...


class IncrementLocalInstruction(Instruction):
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
        return (
            type(other) is type(self) and
            other.index == self.index and
            other.value == self.value
        ) or other is type(self)

    def copy(self) -> "IncrementLocalInstruction":
        return type(self)(self.index, self.value)

    def trace(self, context: "Context") -> None:
        entry = context.get(self.index)
        context.constrain(entry, int_t)
        context.set(self.index, int_t)

    # def lift(self, delta: FrameDelta, scope: Scope, associations: dict[Entry, Value]) -> SetLocalStatement:
    #     old, new = delta.overwrites[self.index]
    #     value = AdditionExpression(
    #         GetLocalExpression(self.index, associations[old]), ConstantValue(Integer(self.value)),
    #     )
    #     associations[new] = value
    #     return SetLocalStatement(self.index, value)

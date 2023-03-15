#!/usr/bin/env python3

"""
Local-related instructions.
"""

from typing import Any, Dict, IO, Optional

from . import Instruction
from ..ir.arithmetic import AdditionExpression
from ..ir.variable import AssignStatement, DeclareStatement
from ..ir.value import ConstantValue
from ... import types
from ...abc import Value
from ...analysis.ir.variable import Local, Scope
from ...analysis.trace import Entry, Frame, FrameDelta
from ...classfile import ClassFile
from ...classfile.constants import Integer
from ...types import BaseType


class LoadLocalInstruction(Instruction):
    """
    Loads the value from a local variable and pushes it to the stack.
    """

    __slots__ = ("index",)

    operands = {"index": ">B"}
    operands_wide = {"index": ">H"}

    type_: Optional[BaseType] = ...  # None means don't check the type

    def __init__(self, index: int) -> None:
        self.index = index

    def __repr__(self) -> str:
        return "<LoadLocalInstruction(opcode=0x%x, mnemonic=%s, index=%i) at %x>" % (
            self.opcode, self.mnemonic, self.index, id(self),
        )

    def __str__(self) -> str:
        return "%s %i" % (self.mnemonic, self.index)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is self.__class__ and other.index == self.index) or other is self.__class__

    def copy(self) -> "LoadLocalInstruction":
        return self.__class__(self.index)

    def trace(self, frame: Frame) -> None:
        frame.push(frame.get(self.index, expect=self.type_))

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> None:
        entry = delta.pushes[0]
        if not isinstance(associations.get(entry, None), Local):
            associations[entry] = Local(self.index, entry.type)


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
        return type(other) is self.__class__ or other is self.__class__

    def copy(self) -> "LoadLocalFixedInstruction":
        return self

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...


class StoreLocalInstruction(Instruction):
    """
    Stores the top value of the stack in the specified local index.
    """

    __slots__ = ("index",)

    operands = {"index": ">B"}
    operands_wide = {"index": ">H"}

    type_: Optional[BaseType] = ...

    def __init__(self, index: int) -> None:
        self.index = index

    def __repr__(self) -> str:
        return "<StoreLocalInstruction(opcode=0x%x, mnemonic=%s, index=%i) at %x>" % (
            self.opcode, self.mnemonic, self.index, id(self),
        )

    def __str__(self) -> str:
        return "%s %i" % (self.mnemonic, self.index)

    def __eq__(self, other: Any) -> bool:
        return (type(other) is self.__class__ and other.index == self.index) or other is self.__class__

    def copy(self) -> "StoreLocalInstruction":
        return self.__class__(self.index)

    def trace(self, frame: Frame) -> None:
        if self.type_ is not None:
            *_, entry = frame.pop(self.type_.internal_size, tuple_=True)
        else:
            entry = frame.pop()
        frame.set(self.index, entry, expect=self.type_)

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> Optional[AssignStatement]:
        if not self.index in delta.overwrites:
            return None

        entry = delta.pops[-1]
        local = Local(scope.variable_id, self.index, entry.type)

        if type(associations.get(entry, None)) is not Local:
            statement = DeclareStatement(local, associations[entry])
            associations[entry] = local
        else:
            local = entry
            statement = AssignStatement(local, associations[entry])

        return statement


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
        return type(other) is self.__class__ or other is self.__class__

    def copy(self) -> "StoreLocalFixedInstruction":
        return self

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        ...

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
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
            type(other) is self.__class__ and
            other.index == self.index and
            other.value == self.value
        ) or other is self.__class__

    def copy(self) -> "IncrementLocalInstruction":
        return self.__class__(self.index, self.value)

    def trace(self, frame: Frame) -> None:
        entry = frame.get(self.index, expect=types.int_t)
        frame.set(self.index, types.int_t)

    def lift(self, delta: FrameDelta, scope: Scope, associations: Dict[Entry, Value]) -> AssignStatement:
        old, new = delta.overwrites[self.index]
        associations[new] = AdditionExpression(associations[old], ConstantValue(Integer(self.value)))
        return AssignStatement(associations[old], associations[new])

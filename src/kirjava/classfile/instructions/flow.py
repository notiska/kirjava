#!/usr/bin/env python3

"""
Control flow related instructions.
"""

import struct
from abc import ABC
from typing import Any, Dict, IO, List

from . import Instruction, MetaInstruction
from .. import ClassFile
from ... import types
from ...analysis import Error
from ...analysis.trace import _check_reference_type, Entry, State
from ...types import BaseType


class JumpInstruction(Instruction, ABC):
    """
    An instruction that jumps to a bytecode offset.
    """

    __slots__ = ("offset",)

    def __init__(self, offset: int = 0) -> None:
        self.offset = offset

    def __repr__(self) -> str:
        return "<JumpInstruction(opcode=0x%x, mnemonic=%s, offset=%i) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def __str__(self) -> str:
        return "%s %+i" % (self.mnemonic, self.offset)

    def __eq__(self, other: Any) -> bool:
        return (
            (isinstance(other, MetaInstruction) and other == self.__class__) or
            (other.__class__ == self.__class__ and other.offset == self.offset)
        )


class ConditionalJumpInstruction(JumpInstruction, ABC):
    """
    A jump instruction that jumps only if a certain condition is met.
    """

    def __repr__(self) -> str:
        return "<ConditionalJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%i) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )


class UnaryComparisonJumpInstruction(ConditionalJumpInstruction, ABC):
    """
    A conditional jump that compares one value to a fixed value.
    """

    type_: BaseType = ...

    def __repr__(self) -> str:
        return "<UnaryComparisonJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%i) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        if self.type_ is None:
            entry = state.pop(1)
            errors.append(_check_reference_type(offset, self, entry.type))
        else:
            entry, *_ = state.pop(self.type_.internal_size, tuple_=True)

            if not self.type_.can_merge(entry.type):
                errors.append(Error(offset, self, "expected type %s, got %s" % (self.type_, entry.type)))


class BinaryComparisonJumpInstruction(ConditionalJumpInstruction, ABC):
    """
    A conditional jump instruction that comapares two values.
    """

    type_: BaseType = ...

    def __repr__(self) -> str:
        return "<BinaryComparisonJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%i) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        # Future-proofing, tho it is slower :(
        if self.type_ is None:
            entry_a, entry_b = state.pop(2)
            errors.append(_check_reference_type(offset, self, entry_a.type))
            errors.append(_check_reference_type(offset, self, entry_b.type))
        else:
            entry_a, *_ = state.pop(self.type_.internal_size, tuple_=True)
            entry_b, *_ = state.pop(self.type_.internal_size, tuple_=True)

            if not self.type_.can_merge(entry_a.type):
                errors.append(Error(offset, self, "expected type %s, got %s" % (self.type_, entry_a.type)))
            if not self.type_.can_merge(entry_b.type):
                errors.append(Error(offset, self, "expected type %s, got %s" % (self.type_, entry_b.type)))


class TableSwitchInstruction(Instruction, ABC):
    """
    Continues execution at the address in the jump table, given an index on the top of the stack.
    """

    __slots__ = ("default", "low", "high", "offsets")

    def __init__(self, default: int, low: int, high: int, offsets: List[int]) -> None:
        self.default = default
        self.low = low
        self.high = high
        self.offsets = offsets.copy()

    def __repr__(self) -> str:
        return "<TableSwitchInstruction(opcode=0x%x, mnemonic=%s, default=%i, low=%i, high=%i, offsets=%r) at %x>" % (
            self.opcode, self.mnemonic, self.default, self.low, self.high, self.offsets, id(self),
        )
               
    def __str__(self) -> str:
        return "%s %i to %i default %+i offsets %s" % (
            self.mnemonic, self.low, self.high, self.default, 
            ", ".join(map(lambda offset: "%+i" % offset, self.offsets)),
        )

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, MetaInstruction) and other == self.__class__) or (
            other.__class__ == self.__class__ and
            other.default == self.default and
            other.low == self.low and
            other.high == self.high and
            other.offsets == self.offsets
        )

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        buffer.read((4 - buffer.tell() % 4) % 4)  # Padding

        self.default, self.low, self.high = struct.unpack(">iii", buffer.read(12))

        self.offsets = []
        for index in range((self.high - self.low) + 1):
            self.offsets.append(struct.unpack(">i", buffer.read(4))[0])

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        buffer.write(b"\x00" * ((4 - buffer.tell() % 4) % 4))
        buffer.write(struct.pack(">iii", self.default, self.low, self.high))
        for offset in self.offsets:
            buffer.write(struct.pack(">i", offset))

    def get_size(self, offset: int, wide: bool = False) -> None:
        return 1 + 3 - offset % 4 + 12 + 4 * len(self.offsets)

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry = state.pop()
        if entry.type != types.int_t:
            errors.append(Error(offset, self, "expected type int, got %s" % entry.type))


class LookupSwitchInstruction(Instruction, ABC):  # FIXME: Sorting required?
    """
    Continues execution at the address in the jump table, given a key match on the top of the stack.
    """

    __slots__ = ("default", "offsets")

    def __init__(self, default: int, offsets: Dict[int, int]) -> None:
        self.default = default
        self.offsets = offsets.copy()

    def __repr__(self) -> str:
        return "<LookupSwitchInstruction(opcode=0x%x, mnemonic=%s, default=%i, offsets=%r) at %x>" % (
            self.opcode, self.mnemonic, self.default, self.offsets, id(self),
        )
               
    def __str__(self) -> str:
        return "%s default %+i offsets %s" % (
            self.mnemonic, self.default, 
            ", ".join(map(lambda pair: "%i: %+i" % pair, self.offsets.items())),
        )

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, MetaInstruction) and other == self.__class__) or (
            other.__class__ == self.__class__ and
            other.default == self.default and
            other.offsets == self.offsets
        )

    def read(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        buffer.read((4 - buffer.tell() % 4) % 4)

        self.default, = struct.unpack(">i", buffer.read(4))

        self.offsets = {}
        count, = struct.unpack(">i", buffer.read(4))
        for index in range(count):
            match, offset = struct.unpack(">ii", buffer.read(8))
            self.offsets[match] = offset

    def write(self, class_file: ClassFile, buffer: IO[bytes], wide: bool) -> None:
        buffer.write(b"\x00" * ((4 - (buffer.tell() % 4)) % 4))
        buffer.write(struct.pack(">ii", self.default, len(self.offsets)))
        for match, offset in self.offsets.items():
            buffer.write(struct.pack(">ii", match, offset))

    def get_size(self, offset: int, wide: bool = False) -> None:
        return 1 + 3 - offset % 4 + 8 + 8 * len(self.offsets)

    def step(self, offset: int, state: State, errors: List[Error], no_verify: bool = False) -> None:
        entry = state.pop()
        if entry.type != types.int_t:
            errors.append(Error(offset, self, "expected type int, got %s" % entry.type))

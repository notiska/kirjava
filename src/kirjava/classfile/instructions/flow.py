#!/usr/bin/env python3

"""
Control flow related instructions.
"""

import struct
from abc import ABC
from typing import Any, Dict, IO, Iterable, List, Union

from . import Instruction, MetaInstruction
from .. import ClassFile
from ... import types
from ...abc import Error, TypeChecker
from ...analysis.trace import BlockInstruction, State
from ...types import BaseType


class JumpInstruction(Instruction, ABC):
    """
    An instruction that jumps to a bytecode offset.
    """

    __slots__ = ("offset",)

    def __init__(self, offset: Union[int, None] = None) -> None:
        self.offset = offset

    def __repr__(self) -> str:
        return "<JumpInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def __str__(self) -> str:
        if self.offset is None:
            return self.mnemonic
        return "%s %+i" % (self.mnemonic, self.offset)

    def __eq__(self, other: Any) -> bool:
        return (
            (isinstance(other, MetaInstruction) and other == self.__class__) or
            (other.__class__ == self.__class__ and other.offset == self.offset)
        )

    def copy(self) -> "JumpInstruction":
        return self.__class__(self.offset)


class JsrInstruction(JumpInstruction, ABC):
    """
    A jump to subroutine instruction.
    """

    def __repr__(self) -> str:
        return "<JsrInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        state.push(source, types.return_address_t)


class RetInstruction(JumpInstruction, ABC):
    """
    A return from subroutine instruction.
    """

    __slots__ = ("index",)

    operands = {"index": ">B"}
    operands_wide = {"index": ">H"}

    def __init__(self, index: int) -> None:
        """
        :param index: The index of the local variable to load the return address from.
        """

        super().__init__(None)

        self.index = index

    def __repr__(self) -> str:
        return "<RetInstruction(opcode=0x%x, mnemonic=%s, index=%i) at %x>" % (
            self.opcode, self.mnemonic, self.index, id(self),
        )

    def __str__(self) -> str:
        return "%s %i" % (self.mnemonic, self.index)

    def __eq__(self, other: Any) -> bool:
        return (
            (isinstance(other, MetaInstruction) and other == self.__class__) or
            (other.__class__ == self.__class__ and other.index == self.index)
        )

    def copy(self) -> "RetInstruction":
        return self.__class__(self.index)

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.get(source, self.index)
        if not checker.check_merge(types.return_address_t, entry.type):
            errors.append(Error(source, "expected type returnAddress", "got %s (via %s)" % (entry.type, entry.source)))


class ConditionalJumpInstruction(JumpInstruction, ABC):
    """
    A jump instruction that jumps only if a certain condition is met.
    """

    def __repr__(self) -> str:
        return "<ConditionalJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )


class UnaryComparisonJumpInstruction(ConditionalJumpInstruction, ABC):
    """
    A conditional jump that compares one value to a fixed value.
    """

    type_: BaseType = ...

    def __repr__(self) -> str:
        return "<UnaryComparisonJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        if self.type_ is None:
            entry = state.pop(source)
            if not checker.check_reference(entry.type):
                errors.append(Error(source, "expected reference type", "got %s (via %s)" % (entry.type, entry.source)))
        else:
            entry, *_ = state.pop(source, self.type_.internal_size, tuple_=True)

            if not checker.check_merge(self.type_, entry.type):
                errors.append(Error(
                    source, "expected type %s" % self.type_, "got %s (via %s)" % (entry.type, entry.source),
                ))


class BinaryComparisonJumpInstruction(ConditionalJumpInstruction, ABC):
    """
    A conditional jump instruction that comapares two values.
    """

    type_: BaseType = ...

    def __repr__(self) -> str:
        return "<BinaryComparisonJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        if self.type_ is None:
            entry_a, entry_b = state.pop(source, 2)
        else:
            entry_a, *_ = state.pop(source, self.type_.internal_size, tuple_=True)
            entry_b, *_ = state.pop(source, self.type_.internal_size, tuple_=True)

        if not checker.check_merge(self.type_, entry_a.type):
            errors.append(Error(
                source, "expected type %s" % self.type_, "got %s (via %s)" % (entry_a.type, entry_a.source),
            ))
        if not checker.check_merge(self.type_, entry_b.type):
            errors.append(Error(
                source, "expected type %s" % self.type_, "got %s (via %s)" % (entry_b.type, entry_b.source),
            ))


class TableSwitchInstruction(Instruction, ABC):
    """
    Continues execution at the address in the jump table, given an index on the top of the stack.
    """

    __slots__ = ("default", "low", "high", "offsets")

    def __init__(self, default: int, low: int, high: int, offsets: Iterable[int]) -> None:
        self.default = default
        self.low = low
        self.high = high
        self.offsets = list(offsets)

    def __repr__(self) -> str:
        return "<TableSwitchInstruction(opcode=0x%x, mnemonic=%s, default=%s, low=%i, high=%i, offsets=%r) at %x>" % (
            self.opcode, self.mnemonic, self.default, self.low, self.high, self.offsets, id(self),
        )
               
    def __str__(self) -> str:
        if self.default is None:
            return "%s %i to %i" % (self.mnemonic, self.low, self.high)
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

    def copy(self) -> "TableSwitchInstruction":
        return self.__class__(self.default, self.low, self.high, self.offsets)

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

    def get_size(self, offset: int, wide: bool = False) -> int:
        return 1 + 3 - offset % 4 + 12 + 4 * len(self.offsets)

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_merge(types.int_t, entry.type):
            errors.append(Error(source, "expected type int", "got %s (via %s)" % (entry.type, entry.source)))


class LookupSwitchInstruction(Instruction, ABC):  # FIXME: Sorting required?
    """
    Continues execution at the address in the jump table, given a key match on the top of the stack.
    """

    __slots__ = ("default", "offsets")

    def __init__(self, default: int, offsets: Dict[int, int]) -> None:
        self.default = default
        self.offsets = offsets.copy()

    def __repr__(self) -> str:
        return "<LookupSwitchInstruction(opcode=0x%x, mnemonic=%s, default=%s, offsets=%r) at %x>" % (
            self.opcode, self.mnemonic, self.default, self.offsets, id(self),
        )
               
    def __str__(self) -> str:
        if self.default is None:
            return self.mnemonic
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

    def copy(self) -> "LookupSwitchInstruction":
        return self.__class__(self.default, self.offsets)

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
        for match, offset in sorted(self.offsets.items(), key=lambda item: item[0]):
            buffer.write(struct.pack(">ii", match, offset))

    def get_size(self, offset: int, wide: bool = False) -> int:
        return 1 + 3 - offset % 4 + 8 + 8 * len(self.offsets)

    def trace(self, source: BlockInstruction, state: State, errors: List[Error], checker: TypeChecker) -> None:
        entry = state.pop(source)
        if not checker.check_merge(types.int_t, entry.type):
            errors.append(Error(source, "expected type int", "got %s (via %s)" % (entry.type, entry.source)))

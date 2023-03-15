#!/usr/bin/env python3

"""
Control flow related instructions.
"""

import struct
from enum import Enum
from typing import Any, Dict, IO, Iterable, Optional

from . import Instruction
from ... import types
from ...analysis.trace import Entry, Frame
from ...classfile import ClassFile
from ...types import BaseType


class JumpInstruction(Instruction):
    """
    An instruction that jumps to a bytecode offset.
    """

    __slots__ = ("offset",)

    def __init__(self, offset: Optional[int] = None) -> None:
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
        return (type(other) is type(self) and other.offset == self.offset) or other is type(self)

    def copy(self) -> "JumpInstruction":
        return self.__class__(self.offset)

    def trace(self, frame: Frame) -> "JumpInstruction.Troolean":
        """
        :return: will this jump instruction actually jump?
        """

        return JumpInstruction.Troolean.ALWAYS

    # ------------------------------ Classes ------------------------------ #

    class Troolean(Enum):
        """
        A three-state enum for representing jump predicates.
        """

        ALWAYS = 0
        MAYBE  = 1
        NEVER  = 2


class JsrInstruction(JumpInstruction):
    """
    A jump to subroutine instruction.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "<JsrInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def trace(self, frame: Frame) -> JumpInstruction.Troolean:
        frame.push(types.return_address_t)
        return JumpInstruction.Troolean.ALWAYS


class RetInstruction(JumpInstruction):
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
        return (type(other) is type(self) and other.index == self.index) or other is type(self)

    def copy(self) -> "RetInstruction":
        return self.__class__(self.index)

    def trace(self, frame: Frame) -> JumpInstruction.Troolean:
        frame.get(self.index, expect=types.return_address_t)
        return JumpInstruction.Troolean.ALWAYS


class ConditionalJumpInstruction(JumpInstruction):
    """
    A jump instruction that jumps only if a certain condition is met.
    """

    __slots__ = ()

    EQ = 0
    NE = 1
    LT = 2
    GE = 3
    GT = 4
    LE = 5

    comparison: int = ...

    def __repr__(self) -> str:
        return "<ConditionalJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )


class UnaryComparisonJumpInstruction(ConditionalJumpInstruction):
    """
    A conditional jump that compares one value to a fixed value.
    """

    __slots__ = ()

    type_: BaseType = ...

    def __repr__(self) -> str:
        return "<UnaryComparisonJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def trace(self, frame: Frame) -> JumpInstruction.Troolean:
        if self.type_ is not None:
            frame.pop(self.type_.internal_size, expect=self.type_)
        else:
            frame.pop(expect=None)

        return JumpInstruction.Troolean.MAYBE


class BinaryComparisonJumpInstruction(ConditionalJumpInstruction):
    """
    A conditional jump instruction that compares two values.
    """

    __slots__ = ()

    type_: BaseType = ...

    def __repr__(self) -> str:
        return "<BinaryComparisonJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def trace(self, frame: Frame) -> JumpInstruction.Troolean:
        if self.type_ is not None:
            entry_a, *_ = frame.pop(self.type_.internal_size, tuple_=True, expect=self.type_)
            entry_b, *_ = frame.pop(self.type_.internal_size, tuple_=True, expect=self.type_)
        else:
            entry_a, entry_b = frame.pop(2, expect=None)

        return JumpInstruction.Troolean.MAYBE  # self.compare(entry_a, entry_b)

    # @abstractmethod
    # def compare(self, entry_a: Entry, entry_b: Entry) -> JumpInstruction.Troolean:
    #     """
    #     Compares the two entries provided to this instruction and returns whether this jump will occur.
    #
    #     :param entry_a: The first entry.
    #     :param entry_b: The second entry.
    #     :return: The troolean indicating whether this jump will occur.
    #     """
    #
    #     ...


class TableSwitchInstruction(Instruction):
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
        return other is type(self) or (
            type(other) is type(self) and
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

    def trace(self, frame: Frame) -> None:
        entry = frame.pop(expect=types.int_t)


class LookupSwitchInstruction(Instruction):
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
        return other is type(self) or (
            type(other) is type(self) and
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

    def trace(self, frame: Frame) -> None:
        entry = frame.pop(expect=types.int_t)

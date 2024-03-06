#!/usr/bin/env python3

__all__ = (
    "JumpInstruction", "SwitchInstruction",
    "ConditionalJumpInstruction",
    "UnaryComparisonJumpInstruction", "BinaryComparisonJumpInstruction",
    "JsrInstruction", "RetInstruction",
    "TableSwitchInstruction", "LookupSwitchInstruction",
)

"""
Control flow related instructions.
"""

import operator
import struct
import typing
from enum import Enum
from typing import Any, IO

from . import Instruction
from ..types import int_t, return_address_t, ReturnAddress, Type, Verification

if typing.TYPE_CHECKING:
    from ..analysis import Context
    from ..classfile import ClassFile


class JumpInstruction(Instruction):
    """
    An instruction that jumps to a bytecode offset.
    """

    __slots__ = ("offset",)

    def __init__(self, offset: int | None = None) -> None:
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
        return type(self)(self.offset)


class SwitchInstruction(Instruction):
    """
    The base class for switch instructions.
    """

    __slots__ = ("default", "offsets")  # As a bare minimum, they must have a default and jump table

    operands = {"_": ">B"}  # Dummy operands so that the instruction is not mistaken for immutable.

    def __init__(self, default: int, offsets: dict[int, int]) -> None:
        """
        :param default: The default offset to jump to.
        :param offsets: The offsets to jump to, keyed by the index/value in the jump table.
        """

        self.default = default
        self.offsets = offsets.copy()

    def __repr__(self) -> str:
        return "<SwitchInstruction(opcode=0x%x, mnemonic=%s, default=%s, offsets=%r) at %x>" % (
            self.opcode, self.mnemonic, self.default, self.offsets, id(self),
        )


class JsrInstruction(JumpInstruction):
    """
    A jump to subroutine instruction.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "<JsrInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def trace(self, context: "Context") -> None:
        context.push(ReturnAddress(context.source))


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
        return type(self)(self.index)

    def trace(self, context: "Context") -> None:
        context.constrain(context.get(self.index), return_address_t)


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

    type: Type = ...

    def __repr__(self) -> str:
        return "<UnaryComparisonJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def trace(self, context: "Context") -> None:
        *_, entry = context.pop(1 + self.type.wide, as_tuple=True)
        context.constrain(entry, self.type)


class BinaryComparisonJumpInstruction(ConditionalJumpInstruction):
    """
    A conditional jump instruction that compares two values.
    """

    __slots__ = ()

    type: Verification = ...

    def __repr__(self) -> str:
        return "<BinaryComparisonJumpInstruction(opcode=0x%x, mnemonic=%s, offset=%s) at %x>" % (
            self.opcode, self.mnemonic, self.offset, id(self),
        )

    def trace(self, context: "Context") -> None:
        *_, entry_a = context.pop(1 + self.type.wide, as_tuple=True)
        context.constrain(entry_a, self.type)
        *_, entry_b = context.pop(1 + self.type.wide, as_tuple=True)
        context.constrain(entry_b, self.type)

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


class TableSwitchInstruction(SwitchInstruction):
    """
    Continues execution at the address in the jump table, given an index on the top of the stack.
    """

    __slots__ = ("low", "high")

    def __init__(self, default: int, low: int, high: int, offsets: dict[int, int]) -> None:
        """
        :param low: The lowest index in the jump table.
        :param high: The highest index in the jump table.
        """

        super().__init__(default, offsets)

        self.low = low
        self.high = high

    def __repr__(self) -> str:
        return "<TableSwitchInstruction(opcode=0x%x, mnemonic=%s, default=%s, low=%i, high=%i, offsets=%r) at %x>" % (
            self.opcode, self.mnemonic, self.default, self.low, self.high, self.offsets, id(self),
        )
               
    def __str__(self) -> str:
        if self.default is None:
            return "%s %i to %i" % (self.mnemonic, self.low, self.high)
        return "%s %i to %i default %+i offsets %s" % (
            self.mnemonic, self.low, self.high, self.default, 
            # The next line is not pretty, be warned
            ", ".join(map("%+i".__mod__, map(operator.itemgetter(1), sorted(self.offsets.items(), key=operator.itemgetter(0))))),
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
        return type(self)(self.default, self.low, self.high, self.offsets)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        buffer.read((4 - buffer.tell() % 4) % 4)  # Padding

        self.default, self.low, self.high = struct.unpack(">iii", buffer.read(12))

        self.offsets = {}
        for index in range((self.high - self.low) + 1):
            self.offsets[index], = struct.unpack(">i", buffer.read(4))

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        buffer.write(b"\x00" * ((4 - buffer.tell() % 4) % 4))
        buffer.write(struct.pack(">iii", self.default, self.low, self.high))
        for _, offset in sorted(self.offsets.items(), key=operator.itemgetter(0)):
            buffer.write(struct.pack(">i", offset))

    def get_size(self, offset: int, wide: bool = False) -> int:
        return 1 + 3 - offset % 4 + 12 + 4 * len(self.offsets)

    def trace(self, context: "Context") -> None:
        context.constrain(context.pop(), int_t)


class LookupSwitchInstruction(SwitchInstruction):
    """
    Continues execution at the address in the jump table, given a key match on the top of the stack.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "<LookupSwitchInstruction(opcode=0x%x, mnemonic=%s, default=%s, offsets=%r) at %x>" % (
            self.opcode, self.mnemonic, self.default, self.offsets, id(self),
        )
               
    def __str__(self) -> str:
        if self.default is None:
            return self.mnemonic
        return "%s default %+i offsets %s" % (
            self.mnemonic, self.default, 
            ", ".join(map("%i: %+i".__mod__, self.offsets.items())),
        )

    def __eq__(self, other: Any) -> bool:
        return other is type(self) or (
            type(other) is type(self) and
            other.default == self.default and
            other.offsets == self.offsets
        )

    def copy(self) -> "LookupSwitchInstruction":
        return type(self)(self.default, self.offsets)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        buffer.read((4 - buffer.tell() % 4) % 4)

        self.default, = struct.unpack(">i", buffer.read(4))

        self.offsets = {}
        count, = struct.unpack(">i", buffer.read(4))
        for index in range(count):
            match, offset = struct.unpack(">ii", buffer.read(8))
            self.offsets[match] = offset

    def write(self, class_file: "ClassFile", buffer: IO[bytes], wide: bool) -> None:
        buffer.write(b"\x00" * ((4 - (buffer.tell() % 4)) % 4))
        buffer.write(struct.pack(">ii", self.default, len(self.offsets)))
        for match, offset in sorted(self.offsets.items(), key=operator.itemgetter(0)):
            buffer.write(struct.pack(">ii", match, offset))

    def get_size(self, offset: int, wide: bool = False) -> int:
        return 1 + 3 - offset % 4 + 8 + 8 * len(self.offsets)

    def trace(self, context: "Context") -> None:
        context.constrain(context.pop(), int_t)

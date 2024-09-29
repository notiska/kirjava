#!/usr/bin/env python3

__all__ = (
    "nop", "wide",
    "monitorenter", "monitorexit",
    "breakpoint_", "impdep1", "impdep2",
    "Nop", "Wide", "MonitorEnter", "MonitorExit", "Internal", "Unknown",
)

import typing
from os import SEEK_CUR
from typing import IO

from . import Instruction
# from ...model.types import *
# from ...model.values.constants import Null

if typing.TYPE_CHECKING:
    # from ..analyse.frame import Frame
    # from ..analyse.state import State
    from ..fmt import ConstPool


class Nop(Instruction):
    """
    A `nop` instruction.

    Does nothing.
    """

    __slots__ = ()

    throws = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Nop":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Nop(offset=%i)>" % self.offset
        return "<Nop>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Nop)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     ...


class Wide(Instruction):  # TODO: Test that we can have random wide instructions thrown in.
    """
    A `wide` instruction.

    Indicates that the following instruction is a wide mutation, if applicable.
    """

    __slots__ = ()

    throws = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Instruction:
        # Note: random wide instructions can cause the JVM to hang, they're not valid at all. We'll parse them as-is
        #       here, though.
        try:
            opcode, = stream.read(1)
        except ValueError:
            return cls()
        subclass: type[Instruction] | None = Instruction.lookup(opcode, True)
        if subclass is None:
            stream.seek(-1, SEEK_CUR)  # Pretend we didn't just read another opcode.
            return cls()
        return subclass._read(stream, pool)

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Wide(offset=%i)>" % self.offset
        return "<Wide>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Wide)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     ...


class MonitorEnter(Instruction):
    """
    A `monitorenter` instruction.

    Enters a monitor for the object reference on the stack.
    """

    __slots__ = ()

    throws = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "MonitorEnter":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<MonitorEnter(offset=%i)>" % self.offset
        return "<MonitorEnter>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MonitorEnter)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.pop(reference_t, self)
    #     if isinstance(value.value, Null) or value.type is null_t:
    #         frame.throw(Class("java/lang/NullPointerException"), self)
    #     return state.step(self, (value,))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     value, = step.inputs
    #     codegen.emit(IRMonitorEnter(step, codegen.value(value)))


class MonitorExit(Instruction):
    """
    A `monitorexit` instruction.

    Exits a monitor for the object reference on the stack.
    """

    __slots__ = ()

    throws = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "MonitorExit":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<MonitorExit(offset=%i)>" % self.offset
        return "<MonitorExit>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MonitorExit)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.pop(reference_t, self)
    #     if isinstance(value.value, Null) or value.type is null_t:
    #         frame.throw(Class("java/lang/NullPointerException"), self)
    #     return state.step(self, (value,))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     value, = step.inputs
    #     codegen.emit(IRMonitorExit(step, codegen.value(value)))


class Internal(Instruction):  # FIXME: Too broad.
    """
    An internal instruction base.
    """

    __slots__ = ()

    throws = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Internal":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Internal(offset=%i, opcode=0x%02x)>" % (self.offset, self.opcode)
        return "<Internal(opcode=0x%02x)>" % self.opcode

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Internal) and self.opcode == other.opcode

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))


class Unknown(Instruction):
    """
    An instruction with an unknown opcode.

    Attributes
    ----------
    opcode: int
        The reported opcode of the instruction.
    """

    __slots__ = ("opcode",)

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Unknown":
        raise ValueError("can't read unknown opcode")

    def __init__(self, opcode: int) -> None:
        super().__init__()
        self.opcode = opcode

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<Unknown(offset=%i, opcode=0x%02x)>" % (self.offset, self.opcode)
        return "<Unknown(opcode=0x%02x)>" % self.opcode

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i:opcode(0x%02x)" % (self.offset, self.opcode)
        return "opcode(0x%02x)" % self.opcode

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Unknown) and self.opcode == other.opcode

    def copy(self) -> "Unknown":
        copy = type(self)(self.opcode)
        copy.offset = self.offset
        return copy

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))


nop   = Nop.make(0x00, "nop")
wide = Wide.make(0xc4, "wide")

monitorenter = MonitorEnter.make(0xc2, "monitorenter")
monitorexit   = MonitorExit.make(0xc3, "monitorexit")

breakpoint_ = Internal.make(0xca, "breakpoint")
impdep1     = Internal.make(0xfe, "impdep1")
impdep2     = Internal.make(0xff, "impdep2")

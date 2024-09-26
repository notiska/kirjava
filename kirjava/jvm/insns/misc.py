#!/usr/bin/env python3

__all__ = (
    "nop", "wide",
    "monitorenter", "monitorexit",
    "breakpoint_", "impdep1", "impdep2",
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
        return "<Nop(offset=%s)>" % self.offset

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
        return "<Wide(offset=%s)>" % self.offset

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
        return "<MonitorEnter(offset=%s)>" % self.offset

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
        return "<MonitorExit(offset=%s)>" % self.offset

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
        return "<Internal(offset=%s, mnemonic=%s)>" % (self.offset, self.mnemonic)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Internal) and self.opcode == other.opcode

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))


nop   = Nop.make(0x00, "nop")
wide = Wide.make(0xc4, "wide")

monitorenter = MonitorEnter.make(0xc2, "monitorenter")
monitorexit   = MonitorExit.make(0xc3, "monitorexit")

breakpoint_ = Internal.make(0xca, "breakpoint")
impdep1     = Internal.make(0xfe, "impdep1")
impdep2     = Internal.make(0xff, "impdep2")

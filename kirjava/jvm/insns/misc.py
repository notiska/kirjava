#!/usr/bin/env python3

__all__ = (
    "nop", "wide",
    "monitorenter", "monitorexit",
    "breakpoint_", "impdep1", "impdep2",
)

import typing
from typing import IO

from . import Instruction
from ...model.types import *
from ...model.values.constants import Null

if typing.TYPE_CHECKING:
    from ..analyse.frame import Frame
    from ..analyse.state import State
    from ..fmt import ConstPool


class Nop(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Nop":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    def trace(self, frame: "Frame", state: "State") -> None:
        ...


class Wide(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Wide":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    def trace(self, frame: "Frame", state: "State") -> None:
        ...


class MonitorEnter(Instruction):

    __slots__ = ()

    can_throw = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "MonitorEnter":
        return cls()

    def __init__(self) -> None:
        self.offset = None

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

    __slots__ = ()

    can_throw = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "MonitorExit":
        return cls()

    def __init__(self) -> None:
        self.offset = None

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


class Internal(Instruction):

    __slots__ = ()

    can_throw = False  # FIXME: Debatable, will have to get around to this in the future.

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Internal":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))


nop   = Nop.make(0x00, "nop")
wide = Wide.make(0xc4, "wide")

monitorenter = MonitorEnter.make(0xc2, "monitorenter")
monitorexit   = MonitorExit.make(0xc3, "monitorexit")

breakpoint_ = Internal.make(0xca, "breakpoint")
impdep1     = Internal.make(0xfe, "impdep1")
impdep2     = Internal.make(0xff, "impdep2")

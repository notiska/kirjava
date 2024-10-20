#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "nop", "wide",
    "monitorenter", "monitorexit",
    "breakpoint_", "impdep1", "impdep2",
    "Nop", "Wide", "MonitorEnter", "MonitorExit", "Internal", "Unknown",
)

import sys
import typing
from os import SEEK_CUR
from typing import IO

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from . import Instruction
from ...model.types import Class
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

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Nop(offset={self.offset})>"
        return "<Nop>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Nop)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     ...


class Wide(Instruction):
    """
    A `wide` instruction.

    Indicates that the following instruction is a wide mutation, if applicable.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    _cache: dict[int, type[Instruction] | None] = {}

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Instruction:  # type: ignore[override]
        # Note: random wide instructions can cause the JVM to hang, they're not valid at all. We'll parse them as-is
        #       here, though.
        try:
            opcode, = stream.read(1)
        except ValueError:
            return cls()
        subclass: type[Instruction] | None = cls._cache.get(opcode)
        if subclass is None:
            subclass = Instruction.lookup(opcode, True)
            cls._cache[opcode] = subclass
        if subclass is None:
            stream.seek(-1, SEEK_CUR)  # Pretend we didn't just read another opcode.
            return cls()
        return subclass._read(stream, pool)

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Wide(offset={self.offset})>"
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

    lt_throws = frozenset()
    rt_throws = frozenset({Class("java/lang/NullPointerException")})
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<MonitorEnter(offset={self.offset})>"
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

    lt_throws = frozenset()
    rt_throws = frozenset({Class("java/lang/IllegalMonitorStateException"), Class("java/lang/NullPointerException")})
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<MonitorExit(offset={self.offset})>"
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
    An internal instruction.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Internal(offset={self.offset}, opcode=0x{self.opcode:02x})>"
        return f"<Internal(opcode=0x{self.opcode:02x})>"

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

    lt_throws = frozenset()  # FIXME: What exception is thrown upon illegal opcode?
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        raise ValueError("can't read unknown opcode")

    def __init__(self, opcode: int) -> None:
        super().__init__()
        self.opcode = opcode

    def __copy__(self) -> "Unknown":
        copy = type(self)(self.opcode)
        copy.offset = self.offset
        return copy

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Unknown(offset={self.offset}, opcode=0x{self.opcode:02x})>"
        return f"<Unknown(opcode=0x{self.opcode:02x})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:opcode(0x{self.opcode:02x})"
        return f"opcode(0x{self.opcode:02x})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Unknown) and self.opcode == other.opcode

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))


nop   = Nop.make(0x00, "nop")
wide = Wide.make(0xc4, "wide")

monitorenter = MonitorEnter.make(0xc2, "monitorenter")
monitorexit   = MonitorExit.make(0xc3, "monitorexit")

breakpoint_ = Internal.make(0xca, "breakpoint")
impdep1     = Internal.make(0xfe, "impdep1")
impdep2     = Internal.make(0xff, "impdep2")

#!/usr/bin/env python3

__all__ = (
    "iload", "lload", "fload", "dload", "aload",
    "iload_w", "lload_w", "fload_w", "dload_w", "aload_w",
    "iload_0", "iload_1", "iload_2", "iload_3",
    "lload_0", "lload_1", "lload_2", "lload_3",
    "fload_0", "fload_1", "fload_2", "fload_3",
    "dload_0", "dload_1", "dload_2", "dload_3",
    "aload_0", "aload_1", "aload_2", "aload_3",
    "istore", "lstore", "fstore", "dstore", "astore",
    "istore_w", "lstore_w", "fstore_w", "dstore_w", "astore_w",
    "istore_0", "istore_1", "istore_2", "istore_3",
    "lstore_0", "lstore_1", "lstore_2", "lstore_3",
    "fstore_0", "fstore_1", "fstore_2", "fstore_3",
    "dstore_0", "dstore_1", "dstore_2", "dstore_3",
    "astore_0", "astore_1", "astore_2", "astore_3",
    "iinc", "iinc_w",
    "LoadLocal", "StoreLocal",
    "LoadLocalAt", "StoreLocalAt", "IInc",
    "LoadLocalAtWide", "StoreLocalAtWide", "IIncWide",
)

import typing
from typing import IO

from . import Instruction
from .misc import wide
from .._struct import *
from ...model.types import *
# from ...model.values.constants import *

if typing.TYPE_CHECKING:
    # from ..analyse.frame import Frame
    # from ..analyse.state import State
    from ..fmt import ConstPool
    # from ..verify import Verifier


class LoadLocal(Instruction):
    """
    A local variable load instruction base.

    Loads a local variable from the provided index.

    Attributes
    ----------
    type: Type
        The expected type of the local variable.
    index: int
        The local variable array index to load from.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    type: Type
    index: int

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "LoadLocal":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<LoadLocal(offset=%i, type=%s, index=%i)>" % (self.offset, self.type, self.index)
        return "<LoadLocal(type=%s, index=%i)>" % (self.type, self.index)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LoadLocal) and self.opcode == other.opcode

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     return state.step(self, (), frame.push(frame.load(self.index, self.type, self), self))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     ...


class StoreLocal(Instruction):
    """
    A local variable store instruction base.

    Attributes
    ----------
    type: Type
        The type of value to store.
    index: int
        The local variable array index to store to.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    type: Type
    index: int

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "StoreLocal":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<StoreLocal(offset=%i, type=%s, index=%i)>" % (self.offset, self.type, self.index)
        return "<StoreLocal(type=%s, index=%i)>" % (self.type, self.index)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StoreLocal) and self.opcode == other.opcode

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     # astore instructions have special cases for return addresses, which need to be accounted for.
    #     if self.type is reference_t:
    #         entry = frame.pop(None, self)
    #         if not isinstance(entry.type, ReturnAddress):
    #             entry = entry.constrain(reference_t, self)
    #     else:
    #         entry = frame.pop(self.type, self)
    #     frame.store(self.index, entry, self)
    #     return state.step(self, (entry,))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     ...


class LoadLocalAt(LoadLocal):
    """
    A local variable load instruction base, where the index is explicitly provided.
    """

    __slots__ = ("index",)

    type: Type

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "LoadLocalAt":
        index, = stream.read(1)
        return cls(index)

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<LoadLocalAt(offset=%i, type=%s, index=%i)>" % (self.offset, self.type, self.index)
        return "<LoadLocalAt(type=%s, index=%i)>" % (self.type, self.index)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i:%s(%i)" % (self.offset, self.mnemonic, self.index)
        return "%s(%i)" % (self.mnemonic, self.index)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LoadLocalAt) and self.opcode == other.opcode and self.index == other.index

    def copy(self) -> "LoadLocalAt":
        copy = type(self)(self.index)
        copy.offset = self.offset
        return copy

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, self.index)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.index <= 255):
    #         verifier.report("invalid local index", instruction=self)


class StoreLocalAt(StoreLocal):
    """
    A local variable store instruction base, where the index is explicitly provided.
    """

    __slots__ = ("index",)

    type: Type

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "StoreLocalAt":
        index, = stream.read(1)
        return cls(index)

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<StoreLocalAt(offset=%i, type=%s, index=%i)>" % (self.offset, self.type, self.index)
        return "<StoreLocalAt(type=%s, index=%i)>" % (self.type, self.index)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i:%s(%i)" % (self.offset, self.mnemonic, self.index)
        return "%s(%i)" % (self.mnemonic, self.index)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StoreLocalAt) and self.opcode == other.opcode and self.index == other.index

    def copy(self) -> "StoreLocalAt":
        copy = type(self)(self.index)
        copy.offset = self.offset
        return copy

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, self.index)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.index <= 255):
    #         verifier.report("invalid local index", instruction=self)


class IInc(Instruction):
    """
    An `iinc` instruction.

    Increments a local variable by a fixed amount.

    Attributes
    ----------
    index: int
        The index of the local variable to increment.
    value: int
        The signed amount to increment the local variable by.
    """

    __slots__ = ("index", "value")

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "IInc":
        index, value = unpack_Bb(stream.read(2))
        return cls(index, value)

    def __init__(self, index: int, value: int) -> None:
        super().__init__()
        self.index = index
        self.value = value

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<IInc(offset=%i, index=%i, value=%i)>" % (self.offset, self.index, self.value)
        return "<IInc(index=%i, value=%i)>" % (self.index, self.value)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i:iinc(%i,%+i)" % (self.offset, self.index, self.value)
        return "iinc(%i,%+i)" % (self.index, self.value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IInc) and self.index == other.index and self.value == other.value

    def copy(self) -> "IInc":
        copy = iinc(self.index, self.value)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BBb(self.opcode, self.index, self.value))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.index <= 255):
    #         verifier.report("invalid local index", instruction=self)
    #     if not (-128 <= self.value <= 127):
    #         verifier.report("invalid increment value", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.load(self.index, int_t, self)
    #     metadata = Source.Metadata(self, logger)
    #     if isinstance(value.value, Integer):
    #         result = frame.store(self.index, value.value + Integer(self.value), self)
    #         metadata.debug("%s + %i", value.value, self.value)
    #     else:
    #         result = frame.store(self.index, int_t, self)
    #     return state.step(self, (value,), result, metadata)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     value_var = codegen.variable(int_t)
    #     out_var = codegen.variable(int_t)
    #     step.output.value = out_var
    #     codegen.emit(Load(step, value_var, Integer(self.value)))
    #     codegen.emit(Addition(step, out_var, value_var, codegen.value(step.inputs[0])))


class LoadLocalAtWide(LoadLocalAt):
    """
    A load local instruction with a wide mutation.
    """

    __slots__ = ()

    mutated = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "LoadLocalAtWide":
        index, = unpack_H(stream.read(2))
        return cls(index)

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<LoadLocalAtWide(offset=%i, type=%s, index=%i)>" % (self.offset, self.type, self.index)
        return "<LoadLocalAtWide(type=%s, index=%i)>" % (self.type, self.index)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LoadLocalAtWide) and self.opcode == other.opcode and self.index == other.index

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BBH(wide.opcode, self.opcode, self.index))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.index <= 65535):
    #         verifier.report("invalid local index", instruction=self)


class StoreLocalAtWide(StoreLocalAt):
    """
    A store local instruction with a wide mutation.
    """

    __slots__ = ()

    mutated = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "StoreLocalAtWide":
        index, = unpack_H(stream.read(2))
        return cls(index)

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<StoreLocalAtWide(offset=%i, index=%i)>" % (self.offset, self.index)
        return "<StoreLocalAtWide(index=%i)>" % self.index

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StoreLocalAtWide) and self.opcode == other.opcode and self.index == other.index

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BBH(wide.opcode, self.opcode, self.index))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.index <= 65535):
    #         verifier.report("invalid local index", instruction=self)


class IIncWide(IInc):
    """
    An `iinc` instruction with a wide mutation.
    """

    __slots__ = ()

    mutated = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "IIncWide":
        index, value = unpack_Hh(stream.read(4))
        return cls(index, value)

    def __repr__(self) -> str:
        if self.offset is not None:
            return "<IIncWide(offset=%i, index=%i, value=%i)>" % (self.offset, self.index, self.value)
        return "<IIncWide(index=%i, value=%i)>" % (self.index, self.value)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i:iinc_w(%i,%+i)" % (self.offset, self.index, self.value)
        return "iinc_w(%i,%+i)" % (self.index, self.value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IIncWide) and self.index == other.index and self.value == other.value

    def copy(self) -> "IIncWide":
        copy = iinc_w(self.index, self.value)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BBHh(wide.opcode, self.opcode, self.index, self.value))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.index <= 65535):
    #         verifier.report("invalid local index", instruction=self)
    #     if not (-32768 <= self.value <= 32767):
    #         verifier.report("invalid increment value", instruction=self)


iload = LoadLocalAt.make(0x15, "iload", type=int_t)
lload = LoadLocalAt.make(0x16, "lload", type=long_t)
fload = LoadLocalAt.make(0x17, "fload", type=float_t)
dload = LoadLocalAt.make(0x18, "dload", type=double_t)
aload = LoadLocalAt.make(0x19, "aload", type=reference_t)

iload_w = LoadLocalAtWide.make(0x15, "iload_w", type=int_t)
lload_w = LoadLocalAtWide.make(0x16, "lload_w", type=long_t)
fload_w = LoadLocalAtWide.make(0x17, "fload_w", type=float_t)
dload_w = LoadLocalAtWide.make(0x18, "dload_w", type=double_t)
aload_w = LoadLocalAtWide.make(0x19, "aload_w", type=reference_t)

iload_0 = LoadLocal.make(0x1a, "iload_0", type=int_t, index=0)
iload_1 = LoadLocal.make(0x1b, "iload_1", type=int_t, index=1)
iload_2 = LoadLocal.make(0x1c, "iload_2", type=int_t, index=2)
iload_3 = LoadLocal.make(0x1d, "iload_3", type=int_t, index=3)

lload_0 = LoadLocal.make(0x1e, "lload_0", type=long_t, index=0)
lload_1 = LoadLocal.make(0x1f, "lload_1", type=long_t, index=1)
lload_2 = LoadLocal.make(0x20, "lload_2", type=long_t, index=2)
lload_3 = LoadLocal.make(0x21, "lload_3", type=long_t, index=3)

fload_0 = LoadLocal.make(0x22, "fload_0", type=float_t, index=0)
fload_1 = LoadLocal.make(0x23, "fload_1", type=float_t, index=1)
fload_2 = LoadLocal.make(0x24, "fload_2", type=float_t, index=2)
fload_3 = LoadLocal.make(0x25, "fload_3", type=float_t, index=3)

dload_0 = LoadLocal.make(0x26, "dload_0", type=double_t, index=0)
dload_1 = LoadLocal.make(0x27, "dload_1", type=double_t, index=1)
dload_2 = LoadLocal.make(0x28, "dload_2", type=double_t, index=2)
dload_3 = LoadLocal.make(0x29, "dload_3", type=double_t, index=3)

aload_0 = LoadLocal.make(0x2a, "aload_0", type=reference_t, index=0)
aload_1 = LoadLocal.make(0x2b, "aload_1", type=reference_t, index=1)
aload_2 = LoadLocal.make(0x2c, "aload_2", type=reference_t, index=2)
aload_3 = LoadLocal.make(0x2d, "aload_3", type=reference_t, index=3)

istore = StoreLocalAt.make(0x36, "istore", type=int_t)
lstore = StoreLocalAt.make(0x37, "lstore", type=long_t)
fstore = StoreLocalAt.make(0x38, "fstore", type=float_t)
dstore = StoreLocalAt.make(0x39, "dstore", type=double_t)
astore = StoreLocalAt.make(0x3a, "astore", type=reference_t)

istore_w = StoreLocalAtWide.make(0x36, "istore_w", type=int_t)
lstore_w = StoreLocalAtWide.make(0x37, "lstore_w", type=long_t)
fstore_w = StoreLocalAtWide.make(0x38, "fstore_w", type=float_t)
dstore_w = StoreLocalAtWide.make(0x39, "dstore_w", type=double_t)
astore_w = StoreLocalAtWide.make(0x3a, "astore_w", type=reference_t)

istore_0 = StoreLocal.make(0x3b, "istore_0", type=int_t, index=0)
istore_1 = StoreLocal.make(0x3c, "istore_1", type=int_t, index=1)
istore_2 = StoreLocal.make(0x3d, "istore_2", type=int_t, index=2)
istore_3 = StoreLocal.make(0x3e, "istore_3", type=int_t, index=3)

lstore_0 = StoreLocal.make(0x3f, "lstore_0", type=long_t, index=0)
lstore_1 = StoreLocal.make(0x40, "lstore_1", type=long_t, index=1)
lstore_2 = StoreLocal.make(0x41, "lstore_2", type=long_t, index=2)
lstore_3 = StoreLocal.make(0x42, "lstore_3", type=long_t, index=3)

fstore_0 = StoreLocal.make(0x43, "fstore_0", type=float_t, index=0)
fstore_1 = StoreLocal.make(0x44, "fstore_1", type=float_t, index=1)
fstore_2 = StoreLocal.make(0x45, "fstore_2", type=float_t, index=2)
fstore_3 = StoreLocal.make(0x46, "fstore_3", type=float_t, index=3)

dstore_0 = StoreLocal.make(0x47, "dstore_0", type=double_t, index=0)
dstore_1 = StoreLocal.make(0x48, "dstore_1", type=double_t, index=1)
dstore_2 = StoreLocal.make(0x49, "dstore_2", type=double_t, index=2)
dstore_3 = StoreLocal.make(0x4a, "dstore_3", type=double_t, index=3)

astore_0 = StoreLocal.make(0x4b, "astore_0", type=reference_t, index=0)
astore_1 = StoreLocal.make(0x4c, "astore_1", type=reference_t, index=1)
astore_2 = StoreLocal.make(0x4d, "astore_2", type=reference_t, index=2)
astore_3 = StoreLocal.make(0x4e, "astore_3", type=reference_t, index=3)

iinc       = IInc.make(0x84, "iinc")
iinc_w = IIncWide.make(0x84, "iinc_w")

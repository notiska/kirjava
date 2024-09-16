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
)

import logging
import typing
from typing import IO

from . import Instruction
from .._struct import *
from ...model.types import *
from ...model.values.constants import *

if typing.TYPE_CHECKING:
    from ..analyse.frame import Frame
    from ..analyse.state import State
    from ..fmt import ConstPool
    from ..verify import Verifier

logger = logging.getLogger("ijd.jvm.insns.local")


class LoadLocal(Instruction):

    __slots__ = ()

    can_throw = False

    type: Type
    index: int

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "LoadLocal":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def __repr__(self) -> str:
        return "<LoadLocal(offset=%s, index=%i)>" % (self.offset, self.index)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     return state.step(self, (), frame.push(frame.load(self.index, self.type, self), self))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     ...


class StoreLocal(Instruction):

    __slots__ = ()

    can_throw = False

    type: Type
    index: int

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "StoreLocal":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def __repr__(self) -> str:
        return "<StoreLocal(offset=%s, index=%i)>" % (self.offset, self.index)

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

    __slots__ = ("index",)

    type: Type

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "LoadLocalAt":
        index, = stream.read(1)
        return cls(index)

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index

    def __repr__(self) -> str:
        return "<LoadLocalAt(offset=%s, index=%i)>" % (self.offset, self.index)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: %s %i" % (self.offset, self.mnemonic, self.index)
        return "%s %i" % (self.mnemonic, self.index)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, self.index)))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.index <= 255):
            verifier.report("invalid local index", instruction=self)


class StoreLocalAt(StoreLocal):

    __slots__ = ("index",)

    type: Type

    @classmethod
    def pool(cls, stream: IO[bytes], pool: "ConstPool") -> "StoreLocalAt":
        index, = stream.read(1)
        return cls(index)

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index

    def __repr__(self) -> str:
        return "<StoreLocalAt(offset=%s, index=%i)>" % (self.offset, self.index)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: %s %i" % (self.offset, self.mnemonic, self.index)
        return "%s %i" % (self.mnemonic, self.index)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, self.index)))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.index <= 255):
            verifier.report("invalid local index", instruction=self)


class IncLocal(Instruction):

    __slots__ = ("index", "value")

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "IncLocal":
        index, value = unpack_Bb(stream.read(2))
        return cls(index, value)

    def __init__(self, index: int, value: int) -> None:
        self.offset = None
        self.index = index
        self.value = value

    def __repr__(self) -> str:
        return "<IncLocal(offset=%s, index=%i, value=%i)>" % (self.offset, self.index, self.value)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: iinc %i by %i" % (self.offset, self.index, self.value)
        return "iinc %i by %i" % (self.index, self.value)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BBb(self.opcode, self.index, self.value))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.index <= 255):
            verifier.report("invalid local index", instruction=self)
        if not (-128 <= self.value <= 127):
            verifier.report("invalid increment value", instruction=self)

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

    __slots__ = ()

    mutate_w = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "LoadLocalAtWide":
        index, = unpack_H(stream.read(2))
        return cls(index)

    def __repr__(self) -> str:
        return "<LoadLocalAtWide(offset=%s, index=%i)>" % (self.offset, self.index)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, self.index))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.index <= 65535):
            verifier.report("invalid local index", instruction=self)


class StoreLocalAtWide(StoreLocalAt):

    __slots__ = ()

    mutate_w = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "StoreLocalAtWide":
        index, = unpack_H(stream.read(2))
        return cls(index)

    def __repr__(self) -> str:
        return "<StoreLocalAtWide(offset=%s, index=%i)>" % (self.offset, self.index)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, self.index))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.index <= 65535):
            verifier.report("invalid local index", instruction=self)


class IncLocalWide(IncLocal):

    __slots__ = ()

    mutate_w = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "IncLocalWide":
        index, value = unpack_Hh(stream.read(4))
        return cls(index, value)

    def __repr__(self) -> str:
        return "<IncLocalWide(offset=%s, index=%i, value=%i)>" % (self.offset, self.index, self.value)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: iinc_w %i by %i" % (self.offset, self.index, self.value)
        return "iinc_w %i by %i" % (self.index, self.value)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHh(self.opcode, self.index, self.value))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.index <= 65535):
            verifier.report("invalid local index", instruction=self)
        if not (-32768 <= self.value <= 32767):
            verifier.report("invalid increment value", instruction=self)


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

iinc       = IncLocal.make(0x84, "iinc")
iinc_w = IncLocalWide.make(0x84, "iinc_w")

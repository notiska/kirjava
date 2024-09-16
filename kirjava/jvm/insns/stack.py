#!/usr/bin/env python3

__all__ = (
    "aconst_null",
    "iconst_m1", "iconst_0", "iconst_1", "iconst_2", "iconst_3", "iconst_4", "iconst_5",
    "lconst_0", "lconst_1",
    "fconst_0", "fconst_1", "fconst_2",
    "dconst_0", "dconst_1",
    "bipush", "sipush",
    "ldc", "ldc_w", "ldc2_w",
    "new",
    "pop", "pop2", "dup", "dup_x1", "dup_x2", "dup2", "dup2_x1", "dup2_x2", "swap",
)

import logging
import typing
from typing import IO

from . import Instruction
from .._struct import *
from ..fmt.constants import *
from ...model.types import *
from ...model.values.constants import *

if typing.TYPE_CHECKING:
    from ..analyse.frame import Frame
    from ..analyse.state import State
    from ..fmt import ConstPool
    from ..verify import Verifier

logger = logging.getLogger("ijd.jvm.insns.stack")


class PushConstant(Instruction):

    __slots__ = ()

    can_throw = False

    constant: Constant

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "PushConstant":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     return state.step(self, (), frame.push(self.constant, self))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     entry = step.output
    #     if entry.value is not None:
    #         return
    #     variable = codegen.variable(entry.type)
    #     codegen.block.insns.append(Load(variable, self.constant))
    #     entry.value = variable


class PushByteConstant(PushConstant):

    __slots__ = ("constant",)

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "PushByteConstant":
        value, = stream.read(1)
        return cls(Integer(value))

    def __init__(self, constant: Integer) -> None:
        super().__init__()
        self.constant: Integer = constant

    def __repr__(self) -> str:
        return "<PushByteConstant(offset=%s, constant=%s)>" % (self.offset, self.constant)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: %s %s" % (self.offset, self.mnemonic, self.constant)
        return "%s %s" % (self.mnemonic, self.constant)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, self.constant.value)))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.constant.value <= 255):
            verifier.report("invalid byte constant value", instruction=self)


class PushShortConstant(PushConstant):

    __slots__ = ("constant",)

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "PushShortConstant":
        value, = unpack_H(stream.read(2))
        return cls(Integer(value))

    def __init__(self, constant: Integer) -> None:
        super().__init__()
        self.constant: Integer = constant

    def __repr__(self) -> str:
        return "<PushShortConstant(offset=%s, constant=%s)>" % (self.offset, self.constant)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: %s %s" % (self.offset, self.mnemonic, self.constant)
        return "%s %s" % (self.mnemonic, self.constant)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, self.constant.value))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.constant.value <= 65535):
            verifier.report("invalid short constant value", instruction=self)


class LoadConstant(Instruction):

    __slots__ = ("info",)

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "LoadConstant":
        index, = stream.read(1)
        return cls(pool[index])

    @property
    def can_throw(self) -> bool:
        # FIXME: I'm not sure about this, more testing on condys please!!
        return isinstance(self.info, (ClassInfo, MethodHandleInfo, DynamicInfo))

    def __init__(self, info: ConstInfo) -> None:
        self.offset = None
        self.info = info

    def __repr__(self) -> str:
        return "<LoadConstant(offset=%s, info=%s)>" % (self.offset, self.info)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: %s %s" % (self.offset, self.mnemonic, self.info)
        return "%s %s" % (self.mnemonic, self.info)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, pool.add(self.info))))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types and not self.info.loadable:
            verifier.report("constant is not loadable", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     metadata = Source.Metadata(self, logger)
    #     try:
    #         constant = self.ref.info.unwrap()
    #     except Exception as error:  # Honestly, a whole bunch of errors could be thrown here.
    #         metadata.error("%s", error)
    #         constant = Index(self.ref.index)
    #     return state.step(self, (), frame.push(constant, self), metadata)

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     constant = step.output.value
    #     if constant is None:  # Constant propagation is off, so the output won't have a constant value.
    #         try:
    #             constant = self.ref.info.unwrap()
    #         except Exception:
    #             constant = Index(self.ref.index)
    #
    #         variable = codegen.variable(constant.type)
    #         step.output.value = variable
    #         codegen.block.insns.append(Load(variable, constant))
    #
    #     elif constant.type is top_t or constant.type == class_t:  # Loading classes may cause exceptions.
    #         codegen.block.insns.append(Load(None, constant))


class LoadConstantWide(LoadConstant):

    __slots__ = ()

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "LoadConstantWide":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __repr__(self) -> str:
        return "<LoadConstantWide(offset=%s, info=%r)>" % (self.offset, self.info)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.info)))


class New(Instruction):

    __slots__ = ("class_",)

    can_throw = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "New":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, class_: ConstInfo) -> None:
        self.offset = None
        self.class_ = class_

    def __repr__(self) -> str:
        return "<New(offset=%s, class_=%r)>" % (self.offset, self.class_)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: new %s" % (self.offset, self.class_)
        return "new %s" % self.class_

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.class_)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types and not isinstance(self.class_, ClassInfo):
            verifier.report("class is not a class constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     return state.step(self, (), frame.push(Uninitialized(self), self))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     class_ = self.class_.unwrap()  # TODO: CP ref, in case this throws.
    #     variable = codegen.variable(class_.as_rtype())
    #     step.output.value = variable
    #     codegen.emit(IRNew(step, variable, class_))


class Pop(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Pop":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     popped = frame.pop(None, self)
    #     if popped.hidword or popped.split:  # Looking for an unsplit LoDWord.
    #         return
    #     # Note: the copying is really a precaution because this entry may exist in other areas (dup'd on the stack,
    #     # in locals), and obviously in those areas it's not split, or well it may be, but it's not the same entry.
    #     entry = frame.stack[-1].copy()
    #     entry.split = True
    #     frame.stack[-1] = entry


class Pop2(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Pop2":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     frame.pop(None, self)
    #     popped = frame.pop(None, self)
    #     if popped.hidword or popped.split:
    #         return
    #     entry = frame.stack[-1].copy()
    #     entry.split = True
    #     frame.stack[-1] = entry


class Dup(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Dup":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     entry = frame.stack[-1]
    #     if entry.hidword:
    #         frame.stack.append(entry)
    #         return
    #     entry = entry.copy()
    #     entry.split = True
    #     frame.stack.append(entry)


class DupX1(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "DupX1":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     entry = frame.stack[-1]
    #     if entry.hidword:
    #         frame.stack.insert(-2, entry)
    #         return
    #     entry = entry.copy()
    #     entry.split = True
    #     frame.stack.insert(-2, entry)


class DupX2(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "DupX2":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     entry = frame.stack[-1]
    #     if entry.hidword:
    #         frame.stack.insert(-3, entry)
    #         return
    #     entry = entry.copy()
    #     entry.split = True
    #     frame.stack.insert(-3, entry)


class Dup2(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Dup2":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     # [a, b] -> [a, b, a]
    #     #  ^
    #     # [a, b, a] -> [a, b, a, b]
    #     #     ^
    #     entry = frame.stack[-2]
    #     if entry.hidword:
    #         frame.stack.append(entry)
    #         frame.stack.append(frame.stack[-2])
    #         return
    #     entry = entry.copy()
    #     entry.split = True
    #     frame.stack.append(entry)
    #     frame.stack.append(frame.stack[-2])


class Dup2X1(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Dup2X1":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     frame.stack.insert(-3, frame.stack[-2])
    #     frame.stack.insert(-3, frame.stack[-1])


class Dup2X2(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Dup2X2":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     for entry in frame.stack[-2:]:
    #         frame.stack.insert(-4, entry.copy())


class Swap(Instruction):

    __slots__ = ()

    can_throw = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Swap":
        return cls()

    def __init__(self) -> None:
        self.offset = None

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     if frame.stack[-1].type.wide:
    #         entry = frame.stack[-1].copy()
    #         entry.split = True
    #         frame.stack[-1] = entry
    #     if frame.stack[-2].type.wide:
    #         entry = frame.stack[-2].copy()
    #         entry.split = True
    #         frame.stack[-2] = entry
    #     frame.stack[-1], frame.stack[-2] = frame.stack[-2], frame.stack[-1]


aconst_null = PushConstant.make(0x01, "aconst_null", constant=Null())

iconst_m1 = PushConstant.make(0x02, "iconst_m1", constant=Integer(-1))
iconst_0  = PushConstant.make(0x03, "iconst_0", constant=Integer(0))
iconst_1  = PushConstant.make(0x04, "iconst_1", constant=Integer(1))
iconst_2  = PushConstant.make(0x05, "iconst_2", constant=Integer(2))
iconst_3  = PushConstant.make(0x06, "iconst_3", constant=Integer(3))
iconst_4  = PushConstant.make(0x07, "iconst_4", constant=Integer(4))
iconst_5  = PushConstant.make(0x08, "iconst_5", constant=Integer(5))

lconst_0 = PushConstant.make(0x09, "lconst_0", constant=Long(0))
lconst_1 = PushConstant.make(0x0a, "lconst_1", constant=Long(1))

fconst_0 = PushConstant.make(0x0b, "fconst_0", constant=Float(0.0))  # Float(0x00000000))
fconst_1 = PushConstant.make(0x0c, "fconst_1", constant=Float(1.0))  # Float(0x3f800000))
fconst_2 = PushConstant.make(0x0d, "fconst_2", constant=Float(2.0))  # Float(0x40000000))

dconst_0 = PushConstant.make(0x0e, "dconst_0", constant=Double(0.0))  # Double(0x0000000000000000))
dconst_1 = PushConstant.make(0x0f, "dconst_1", constant=Double(1.0))  # Double(0x3ff0000000000000))

bipush  = PushByteConstant.make(0x10, "bipush")
sipush = PushShortConstant.make(0x11, "sipush")

ldc        = LoadConstant.make(0x12, "ldc")
ldc_w  = LoadConstantWide.make(0x13, "ldc_w")
ldc2_w = LoadConstantWide.make(0x14, "ldc2_w")

new = New.make(0xbb, "new")

pop        = Pop.make(0x57, "pop")
pop2      = Pop2.make(0x58, "pop2")
dup        = Dup.make(0x59, "dup")
dup_x1   = DupX1.make(0x5a, "dup_x1")
dup_x2   = DupX2.make(0x5b, "dup_x2")
dup2      = Dup2.make(0x5c, "dup2")
dup2_x1 = Dup2X1.make(0x5d, "dup2_x1")
dup2_x2 = Dup2X2.make(0x5e, "dup2_x2")
swap      = Swap.make(0x5f, "swap")

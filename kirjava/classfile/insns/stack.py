#!/usr/bin/env python3

__all__ = (
    "aconst_null",
    "iconst_m1", "iconst_0", "iconst_1", "iconst_2", "iconst_3", "iconst_4", "iconst_5",
    "lconst_0", "lconst_1",
    "fconst_0", "fconst_1", "fconst_2",
    "dconst_0", "dconst_1",
    "bipush", "sipush",
    "ldc", "ldc_w", "ldc2_w",  # "ldc_l", "ldc_wl", "ldc2_wl",
    "new",  # "new_l",
    "pop", "pop2", "dup", "dup_x1", "dup_x2", "dup2", "dup2_x1", "dup2_x2", "swap",
    "PushConstant", "BIPush", "SIPush",
    "LoadConstant", "LoadConstantWide",  # "LoadConstantLinked", "LoadConstantWideLinked",
    "New",  # "NewLinked",
    "Pop", "Pop2", "Dup", "DupX1", "DupX2", "Dup2", "Dup2X1", "Dup2X2", "Swap",
)

import typing
from copy import deepcopy
from typing import IO

from . import Instruction
from .._struct import *
from ..fmt.constants import *
from ...backend import f32, f64, i32, i64
from ...model.types import error_t, Class
from ...model.values.constants import Constant, Double, Float, Integer, Long, Null

if typing.TYPE_CHECKING:
    # from ..analyse.frame import Frame
    # from ..analyse.state import State
    from ..fmt import ConstPool
    # from ..verify import Verifier


class PushConstant(Instruction):
    """
    A constant push instruction base.

    Pushes a constant onto the top of the stack.

    Attributes
    ----------
    constant: Constant
        The constant to push.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    constant: Constant

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "PushConstant":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<PushConstant(offset={self.offset}, constant={self.constant!s})>"
        return f"<PushConstant(constant={self.constant!s})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PushConstant) and self.opcode == other.opcode and self.constant == other.constant

    # def copy(self) -> "PushConstant":
    #     copy = type(self)(self.constant)
    #     copy.offset = self.offset
    #     return copy

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


class BIPush(PushConstant):
    """
    A `bipush` instruction.

    Pushes a signed byte onto the top of the stack.

    Attributes
    ----------
    value: int
        The byte value to push.
    """

    __slots__ = ("value",)

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "BIPush":
        value, = stream.read(1)
        return cls(value)

    @property  # type: ignore[override]
    def constant(self) -> Integer:
        return Integer(i32(self.value))

    @constant.setter
    def constant(self, value: Integer) -> None:
        self.value = int(value.value)

    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def __copy__(self) -> "BIPush":
        copy = bipush(self.value)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<BIPush(offset={self.offset}, value={self.value})>"
        return f"<BIPush(value={self.value})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:bipush({self.value})"
        return f"bipush({self.value})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BIPush) and self.value == other.value

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, self.value)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.constant.value <= 255):
    #         verifier.report("invalid byte constant value", instruction=self)


class SIPush(PushConstant):
    """
    A `sipush` instruction.

    Pushes a signed short onto the top of the stack.

    Attributes
    ----------
    value: int
        The short value to push.
    """

    __slots__ = ("value",)

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "SIPush":
        value, = unpack_H(stream.read(2))
        return cls(value)

    @property  # type: ignore[override]
    def constant(self) -> Integer:
        return Integer(i32(self.value))

    @constant.setter
    def constant(self, value: Integer) -> None:
        self.value = int(value.value)

    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def __copy__(self) -> "SIPush":
        copy = sipush(self.value)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<SIPush(offset={self.offset}, value={self.value})>"
        return f"<SIPush(value={self.value})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:sipush({self.value})"
        return f"sipush({self.value})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SIPush) and self.value == other.value

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, self.value))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.constant.value <= 65535):
    #         verifier.report("invalid short constant value", instruction=self)


class LoadConstant(Instruction):
    """
    A load constant instruction base.

    Loads a constant from the constant pool and pushes it onto the top of the stack.

    Attributes
    ----------
    info: ConstInfo
        The constant info to load and push onto the stack.
    """

    __slots__ = ("info",)

    lt_throws = frozenset({error_t})
    rt_throws = frozenset()

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "LoadConstant":
        index, = stream.read(1)
        return cls(pool[index])

    def __init__(self, info: ConstInfo) -> None:
        super().__init__()
        self.info = info

    def __copy__(self) -> "LoadConstant":
        copy = type(self)(self.info)
        copy.offset = self.offset
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "LoadConstant":
        copy = type(self)(deepcopy(self.info, memo))
        copy.offset = self.offset
        return copy

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<LoadConstant(offset={self.offset}, info={self.info!s})>"
        return f"<LoadConstant(info={self.info!s})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:{self.mnemonic}({self.info!s})"
        return f"{self.mnemonic}({self.info!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LoadConstant) and self.opcode == other.opcode and self.info == other.info

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, pool.add(self.info))))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not self.info.loadable:
    #         verifier.report("constant is not loadable", instruction=self)

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
    """
    A wide load constant instruction.

    Loads a constant from the constant pool and pushes it onto the top of the stack.
    """

    __slots__ = ()

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "LoadConstantWide":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<LoadConstantWide(offset={self.offset}, info={self.info!s})>"
        return f"<LoadConstantWide(info={self.info!s})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LoadConstantWide) and self.opcode == other.opcode and self.info == other.info

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.info)))


# class LoadConstantLinked(LoadConstant):
#     """
#     A linked `ldc` instruction.
#     """
#
#     lt_throws = frozenset()
#     linked = True


# class LoadConstantWideLinked(LoadConstantLinked):
#     """
#     A linked wide constant load instruction.
#     """
#
#     lt_throws = frozenset()
#     linked = True


class New(Instruction):
    """
    A `new` instruction.

    Creates a new instance of a class.

    Attributes
    ----------
    classref: ConstInfo
        A class constant, used as the type to instantiate.
    """

    __slots__ = ("classref",)

    lt_throws = frozenset({error_t})
    rt_throws = frozenset()  # TODO: True?

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "New":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, classref: ConstInfo) -> None:
        super().__init__()
        self.classref = classref

    def __copy__(self) -> "New":
        copy = new(self.classref)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __deepcopy__(self, memo: dict[int, object]) -> "New":
        copy = new(deepcopy(self.classref, memo))  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<New(offset={self.offset}, classref={self.classref!s})>"
        return f"<New(classref={self.classref!s})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:new({self.classref!s})"
        return f"new({self.classref!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, New) and self.classref == other.classref

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, pool.add(self.classref)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if verifier.check_const_types and not isinstance(self.class_, ClassInfo):
    #         verifier.report("class is not a class constant", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     return state.step(self, (), frame.push(Uninitialized(self), self))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     class_ = self.class_.unwrap()  # TODO: CP ref, in case this throws.
    #     variable = codegen.variable(class_.as_rtype())
    #     step.output.value = variable
    #     codegen.emit(IRNew(step, variable, class_))


# class NewLinked(New):
#     """
#     A linked `new` instruction.
#     """
#
#     lt_throws = frozenset()
#     linked = True


class Pop(Instruction):
    """
    A `pop` instruction.

    Pops the top value from the stack.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Pop":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Pop(offset={self.offset})>"
        return "<Pop>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Pop)

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
    """
    A `pop2` instruction.

    Pops the top two values from the stack.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Pop2":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Pop2(offset={self.offset})>"
        return "<Pop2>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Pop2)

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
    """
    A `dup` instruction.

    Duplicates the top value on the stack.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Dup":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Dup(offset={self.offset})>"
        return "<Dup>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Dup)

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
    """
    A `dup_x1` instruction.

    Duplicate the top value on the stack and insert it one value down.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "DupX1":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<DupX1(offset={self.offset})>"
        return "<DupX1>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DupX1)

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
    """
    A `dup_x2` instruction.

    Duplicate the top value on the stack and insert it two values down.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "DupX2":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<DupX2(offset={self.offset})>"
        return "<DupX2>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DupX2)

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
    """
    A `dup2` instruction.

    Duplicates the top two values on the stack.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Dup2":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Dup2(offset={self.offset})>"
        return "<Dup2>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Dup2)

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
    """
    A `dup2_x1` instruction.

    Duplicates the top two values on the stack and inserts them three values down.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Dup2X1":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Dup2X1(offset={self.offset})>"
        return "<Dup2X1>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Dup2X1)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     frame.stack.insert(-3, frame.stack[-2])
    #     frame.stack.insert(-3, frame.stack[-1])


class Dup2X2(Instruction):
    """
    A `dup2_x2` instruction.

    Duplicates the top two values on the stack and inserts them four values down.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Dup2X2":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Dup2X2(offset={self.offset})>"
        return "<Dup2X2>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Dup2X2)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> None:
    #     for entry in frame.stack[-2:]:
    #         frame.stack.insert(-4, entry.copy())


class Swap(Instruction):
    """
    A `swap` instruction.

    Swaps the top two stack values.
    """

    __slots__ = ()

    lt_throws = frozenset()
    rt_throws = frozenset()
    linked = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Swap":
        return cls()

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Swap(offset={self.offset})>"
        return "<Swap>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Swap)

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

iconst_m1 = PushConstant.make(0x02, "iconst_m1", constant=Integer(i32(-1)))
iconst_0  = PushConstant.make(0x03, "iconst_0", constant=Integer(i32(0)))
iconst_1  = PushConstant.make(0x04, "iconst_1", constant=Integer(i32(1)))
iconst_2  = PushConstant.make(0x05, "iconst_2", constant=Integer(i32(2)))
iconst_3  = PushConstant.make(0x06, "iconst_3", constant=Integer(i32(3)))
iconst_4  = PushConstant.make(0x07, "iconst_4", constant=Integer(i32(4)))
iconst_5  = PushConstant.make(0x08, "iconst_5", constant=Integer(i32(5)))

lconst_0 = PushConstant.make(0x09, "lconst_0", constant=Long(i64(0)))
lconst_1 = PushConstant.make(0x0a, "lconst_1", constant=Long(i64(1)))

fconst_0 = PushConstant.make(0x0b, "fconst_0", constant=Float(f32(0.0)))  # Float(0x00000000))
fconst_1 = PushConstant.make(0x0c, "fconst_1", constant=Float(f32(1.0)))  # Float(0x3f800000))
fconst_2 = PushConstant.make(0x0d, "fconst_2", constant=Float(f32(2.0)))  # Float(0x40000000))

dconst_0 = PushConstant.make(0x0e, "dconst_0", constant=Double(f64(0.0)))  # Double(0x0000000000000000))
dconst_1 = PushConstant.make(0x0f, "dconst_1", constant=Double(f64(1.0)))  # Double(0x3ff0000000000000))

bipush = BIPush.make(0x10, "bipush")
sipush = SIPush.make(0x11, "sipush")

ldc               = LoadConstant.make(0x12, "ldc")
ldc_w         = LoadConstantWide.make(0x13, "ldc_w")
ldc2_w        = LoadConstantWide.make(0x14, "ldc2_w")
# ldc_l       = LoadConstantLinked.make(0x12, "ldc_l")
# ldc_wl  = LoadConstantWideLinked.make(0x13, "ldc_wl")
# ldc2_wl = LoadConstantWideLinked.make(0x14, "ldc2_wl")

new         = New.make(0xbb, "new")
# new_l = NewLinked.make(0xbb, "new_l")

pop        = Pop.make(0x57, "pop")
pop2      = Pop2.make(0x58, "pop2")
dup        = Dup.make(0x59, "dup")
dup_x1   = DupX1.make(0x5a, "dup_x1")
dup_x2   = DupX2.make(0x5b, "dup_x2")
dup2      = Dup2.make(0x5c, "dup2")
dup2_x1 = Dup2X1.make(0x5d, "dup2_x1")
dup2_x2 = Dup2X2.make(0x5e, "dup2_x2")
swap      = Swap.make(0x5f, "swap")
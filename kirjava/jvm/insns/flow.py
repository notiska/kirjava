#!/usr/bin/env python3

__all__ = (
    "goto", "jsr", "ret", "ret_w", "goto_w", "jsr_w",
    "ifeq", "ifne", "iflt", "ifge", "ifgt", "ifle",
    "if_icmpeq", "if_icmpne", "if_icmplt", "if_icmpge", "if_icmpgt", "if_icmple",
    "if_acmpeq", "if_acmpne",
    "ifnull", "ifnonnull",
    "tableswitch", "lookupswitch",
    "ireturn", "lreturn", "freturn", "dreturn", "areturn", "return_",
    "athrow",
)

import logging
import typing
from typing import IO, Optional

from . import Instruction
from .._struct import *
from ...model.types import *
from ...model.values.constants import *

if typing.TYPE_CHECKING:
    from ..analyse.frame import Frame
    from ..analyse.state import State
    from ..fmt import ConstPool
    from ..verify import Verifier
    from ...model.values import Value

logger = logging.getLogger("ijd.jvm.insns.flow")


class Jump(Instruction):

    __slots__ = ("delta",)

    can_throw = False

    conditional = False

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Jump":
        delta, = unpack_h(stream.read(2))
        return cls(delta)

    def __init__(self, delta: int | None) -> None:
        self.offset = None
        self.delta = delta

    def __repr__(self) -> str:
        return "<Jump(opcode=0x%x, mnemonic=%s, offset=%s, delta=%s)>" % (
            self.opcode, self.mnemonic, self.offset, self.delta,
        )

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: %s %+i,%i" % (self.offset, self.mnemonic, self.delta, self.offset + self.delta)
        return "%s %+i" % (self.mnemonic, self.delta)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_Bh(self.opcode, self.delta))

    def verify(self, verifier: "Verifier") -> None:
        if self.offset is not None and not (-32768 <= self.offset <= 32767):
            verifier.report("invalid jump offset", instruction=self)

    def trace(self, frame: "Frame", state: "State") -> Optional["State.Step"]:
        ...

    # class Metadata(Source.Metadata):
    #
    #     __slots__ = ("jumps",)
    #
    #     def __init__(self, source: "Jump", jumps: bool | None = None) -> None:
    #         super().__init__(source, logger)
    #         self.jumps = jumps
    #
    #     def __repr__(self) -> str:
    #         return "<Jump.Metadata(jumps=%s)>" % self.jumps


class JumpWide(Jump):

    __slots__ = ()

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "JumpWide":
        delta, = unpack_i(stream.read(4))
        return cls(delta)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_Bi(self.opcode, self.delta))

    def verify(self, verifier: "Verifier") -> None:
        if self.offset is not None and not (-2147483648 <= self.offset <= 2147483647):
            verifier.report("invalid jump offset", instruction=self)


class Compare(Jump):

    __slots__ = ()

    conditional = True

    EQ = 0
    NE = 1
    LT = 2
    GE = 3
    GT = 4
    LE = 5

    comparison: int
    type: Type

    def __repr__(self) -> str:
        return "<Compare(opcode=0x%x, mnemonic=%s, offset=%i, delta=%i)>" % (
            self.opcode, self.mnemonic, self.offset, self.delta,
        )

    # def evaluate(self, left: "Value", right: "Value") -> Jump.Metadata:
    #     """
    #     Checks if two values will evaluate this comparison condition.
    #
    #     Parameters
    #     ----------
    #     left: Value
    #         The left hand side value in the comparison.
    #     right: Value
    #         The right hand side value in the comparison.
    #
    #     Returns
    #     -------
    #     Jump.Metadata
    #         Jump metadata indicating the result of the comparison.
    #     """
    #
    #     metadata = Jump.Metadata(self)
    #     try:
    #         if self.comparison == Compare.EQ:
    #             metadata.jumps = left == right
    #             metadata.debug("%s == %s", left, right)
    #         elif self.comparison == Compare.NE:
    #             metadata.jumps = left != right
    #             metadata.debug("%s != %s", left, right)
    #         elif self.comparison == Compare.LT:
    #             metadata.jumps = left < right
    #             metadata.debug("%s < %s", left, right)
    #         elif self.comparison == Compare.GE:
    #             metadata.jumps = left >= right
    #             metadata.debug("%s >= %s", left, right)
    #         elif self.comparison == Compare.GT:
    #             metadata.jumps = left > right
    #             metadata.debug("%s > %s", left, right)
    #         elif self.comparison == Compare.LE:
    #             metadata.jumps = left <= right
    #             metadata.debug("%s <= %s", left, right)
    #         else:
    #             assert False, "unknown comparison %i for %r" % (self.comparison, self)
    #     except TypeError as error:
    #         metadata.error("%s", error)
    #
    #     return metadata

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     right = frame.pop(self.type, self)
    #     left = frame.pop(self.type, self)
    #
    #     metadata = None
    #
    #     # Check for exact matching, this could've been caused by a `dup` or loading twice from a local, etc.
    #     if right is left:
    #         if self.comparison == Compare.EQ:
    #             metadata = Source.Metadata(self, True)
    #             metadata.debug("%s == %s (exact entry match)", left, right)
    #         elif self.comparison == Compare.NE:
    #             metadata = Source.Metadata(self, True)
    #             metadata.debug("%s != %s (exact entry match)", left, right)
    #
    #     # Otherwise, we need to fall back to constant propagation, if viable.
    #     if left.value is not None and right.value is not None:
    #         metadata = self.evaluate(left.value, right.value)
    #
    #     # Check for unmatched types, note that we need to be careful to ensure that both types are not generified,
    #     # otherwise we don't know their true type and this evaluation would not work.
    #     # FIXME: This could potentially be done properly if we knew the type hierarchy.
    #     # if not right.generified and not left.generified and right.type != left.type:
    #     #     if self.comparison == Compare.EQ:
    #     #         jumps = False
    #     #     elif self.comparison == Compare.NE:
    #     #         jumps = True
    #     #
    #     #     if jumps is not None:
    #     #         logger.debug(
    #     #             "Propagate %s <=> %s from %r via type unmatch, jump evaluates: %s.",
    #     #             left, right, self, jumps,
    #     #         )
    #     #         return Trace.Step(self, (left, right), jump_resolved=True, jump_data=jumps)
    #
    #     return state.step(self, (left, right), None, metadata)


class CompareToZero(Compare):

    __slots__ = ()

    type = int_t

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.pop(int_t, self)
    #     metadata = None
    #     if isinstance(value.value, Integer):
    #         # FIXME: Correct order, just double check this.
    #         metadata = self.evaluate(value.value, Integer(0))
    #     return state.step(self, (value,), None, metadata)


class CompareToNull(Compare):

    __slots__ = ()

    type = reference_t

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.pop(reference_t, self)
    #     metadata = None
    #     if value.type is null_t:
    #         metadata = Jump.Metadata(self, True)
    #         metadata.debug("%s == null (null type match)", value)
    #     elif value.value is not None:
    #         metadata = self.evaluate(value.value, Null())
    #     return state.step(self, (value,), None, metadata)


class Jsr(Jump):

    __slots__ = ()

    def __repr__(self) -> str:
        return "<Jsr(offset=%s, delta=%i)>" % (self.offset, self.delta)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: jsr %+i,%i" % (self.offset, self.delta, self.offset + self.delta)
        return "jsr %+i" % self.delta

    # def trace(self, frame: "Frame", state: "State.Step") -> "State.Step":
    #     return state.step(self, (), frame.push(ReturnAddress(self)))


class JsrWide(Jsr):

    __slots__ = ()

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "JsrWide":
        delta, = unpack_i(stream.read(4))
        return cls(delta)

    def __repr__(self) -> str:
        return "<JsrWide(offset=%s, delta=%i)>" % (self.offset, self.delta)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: jsr_w %+i,%i" % (self.offset, self.delta, self.offset + self.delta)
        return "jsr_w %+i" % self.delta

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_Bi(self.opcode, self.delta))

    def verify(self, verifier: "Verifier") -> None:
        if not (-2147483648 <= self.offset <= 2147483647):
            verifier.report("invalid jump offset", instruction=self)


class Ret(Jump):

    __slots__ = ("index",)

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Ret":
        index, = stream.read(1)
        return cls(index)

    def __init__(self, index: int) -> None:
        super().__init__(None)
        self.index = index

    def __repr__(self) -> str:
        return "<Ret(offset=%s, index=%i)>" % (self.offset, self.index)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: ret %i" % (self.offset, self.index)
        return "ret %i" % self.index

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, self.index)))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.index <= 255):
            verifier.report("invalid local index", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     retaddr = frame.load(self.index, return_address_t, self)
    #     metadata = Ret.Metadata(self, retaddr)
    #     if isinstance(retaddr.type, ReturnAddress):
    #         metadata.debug("subroutine resolves to %s", retaddr.type.source)
    #     # TODO: Support for other types, even though this is invalid.
    #     return state.step(self, (retaddr,), None, metadata)

    # class Metadata(Source.Metadata):
    #
    #     __slots__ = ("retaddr",)
    #
    #     def __init__(self, source: "Ret", retaddr: ReturnAddress) -> None:
    #         super().__init__(source, logger)
    #         self.retaddr = retaddr
    #
    #     def __repr__(self) -> str:
    #         return "<Ret.Metadata(retaddr=%r)>" % self.retaddr


class RetWide(Ret):

    __slots__ = ()

    mutate_w = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "RetWide":
        index, = unpack_H(stream.read(2))
        return cls(index)

    def __repr__(self) -> str:
        return "<RetWide(offset=%s, index=%i)>" % (self.offset, self.index)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: ret_w %i" % (self.offset, self.index)
        return "ret_w %i" % self.index

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.opcode, self.index))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.index <= 65535):
            verifier.report("invalid local index", instruction=self)


class Switch(Instruction):

    __slots__ = ("default", "offsets")

    can_throw = False

    def __init__(self, default: int, offsets: dict[int, int] = None) -> None:
        self.offset = None
        self.default = default
        self.offsets = {}

        if offsets is not None:
            self.offsets.update(offsets)

    def __repr__(self) -> str:
        return "<Switch(offset=%s, default=%i, offsets=%r)>" % (self.offset, self.default, self.offsets)

    # class Metadata(Source.Metadata):
    #
    #     __slots__ = ("resolved", "value")
    #
    #     def __init__(self, source: "Switch", resolved: bool = False, value: int | None = None) -> None:
    #         super().__init__(source, logger)
    #         self.resolved = resolved
    #         self.value = value
    #
    #     def __repr__(self) -> str:
    #         return "<Switch.Metadata(resolved=%s, value=%s)>" % (self.resolved, self.value)


class TableSwitch(Switch):

    __slots__ = ("low", "high")

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "TableSwitch":
        stream.read((4 - stream.tell()) % 4)
        default, low, high = unpack_iii(stream.read(12))
        offsets = {}
        for index in range(low, high + 1):
            offsets[index], = unpack_i(stream.read(4))
        return cls(default, low, high, offsets)

    def __init__(self, default: int, low: int, high: int, offsets: dict[int, int] = None) -> None:
        super().__init__(default, offsets)
        self.low = low
        self.high = high

    def __repr__(self) -> str:
        return "<TableSwitch(offset=%s, default=%i, low=%i, high=%i, offsets=%r)>" % (
            self.offset, self.default, self.low, self.high, self.offsets,
        )

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: tableswitch %i-%i ..." % (self.offset, self.low, self.high)
        return "tableswitch %i-%i ..." % (self.low, self.high)
        # if self.offset is not None:
        #     return "%i: tableswitch %i-%i default %+i,%i offsets %s" % (
        #         self.offset, self.low, self.high, self.default, self.offset + self.default,
        #         ", ".join("%i -> %+i,%i" % (key, value, self.offset + value) for key, value in self.offsets.items()),
        #     )
        # return "tableswitch %i-%i default %+i offsets %s" % (
        #     self.low, self.high, self.default,
        #     ", ".join("%i -> %+i" % (key, value) for key, value in self.offsets.items()),
        # )

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        ...  # TODO

    def verify(self, verifier: "Verifier") -> None:
        ...  # TODO

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.pop(int_t, self)
    #     metadata = Switch.Metadata(self)
    #     if isinstance(value.value, Integer):
    #         key = int(value.value.value)  # :)
    #         metadata.resolved = True
    #         if not key in range(self.low, self.high + 1):
    #             metadata.debug("switch default (%i)", key)
    #         else:
    #             assert key in self.offsets, "table value %s not in offsets for %r" % (key, self)  # FIXME: Handle?
    #             metadata.value = key
    #             metadata.debug("switch value %i", key)
    #     return state.step(self, (value,), None, metadata)


class LookupSwitch(Switch):

    __slots__ = ()

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "LookupSwitch":
        stream.read((4 - stream.tell()) % 4)
        default, npairs = unpack_ii(stream.read(8))
        offsets = {}
        for _ in range(npairs):
            key, offset = unpack_ii(stream.read(8))
            offsets[key] = offset
        return cls(default, offsets)

    def __repr__(self) -> str:
        return "<LookupSwitch(offset=%s, default=%i, offsets=%r)>" % (self.offset, self.default, self.offsets)

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: lookupswitch ..." % self.offset
        return "lookupswitch ..."
        # if self.offset is not None:
        #     return "%i: lookupswitch default %+i,%i offsets %s" % (
        #         self.offset, self.default, self.offset + self.default,
        #         ", ".join("%i -> %+i,%i" % (key, value, self.offset + value) for key, value in self.offsets.items()),
        #     )
        # return "lookupswitch default %+i offsets %s" % (
        #     self.default, ", ".join("%i -> %+i" % (key, value) for key, value in self.offsets.items()),
        # )

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        ...  # TODO

    def verify(self, verifier: "Verifier") -> None:
        ...  # TODO

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.pop(int_t, self)
    #     metadata = Switch.Metadata(self)
    #     if isinstance(value.value, Integer):
    #         key = int(value.value.value)
    #         metadata.resolved = True
    #         if not key in self.offsets:
    #             metadata.debug("switch default (%i)", key)
    #         else:
    #             metadata.value = key
    #             metadata.debug("switch value %i", key)
    #     return state.step(self, (value,), None, metadata)


class Return(Jump):

    __slots__ = ()

    can_throw = True

    type: Type

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Return":
        return cls()

    def __init__(self) -> None:
        super().__init__(None)

    def __repr__(self) -> str:
        return "<Return(offset=%s)>" % self.offset

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: %s" % (self.offset, self.mnemonic)
        return self.mnemonic

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     if self.type is void_t:
    #         return state.step(self, ())
    #     value = frame.pop(self.type, self)
    #     frame.return_(value, self)
    #     return state.step(self, (value,))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     if self.type is void_t:
    #         codegen.emit(IRReturn(step, None))
    #     else:
    #         codegen.emit(IRReturn(step, codegen.value(step.inputs[0])))


class Throw(Jump):

    __slots__ = ()

    can_throw = True

    @classmethod
    def parse(cls, stream: IO[bytes], pool: "ConstPool") -> "Throw":
        return cls()

    def __init__(self) -> None:
        super().__init__(None)

    def __repr__(self) -> str:
        return "<Throw(offset=%s)>" % self.offset

    def __str__(self) -> str:
        if self.offset is not None:
            return "%i: athrow" % self.offset
        return "athrow"

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.pop(reference_t, self)
    #     if isinstance(value.value, Null) or value.type is null_t:
    #         frame.throw(Class("java/lang/NullPointerException"), self)
    #         # Fallthrough, already returns correctly.
    #     else:
    #         value = value.constrain(throwable_t, self)
    #         frame.throw(value)
    #     return state.step(self, (value,))

    # def lift(self, step: "State.Step", codegen: "CodeGen") -> None:
    #     codegen.emit(IRThrow(step, codegen.value(step.inputs[0])))


ifeq = CompareToZero.make(0x99, "ifeq", comparison=Compare.EQ)
ifne = CompareToZero.make(0x9a, "ifne", comparison=Compare.NE)
iflt = CompareToZero.make(0x9b, "iflt", comparison=Compare.LT)
ifge = CompareToZero.make(0x9c, "ifge", comparison=Compare.GE)
ifgt = CompareToZero.make(0x9d, "ifgt", comparison=Compare.GT)
ifle = CompareToZero.make(0x9e, "ifle", comparison=Compare.LE)

if_icmpeq = Compare.make(0x9f, "if_icmpeq", comparison=Compare.EQ, type=int_t)
if_icmpne = Compare.make(0xa0, "if_icmpne", comparison=Compare.NE, type=int_t)
if_icmplt = Compare.make(0xa1, "if_icmplt", comparison=Compare.LT, type=int_t)
if_icmpge = Compare.make(0xa2, "if_icmpge", comparison=Compare.GE, type=int_t)
if_icmpgt = Compare.make(0xa3, "if_icmpgt", comparison=Compare.GT, type=int_t)
if_icmple = Compare.make(0xa4, "if_icmple", comparison=Compare.LE, type=int_t)

if_acmpeq = Compare.make(0xa5, "if_acmpeq", comparison=Compare.EQ, type=reference_t)
if_acmpne = Compare.make(0xa6, "if_acmpne", comparison=Compare.NE, type=reference_t)

ifnull    = CompareToNull.make(0xc6, "ifnull", comparison=Compare.EQ)
ifnonnull = CompareToNull.make(0xc7, "ifnonnull", comparison=Compare.NE)

goto       = Jump.make(0xa7, "goto")
jsr         = Jsr.make(0xa8, "jsr")
ret         = Ret.make(0xa9, "ret")
ret_w   = RetWide.make(0xa9, "ret_w")

goto_w = JumpWide.make(0xc8, "goto_w")
jsr_w   = JsrWide.make(0xc9, "jsr_w")

tableswitch   = TableSwitch.make(0xaa, "tableswitch")
lookupswitch = LookupSwitch.make(0xab, "lookupswitch")

ireturn = Return.make(0xac, "ireturn", type=int_t)
lreturn = Return.make(0xad, "lreturn", type=long_t)
freturn = Return.make(0xae, "freturn", type=float_t)
dreturn = Return.make(0xaf, "dreturn", type=double_t)
areturn = Return.make(0xb0, "areturn", type=reference_t)
return_ = Return.make(0xb1, "return", type=void_t)

athrow = Throw.make(0xbf, "athrow")

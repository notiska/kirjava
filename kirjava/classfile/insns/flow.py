#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "goto", "jsr", "ret", "ret_w", "goto_w", "jsr_w",
    "ifeq", "ifne", "iflt", "ifge", "ifgt", "ifle",
    "if_icmpeq", "if_icmpne", "if_icmplt", "if_icmpge", "if_icmpgt", "if_icmple",
    "if_acmpeq", "if_acmpne",
    "ifnull", "ifnonnull",
    "tableswitch", "lookupswitch",
    "ireturn", "lreturn", "freturn", "dreturn", "areturn", "return_",
    "athrow",
    "Jump", "GotoWide",
    "Compare", "CompareToZero", "IfEq", "IfNe", "CompareToNull",
    "Jsr", "JsrWide", "Ret", "RetWide",
    "Switch", "TableSwitch", "LookupSwitch",
    "Return", "AThrow",
)

import typing
from enum import Enum
from typing import IO, Mapping

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
    # from ...model.values import Value


class Jump(Instruction):
    """
    A jump instruction base.

    Jumps to a relative offset in the instructions.

    Attributes
    ----------
    conditional: bool
        Whether this jump is conditional.
    """

    __slots__ = ("delta",)

    rt_throws = frozenset()
    lt_throws = frozenset()
    linked = True

    conditional = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Jump":
        delta, = unpack_h(stream.read(2))
        return cls(delta)

    def __init__(self, delta: int | None) -> None:
        super().__init__()
        self.delta = delta

    def __copy__(self) -> "Jump":
        copy = type(self)(self.delta)
        copy.offset = self.offset
        return copy

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Jump(offset={self.offset}, delta={self.delta})>"
        return f"<Jump(delta={self.delta})>"

    def __str__(self) -> str:
        if self.delta is None:
            if self.offset is not None:
                return f"{self.offset}:{self.mnemonic}"
            return self.mnemonic
        if self.offset is not None:
            return f"{self.offset}:{self.mnemonic}({self.delta:+},{self.offset + self.delta})"
        return f"{self.mnemonic}({self.delta:+})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Jump) and self.opcode == other.opcode and self.delta == other.delta

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_Bh(self.opcode, self.delta))

    # def verify(self, verifier: "Verifier") -> None:
    #     if self.offset is not None and not (-32768 <= self.offset <= 32767):
    #         verifier.report("invalid jump offset", instruction=self)

    # def trace(self, frame: "Frame", state: "State") -> Optional["State.Step"]:
    #     ...

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


class GotoWide(Jump):
    """
    A `goto_w` instruction.

    Unconditionally jumps to a relative offset above the 16-bit limit in the
    instructions.
    """

    __slots__ = ()

    delta: int

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "GotoWide":
        delta, = unpack_i(stream.read(4))
        return cls(delta)

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<GotoWide(offset={self.offset}, delta={self.delta})>"
        return f"<GotoWide(delta={self.delta})>"

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_Bi(self.opcode, self.delta))

    # def verify(self, verifier: "Verifier") -> None:
    #     if self.offset is not None and not (-2147483648 <= self.offset <= 2147483647):
    #         verifier.report("invalid jump offset", instruction=self)


class Compare(Jump):
    """
    A comparative conditional jump instruction base.

    Compares two values and jumps based on the result.

    Attributes
    ----------
    comparison: Compare.Type
        The comparison type to perform.
    type: Type
        The type of stack value(s) to compare.
    """

    __slots__ = ()

    conditional = True

    comparison: "Compare.Type"  # type: ignore[name-defined]
    type: Type

    delta: int

    def __repr__(self) -> str:
        if self.offset is not None:
            return (
                f"<Compare(offset={self.offset}, comparison={self.comparison!s}, type={self.type!s}, "
                f"delta={self.delta})>"
            )
        return f"<Compare(comparison={self.comparison!s}, type={self.type!s}, delta={self.delta})>"

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

    class Type(Enum):
        """
        The type of comparison.
        """

        EQ = "EQ"
        NE = "NE"
        LT = "LT"
        GE = "GE"
        GT = "GT"
        LE = "LE"


class CompareToZero(Compare):
    """
    A compare to zero instruction base.

    Compares an int stack value to zero.
    """

    __slots__ = ()

    type = int_t

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<CompareToZero(offset={self.offset}, comparison={self.comparison!s}, delta={self.delta})>"
        return f"<CompareToZero(comparison={self.comparison!s}, delta={self.delta})>"

    # def trace(self, frame: "Frame", state: "State") -> "State.Step":
    #     value = frame.pop(int_t, self)
    #     metadata = None
    #     if isinstance(value.value, Integer):
    #         # FIXME: Correct order, just double check this.
    #         metadata = self.evaluate(value.value, Integer(0))
    #     return state.step(self, (value,), None, metadata)


class IfEq(CompareToZero):
    """
    An `ifeq` instruction.

    Compares an int stack value to zero, or in older versions, also acts as an
    `ifnull` instruction.
    """

    comparison = Compare.Type.EQ

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<IfEq(offset={self.offset}, delta={self.delta})>"
        return f"<IfEq(delta={self.delta})>"


class IfNe(CompareToZero):
    """
    An `ifne` instruction.

    Compares an int stack value to zero, or in older versions, also acts as an
    `ifnonnull` instruction.
    """

    comparison = Compare.Type.NE

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<IfNe(offset={self.offset}, delta={self.delta})>"
        return f"<IfNe(delta={self.delta})>"


class CompareToNull(Compare):
    """
    A compare to null instruction base.

    Compares a reference stack value to null.
    """

    __slots__ = ()

    type = reference_t

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<CompareToNull(offset={self.offset}, comparison={self.comparison!s}, delta={self.delta})>"
        return f"<CompareToNull(comparison={self.comparison!s}, delta={self.delta})>"

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
    """
    A `jsr` instruction.

    Unconditionally jumps to a subroutine, pushing the return address onto the stack.
    """

    __slots__ = ()

    delta: int

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Jsr(offset={self.offset}, delta={self.delta})>"
        return f"<Jsr(delta={self.delta})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:jsr({self.delta:+},{self.delta + self.offset})"
        return f"jsr({self.delta:+})"

    # def trace(self, frame: "Frame", state: "State.Step") -> "State.Step":
    #     return state.step(self, (), frame.push(ReturnAddress(self)))


class JsrWide(Jsr):
    """
    A `jsr_w` instruction.

    Unconditionally jumps to a subroutine with a relative offset greater than the
    16-bit limit, pushing the return address onto the stack.
    """

    __slots__ = ()

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "JsrWide":
        delta, = unpack_i(stream.read(4))
        return cls(delta)

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<JsrWide(offset={self.offset}, delta={self.delta})>"
        return f"<JsrWide(delta={self.delta})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:jsr_w({self.delta:+},{self.offset + self.delta})"
        return f"jsr_w({self.delta:+})"

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_Bi(self.opcode, self.delta))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (-2147483648 <= self.offset <= 2147483647):
    #         verifier.report("invalid jump offset", instruction=self)


class Ret(Jump):
    """
    A `ret` instruction.

    Returns from a subroutine, to the address stored in the local variable at the
    given index.
    """

    __slots__ = ("index",)

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Ret":
        index, = stream.read(1)
        return cls(index)

    def __init__(self, index: int) -> None:
        super().__init__(None)
        self.index = index

    def __copy__(self) -> "Ret":
        copy = type(self)(self.index)
        copy.offset = self.offset
        return copy

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Ret(offset={self.offset}, index={self.index})>"
        return f"<Ret(index={self.index})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:ret({self.index})"
        return f"ret({self.index})"

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode, self.index)))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.index <= 255):
    #         verifier.report("invalid local index", instruction=self)

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
    """
    A `ret_w` pseudo-instruction (wide mutation).

    Returns from a subroutine, to the address stored in the local variable at the
    given 16-bit index (as compared to the 8-bit index with `ret`).
    """

    __slots__ = ()

    mutated = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "RetWide":
        index, = unpack_H(stream.read(2))
        return cls(index)

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<RetWide(offset={self.offset}, index={self.index})>"
        return f"<RetWide(index={self.index})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:ret_w({self.index})"
        return f"ret_w({self.index})"

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BBH(wide.opcode, self.opcode, self.index))

    # def verify(self, verifier: "Verifier") -> None:
    #     if not (0 <= self.index <= 65535):
    #         verifier.report("invalid local index", instruction=self)


class Switch(Instruction):
    """
    A switch instruction base.

    Jumps to a relative offset based on a key value.

    Attributes
    ----------
    default: int
        The default offset to jump to if the key is not found.
    offsets: dict[int, int]
        A mapping of key values to relative offsets.
    """

    __slots__ = ("default", "offsets")

    rt_throws = frozenset()
    lt_throws = frozenset()
    linked = True

    def __init__(self, default: int, offsets: Mapping[int, int] | None = None) -> None:
        super().__init__()
        self.default = default
        self.offsets: dict[int, int] = {}
        if offsets is not None:
            self.offsets.update(offsets)

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
    """
    A `tableswitch` instruction.

    A 0-based jump table in which the key is the index of the offset value.

    Attributes
    ----------
    low: int
        The low value of the switch, the offset is calculated by `key - low`.
        If `key < low`, the `default` offset is used.
    high: int
        The highest value of the switch. If `key > high`, the `default` offset is
        used.
    """

    __slots__ = ("low", "high")

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "TableSwitch":
        stream.read((4 - stream.tell()) % 4)
        default, low, high = unpack_iii(stream.read(12))
        offsets = {}
        for index in range(low, high + 1):
            offsets[index], = unpack_i(stream.read(4))
        return cls(default, low, high, offsets)

    def __init__(self, default: int, low: int, high: int, offsets: Mapping[int, int] | None = None) -> None:
        super().__init__(default, offsets)
        self.low = low
        self.high = high

    def __copy__(self) -> "TableSwitch":
        copy = tableswitch(self.default, self.low, self.high, self.offsets)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.offset is not None:
            return (
                f"<TableSwitch(offset={self.offset}, default={self.default}, low={self.low}, high={self.high}, "
                f"offsets={self.offsets!r})>"
            )
        return f"<TableSwitch(default={self.default}, low={self.low}, high={self.high}, offsets={self.offsets!r})>"

    def __str__(self) -> str:
        # FIXME: Implement.
        if self.offset is not None:
            return f"{self.offset}:tableswitch({self.low}-{self.high},...)"
        return f"tableswitch({self.low}-{self.high},...)"
        # if self.offset is not None:
        #     return "%i: tableswitch %i-%i default %+i,%i offsets %s" % (
        #         self.offset, self.low, self.high, self.default, self.offset + self.default,
        #         ", ".join("%i -> %+i,%i" % (key, value, self.offset + value) for key, value in self.offsets.items()),
        #     )
        # return "tableswitch %i-%i default %+i offsets %s" % (
        #     self.low, self.high, self.default,
        #     ", ".join("%i -> %+i" % (key, value) for key, value in self.offsets.items()),
        # )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TableSwitch) and
            self.default == other.default and
            self.low == other.low and
            self.high == other.high and
            self.offsets == other.offsets
        )

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))
        stream.write(b"\x00" * (3 - (stream.tell() - 1) % 4))
        stream.write(pack_iii(self.default, self.low, self.high))
        for index in range(self.low, self.high + 1):
            stream.write(pack_i(self.offsets[index]))

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
    """
    A `lookupswitch` instruction.

    A key-value jump table.
    """

    __slots__ = ()

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "LookupSwitch":
        stream.read((4 - stream.tell()) % 4)
        default, count = unpack_ii(stream.read(8))
        offsets = {}
        for _ in range(count):
            key, offset = unpack_ii(stream.read(8))
            offsets[key] = offset
        return cls(default, offsets)

    def __copy__(self) -> "LookupSwitch":
        copy = lookupswitch(self.default, self.offsets)  # type: ignore[call-arg]
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<LookupSwitch(offset={self.offset}, default={self.default}, offsets={self.offsets!r})>"
        return f"<LookupSwitch(default={self.default}, offsets={self.offsets!r})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:lookupswitch(...)"
        return "lookupswitch(...)"
        # if self.offset is not None:
        #     return "%i: lookupswitch default %+i,%i offsets %s" % (
        #         self.offset, self.default, self.offset + self.default,
        #         ", ".join("%i -> %+i,%i" % (key, value, self.offset + value) for key, value in self.offsets.items()),
        #     )
        # return "lookupswitch default %+i offsets %s" % (
        #     self.default, ", ".join("%i -> %+i" % (key, value) for key, value in self.offsets.items()),
        # )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LookupSwitch) and self.default == other.default and self.offsets == other.offsets

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.opcode,)))
        stream.write(b"\x00" * (3 - (stream.tell() - 1) % 4))
        stream.write(pack_ii(self.default, len(self.offsets)))
        for key, offset in self.offsets.items():  # sorted(self.offsets.items(), key=itemgetter(0)):
            stream.write(pack_ii(key, offset))

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
    """
    A return instruction base.

    Returns from the current method.

    Attributes
    ----------
    type: Type
        The type of value to return.
    """

    __slots__ = ()

    rt_throws = frozenset({Class("java/lang/IllegalMonitorStateException")})

    type: Type

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "Return":
        return cls()

    def __init__(self) -> None:
        super().__init__(None)

    def __copy__(self) -> "Return":
        copy = type(self)()
        copy.offset = self.offset
        return copy

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<Return(offset={self.offset}, type={self.type!s})>"
        return f"<Return(type={self.type!s})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:{self.mnemonic}"
        return self.mnemonic

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Return) and self.opcode == other.opcode

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


class AThrow(Jump):
    """
    An `athrow` instruction.

    Throws the exception on the top of the stack.
    """

    __slots__ = ()

    rt_throws = frozenset({throwable_t})  # Specifics (monitor state / NPE) aren't really needed in this case.

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "AThrow":
        return cls()

    def __init__(self) -> None:
        super().__init__(None)

    def __copy__(self) -> "AThrow":
        copy = athrow()
        copy.offset = self.offset
        return copy  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<AThrow(offset={self.offset})>"
        return "<AThrow>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:athrow"
        return "athrow"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AThrow)

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


ifeq          = IfEq.make(0x99, "ifeq")
ifne          = IfNe.make(0x9a, "ifne")
iflt = CompareToZero.make(0x9b, "iflt", comparison=Compare.Type.LT)
ifge = CompareToZero.make(0x9c, "ifge", comparison=Compare.Type.GE)
ifgt = CompareToZero.make(0x9d, "ifgt", comparison=Compare.Type.GT)
ifle = CompareToZero.make(0x9e, "ifle", comparison=Compare.Type.LE)

if_icmpeq = Compare.make(0x9f, "if_icmpeq", comparison=Compare.Type.EQ, type=int_t)
if_icmpne = Compare.make(0xa0, "if_icmpne", comparison=Compare.Type.NE, type=int_t)
if_icmplt = Compare.make(0xa1, "if_icmplt", comparison=Compare.Type.LT, type=int_t)
if_icmpge = Compare.make(0xa2, "if_icmpge", comparison=Compare.Type.GE, type=int_t)
if_icmpgt = Compare.make(0xa3, "if_icmpgt", comparison=Compare.Type.GT, type=int_t)
if_icmple = Compare.make(0xa4, "if_icmple", comparison=Compare.Type.LE, type=int_t)

if_acmpeq = Compare.make(0xa5, "if_acmpeq", comparison=Compare.Type.EQ, type=reference_t)
if_acmpne = Compare.make(0xa6, "if_acmpne", comparison=Compare.Type.NE, type=reference_t)

ifnull    = CompareToNull.make(0xc6, "ifnull", comparison=Compare.Type.EQ)
ifnonnull = CompareToNull.make(0xc7, "ifnonnull", comparison=Compare.Type.NE)

goto       = Jump.make(0xa7, "goto")
jsr         = Jsr.make(0xa8, "jsr")
ret         = Ret.make(0xa9, "ret")
ret_w   = RetWide.make(0xa9, "ret_w")

goto_w = GotoWide.make(0xc8, "goto_w")
jsr_w   = JsrWide.make(0xc9, "jsr_w")

tableswitch   = TableSwitch.make(0xaa, "tableswitch")
lookupswitch = LookupSwitch.make(0xab, "lookupswitch")

ireturn = Return.make(0xac, "ireturn", type=int_t)
lreturn = Return.make(0xad, "lreturn", type=long_t)
freturn = Return.make(0xae, "freturn", type=float_t)
dreturn = Return.make(0xaf, "dreturn", type=double_t)
areturn = Return.make(0xb0, "areturn", type=reference_t)
return_ = Return.make(0xb1, "return", type=void_t)

athrow = AThrow.make(0xbf, "athrow")

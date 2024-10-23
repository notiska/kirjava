#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Debug",
    "LineNumber", "LocalStart", "LocalEnd",
)

import typing
from copy import deepcopy
from typing import IO, Optional

from . import Instruction
from ..version import JAVA_MIN
from ..._compat import Self

if typing.TYPE_CHECKING:
    from ..fmt import ConstInfo, ConstPool


class Debug(Instruction):
    """
    A debug pseudo-instruction.
    """

    __slots__ = ()

    since = JAVA_MIN

    lt_throws = frozenset()
    rt_throws = frozenset()

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        raise ValueError("cannot read debug instruction")

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        ...


class LineNumber(Debug):
    """
    A line number indicator pseudo-instruction.

    Indicates that any code after this instruction, until the next line number
    indicator, was compiled from the given source code line number.

    Attributes
    ----------
    line: int
        The source code line number.
    """

    __slots__ = ("line",)

    opcode = -1
    mnemonic = "line"

    def __init__(self, line: int) -> None:
        super().__init__()
        self.line = line

    def __copy__(self) -> "LineNumber":
        copied = LineNumber(self.line)
        copied.offset = self.offset
        return copied

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<LineNumber(offset={self.offset}, line={self.line})>"
        return f"<LineNumber(line={self.line})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:line({self.line})"
        return f"line({self.line})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LineNumber) and self.line == other.line


class LocalStart(Debug):
    """
    A local variable range start pseudo-instruction

    Indicates that a local variable's valid range starts after this instruction.

    Attributes
    ----------
    index: int
        The index of the local variable in the local variable array.
    name: ConstInfo
        A UTF8 constant, used as the name of the local variable in the source code.
    descriptor: ConstInfo | None
        A UTF8 constant, used a descriptor representing the type of the local
        variable in the source code.
        If `None`, no type information was provided.
    signature: ConstInfo | None
        A UTF8 constant, used as a signature representing the generic (or not) type
        of the local variable in the source code.
        If `None`, no generic type information was provided.
    """

    __slots__ = ("index", "name", "descriptor", "signature")

    opcode = -1
    mnemonic = "localstart"

    def __init__(
            self, index: int, name: "ConstInfo",
            descriptor: Optional["ConstInfo"] = None,
            signature:  Optional["ConstInfo"] = None,
    ) -> None:
        super().__init__()
        self.index = index
        self.name = name
        self.descriptor = descriptor
        self.signature = signature

    def __copy__(self) -> "LocalStart":
        copied = LocalStart(self.index, self.name, self.descriptor, self.signature)
        copied.offset = self.offset
        return copied

    def __deepcopy__(self, memo: dict[int, object]) -> "LocalStart":
        copied = LocalStart(
            self.index, deepcopy(self.name, memo),
            deepcopy(self.descriptor, memo) if self.descriptor is not None else None,
            deepcopy(self.signature, memo) if self.signature is not None else None,
        )
        copied.offset = self.offset
        return copied

    def __repr__(self) -> str:
        if self.offset is not None:
            return (
                f"<LocalStart(offset={self.offset}, index={self.index}, name={self.name!s}, "
                f"descriptor={self.descriptor!s}, signature={self.signature!s})>"
            )
        return (
            f"<LocalStart(index={self.index}, name={self.name!s}, descriptor={self.descriptor!s}, "
            f"signature={self.signature!s})>"
        )

    def __str__(self) -> str:
        desc_str = str(self.descriptor) if self.descriptor is not None else "[none]"
        sig_str = str(self.signature) if self.signature is not None else "[none]"
        if self.offset is not None:
            return f"{self.offset}:localstart({self.index},{self.name!s},{desc_str},{sig_str})"
        return f"localstart({self.index},{self.name!s},{desc_str},{sig_str})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, LocalStart) and
            self.index == other.index and
            self.name == other.name and
            self.descriptor == other.descriptor and
            self.signature == other.signature
        )


class LocalEnd(Debug):
    """
    A local variable range end pseudo-instruction.

    Indicates that a local variable's valid range ends after this instruction.

    Attributes
    ----------
    index: int
        The index of the local variable in the local variable array.
    """

    __slots__ = ("index",)

    opcode = -1
    mnemonic = "localend"

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index

    def __copy__(self) -> "LocalEnd":
        copied = LocalEnd(self.index)
        copied.offset = self.offset
        return copied

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"<LocalEnd(offset={self.offset}, index={self.index})>"
        return f"<LocalEnd(index={self.index})>"

    def __str__(self) -> str:
        if self.offset is not None:
            return f"{self.offset}:localend({self.index})"
        return f"localend({self.index})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LocalEnd) and self.index == other.index

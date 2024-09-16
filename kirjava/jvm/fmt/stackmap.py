#!/usr/bin/env python3

__all__ = (
    "VerificationTypeInfo", "StackMapFrame",

    "TopVarInfo", "IntegerVarInfo", "FloatVarInfo",
    "LongVarInfo", "DoubleVarInfo", "NullVarInfo",
    "UninitializedThisVarInfo", "ObjectVarInfo", "UninitializedVarInfo",

    "SameFrame", "SameLocalsOneStackItemFrame", "SameLocalsOneStackItemFrameExtended",
    "ChopFrame", "SameFrameExtended", "AppendFrame",
    "FullFrame",
)

"""
JVM class file stack map frame and verification type structs.
"""

import typing
from functools import cache
from typing import IO

from .constants import ClassInfo, ConstInfo
from .._struct import *

if typing.TYPE_CHECKING:
    from .pool import ConstPool
    from ..verify import Verifier


class VerificationTypeInfo:
    """
    A verification_type_info union.

    Indicates an expected type in either the operand stack or local variable array,
    at a key execution point in the bytecode.

    Attributes
    ----------
    tag: int
        An integer used to identify the type of verification type info.

    Methods
    -------
    lookup(tag: int) -> type[VerificationTypeInfo] | None
        Looks up a verification type by tag.
    read(stream: IO[bytes], pool: ConstPool) -> VerificationTypeInfo
        Reads a verification type from a binary stream.
    """

    __slots__ = ()

    tag: int

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "VerificationTypeInfo":
        """
        Internal verification type read.
        """

        return cls()

    @classmethod
    @cache
    def lookup(cls, tag: int) -> type["VerificationTypeInfo"] | None:
        """
        Looks up a verification type by tag.

        Parameters
        ----------
        tag: int
            The tag to look up.

        Returns
        -------
        type[VerificationTypeInfo] | None
            The verification type subclass, or `None` if not found.
        """

        for subclass in cls.__subclasses__():
            if subclass.tag == tag:
                return subclass
        return None

    @classmethod
    def read(cls, stream: IO[bytes], pool: "ConstPool") -> "VerificationTypeInfo":
        """
        Reads a verification type from a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        pool: ConstPool
            The class file constant pool.
        """

        tag, = stream.read(1)
        subclass: type[VerificationTypeInfo] | None = cls.lookup(tag)
        if subclass is None:
            raise ValueError("invalid tag %i for verification type" % tag)
        return subclass._read(stream, pool)

    def __repr__(self) -> str:
        raise NotImplementedError("repr() is not implemented for %r" % type(self))

    def __str__(self) -> str:
        raise NotImplementedError("str() is not implemented for %r" % type(self))

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError("== is not implemented for %r" % type(self))

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        """
        Writes this verification type to the binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        pool: ConstPool
            The class file constant pool.
        """

        stream.write(bytes((self.tag,)))

    def verify(self, verifier: "Verifier") -> None:
        """
        Verifies that this verification type is valid.

        Parameters
        ----------
        verifier: Verifier
            The verifier to use and report to.
        """

        ...


class StackMapFrame:
    """
    A stack_map_frame union.

    Indicates the expected types on the operand stack and in the local variable
    array at a given point in the bytecode.

    Attributes
    ----------
    tags: range
        A range of integers indicating the valid tag values for this frame.
    tag: int
        An integer indicating the frame type and any additional information about
        the frame.

    Methods
    -------
    lookup(tag: int) -> type[StackMapFrame] | None
        Looks up a stack map frame by tag.
    read(stream: IO[bytes], pool: ConstPool) -> StackMapFrame
        Reads a stack map frame from the binary stream.
    write(self, stream: IO[bytes], pool: ConstPool) -> None
        Writes this stack map frame to the binary stream.
    verify(self, verifier: Verifier) -> None
        Verifies that this stack map frame is valid.
    """

    __slots__ = ()

    tags: range
    tag: int

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", tag: int) -> "StackMapFrame":
        """
        Stack map frame internal read.
        """

        raise NotImplementedError("_read() is not implemented for %r" % cls)

    @classmethod
    @cache
    def lookup(cls, tag: int) -> type["StackMapFrame"] | None:
        """
        Looks up a stack map frame by tag.

        Parameters
        ----------
        tag: int
            The tag to look up.

        Returns
        -------
        type[StackMapFrame] | None
            The stack map frame subclass, or `None` if not found.
        """

        for subclass in cls.__subclasses__():
            if tag in subclass.tags:
                return subclass
        return None

    @classmethod
    def read(cls, stream: IO[bytes], pool: "ConstPool") -> "StackMapFrame":
        """
        Reads a stack map frame from the binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        pool: ConstPool
            The class file constant pool.
        """

        tag, = stream.read(1)
        subclass: type[StackMapFrame] | None = cls.lookup(tag)
        assert subclass is not None, "unknown stack map frame tag %i" % tag  # Should be impossible if my impl is fine.
        return subclass._read(stream, pool, tag)

    # def __init__(self, tag: int) -> None:
    #     if not tag in self.tags:
    #         raise ValueError("invalid tag %i for %r, should be between %i and %i" % (
    #             tag, type(self), self.tags.start, self.tags.stop - 1,
    #         ))
    #     self.tag = tag

    def __repr__(self) -> str:
        raise NotImplementedError("repr() is not implemented for %r" % type(self))

    def __str__(self) -> str:
        raise NotImplementedError("str() is not implemented for %r" % type(self))

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError("== is not implemented for %r" % type(self))

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        """
        Writes this stack map frame to the binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        pool: ConstPool
            The class file constant pool.
        """

        raise NotImplementedError("write() is not implemented for %r" % type(self))

    def verify(self, verifier: "Verifier") -> None:
        """
        Verifies that this stack map frame is valid.

        Parameters
        ----------
        verifier: Verifier
            The verifier to use and report to.
        """

        if not self.tag in self.tags:
            verifier.fatal(self, "invalid stack map frame tag")


# ---------------------------------------- Verification Types ---------------------------------------- #

class TopVarInfo(VerificationTypeInfo):
    """
    A Top_variable_info struct.
    """

    __slots__ = ()

    tag = 0

    def __repr__(self) -> str:
        return "<TopVarInfo>"

    def __str__(self) -> str:
        return "top"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TopVarInfo)


class IntegerVarInfo(VerificationTypeInfo):
    """
    An Integer_variable_info struct.
    """

    __slots__ = ()

    tag = 1

    def __repr__(self) -> str:
        return "<IntegerVarInfo>"

    def __str__(self) -> str:
        return "int"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IntegerVarInfo)


class FloatVarInfo(VerificationTypeInfo):
    """
    A Float_variable_info struct.
    """

    __slots__ = ()

    tag = 2

    def __repr__(self) -> str:
        return "<FloatVarInfo>"

    def __str__(self) -> str:
        return "float"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FloatVarInfo)


class DoubleVarInfo(VerificationTypeInfo):
    """
    A Double_variable_info struct.
    """

    __slots__ = ()

    tag = 3

    def __repr__(self) -> str:
        return "<DoubleVarInfo>"

    def __str__(self) -> str:
        return "double"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DoubleVarInfo)


class LongVarInfo(VerificationTypeInfo):
    """
    A Long_variable_info struct.
    """

    __slots__ = ()

    tag = 4

    def __repr__(self) -> str:
        return "<LongVarInfo>"

    def __str__(self) -> str:
        return "long"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LongVarInfo)


class NullVarInfo(VerificationTypeInfo):
    """
    A Null_variable_info struct.
    """

    __slots__ = ()

    tag = 5

    def __repr__(self) -> str:
        return "<NullVarInfo>"

    def __str__(self) -> str:
        return "null"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NullVarInfo)


class UninitializedThisVarInfo(VerificationTypeInfo):
    """
    An UninitializedThis_variable_info struct.
    """

    __slots__ = ()

    tag = 6

    def __repr__(self) -> str:
        return "<UninitializedThisVarInfo>"

    def __str__(self) -> str:
        return "uninitializedThis"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UninitializedThisVarInfo)


class ObjectVarInfo(VerificationTypeInfo):
    """
    An Object_variable_info struct.

    Attributes
    ----------
    type: ConstInfo
        A class constant, used to represent the class of the object.
    """

    __slots__ = ("type",)

    tag = 7

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "ObjectVarInfo":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, type_: ConstInfo) -> None:
        self.type = type_

    def __repr__(self) -> str:
        return "<ObjectVarInfo(type=%r)>" % self.type

    def __str__(self) -> str:
        return "object[%s] " % self.type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ObjectVarInfo) and self.type == other.type

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.tag, pool.add(self.type)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types and not isinstance(self.type, ClassInfo):
            verifier.fatal(self, "type is not a class constant")


class UninitializedVarInfo(VerificationTypeInfo):
    """
    An Uninitialized_variable_info struct.

    Attributes
    ----------
    offset: int
        The bytecode offset of the `new` instruction that created the uninitialised
        object.
    """

    __slots__ = ("offset",)

    tag = 8

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "UninitializedVarInfo":
        offset, = unpack_H(stream.read(2))
        return cls(offset)

    def __init__(self, offset: int) -> None:
        self.offset = offset

    def __repr__(self) -> str:
        return "<UninitializedVarInfo(offset=%i)>" % self.offset

    def __str__(self) -> str:
        return "uninitialized[%i]" % self.offset

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UninitializedVarInfo) and self.offset == other.offset

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.tag, self.offset))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.offset <= 65535):
            verifier.fatal(self, "invalid bytecode offset")


# ---------------------------------------- Stack Map Frames ---------------------------------------- #

class SameFrame(StackMapFrame):
    """
    A same_frame struct.

    Indicates that the operand stack is empty and the local variables have the same
    types as the previous frame.

    Attributes
    ----------
    delta: int
        The bytecode offset delta from the previous frame.
    """

    __slots__ = ("tag",)

    tags = range(0, 64)

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", tag: int) -> "SameFrame":
        return cls(tag)

    @property
    def delta(self) -> int:
        return self.tag

    def __init__(self, tag: int) -> None:
        self.tag = tag

    def __repr__(self) -> str:
        return "<SameFrame(tag=%i)>" % self.tag

    def __str__(self) -> str:
        return "same_frame[%i]" % self.tag

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SameFrame) and self.tag == other.tag

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.tag,)))


class SameLocalsOneStackItemFrame(StackMapFrame):
    """
    A same_locals_1_stack_item_frame struct.

    Indicates that the operand stack has one entry and the local variables have the
    same types as the previous frame.

    Attributes
    ----------
    delta: int
        The bytecode offset delta from the previous frame.
    stack: VerificationTypeInfo
        The type of the single stack entry.
    """

    __slots__ = ("tag", "stack")

    tags = range(64, 128)

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", tag: int) -> "SameLocalsOneStackItemFrame":
        stack = VerificationTypeInfo.read(stream, pool)
        return cls(tag, stack)

    @property
    def delta(self) -> int:
        return self.tag - 64

    def __init__(self, tag: int, stack: VerificationTypeInfo) -> None:
        self.tag = tag
        self.stack = stack

    def __repr__(self) -> str:
        return "<SameLocalsOneStackItemFrame(tag=%i, stack=%r)>" % (self.tag, self.stack)

    def __str__(self) -> str:
        return "same_locals_1_stack_item_frame[%i,%s]" % (self.tag, self.stack)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SameLocalsOneStackItemFrame) and self.tag == other.tag and self.stack == other.stack

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((self.tag,)))
        self.stack.write(stream, pool)

    def verify(self, verifier: "Verifier") -> None:
        super().verify(verifier)
        self.stack.verify(verifier)


class SameLocalsOneStackItemFrameExtended(StackMapFrame):
    """
    A same_locals_1_stack_item_frame_extended struct.

    Indicates that the operand stack has one entry and the local variables have the
    same types as the previous frame.
    The offset delta is also explicitly specified.

    Attributes
    ----------
    delta: int
        The bytecode offset delta from the previous frame.
    stack: VerificationTypeInfo
        The verification type of the single operand stack entry.
    """

    __slots__ = ("delta", "stack")

    tags = range(247, 248)
    tag = 247

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", tag: int) -> "SameLocalsOneStackItemFrameExtended":
        delta, = unpack_H(stream.read(2))
        stack = VerificationTypeInfo.read(stream, pool)
        return cls(delta, stack)

    def __init__(self, delta: int, stack: VerificationTypeInfo) -> None:
        self.delta = delta
        self.stack = stack

    def __repr__(self) -> str:
        return "<SameLocalsOneStackItemFrameExtended(delta=%i, stack=%r)>" % (self.delta, self.stack)

    def __str__(self) -> str:
        return "same_local_1_stack_item_frame_extended[%i,%s]" % (self.delta, self.stack)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, SameLocalsOneStackItemFrameExtended) and
            self.delta == other.delta and
            self.stack == other.stack
        )

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(247, self.delta))
        self.stack.write(stream, pool)

    def verify(self, verifier: "Verifier") -> None:
        super().verify(verifier)
        if not (0 <= self.delta <= 65535):
            verifier.fatal(self, "invalid bytecode offset")
        self.stack.verify(verifier)


class ChopFrame(StackMapFrame):
    """
    A chop_frame struct.

    Indicates that the operand stack is empty and there are fewer local variables
    than the previous frame.

    Attributes
    ----------
    chopped: int
        The number of locals that are absent in this frame.
    delta: int
        The bytecode offset delta from the previous frame.
    """

    __slots__ = ("tag", "delta")

    tags = range(248, 251)

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", tag: int) -> "ChopFrame":
        delta, = unpack_H(stream.read(2))
        return cls(tag, delta)

    @property
    def chopped(self) -> int:
        return 251 - self.tag

    def __init__(self, tag: int, delta: int) -> None:
        self.tag = tag
        self.delta = delta

    def __repr__(self) -> str:
        return "<ChopFrame(tag=%i, delta=%i)>" % (self.tag, self.delta)

    def __str__(self) -> str:
        return "chop_frame[%i,%i]" % (self.tag, self.delta)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ChopFrame) and self.tag == other.tag and self.delta == other.delta

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.tag, self.delta))

    def verify(self, verifier: "Verifier") -> None:
        super().verify(verifier)
        if not (0 <= self.delta <= 65535):
            verifier.fatal(self, "invalid bytecode offset")


class SameFrameExtended(StackMapFrame):
    """
    A same_frame_extended struct.

    Indicates that the operand stack is empty and the local variables have the same
    types as the previous frame.
    The offset delta is also explicitly specified.

    Attributes
    ----------
    delta: int
        The bytecode offset delta from the previous frame.
    """

    __slots__ = ("delta",)

    tags = range(251, 252)
    tag = 251

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", tag: int) -> "SameFrameExtended":
        delta, = unpack_H(stream.read(2))
        return cls(delta)

    def __init__(self, delta: int) -> None:
        self.delta = delta

    def __repr__(self) -> str:
        return "<SameFrameExtended(delta=%i)>" % self.delta

    def __str__(self) -> str:
        return "same_frame_extended[%i]" % self.delta

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SameFrameExtended) and self.delta == other.delta

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(251, self.delta))

    def verify(self, verifier: "Verifier") -> None:
        super().verify(verifier)
        if not (0 <= self.delta <= 65535):
            verifier.fatal(self, "invalid bytecode offset")


class AppendFrame(StackMapFrame):
    """
    An append_frame struct.

    Indicates that the operand stack is empty and there are more local variables than
    the previous frame.

    Attributes
    ----------
    delta: int
        The bytecode offset delta from the previous frame.
    locals: tuple[VerificationTypeInfo, ...]
        The types of the additional local variables.
    """

    __slots__ = ("tag", "delta", "locals")

    tags = range(252, 255)

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", tag: int) -> "AppendFrame":
        delta, = unpack_H(stream.read(2))
        locals_ = tuple(VerificationTypeInfo.read(stream, pool) for _ in range(tag - 251))
        return cls(tag, delta, locals_)

    def __init__(self, tag: int, delta: int, locals_: tuple[VerificationTypeInfo, ...]) -> None:
        # if tag - 251 != len(locals_):
        #     raise ValueError("invalid tag %i for %r, should reflect locals count" % (tag, type(self)))
        self.tag = tag
        self.delta = delta
        self.locals = locals_

    def __repr__(self) -> str:
        return "<AppendFrame(tag=%i, delta=%i, locals=%r)>" % (self.tag, self.delta, self.locals)

    def __str__(self) -> str:
        return "append_frame[%i,%i,[%s]" % (self.tag, self.delta, ",".join(map(str, self.locals)))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, AppendFrame) and
            self.tag == other.tag and
            self.delta == other.delta and
            self.locals == other.locals
        )

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.tag, self.delta))
        for local in self.locals:
            local.write(stream, pool)

    def verify(self, verifier: "Verifier") -> None:
        super().verify(verifier)
        if self.tag - 251 != len(self.locals):
            verifier.fatal(self, "invalid tag for locals count")
        if not (0 <= self.delta <= 65535):
            verifier.fatal(self, "invalid bytecode offset")
        for local in self.locals:
            local.verify(verifier)


class FullFrame(StackMapFrame):
    """
    A full_frame struct.

    Indicates that the operand stack and local variables are completely different
    from the previous frame, and are explicitly specified.

    Attributes
    ----------
    delta: int
        The bytecode offset delta from the previous frame.
    locals: tuple[VerificationTypeInfo, ...]
        The types of the local variables.
    stack: tuple[VerificationTypeInfo, ...]
        The types on the operand stack.
    """

    __slots__ = ("delta", "locals", "stack")

    tags = range(255, 256)
    tag = 255

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", tag: int) -> "FullFrame":
        delta, locals_count = unpack_HH(stream.read(4))
        locals_ = tuple(VerificationTypeInfo.read(stream, pool) for _ in range(locals_count))
        stack_count, = unpack_H(stream.read(2))
        stack = tuple(VerificationTypeInfo.read(stream, pool) for _ in range(stack_count))
        return cls(delta, locals_, stack)

    def __init__(
            self, delta: int, locals_: tuple[VerificationTypeInfo, ...], stack: tuple[VerificationTypeInfo, ...],
    ) -> None:
        self.delta = delta
        self.locals = locals_
        self.stack = stack

    def __repr__(self) -> str:
        return "<FullFrame(delta=%i, locals=%r, stack=%r)>" % (self.delta, self.locals, self.stack)

    def __str__(self) -> str:
        return "full_frame[%i,[%s],[%s]]" % (
            self.delta, ",".join(map(str, self.locals)), ",".join(map(str, self.stack)),
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FullFrame) and
            self.delta == other.delta and
            self.locals == other.locals and
            self.stack == other.stack
        )

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(255, self.delta, len(self.locals)))
        for local in self.locals:
            local.write(stream, pool)
        stream.write(pack_H(len(self.stack)))
        for stack in self.stack:
            stack.write(stream, pool)

    def verify(self, verifier: "Verifier") -> None:
        super().verify(verifier)
        if not (0 <= self.delta <= 65535):
            verifier.fatal(self, "invalid bytecode offset")
        if len(self.locals) > 65535:
            verifier.fatal(self, "too many locals")
        if len(self.stack) > 65535:
            verifier.fatal(self, "too many stack entries")
        for local in self.locals:
            local.verify(verifier)
        for stack in self.stack:
            stack.verify(verifier)

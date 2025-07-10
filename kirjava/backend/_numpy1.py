#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "u8", "u16", "u32", "u64",
    "i8", "i16", "i32", "i64",
    "f32", "f64",
    "isnan",
    "unpack_u8", "pack_u8", "unpack_u16", "pack_u16", "unpack_u32", "pack_u32", "unpack_u64", "pack_u64",
    "unpack_i8", "pack_i8", "unpack_i16", "pack_i16", "unpack_i32", "pack_i32", "unpack_i64", "pack_i64",
    "unpack_f32", "pack_f32", "unpack_f64", "pack_f64",
)

"""
A numpy <2.0.0 backend implementation:
 - https://numpy.org/devdocs/release/2.0.0-notes.html
"""

import math
from typing import Any, SupportsInt, SupportsFloat

import numpy as np

if np.__version__ >= "2.0.0":
    raise ImportError(f"numpy version {np.__version__} not supported, need <2.0.0")


_u8  = np.dtype(">u1")
_u16 = np.dtype(">u2")
_u32 = np.dtype(">u4")
_u64 = np.dtype(">u8")

_i8  = np.dtype(">i1")
_i16 = np.dtype(">i2")
_i32 = np.dtype(">i4")
_i64 = np.dtype(">i8")

_f32 = np.dtype(">f4")
_f64 = np.dtype(">f8")


def isnan(value: Any) -> bool:
    """
    Checks if a value is NaN.
    """

    if isinstance(value, f32):
        return bool(np.isnan(value._value))
    elif isinstance(value, f64):
        return bool(np.isnan(value._value))
    elif isinstance(value, float):
        return math.isnan(value)
    return False  # TODO: Type error?


def unpack_u8(data: bytes) -> "u8":
    try:
        return u8(np.frombuffer(data, dtype=_u8)[0])
    except IndexError:
        raise ValueError("1 byte needed to unpack u8") from None


def pack_u8(value: "u8") -> bytes:
    return np.array(value._value, dtype=_u8).tobytes()


def unpack_u16(data: bytes) -> "u16":
    try:
        return u16(np.frombuffer(data, dtype=_u16)[0])
    except IndexError:
        raise ValueError("2 bytes needed to unpack u16") from None


def pack_u16(value: "u16") -> bytes:
    return np.array(value._value, dtype=_u16).tobytes()


def unpack_u32(data: bytes) -> "u32":
    try:
        return u32(np.frombuffer(data, dtype=_u32)[0])
    except IndexError:
        raise ValueError("4 bytes needed to unpack u32") from None


def pack_u32(value: "u32") -> bytes:
    return np.array(value._value, dtype=_u32).tobytes()


def unpack_u64(data: bytes) -> "u64":
    try:
        return u64(np.frombuffer(data, dtype=_u64)[0])
    except IndexError:
        raise ValueError("8 bytes needed to unpack u64") from None


def pack_u64(value: "u64") -> bytes:
    return np.array(value._value, dtype=_u64).tobytes()


def unpack_i8(data: bytes) -> "i8":
    try:
        return i8(np.frombuffer(data, dtype=_i8)[0])
    except IndexError:
        raise ValueError("1 byte needed to unpack i8") from None


def pack_i8(value: "i8") -> bytes:
    return np.array(value._value, dtype=_i8).tobytes()


def unpack_i16(data: bytes) -> "i16":
    try:
        return i16(np.frombuffer(data, dtype=_i16)[0])
    except IndexError:
        raise ValueError("2 bytes needed to unpack i16") from None


def pack_i16(value: "i16") -> bytes:
    return np.array(value._value, dtype=_i16).tobytes()


def unpack_i32(data: bytes) -> "i32":
    try:
        return i32(np.frombuffer(data, dtype=_i32)[0])
    except IndexError:
        raise ValueError("4 bytes needed to unpack i32") from None


def pack_i32(value: "i32") -> bytes:
    return np.array(value._value, dtype=_i32).tobytes()


def unpack_i64(data: bytes) -> "i64":
    try:
        return i64(np.frombuffer(data, dtype=_i64)[0])
    except IndexError:
        raise ValueError("8 bytes needed to unpack i64") from None


def pack_i64(value: "i64") -> bytes:
    return np.array(value._value, dtype=_i64).tobytes()


def unpack_f32(data: bytes) -> "f32":
    try:
        return f32(np.frombuffer(data, dtype=_f32)[0])
    except IndexError:
        raise ValueError("4 bytes needed to unpack f32") from None


def pack_f32(value: "f32") -> bytes:
    return np.array(value._value, dtype=_f32).tobytes()


def unpack_f64(data: bytes) -> "f64":
    try:
        return f64(np.frombuffer(data, dtype=_f64)[0])
    except IndexError:
        raise ValueError("8 bytes needed to unpack f64") from None


def pack_f64(value: "f64") -> bytes:
    return np.array(value._value, dtype=_f64).tobytes()


class u8:

    __slots__ = ("_value",)

    def __init__(self, value: SupportsInt) -> None:
        if isinstance(value, np.uint8):
            self._value = value
            return
        self._value = np.uint8(value)
        if self._value != value:  # Kinda hacky, oh well.
            raise OverflowError(f"{value} out of bounds for u8")

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __lt__(self, other: Any) -> bool:
        return bool(self._value < other)

    def __le__(self, other: Any) -> bool:
        return bool(self._value <= other)

    def __eq__(self, other: Any) -> bool:
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return bool(self._value != other)

    def __gt__(self, other: Any) -> bool:
        return bool(self._value > other)

    def __ge__(self, other: Any) -> bool:
        return bool(self._value >= other)

    def __hash__(self) -> int:
        return hash(self._value)

    def __add__(self, other: SupportsInt) -> "u8":
        return u8(self._value + np.uint8(other))

    def __sub__(self, other: SupportsInt) -> "u8":
        return u8(self._value - np.uint8(other))

    def __mul__(self, other: SupportsInt) -> "u8":
        return u8(self._value * np.uint8(other))

    def __mod__(self, other: SupportsInt) -> "u8":
        return u8(self._value % np.uint8(other))

    def __floordiv__(self, other: SupportsInt) -> "u8":
        return u8(self._value // np.uint8(other))

    def __truediv__(self, other: SupportsInt) -> "u8":
        return u8(self._value // np.uint8(other))

    def __neg__(self) -> "u8":
        return u8(-self._value)

    def __abs__(self) -> "u8":
        return self

    def __invert__(self) -> "u8":
        return u8(~self._value)

    def __lshift__(self, other: SupportsInt) -> "u8":
        return u8(self._value << np.uint8(other))

    def __rshift__(self, other: SupportsInt) -> "u8":
        return u8(self._value >> np.uint8(other))

    def __and__(self, other: SupportsInt) -> "u8":
        return u8(self._value & np.uint8(other))

    def __xor__(self, other: SupportsInt) -> "u8":
        return u8(self._value ^ np.uint8(other))

    def __or__(self, other: SupportsInt) -> "u8":
        return u8(self._value | np.uint8(other))


class u16:

    __slots__ = ("_value",)

    def __init__(self, value: SupportsInt) -> None:
        if isinstance(value, np.uint16):
            self._value = value
            return
        self._value = np.uint16(value)
        if self._value != value:
            raise OverflowError(f"{value} out of bounds for u16")

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __lt__(self, other: Any) -> bool:
        return bool(self._value < other)

    def __le__(self, other: Any) -> bool:
        return bool(self._value <= other)

    def __eq__(self, other: Any) -> bool:
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return bool(self._value != other)

    def __gt__(self, other: Any) -> bool:
        return bool(self._value > other)

    def __ge__(self, other: Any) -> bool:
        return bool(self._value >= other)

    def __hash__(self) -> int:
        return hash(self._value)

    def __add__(self, other: SupportsInt) -> "u16":
        return u16(self._value + np.uint16(other))

    def __sub__(self, other: SupportsInt) -> "u16":
        return u16(self._value - np.uint16(other))

    def __mul__(self, other: SupportsInt) -> "u16":
        return u16(self._value * np.uint16(other))

    def __mod__(self, other: SupportsInt) -> "u16":
        return u16(self._value % np.uint16(other))

    def __floordiv__(self, other: SupportsInt) -> "u16":
        return u16(self._value // np.uint16(other))

    def __truediv__(self, other: SupportsInt) -> "u16":
        return u16(self._value // np.uint16(other))

    def __neg__(self) -> "u16":
        return u16(-self._value)

    def __abs__(self) -> "u16":
        return self

    def __invert__(self) -> "u16":
        return u16(~self._value)

    def __lshift__(self, other: SupportsInt) -> "u16":
        return u16(self._value << np.uint16(other))

    def __rshift__(self, other: SupportsInt) -> "u16":
        return u16(self._value >> np.uint16(other))

    def __and__(self, other: SupportsInt) -> "u16":
        return u16(self._value & np.uint16(other))

    def __xor__(self, other: SupportsInt) -> "u16":
        return u16(self._value ^ np.uint16(other))

    def __or__(self, other: SupportsInt) -> "u16":
        return u16(self._value | np.uint16(other))


class u32:

    __slots__ = ("_value",)

    def __init__(self, value: SupportsInt) -> None:
        if isinstance(value, np.uint32):
            self._value = value
            return
        self._value = np.uint32(value)
        if self._value != value:
            raise OverflowError(f"{value} out of bounds for u32")

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __lt__(self, other: Any) -> bool:
        return bool(self._value < other)

    def __le__(self, other: Any) -> bool:
        return bool(self._value <= other)

    def __eq__(self, other: Any) -> bool:
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return bool(self._value != other)

    def __gt__(self, other: Any) -> bool:
        return bool(self._value > other)

    def __ge__(self, other: Any) -> bool:
        return bool(self._value >= other)

    def __hash__(self) -> int:
        return hash(self._value)

    def __add__(self, other: SupportsInt) -> "u32":
        return u32(self._value + np.uint32(other))

    def __sub__(self, other: SupportsInt) -> "u32":
        return u32(self._value - np.uint32(other))

    def __mul__(self, other: SupportsInt) -> "u32":
        return u32(self._value * np.uint32(other))

    def __mod__(self, other: SupportsInt) -> "u32":
        return u32(self._value % np.uint32(other))

    def __floordiv__(self, other: SupportsInt) -> "u32":
        return u32(self._value // np.uint32(other))

    def __truediv__(self, other: SupportsInt) -> "u32":
        return u32(self._value // np.uint32(other))

    def __neg__(self) -> "u32":
        return u32(-self._value)

    def __abs__(self) -> "u32":
        return self

    def __invert__(self) -> "u32":
        return u32(~self._value)

    def __lshift__(self, other: SupportsInt) -> "u32":
        return u32(self._value << np.uint32(other))

    def __rshift__(self, other: SupportsInt) -> "u32":
        return u32(self._value >> np.uint32(other))

    def __and__(self, other: SupportsInt) -> "u32":
        return u32(self._value & np.uint32(other))

    def __xor__(self, other: SupportsInt) -> "u32":
        return u32(self._value ^ np.uint32(other))

    def __or__(self, other: SupportsInt) -> "u32":
        return u32(self._value | np.uint32(other))


class u64:

    __slots__ = ("_value",)

    def __init__(self, value: SupportsInt) -> None:
        if isinstance(value, np.uint64):
            self._value = value
            return
        self._value = np.uint64(value)
        if self._value != value:
            raise OverflowError(f"{value} out of bounds for u64")

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __lt__(self, other: Any) -> bool:
        return bool(self._value < other)

    def __le__(self, other: Any) -> bool:
        return bool(self._value <= other)

    def __eq__(self, other: Any) -> bool:
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return bool(self._value != other)

    def __gt__(self, other: Any) -> bool:
        return bool(self._value > other)

    def __ge__(self, other: Any) -> bool:
        return bool(self._value >= other)

    def __hash__(self) -> int:
        return hash(self._value)

    def __add__(self, other: SupportsInt) -> "u64":
        return u64(self._value + np.uint64(other))

    def __sub__(self, other: SupportsInt) -> "u64":
        return u64(self._value - np.uint64(other))

    def __mul__(self, other: SupportsInt) -> "u64":
        return u64(self._value * np.uint64(other))

    def __mod__(self, other: SupportsInt) -> "u64":
        return u64(self._value % np.uint64(other))

    def __floordiv__(self, other: SupportsInt) -> "u64":
        return u64(self._value // np.uint64(other))

    def __truediv__(self, other: SupportsInt) -> "u64":
        return u64(self._value // np.uint64(other))

    def __neg__(self) -> "u64":
        return u64(-self._value)

    def __abs__(self) -> "u64":
        return self

    def __invert__(self) -> "u64":
        return u64(~self._value)

    def __lshift__(self, other: SupportsInt) -> "u64":
        return u64(self._value << np.uint64(other))

    def __rshift__(self, other: SupportsInt) -> "u64":
        return u64(self._value >> np.uint64(other))

    def __and__(self, other: SupportsInt) -> "u64":
        return u64(self._value & np.uint64(other))

    def __xor__(self, other: SupportsInt) -> "u64":
        return u64(self._value ^ np.uint64(other))

    def __or__(self, other: SupportsInt) -> "u64":
        return u64(self._value | np.uint64(other))


class i8:

    __slots__ = ("_value",)

    def __init__(self, value: SupportsInt) -> None:
        if isinstance(value, np.int8):
            self._value = value
            return
        self._value = np.int8(value)
        if self._value != value:
            raise OverflowError(f"{value} out of bounds for i8")

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __lt__(self, other: Any) -> bool:
        return bool(self._value < other)

    def __le__(self, other: Any) -> bool:
        return bool(self._value <= other)

    def __eq__(self, other: Any) -> bool:
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return bool(self._value != other)

    def __gt__(self, other: Any) -> bool:
        return bool(self._value > other)

    def __ge__(self, other: Any) -> bool:
        return bool(self._value >= other)

    def __hash__(self) -> int:
        return hash(self._value)

    def __add__(self, other: SupportsInt) -> "i8":
        return i8(self._value + np.int8(other))

    def __sub__(self, other: SupportsInt) -> "i8":
        return i8(self._value - np.int8(other))

    def __mul__(self, other: SupportsInt) -> "i8":
        return i8(self._value * np.int8(other))

    def __mod__(self, other: SupportsInt) -> "i8":
        return i8(self._value % np.int8(other))

    def __floordiv__(self, other: SupportsInt) -> "i8":
        return i8(self._value // np.int8(other))

    def __truediv__(self, other: SupportsInt) -> "i8":
        return i8(self._value // np.int8(other))

    def __neg__(self) -> "i8":
        return i8(-self._value)

    def __abs__(self) -> "i8":
        return i8(abs(self._value))

    def __invert__(self) -> "i8":
        return i8(~self._value)

    def __lshift__(self, other: SupportsInt) -> "i8":
        return i8(self._value << np.int8(other))

    def __rshift__(self, other: SupportsInt) -> "i8":
        return i8(self._value >> np.int8(other))

    def __and__(self, other: SupportsInt) -> "i8":
        return i8(self._value & np.int8(other))

    def __xor__(self, other: SupportsInt) -> "i8":
        return i8(self._value ^ np.int8(other))

    def __or__(self, other: SupportsInt) -> "i8":
        return i8(self._value | np.int8(other))


class i16:

    __slots__ = ("_value",)

    def __init__(self, value: SupportsInt) -> None:
        if isinstance(value, np.int16):
            self._value = value
            return
        self._value = np.int16(value)
        if self._value != value:
            raise OverflowError(f"{value} out of bounds for i16")

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __lt__(self, other: Any) -> bool:
        return bool(self._value < other)

    def __le__(self, other: Any) -> bool:
        return bool(self._value <= other)

    def __eq__(self, other: Any) -> bool:
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return bool(self._value != other)

    def __gt__(self, other: Any) -> bool:
        return bool(self._value > other)

    def __ge__(self, other: Any) -> bool:
        return bool(self._value >= other)

    def __hash__(self) -> int:
        return hash(self._value)

    def __add__(self, other: SupportsInt) -> "i16":
        return i16(self._value + np.int16(other))

    def __sub__(self, other: SupportsInt) -> "i16":
        return i16(self._value - np.int16(other))

    def __mul__(self, other: SupportsInt) -> "i16":
        return i16(self._value * np.int16(other))

    def __mod__(self, other: SupportsInt) -> "i16":
        return i16(self._value % np.int16(other))

    def __floordiv__(self, other: SupportsInt) -> "i16":
        return i16(self._value // np.int16(other))

    def __truediv__(self, other: SupportsInt) -> "i16":
        return i16(self._value // np.int16(other))

    def __neg__(self) -> "i16":
        return i16(-self._value)

    def __abs__(self) -> "i16":
        return i16(abs(self._value))

    def __invert__(self) -> "i16":
        return i16(~self._value)

    def __lshift__(self, other: SupportsInt) -> "i16":
        return i16(self._value << np.int16(other))

    def __rshift__(self, other: SupportsInt) -> "i16":
        return i16(self._value >> np.int16(other))

    def __and__(self, other: SupportsInt) -> "i16":
        return i16(self._value & np.int16(other))

    def __xor__(self, other: SupportsInt) -> "i16":
        return i16(self._value ^ np.int16(other))

    def __or__(self, other: SupportsInt) -> "i16":
        return i16(self._value | np.int16(other))


class i32:

    __slots__ = ("_value",)

    def __init__(self, value: SupportsInt) -> None:
        if isinstance(value, np.int32):
            self._value = value
            return
        self._value = np.int32(value)
        if self._value != value:
            raise OverflowError(f"{value} out of bounds for i32")

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __lt__(self, other: Any) -> bool:
        return bool(self._value < other)

    def __le__(self, other: Any) -> bool:
        return bool(self._value <= other)

    def __eq__(self, other: Any) -> bool:
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return bool(self._value != other)

    def __gt__(self, other: Any) -> bool:
        return bool(self._value > other)

    def __ge__(self, other: Any) -> bool:
        return bool(self._value >= other)

    def __hash__(self) -> int:
        return hash(self._value)

    def __add__(self, other: SupportsInt) -> "i32":
        return i32(self._value + np.int32(other))

    def __sub__(self, other: SupportsInt) -> "i32":
        return i32(self._value - np.int32(other))

    def __mul__(self, other: SupportsInt) -> "i32":
        return i32(self._value * np.int32(other))

    def __mod__(self, other: SupportsInt) -> "i32":
        return i32(self._value % np.int32(other))

    def __floordiv__(self, other: SupportsInt) -> "i32":
        return i32(self._value // np.int32(other))

    def __truediv__(self, other: SupportsInt) -> "i32":
        return i32(self._value // np.int32(other))

    def __neg__(self) -> "i32":
        return i32(-self._value)

    def __abs__(self) -> "i32":
        return i32(abs(self._value))

    def __invert__(self) -> "i32":
        return i32(~self._value)

    def __lshift__(self, other: SupportsInt) -> "i32":
        return i32(self._value << np.int32(other))

    def __rshift__(self, other: SupportsInt) -> "i32":
        return i32(self._value >> np.int32(other))

    def __and__(self, other: SupportsInt) -> "i32":
        return i32(self._value & np.int32(other))

    def __xor__(self, other: SupportsInt) -> "i32":
        return i32(self._value ^ np.int32(other))

    def __or__(self, other: SupportsInt) -> "i32":
        return i32(self._value | np.int32(other))


class i64:

    __slots__ = ("_value",)

    def __init__(self, value: SupportsInt) -> None:
        if isinstance(value, np.int64):
            self._value = value
            return
        self._value = np.int64(value)
        if self._value != value:
            raise OverflowError(f"{value} out of bounds for i64")

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __lt__(self, other: Any) -> bool:
        return bool(self._value < other)

    def __le__(self, other: Any) -> bool:
        return bool(self._value <= other)

    def __eq__(self, other: Any) -> bool:
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return bool(self._value != other)

    def __gt__(self, other: Any) -> bool:
        return bool(self._value > other)

    def __ge__(self, other: Any) -> bool:
        return bool(self._value >= other)

    def __hash__(self) -> int:
        return hash(self._value)

    def __add__(self, other: SupportsInt) -> "i64":
        return i64(self._value + np.int64(other))

    def __sub__(self, other: SupportsInt) -> "i64":
        return i64(self._value - np.int64(other))

    def __mul__(self, other: SupportsInt) -> "i64":
        return i64(self._value * np.int64(other))

    def __mod__(self, other: SupportsInt) -> "i64":
        return i64(self._value % np.int64(other))

    def __floordiv__(self, other: SupportsInt) -> "i64":
        return i64(self._value // np.int64(other))

    def __truediv__(self, other: SupportsInt) -> "i64":
        return i64(self._value // np.int64(other))

    def __neg__(self) -> "i64":
        return i64(-self._value)

    def __abs__(self) -> "i64":
        return i64(abs(self._value))

    def __invert__(self) -> "i64":
        return i64(~self._value)

    def __lshift__(self, other: SupportsInt) -> "i64":
        return i64(self._value << np.int64(other))

    def __rshift__(self, other: SupportsInt) -> "i64":
        return i64(self._value >> np.int64(other))

    def __and__(self, other: SupportsInt) -> "i64":
        return i64(self._value & np.int64(other))

    def __xor__(self, other: SupportsInt) -> "i64":
        return i64(self._value ^ np.int64(other))

    def __or__(self, other: SupportsInt) -> "i64":
        return i64(self._value | np.int64(other))


class f32:

    __slots__ = ("_value",)

    def __init__(self, value: SupportsFloat) -> None:
        self._value = np.float32(value)

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __lt__(self, other: Any) -> bool:
        return bool(self._value < other)

    def __le__(self, other: Any) -> bool:
        return bool(self._value <= other)

    def __eq__(self, other: Any) -> bool:
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return bool(self._value != other)

    def __gt__(self, other: Any) -> bool:
        return bool(self._value > other)

    def __ge__(self, other: Any) -> bool:
        return bool(self._value >= other)

    def __hash__(self) -> int:
        return hash(self._value)

    def __add__(self, other: SupportsFloat) -> "f32":
        return f32(self._value + np.float32(other))

    def __sub__(self, other: SupportsFloat) -> "f32":
        return f32(self._value - np.float32(other))

    def __mul__(self, other: SupportsFloat) -> "f32":
        return f32(self._value * np.float32(other))

    def __mod__(self, other: SupportsFloat) -> "f32":
        return f32(self._value % np.float32(other))

    def __floordiv__(self, other: SupportsFloat) -> "f32":
        return f32(self._value // np.float32(other))

    def __truediv__(self, other: SupportsFloat) -> "f32":
        return f32(self._value / np.float32(other))

    def __neg__(self) -> "f32":
        return f32(-self._value)

    def __abs__(self) -> "f32":
        if self._value >= 0:
            return self
        return f32(-self._value)

    def __trunc__(self) -> "f32":
        return f32(np.trunc(self._value))

    def __floor__(self) -> "f32":
        return f32(np.floor(self._value))

    def __ceil__(self) -> "f32":
        return f32(np.ceil(self._value))

    def __round__(self, places: int | None = None) -> "f32":
        return f32(np.round(self._value))


class f64:

    __slots__ = ("_value",)

    def __init__(self, value: SupportsFloat) -> None:
        self._value = np.float64(value)

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __lt__(self, other: Any) -> bool:
        return bool(self._value < other)

    def __le__(self, other: Any) -> bool:
        return bool(self._value <= other)

    def __eq__(self, other: Any) -> bool:
        return bool(self._value == other)

    def __ne__(self, other: Any) -> bool:
        return bool(self._value != other)

    def __gt__(self, other: Any) -> bool:
        return bool(self._value > other)

    def __ge__(self, other: Any) -> bool:
        return bool(self._value >= other)

    def __hash__(self) -> int:
        return hash(self._value)

    def __add__(self, other: SupportsFloat) -> "f64":
        return f64(self._value + np.float64(other))

    def __sub__(self, other: SupportsFloat) -> "f64":
        return f64(self._value - np.float64(other))

    def __mul__(self, other: SupportsFloat) -> "f64":
        return f64(self._value * np.float64(other))

    def __mod__(self, other: SupportsFloat) -> "f64":
        return f64(self._value % np.float64(other))

    def __floordiv__(self, other: SupportsFloat) -> "f64":
        return f64(self._value // np.float64(other))

    def __truediv__(self, other: SupportsFloat) -> "f64":
        return f64(self._value / np.float64(other))

    def __neg__(self) -> "f64":
        return f64(-self._value)

    def __abs__(self) -> "f64":
        if self._value >= 0:
            return self
        return f64(-self._value)

    def __trunc__(self) -> "f64":
        return f64(np.trunc(self._value))

    def __floor__(self) -> "f64":
        return f64(np.floor(self._value))

    def __ceil__(self) -> "f64":
        return f64(np.ceil(self._value))

    def __round__(self, places: int | None = None) -> "f64":
        return f64(np.round(self._value))

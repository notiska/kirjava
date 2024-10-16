# cython: language=c
# cython: language_level=3

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
A Cython backend implementation.
"""

import math
import sys

from libc cimport math as cmath
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t, int8_t, int16_t, int32_t, int64_t

# Sanity checks.
assert sizeof(uint8_t) == 1, "uint8_t is not 1 byte"
assert sizeof(uint16_t) == 2, "uint16_t is not 2 bytes"
assert sizeof(uint32_t) == 4, "uint32_t is not 4 bytes"
assert sizeof(uint64_t) == 8, "uint64_t is not 8 bytes"
assert sizeof(int8_t) == 1, "int8_t is not 1 byte"
assert sizeof(int16_t) == 2, "int16_t is not 2 bytes"
assert sizeof(int32_t) == 4, "int32_t is not 4 bytes"
assert sizeof(int64_t) == 8, "int64_t is not 8 bytes"
assert sizeof(float) == 4, "float is not 4 bytes"
assert sizeof(double) == 8, "double is not 8 bytes"


cdef class u8:

    cdef uint8_t value

    def __init__(self, value: object) -> None:
        # if isinstance(value, int):
        #     self.value = <uint8_t>value
        self.value = <uint8_t>value

    def __repr__(self) -> str:
        return f"<u8({self.value})>"

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value

    def __float__(self) -> float:
        return float(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __lt__(self, other: object) -> bool:
        # Performance: The `isinstance` check is ~10ns slower for non-u8 checks and negligible for u8 checks.
        # if isinstance(other, u8):
        #     return self.value < (<u8>other).value
        return self.value < other

    def __le__(self, other: object) -> bool:
        return self.value <= other

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __gt__(self, other: object) -> bool:
        return self.value > other

    def __ge__(self, other: object) -> bool:
        return self.value >= other

    def __hash__(self) -> int:
        return self.value

    def __add__(self, other: object) -> u8:
        cdef uint8_t value = self.value + <uint8_t>other
        return u8(value)

    def __sub__(self, other: object) -> u8:
        cdef uint8_t value = self.value - <uint8_t>other
        return u8(value)

    def __mul__(self, other: object) -> u8:
        cdef uint8_t value = self.value * <uint8_t>other
        return u8(value)

    def __mod__(self, other: object) -> u8:
        cdef uint8_t value = self.value % <uint8_t>other
        return u8(value)

    def __floordiv__(self, other: object) -> u8:
        cdef uint8_t value = self.value // <uint8_t>other
        return u8(value)

    def __truediv__(self, other: object) -> u8:
        cdef uint8_t value = self.value // <uint8_t>other
        return u8(value)

    # def __pow__(self, power, modulo: int | None = None) -> u8:
    #     if modulo is not None:
    #         return u8(pow(self.value, power, modulo))
    #     return u8(pow(self.value, power))

    def __neg__(self) -> u8:
        cdef uint8_t value = -self.value
        return u8(value)

    def __abs__(self) -> u8:
        return self

    def __invert__(self) -> u8:
        cdef uint8_t value = ~self.value
        return u8(value)

    def __lshift__(self, other: object) -> u8:
        cdef uint8_t value = self.value << <uint8_t>other
        return u8(value)

    def __rshift__(self, other: object) -> u8:
        cdef uint8_t value = self.value >> <uint8_t>other
        return u8(value)

    def __and__(self, other: object) -> u8:
        cdef uint8_t value = self.value & <uint8_t>other
        return u8(value)

    def __xor__(self, other: object) -> u8:
        cdef uint8_t value = self.value ^ <uint8_t>other
        return u8(value)

    def __or__(self, other: object) -> u8:
        cdef uint8_t value = self.value | <uint8_t>other
        return u8(value)


cdef class u16:

    cdef uint16_t value

    def __init__(self, value: object) -> None:
        self.value = <uint16_t>value

    def __repr__(self) -> str:
        return f"<u16({self.value})>"

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __lt__(self, other: object) -> bool:
        return self.value < other

    def __le__(self, other: object) -> bool:
        return self.value <= other

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __gt__(self, other: object) -> bool:
        return self.value > other

    def __ge__(self, other: object) -> bool:
        return self.value >= other

    def __hash__(self) -> int:
        return self.value

    def __add__(self, other: object) -> u16:
        cdef uint16_t value = self.value + <uint16_t>other
        return u16(value)

    def __sub__(self, other: object) -> u16:
        cdef uint16_t value = self.value - <uint16_t>other
        return u16(value)

    def __mul__(self, other: object) -> u16:
        cdef uint16_t value = self.value * <uint16_t>other
        return u16(value)

    def __mod__(self, other: object) -> u16:
        cdef uint16_t value = self.value % <uint16_t>other
        return u16(value)

    def __floordiv__(self, other: object) -> u16:
        cdef uint16_t value = self.value // <uint16_t>other
        return u16(value)

    def __truediv__(self, other: object) -> u16:
        cdef uint16_t value = self.value // <uint16_t>other
        return u16(value)

    def __neg__(self) -> u16:
        cdef uint16_t value = -self.value
        return u16(value)

    def __abs__(self) -> u16:
        return self

    def __invert__(self) -> u16:
        cdef uint16_t value = ~self.value
        return u16(value)

    def __lshift__(self, other: object) -> u16:
        cdef uint16_t value = self.value << <uint16_t>other
        return u16(value)

    def __rshift__(self, other: object) -> u16:
        cdef uint16_t value = self.value >> <uint16_t>other
        return u16(value)

    def __and__(self, other: object) -> u16:
        cdef uint16_t value = self.value & <uint16_t>other
        return u16(value)

    def __xor__(self, other: object) -> u16:
        cdef uint16_t value = self.value ^ <uint16_t>other
        return u16(value)

    def __or__(self, other: object) -> u16:
        cdef uint16_t value = self.value | <uint16_t>other
        return u16(value)


cdef class u32:

    cdef uint32_t value

    def __init__(self, value: object) -> None:
        self.value = <uint32_t>value

    def __repr__(self) -> str:
        return f"<u32({self.value})>"

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __lt__(self, other: object) -> bool:
        return self.value < other

    def __le__(self, other: object) -> bool:
        return self.value <= other

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __gt__(self, other: object) -> bool:
        return self.value > other

    def __ge__(self, other: object) -> bool:
        return self.value >= other

    def __hash__(self) -> int:
        return self.value

    def __add__(self, other: object) -> u32:
        cdef uint32_t value = self.value + <uint32_t>other
        return u32(value)

    def __sub__(self, other: object) -> u32:
        cdef uint32_t value = self.value - <uint32_t>other
        return u32(value)

    def __mul__(self, other: object) -> u32:
        cdef uint32_t value = self.value * <uint32_t>other
        return u32(value)

    def __mod__(self, other: object) -> u32:
        cdef uint32_t value = self.value % <uint32_t>other
        return u32(value)

    def __floordiv__(self, other: object) -> u32:
        cdef uint32_t value = self.value // <uint32_t>other
        return u32(value)

    def __truediv__(self, other: object) -> u32:
        cdef uint32_t value = self.value // <uint32_t>other
        return u32(value)

    def __neg__(self) -> u32:
        cdef uint32_t value = -self.value
        return u32(value)

    def __abs__(self) -> u32:
        return self

    def __invert__(self) -> u32:
        cdef uint32_t value = ~self.value
        return u32(value)

    def __lshift__(self, other: object) -> u32:
        cdef uint32_t value = self.value << <uint32_t>other
        return u32(value)

    def __rshift__(self, other: object) -> u32:
        cdef uint32_t value = self.value >> <uint32_t>other
        return u32(value)

    def __and__(self, other: object) -> u32:
        cdef uint32_t value = self.value & <uint32_t>other
        return u32(value)

    def __xor__(self, other: object) -> u32:
        cdef uint32_t value = self.value ^ <uint32_t>other
        return u32(value)

    def __or__(self, other: object) -> u32:
        cdef uint32_t value = self.value | <uint32_t>other
        return u32(value)


cdef class u64:

    cdef uint64_t value

    def __init__(self, value: object) -> None:
        self.value = <uint64_t>value

    def __repr__(self) -> str:
        return f"<u64({self.value})>"

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __lt__(self, other: object) -> bool:
        return self.value < other

    def __le__(self, other: object) -> bool:
        return self.value <= other

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __gt__(self, other: object) -> bool:
        return self.value > other

    def __ge__(self, other: object) -> bool:
        return self.value >= other

    def __hash__(self) -> int:
        return self.value

    def __add__(self, other: object) -> u64:
        cdef uint64_t value = self.value + <uint64_t>other
        return u64(value)

    def __sub__(self, other: object) -> u64:
        cdef uint64_t value = self.value - <uint64_t>other
        return u64(value)

    def __mul__(self, other: object) -> u64:
        cdef uint64_t value = self.value * <uint64_t>other
        return u64(value)

    def __mod__(self, other: object) -> u64:
        cdef uint64_t value = self.value % <uint64_t>other
        return u64(value)

    def __floordiv__(self, other: object) -> u64:
        cdef uint64_t value = self.value // <uint64_t>other
        return u64(value)

    def __truediv__(self, other: object) -> u64:
        cdef uint64_t value = self.value // <uint64_t>other
        return u64(value)

    def __neg__(self) -> u64:
        cdef uint64_t value = -self.value
        return u64(value)

    def __abs__(self) -> u64:
        return self

    def __invert__(self) -> u64:
        cdef uint64_t value = ~self.value
        return u64(value)

    def __lshift__(self, other: object) -> u64:
        cdef uint64_t value = self.value << <uint64_t>other
        return u64(value)

    def __rshift__(self, other: object) -> u64:
        cdef uint64_t value = self.value >> <uint64_t>other
        return u64(value)

    def __and__(self, other: object) -> u64:
        cdef uint64_t value = self.value & <uint64_t>other
        return u64(value)

    def __xor__(self, other: object) -> u64:
        cdef uint64_t value = self.value ^ <uint64_t>other
        return u64(value)

    def __or__(self, other: object) -> u64:
        cdef uint64_t value = self.value | <uint64_t>other
        return u64(value)


cdef class i8:

    cdef int8_t value

    def __init__(self, value: object) -> None:
        self.value = <int8_t>value

    def __repr__(self) -> str:
        return f"<i8({self.value})>"

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __lt__(self, other: object) -> bool:
        return self.value < other

    def __le__(self, other: object) -> bool:
        return self.value <= other

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __gt__(self, other: object) -> bool:
        return self.value > other

    def __ge__(self, other: object) -> bool:
        return self.value >= other

    def __hash__(self) -> int:
        return self.value

    def __add__(self, other: object) -> i8:
        cdef int8_t value = self.value + <int8_t>other
        return i8(value)

    def __sub__(self, other: object) -> i8:
        cdef int8_t value = self.value - <int8_t>other
        return i8(value)

    def __mul__(self, other: object) -> i8:
        cdef int8_t value = self.value * <int8_t>other
        return i8(value)

    def __mod__(self, other: object) -> i8:
        cdef int8_t value = self.value % <int8_t>other
        return i8(value)

    def __floordiv__(self, other: object) -> i8:
        cdef int8_t value = self.value // <int8_t>other
        return i8(value)

    def __truediv__(self, other: object) -> i8:
        cdef int8_t value = self.value // <int8_t>other
        return i8(value)

    def __neg__(self) -> i8:
        cdef int8_t value = -self.value
        return i8(value)

    def __abs__(self) -> i8:
        if self.value >= 0:
            return self
        cdef int8_t value = -self.value
        return i8(value)

    def __invert__(self) -> i8:
        cdef int8_t value = ~self.value
        return i8(value)

    def __lshift__(self, other: object) -> i8:
        cdef int8_t value = self.value << <int8_t>other
        return i8(value)

    def __rshift__(self, other: object) -> i8:
        cdef int8_t value = self.value >> <int8_t>other
        return i8(value)

    def __and__(self, other: object) -> i8:
        cdef int8_t value = self.value & <int8_t>other
        return i8(value)

    def __xor__(self, other: object) -> i8:
        cdef int8_t value = self.value ^ <int8_t>other
        return i8(value)

    def __or__(self, other: object) -> i8:
        cdef int8_t value = self.value | <int8_t>other
        return i8(value)


cdef class i16:

    cdef int16_t value

    def __init__(self, value: object) -> None:
        self.value = <int16_t>value

    def __repr__(self) -> str:
        return f"<i16({self.value})>"

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __lt__(self, other: object) -> bool:
        return self.value < other

    def __le__(self, other: object) -> bool:
        return self.value <= other

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __gt__(self, other: object) -> bool:
        return self.value > other

    def __ge__(self, other: object) -> bool:
        return self.value >= other

    def __hash__(self) -> int:
        return self.value

    def __add__(self, other: object) -> i16:
        cdef int16_t value = self.value + <int16_t>other
        return i16(value)

    def __sub__(self, other: object) -> i16:
        cdef int16_t value = self.value - <int16_t>other
        return i16(value)

    def __mul__(self, other: object) -> i16:
        cdef int16_t value = self.value * <int16_t>other
        return i16(value)

    def __mod__(self, other: object) -> i16:
        cdef int16_t value = self.value % <int16_t>other
        return i16(value)

    def __floordiv__(self, other: object) -> i16:
        cdef int16_t value = self.value // other
        return i16(value)

    def __truediv__(self, other: object) -> i16:
        cdef int16_t value = self.value // other
        return i16(value)

    def __neg__(self) -> i16:
        cdef int16_t value = -self.value
        return i16(value)

    def __abs__(self) -> i16:
        if self.value >= 0:
            return self
        cdef int16_t value = -self.value
        return i16(value)

    def __invert__(self) -> i16:
        cdef int16_t value = ~self.value
        return i16(value)

    def __lshift__(self, other: object) -> i16:
        cdef int16_t value = self.value << <int16_t>other
        return i16(value)

    def __rshift__(self, other: object) -> i16:
        cdef int16_t value = self.value >> <int16_t>other
        return i16(value)

    def __and__(self, other: object) -> i16:
        cdef int16_t value = self.value & <int16_t>other
        return i16(value)

    def __xor__(self, other: object) -> i16:
        cdef int16_t value = self.value ^ <int16_t>other
        return i16(value)

    def __or__(self, other: object) -> i16:
        cdef int16_t value = self.value | <int16_t>other
        return i16(value)


cdef class i32:

    cdef int32_t value

    def __init__(self, value: object) -> None:
        self.value = <int32_t>value

    def __repr__(self) -> str:
        return f"<i32({self.value})>"

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __lt__(self, other: object) -> bool:
        return self.value < other

    def __le__(self, other: object) -> bool:
        return self.value <= other

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __gt__(self, other: object) -> bool:
        return self.value > other

    def __ge__(self, other: object) -> bool:
        return self.value >= other

    def __hash__(self) -> int:
        return self.value

    def __add__(self, other: object) -> i32:
        cdef int32_t value = self.value + <int32_t>other
        return i32(value)

    def __sub__(self, other: object) -> i32:
        cdef int32_t value = self.value - <int32_t>other
        return i32(value)

    def __mul__(self, other: object) -> i32:
        cdef int32_t value = self.value * <int32_t>other
        return i32(value)

    def __mod__(self, other: object) -> i32:
        cdef int32_t value = self.value % <int32_t>other
        return i32(value)

    def __floordiv__(self, other: object) -> i32:
        cdef int32_t value = self.value // <int32_t>other
        return i32(value)

    def __truediv__(self, other: object) -> i32:
        cdef int32_t value = self.value // <int32_t>other
        return i32(value)

    def __neg__(self) -> i32:
        cdef int32_t value = -self.value
        return i32(value)

    def __abs__(self) -> i32:
        if self.value >= 0:
            return self
        cdef int32_t value = -self.value
        return i32(value)

    def __invert__(self) -> i32:
        cdef int32_t value = ~self.value
        return i32(value)

    def __lshift__(self, other: object) -> i32:
        cdef int32_t value = self.value << <int32_t>other
        return i32(value)

    def __rshift__(self, other: object) -> i32:
        cdef int32_t value = self.value >> <int32_t>other
        return i32(value)

    def __and__(self, other: object) -> i32:
        cdef int32_t value = self.value & <int32_t>other
        return i32(value)

    def __xor__(self, other: object) -> i32:
        cdef int32_t value = self.value ^ <int32_t>other
        return i32(value)

    def __or__(self, other: object) -> i32:
        cdef int32_t value = self.value | <int32_t>other
        return i32(value)


cdef class i64:

    cdef int64_t value

    def __init__(self, value: object) -> None:
        self.value = <int64_t>value

    def __repr__(self) -> str:
        return f"<i64({self.value})>"

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __lt__(self, other: object) -> bool:
        return self.value < other

    def __le__(self, other: object) -> bool:
        return self.value <= other

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __gt__(self, other: object) -> bool:
        return self.value > other

    def __ge__(self, other: object) -> bool:
        return self.value >= other

    def __hash__(self) -> int:
        return self.value

    def __add__(self, other: object) -> i64:
        cdef int64_t value = self.value + <int64_t>other
        return i64(value)

    def __sub__(self, other: object) -> i64:
        cdef int64_t value = self.value - <int64_t>other
        return i64(value)

    def __mul__(self, other: object) -> i64:
        cdef int64_t value = self.value * <int64_t>other
        return i64(value)

    def __mod__(self, other: object) -> i64:
        cdef int64_t value = self.value % <int64_t>other
        return i64(value)

    def __floordiv__(self, other: object) -> i64:
        cdef int64_t value = self.value // <int64_t>other
        return i64(value)

    def __truediv__(self, other: object) -> i64:
        cdef int64_t value = self.value // <int64_t>other
        return i64(value)

    def __neg__(self) -> i64:
        cdef int64_t value = -self.value
        return i64(value)

    def __abs__(self) -> i64:
        if self.value >= 0:
            return self
        cdef int64_t value = -self.value
        return i64(value)

    def __invert__(self) -> i64:
        cdef int64_t value = ~self.value
        return i64(value)

    def __lshift__(self, other: object) -> i64:
        cdef int64_t value = self.value << <int64_t>other
        return i64(value)

    def __rshift__(self, other: object) -> i64:
        cdef int64_t value = self.value >> <int64_t>other
        return i64(value)

    def __and__(self, other: object) -> i64:
        cdef int64_t value = self.value & <int64_t>other
        return i64(value)

    def __xor__(self, other: object) -> i64:
        cdef int64_t value = self.value ^ <int64_t>other
        return i64(value)

    def __or__(self, other: object) -> i64:
        cdef int64_t value = self.value | <int64_t>other
        return i64(value)


cdef class f32:

    cdef float value

    def __init__(self, value: object) -> None:
        self.value = <float>value

    def __repr__(self) -> str:
        return f"<f32({self.value})>"

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __lt__(self, other: object) -> bool:
        return self.value < other

    def __le__(self, other: object) -> bool:
        return self.value <= other

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __gt__(self, other: object) -> bool:
        return self.value > other

    def __ge__(self, other: object) -> bool:
        return self.value >= other

    def __hash__(self) -> int:
        return hash(self.value)

    def __add__(self, other: object) -> f32:
        # This line will convert any 32-bit float to a double first, and then back to a 32-bit float. This may be
        # slower, but is ultimately is fine to do, as doubles fully encapsulate the range of possible floats. The
        # arithmetic is still being done on 32-bit floats in this case.
        cdef float value = self.value + <float>other
        return f32(value)

    def __sub__(self, other: object) -> f32:
        cdef float value = self.value - <float>other
        return f32(value)

    def __mul__(self, other: object) -> f32:
        cdef float value = self.value * <float>other
        return f32(value)

    def __mod__(self, other: object) -> f32:
        cdef float value = self.value % <float>other
        return f32(value)

    def __floordiv__(self, other: object) -> f32:
        cdef float value = self.value // <float>other
        return f32(value)

    def __truediv__(self, other: object) -> f32:
        cdef float value = self.value / <float>other
        return f32(value)

    def __neg__(self) -> f32:
        cdef float value = -self.value
        return f32(value)

    def __abs__(self) -> f32:
        if self.value >= 0:
            return self
        cdef float value = -self.value
        return f32(value)

    def __trunc__(self) -> f32:
        cdef float value = cmath.truncf(self.value)
        return f32(value)

    def __floor__(self) -> f32:
        cdef float value = cmath.floorf(self.value)
        return f32(value)

    def __ceil__(self) -> f32:
        cdef float value = cmath.ceilf(self.value)
        return f32(value)

    def __round__(self, places: int | None = None) -> f32:
        cdef float value = cmath.roundf(self.value)
        return f32(value)


cdef class f64:
    """
    A 64-bit floating point integer.
    """

    cdef double value

    def __init__(self, value: float) -> None:
        self.value = <double>value

    def __repr__(self) -> str:
        return f"<f64({self.value})>"

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __lt__(self, other: object) -> bool:
        return self.value < other

    def __le__(self, other: object) -> bool:
        return self.value <= other

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __gt__(self, other: object) -> bool:
        return self.value > other

    def __ge__(self, other: object) -> bool:
        return self.value >= other

    def __hash__(self) -> int:
        return hash(self.value)

    def __add__(self, other: object) -> f64:
        cdef float value = self.value + <float>other
        return f64(value)

    def __sub__(self, other: object) -> f64:
        cdef double value = self.value - <double>other
        return f64(value)

    def __mul__(self, other: object) -> f64:
        cdef double value = self.value * <double>other
        return f64(value)

    def __mod__(self, other: object) -> f64:
        cdef double value = self.value % <double>other
        return f64(value)

    def __floordiv__(self, other: object) -> f64:
        cdef double value = self.value // <double>other
        return f64(value)

    def __truediv__(self, other: object) -> f64:
        cdef double value = self.value / <double>other
        return f64(value)

    def __neg__(self) -> f64:
        cdef double value = -self.value
        return f64(value)

    def __abs__(self) -> f64:
        if self.value >= 0:
            return self
        cdef double value = -self.value
        return f64(value)

    def __trunc__(self) -> f64:
        cdef double value = cmath.trunc(self.value)
        return f64(value)

    def __floor__(self) -> f64:
        cdef double value = cmath.floor(self.value)
        return f64(value)

    def __ceil__(self) -> f64:
        cdef double value = cmath.ceil(self.value)
        return f64(value)

    def __round__(self, places: int | None = None) -> f64:
        cdef double value = cmath.round(self.value)
        return f64(value)


cpdef bint isnan(object value):
    """
    Checks if a value is NaN.
    """

    if isinstance(value, f32):
        return cmath.isnan((<f32>value).value)
    elif isinstance(value, f64):
        return cmath.isnan((<f64>value).value)
    elif isinstance(value, float):
        return math.isnan(value)
    return False  # TODO: Type error?


cpdef u8 unpack_u8(bytes data):
    if not data:
        raise ValueError("1 byte needed to unpack u8")
    return u8(data[0])


cpdef bytes pack_u8(u8 value):
    return <bytes>value.value


cpdef u16 _be_unpack_u16(bytes data):
    if len(data) < 2:
        raise ValueError("2 bytes needed to unpack u16")
    cdef uint8_t *cdata = <uint8_t*>data
    return u16((<uint16_t*>cdata)[0])


cpdef u16 _le_unpack_u16(bytes data):
    if len(data) < 2:
        raise ValueError("2 bytes needed to unpack u16")
    cdef uint8_t *cdata = <uint8_t*>data
    cdef uint8_t[2] swap = [cdata[1], cdata[0]]
    return u16((<uint16_t*>swap)[0])


cpdef bytes _be_pack_u16(u16 value):
    cdef uint8_t[2] data = <uint8_t*>&value.value
    return <bytes>data[:2]


cpdef bytes _le_pack_u16(u16 value):
    cdef uint8_t[2] data = <uint8_t*>&value.value
    cdef uint8_t[2] swap = [data[1], data[0]]
    return <bytes>swap[:2]


cpdef u32 _be_unpack_u32(bytes data):
    if len(data) < 4:
        raise ValueError("4 bytes needed to unpack u32")
    cdef uint8_t *cdata = <uint8_t*>data
    return u32((<uint32_t*>cdata)[0])


cpdef u32 _le_unpack_u32(bytes data):
    if len(data) < 4:
        raise ValueError("4 bytes needed to unpack u32")
    cdef uint8_t *cdata = <uint8_t*>data
    cdef uint8_t[4] swap = [cdata[3], cdata[2], cdata[1], cdata[0]]
    return u32((<uint32_t*>swap)[0])


cpdef bytes _be_pack_u32(u32 value):
    cdef uint8_t[4] data = <uint8_t*>&value.value
    return <bytes>data[:4]


cdef bytes _le_pack_u32(u32 value):
    cdef uint8_t[4] data = <uint8_t*>&value.value
    cdef uint8_t[4] swap = [data[3], data[2], data[1], data[0]]
    return <bytes>data[:4]


cpdef u64 _be_unpack_u64(bytes data):
    if len(data) < 8:
        raise ValueError("8 bytes needed to unpack u64")
    cdef uint8_t *cdata = <uint8_t*>data
    return u64((<uint64_t*>cdata)[0])


cpdef u64 _le_unpack_u64(bytes data):
    if len(data) < 8:
        raise ValueError("8 bytes needed to unpack u64")
    cdef uint8_t *cdata = <uint8_t*>data
    cdef uint8_t[8] swap = [cdata[7], cdata[6], cdata[5], cdata[4], cdata[3], cdata[2], cdata[1], cdata[0]]
    return u64((<uint64_t*>swap)[0])


cpdef _be_pack_u64(u64 value):
    cdef uint8_t[8] data = <uint8_t*>&value.value
    return <bytes>data[:8]


cpdef _le_pack_u64(u64 value):
    cdef uint8_t[8] data = <uint8_t*>&value.value
    cdef uint8_t[8] swap = [data[7], data[6], data[5], data[4], data[3], data[2], data[1], data[0]]
    return <bytes>data[:8]


cpdef i8 unpack_i8(bytes data):
    if not data:
        raise ValueError("1 byte needed to unpack i8")
    cdef int8_t *cdata = <int8_t*>data
    return i8(cdata[0])


cpdef bytes pack_i8(i8 value):
    return <bytes>(<uint8_t*>&value.value)[0]  # Yeah, it is what it is.


cpdef i16 _be_unpack_i16(bytes data):
    if len(data) < 2:
        raise ValueError("2 bytes needed to unpack i8")
    cdef uint8_t *cdata = <uint8_t*>data
    return i16((<int16_t*>cdata)[0])


cpdef i16 _le_unpack_i16(bytes data):
    if len(data) < 2:
        raise ValueError("2 bytes needed to unpack i8")
    cdef uint8_t *cdata = <uint8_t*>data
    cdef uint8_t[2] swap = [cdata[1], cdata[0]]
    return i16((<int16_t*>swap)[0])


cpdef bytes _be_pack_i16(i16 value):
    cdef uint8_t[2] data = <uint8_t*>&value.value
    return <bytes>data[:2]


cdef bytes _le_pack_i16(i16 value):
    cdef uint8_t[2] data = <uint8_t*>&value.value
    cdef uint8_t[2] swap = [data[1], data[0]]
    return <bytes>swap[:2]


cpdef i32 _be_unpack_i32(bytes data):
    if len(data) < 4:
        raise ValueError("4 bytes needed to unpack i32")
    cdef uint8_t *cdata = <uint8_t*>data
    return i32((<int32_t*>cdata)[0])


cpdef i32 _le_unpack_i32(bytes data):
    if len(data) < 4:
        raise ValueError("4 bytes needed to unpack i32")
    cdef uint8_t *cdata = <uint8_t*>data
    cdef uint8_t[4] swap = [cdata[3], cdata[2], cdata[1], cdata[0]]
    return i32((<int32_t*>swap)[0])


cpdef bytes _be_pack_i32(i32 value):
    cdef uint8_t[4] data = <uint8_t*>&value.value
    return <bytes>data[:4]


cpdef bytes _le_pack_i32(i32 value):
    cdef uint8_t[4] data = <uint8_t*>&value.value
    cdef uint8_t[4] swap = [data[3], data[2], data[1], data[0]]
    return <bytes>swap[:4]


cpdef i64 _be_unpack_i64(bytes data):
    if len(data) < 8:
        raise ValueError("8 bytes needed to unpack i64")
    cdef uint8_t *cdata = <uint8_t*>data
    return i64((<int64_t*>cdata)[0])


cpdef i64 _le_unpack_i64(bytes data):
    if len(data) < 8:
        raise ValueError("8 bytes needed to unpack i64")
    cdef uint8_t *cdata = <uint8_t*>data
    cdef uint8_t[8] swap = [cdata[7], cdata[6], cdata[5], cdata[4], cdata[3], cdata[2], cdata[1], cdata[0]]
    return i64((<int64_t*>swap)[0])


cpdef bytes _be_pack_i64(i64 value):
    cdef uint8_t[8] data = <uint8_t*>&value.value
    return <bytes>data[:8]


cpdef bytes _le_pack_i64(i64 value):
    cdef uint8_t[8] data = <uint8_t*>&value.value
    cdef uint8_t[8] swap = [data[7], data[6], data[5], data[4], data[3], data[2], data[1], data[0]]
    return <bytes>swap[:8]


cpdef f32 _be_unpack_f32(bytes data):
    if len(data) < 4:
        raise ValueError("4 bytes needed to unpack f32")
    cdef uint8_t *cdata = <uint8_t*>data
    return f32((<float*>cdata)[0])


cpdef f32 _le_unpack_f32(bytes data):
    if len(data) < 4:
        raise ValueError("4 bytes needed to unpack f32")
    cdef uint8_t *cdata = <uint8_t*>data
    cdef uint8_t[4] swap = [cdata[3], cdata[2], cdata[1], cdata[0]]
    return f32((<float*>swap)[0])



cpdef bytes _be_pack_f32(f32 value):
    cdef uint8_t[4] data = <uint8_t*>&value.value
    return <bytes>data[:4]


cpdef bytes _le_pack_f32(f32 value):
    cdef uint8_t[4] data = <uint8_t*>&value.value
    cdef uint8_t[4] swap = [data[3], data[2], data[1], data[0]]
    return <bytes>swap[:4]


cpdef f64 _be_unpack_f64(bytes data):
    if len(data) < 8:
        raise ValueError("8 bytes needed to unpack f64")
    cdef uint8_t *cdata = <uint8_t*>data
    return f64((<double*>cdata)[0])


cpdef f64 _le_unpack_f64(bytes data):
    if len(data) < 8:
        raise ValueError("8 bytes needed to unpack f64")
    cdef uint8_t *cdata = <uint8_t*>data
    cdef uint8_t *swap = [cdata[7], cdata[6], cdata[5], cdata[4], cdata[3], cdata[2], cdata[1], cdata[0]]
    return f64((<double*>swap)[0])


cpdef bytes _be_pack_f64(f64 value):
    cdef uint8_t[8] data = <uint8_t*>&value.value
    return <bytes>data[:8]


cpdef bytes _le_pack_f64(f64 value):
    cdef uint8_t[8] data = <uint8_t*>&value.value
    cdef uint8_t[8] swap = [data[7], data[6], data[5], data[4], data[3], data[2], data[1], data[0]]
    return <bytes>swap[:8]


if sys.byteorder == "big":
    unpack_u16 = _be_unpack_u16
    pack_u16   = _be_pack_u16
    unpack_u32 = _be_unpack_u32
    pack_u32   = _be_pack_u32
    unpack_u64 = _be_unpack_u64
    pack_u64   = _be_pack_u64
    unpack_i16 = _be_unpack_i16
    pack_i16   = _be_pack_i16
    unpack_i32 = _be_unpack_i32
    pack_i32   = _be_pack_i32
    unpack_i64 = _be_unpack_i64
    pack_i64   = _be_pack_i64
    unpack_f32 = _be_unpack_f32
    pack_f32   = _be_pack_f32
    unpack_f64 = _be_unpack_f64
    pack_f64   = _be_pack_f64
elif sys.byteorder == "little":
    unpack_u16 = _le_unpack_u16
    pack_u16   = _le_pack_u16
    unpack_u32 = _le_unpack_u32
    pack_u32   = _le_pack_u32
    unpack_u64 = _le_unpack_u64
    pack_u64   = _le_pack_u64
    unpack_i16 = _le_unpack_i16
    pack_i16   = _le_pack_i16
    unpack_i32 = _le_unpack_i32
    pack_i32   = _le_pack_i32
    unpack_i64 = _le_unpack_i64
    pack_i64   = _le_pack_i64
    unpack_f32 = _le_unpack_f32
    pack_f32   = _le_pack_f32
    unpack_f64 = _le_unpack_f64
    pack_f64   = _le_pack_f64
else:
    raise ValueError(f"unknown byteorder {sys.byteorder!r}")

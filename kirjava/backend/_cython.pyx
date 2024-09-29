# cython: language=c
# cython: language_level=3

__all__ = (
    "u8", "u16", "u32", "u64",
    "i8", "i16", "i32", "i64",
    "f32", "f64",
    "isnan",
)

"""
A Cython backend implementation.
"""

# TODO: Complete this.

import math

from libc.math cimport isnan as c_isnan
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


cdef class u16:
    cdef uint16_t value


cdef class u32:
    cdef uint32_t value


cdef class u64:
    cdef uint64_t value


cdef class i8:
    cdef int8_t value


cdef class i16:
    cdef int16_t value


cdef class i32:
    cdef int32_t value


cdef class i64:
    cdef int64_t value


cdef class f32:
    cdef float value


cdef class f64:
    """
    A 64-bit floating point integer.
    """

    cdef double value

    def __init__(self, value: float) -> None:
        self.value = <double>value

    def __abs__(self) -> f64:
        if self.value < 0:
            return f64(-self.value)
        return self

    def __add__(self, other: object) -> f64:
        if isinstance(other, f64):
            return f64(self.value + (<f64>other).value)
        elif isinstance(other, f32):
            return f64(self.value + (<f32>other).value)
        return f64(self.value + float(other))

    def __sub__(self, other: object) -> f64:
        if isinstance(other, f64):
            return f64(self.value - (<f64>other).value)
        elif isinstance(other, f32):
            return f64(self.value - (<f32>other).value)
        return f64(self.value - float(other))

    def __mul__(self, other: object) -> f64:
        if isinstance(other, f64):
            return f64(self.value * (<f64>other).value)
        elif isinstance(other, f32):
            return f64(self.value * (<f32>other).value)
        return f64(self.value * float(other))

    def __truediv__(self, other: object) -> f64:
        if isinstance(other, f64):
            return f64(self.value / (<f64>other).value)
        elif isinstance(other, f32):
            return f64(self.value / (<f32>other).value)
        return f64(self.value / float(other))

    def __floordiv__(self, other: object) -> f64:
        if isinstance(other, f64):
            return f64(self.value // (<f64>other).value)
        elif isinstance(other, f32):
            return f64(self.value // (<f32>other).value)
        return f64(self.value // float(other))


cpdef bint isnan(object value):
    """
    Checks if a value is NaN.
    """

    if isinstance(value, f32):
        return c_isnan((<f32>value).value)
    elif isinstance(value, f64):
        return c_isnan((<f64>value).value)
    elif isinstance(value, float):
        return math.isnan(value)
    return False  # TODO: Type error?

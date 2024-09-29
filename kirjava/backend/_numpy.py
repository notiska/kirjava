#!/usr/bin/env python3

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
A numpy backend implementation.
"""

import numpy as np


u8 = np.uint8
u16 = np.uint16
u32 = np.uint32
u64 = np.uint64

i8 = np.int8
i16 = np.int16
i32 = np.int32
i64 = np.int64

f32 = np.float32
f64 = np.float64

isnan = np.isnan

# Serialisation.
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


def unpack_u8(data: bytes) -> u8:
    return np.frombuffer(data, dtype=_u8)[0]


def pack_u8(value: u8) -> bytes:
    return np.array(value, dtype=_u8).tobytes()


def unpack_u16(data: bytes) -> u16:
    return np.frombuffer(data, dtype=_u16)[0]


def pack_u16(value: u16) -> bytes:
    return np.array(value, dtype=_u16).tobytes()


def unpack_u32(data: bytes) -> u32:
    return np.frombuffer(data, dtype=_u32)[0]


def pack_u32(value: u32) -> bytes:
    return np.array(value, dtype=_u32).tobytes()


def unpack_u64(data: bytes) -> u64:
    return np.frombuffer(data, dtype=_u64)[0]


def pack_u64(value: u64) -> bytes:
    return np.array(value, dtype=_u64).tobytes()


def unpack_i8(data: bytes) -> i8:
    return np.frombuffer(data, dtype=_i8)[0]


def pack_i8(value: i8) -> bytes:
    return np.array(value, dtype=_i8).tobytes()


def unpack_i16(data: bytes) -> i16:
    return np.frombuffer(data, dtype=_i16)[0]


def pack_i16(value: i16) -> bytes:
    return np.array(value, dtype=_i16).tobytes()


def unpack_i32(data: bytes) -> i32:
    return np.frombuffer(data, dtype=_i32)[0]


def pack_i32(value: i32) -> bytes:
    return np.array(value, dtype=_i32).tobytes()


def unpack_i64(data: bytes) -> i64:
    return np.frombuffer(data, dtype=_i64)[0]


def pack_i64(value: i64) -> bytes:
    return np.array(value, dtype=_i64).tobytes()


def unpack_f32(data: bytes) -> f32:
    return np.frombuffer(data, dtype=_f32)[0]


def pack_f32(value: f32) -> bytes:
    return np.array(value, dtype=_f32).tobytes()


def unpack_f64(data: bytes) -> f64:
    return np.frombuffer(data, dtype=_f64)[0]


def pack_f64(value: f64) -> bytes:
    return np.array(value, dtype=_f64).tobytes()
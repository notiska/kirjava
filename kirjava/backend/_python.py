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

import math
import struct

# TODO: Range limitations.
u8:   type["u8"] = type("u8", (int,), {})  # type: ignore[no-redef]
u16: type["u16"] = type("u16", (int,), {})  # type: ignore[no-redef]
u32: type["u32"] = type("u32", (int,), {})  # type: ignore[no-redef]
u64: type["u64"] = type("u64", (int,), {})  # type: ignore[no-redef]

i8:   type["i8"] = type("i8", (int,), {})  # type: ignore[no-redef]
i16: type["i16"] = type("i16", (int,), {})  # type: ignore[no-redef]
i32: type["i32"] = type("i32", (int,), {})  # type: ignore[no-redef]
i64: type["i64"] = type("i64", (int,), {})  # type: ignore[no-redef]

f32: type["f32"] = type("f32", (float,), {})  # type: ignore[no-redef]
f64: type["f64"] = type("f64", (float,), {})  # type: ignore[no-redef]

isnan = math.isnan

_struct_u8  = struct.Struct(">B")
unpack_u8   = _struct_u8.unpack
pack_u8     = _struct_u8.pack
_struct_u16 = struct.Struct(">H")
unpack_u16  = _struct_u16.unpack
pack_u16    = _struct_u16.pack
_struct_u32 = struct.Struct(">I")
unpack_u32  = _struct_u32.unpack
pack_u32    = _struct_u32.pack
_struct_u64 = struct.Struct(">Q")
unpack_u64  = _struct_u64.unpack
pack_u64    = _struct_u64.pack

_struct_i8  = struct.Struct(">b")
unpack_i8   = _struct_i8.unpack
pack_i8     = _struct_i8.pack
_struct_i16 = struct.Struct(">h")
unpack_i16  = _struct_i16.unpack
pack_i16    = _struct_i16.pack
_struct_i32 = struct.Struct(">i")
unpack_i32  = _struct_i32.unpack
pack_i32    = _struct_i32.pack
_struct_i64 = struct.Struct(">q")
unpack_i64  = _struct_i64.unpack
pack_i64    = _struct_i64.pack

_struct_f32 = struct.Struct(">f")
unpack_f32  = _struct_f32.unpack
pack_f32    = _struct_f32.pack
_struct_f64 = struct.Struct(">d")
unpack_f64  = _struct_f64.unpack
pack_f64    = _struct_f64.pack

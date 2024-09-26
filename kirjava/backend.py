#!/usr/bin/env python3

__all__ = (
    "u8", "u16", "u32", "u64",
    "i8", "i16", "i32", "i64",
    "f32", "f64",
    "isnan",
)

import logging
import math

logger = logging.getLogger("kirjava.backend")

try:
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

except ImportError:
    logger.debug("No numpy found for backend.")

    # TODO: Implement these.
    # TODO: Fast serialisation and deserialisation.

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

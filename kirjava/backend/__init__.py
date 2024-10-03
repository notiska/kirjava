#!/usr/bin/env python3

__all__ = (
    "USING_CYTHON", "USING_NUMPY",
    "u8", "u16", "u32", "u64",
    "i8", "i16", "i32", "i64",
    "f32", "f64",
    "isnan",
    "unpack_u8", "pack_u8", "unpack_u16", "pack_u16", "unpack_u32", "pack_u32", "unpack_u64", "pack_u64",
    "unpack_i8", "pack_i8", "unpack_i16", "pack_i16", "unpack_i32", "pack_i32", "unpack_i64", "pack_i64",
    "unpack_f32", "pack_f32", "unpack_f64", "pack_f64",
)

"""
The "backend" for the library.
Provides various types and functions for the library to use.
"""

import logging

logger = logging.getLogger("kirjava.backend")

USING_CYTHON = False
USING_NUMPY  = False

try:
    # import pyximport
    # pyximport.install()
    # FIXME: Add typing stubs.
    from ._cython import *  # type: ignore[import-untyped]
    USING_CYTHON = True
except Exception as error:
    logger.debug("Cython backend not available: %s", error)
    logger.debug(repr(error), exc_info=True)

if not USING_CYTHON:
    try:
        from ._numpy import *
        USING_NUMPY = True
    except Exception as error:
        logger.debug("numpy backend not available: %s", error)
        logger.debug(repr(error), exc_info=True)

# if not imported:
#     try:
#         from ._ctypes import *
#         imported = True
#     except Exception as error:
#         logger.debug("ctypes backend not available: %s", error)
#         logger.debug(repr(error), exc_info=True)
#         imported = False

if not USING_CYTHON and not USING_NUMPY:
    # TODO: Some sort of fallback that just handles bytes and not any actual arithmetic functionality where necessary.
    raise ImportError("no backend available")

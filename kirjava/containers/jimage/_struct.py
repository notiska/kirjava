#!/usr/bin/env python3

__all__ = (
    "unpack_HH", "pack_HH",
    "unpack_IIIII", "pack_IIIII",
)

import struct

_struct_HH = struct.Struct("<HH")
unpack_HH  = _struct_HH.unpack
pack_HH    = _struct_HH.pack

_struct_IIIII = struct.Struct("<IIIII")
unpack_IIIII  = _struct_IIIII.unpack
pack_IIIII    = _struct_IIIII.pack

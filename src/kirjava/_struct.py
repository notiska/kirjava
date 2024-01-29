#!/usr/bin/env python3

__all__ = (
    "unpack_BH", "pack_BH", "unpack_BBH", "pack_BBH", "unpack_HHI", "pack_HHI",
    "unpack_HI", "pack_HI",
    "unpack_H", "pack_H", "unpack_HH", "pack_HH", "unpack_HHH", "pack_HHH",
    "unpack_HHHH", "pack_HHHH", "unpack_HHHHH", "pack_HHHHH",
    "unpack_i", "pack_i", "unpack_f", "pack_f", "unpack_q", "pack_q", "unpack_d", "pack_d",
)

"""
It isn't pretty, but it's fast.
"""

import struct

_BH = struct.Struct(">BH")
unpack_BH = _BH.unpack
pack_BH = _BH.pack
_BBH = struct.Struct(">BBH")
unpack_BBH = _BBH.unpack
pack_BBH = _BBH.pack
_HHI = struct.Struct(">HHI")
unpack_HHI = _HHI.unpack
pack_HHI = _HHI.pack

_HI = struct.Struct(">HI")
unpack_HI = _HI.unpack
pack_HI = _HI.pack

_H = struct.Struct(">H")
unpack_H = _H.unpack
pack_H = _H.pack
_HH = struct.Struct(">HH")
unpack_HH = _HH.unpack
pack_HH = _HH.pack
_HHH = struct.Struct(">HHH")
unpack_HHH = _HHH.unpack
pack_HHH = _HHH.pack
_HHHH = struct.Struct(">HHHH")
unpack_HHHH = _HHHH.unpack
pack_HHHH = _HHHH.pack
_HHHHH = struct.Struct(">HHHHH")
unpack_HHHHH = _HHHHH.unpack
pack_HHHHH = _HHHHH.pack

_i = struct.Struct(">i")
unpack_i = _i.unpack
pack_i = _i.pack
_f = struct.Struct(">f")
unpack_f = _f.unpack
pack_f = _f.pack
_q = struct.Struct(">q")
unpack_q = _q.unpack
pack_q = _q.pack
_d = struct.Struct(">d")
unpack_d = _d.unpack
pack_d = _d.pack

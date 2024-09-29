#!/usr/bin/env python3

__all__ = (
    "unpack_BH", "pack_BH", "unpack_HB", "pack_HB",
    "unpack_Bb", "pack_Bb", "unpack_Bh", "pack_Bh", "unpack_BBb", "pack_BBb",
    "unpack_Hh", "pack_Hh",
    "unpack_BBH", "pack_BBH", "unpack_BHB", "pack_BHB", "unpack_BHH", "pack_BHH", "unpack_HBB", "pack_HBB",
    "unpack_BHBB", "pack_BHBB",
    "unpack_BBHh", "pack_BBHh",
    "unpack_HI", "pack_HI", "unpack_HIH", "pack_HIH", "unpack_HHI", "pack_HHI",
    "unpack_h", "pack_h",
    "iter_unpack_H", "unpack_H", "pack_H", "unpack_HH", "pack_HH", "unpack_HHH", "pack_HHH",
    "unpack_HHHH", "pack_HHHH", "unpack_HHHHH", "pack_HHHHH",
    "unpack_I", "pack_I",
    "unpack_i", "pack_i", "unpack_Bi", "pack_Bi", "unpack_ii", "pack_ii", "unpack_iii", "pack_iii",
    # "unpack_f", "pack_f", "unpack_q", "pack_q", "unpack_d", "pack_d",
)

import struct

_struct_BH  = struct.Struct(">BH")
unpack_BH   = _struct_BH.unpack
pack_BH     = _struct_BH.pack
_struct_HB  = struct.Struct(">HB")
unpack_HB   = _struct_HB.unpack
pack_HB     = _struct_HB.pack

_struct_Bb  = struct.Struct(">Bb")
unpack_Bb   = _struct_Bb.unpack
pack_Bb     = _struct_Bb.pack
_struct_Bh  = struct.Struct(">Bh")
unpack_Bh   = _struct_Bh.unpack
pack_Bh     = _struct_Bh.pack
_struct_BBb = struct.Struct(">BBb")
unpack_BBb  = _struct_BBb.unpack
pack_BBb    = _struct_BBb.pack

_struct_Hh  = struct.Struct(">Hh")
unpack_Hh   = _struct_Hh.unpack
pack_Hh     = _struct_Hh.pack

_struct_BBH  = struct.Struct(">BBH")
unpack_BBH   = _struct_BBH.unpack
pack_BBH     = _struct_BBH.pack
_struct_BHB  = struct.Struct(">BHB")
unpack_BHB   = _struct_BHB.unpack
pack_BHB     = _struct_BHB.pack
_struct_BHH  = struct.Struct(">BHH")
unpack_BHH   = _struct_BHH.unpack
pack_BHH     = _struct_BHH.pack
_struct_HBB  = struct.Struct(">HBB")
unpack_HBB   = _struct_HBB.unpack
pack_HBB     = _struct_HBB.pack
_struct_BHBB = struct.Struct(">BHBB")
unpack_BHBB  = _struct_BHBB.unpack
pack_BHBB    = _struct_BHBB.pack

_struct_BBHh = struct.Struct(">BBHh")
unpack_BBHh  = _struct_BBHh.unpack
pack_BBHh    = _struct_BBHh.pack

_struct_HI  = struct.Struct(">HI")
unpack_HI   = _struct_HI.unpack
pack_HI     = _struct_HI.pack
_struct_HIH = struct.Struct(">HIH")
unpack_HIH  = _struct_HIH.unpack
pack_HIH    = _struct_HIH.pack
_struct_HHI = struct.Struct(">HHI")
unpack_HHI  = _struct_HHI.unpack
pack_HHI    = _struct_HHI.pack

_struct_h = struct.Struct(">h")
unpack_h  = _struct_h.unpack
pack_h    = _struct_h.pack

_struct_H     = struct.Struct(">H")
iter_unpack_H = _struct_H.iter_unpack
unpack_H      = _struct_H.unpack
pack_H        = _struct_H.pack
_struct_HH    = struct.Struct(">HH")
unpack_HH     = _struct_HH.unpack
pack_HH       = _struct_HH.pack
_struct_HHH   = struct.Struct(">HHH")
unpack_HHH    = _struct_HHH.unpack
pack_HHH      = _struct_HHH.pack
_struct_HHHH  = struct.Struct(">HHHH")
unpack_HHHH   = _struct_HHHH.unpack
pack_HHHH     = _struct_HHHH.pack
_struct_HHHHH = struct.Struct(">HHHHH")
unpack_HHHHH  = _struct_HHHHH.unpack
pack_HHHHH    = _struct_HHHHH.pack

_struct_I = struct.Struct(">I")
unpack_I  = _struct_I.unpack
pack_I    = _struct_I.pack

_struct_i   = struct.Struct(">i")
unpack_i    = _struct_i.unpack
pack_i      = _struct_i.pack
_struct_Bi  = struct.Struct(">Bi")
unpack_Bi   = _struct_Bi.unpack
pack_Bi     = _struct_Bi.pack
_struct_ii  = struct.Struct(">ii")
unpack_ii   = _struct_ii.unpack
pack_ii     = _struct_ii.pack
_struct_iii = struct.Struct(">iii")
unpack_iii  = _struct_iii.unpack
pack_iii    = _struct_iii.pack

# _struct_f = struct.Struct(">f")
# unpack_f  = _struct_f.unpack
# pack_f    = _struct_f.pack
# _struct_q = struct.Struct(">q")
# unpack_q  = _struct_q.unpack
# pack_q    = _struct_q.pack
# _struct_d = struct.Struct(">d")
# unpack_d  = _struct_d.unpack
# pack_d    = _struct_d.pack

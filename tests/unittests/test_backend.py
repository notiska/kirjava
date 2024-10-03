#!/usr/bin/env python3

import unittest

from kirjava.backend import *


class TestBackend(unittest.TestCase):

    def test_u8(self) -> None:
        self.assertEqual(u8(0), 0)
        self.assertEqual(u8(255), 255)

        self.assertTrue(u8(4) < 5)
        self.assertTrue(u8(4) <= 5)
        self.assertTrue(u8(5) <= 5)
        self.assertTrue(u8(5) == 5)
        self.assertTrue(u8(5) != 6)
        self.assertTrue(u8(5) >= 5)
        self.assertTrue(u8(5) >= 4)
        self.assertTrue(u8(5) > 4)

        with self.assertRaises(OverflowError):
            u8(256)
        with self.assertRaises(OverflowError):
            u8(-1)

        self.assertIsInstance(u8(5) + 1, u8)

        self.assertEqual(u8(255) + 1, 0)
        self.assertEqual(u8(0) - 1, 255)
        self.assertEqual(u8(128) * 2, 0)
        self.assertEqual(u8(255) * 2, 254)
        self.assertEqual(u8(15) % 4, 3)
        self.assertEqual(u8(15) // 2, 7)
        self.assertEqual(-u8(5), 251)
        self.assertEqual(~u8(5), 250)
        self.assertEqual(u8(255) << 1, 254)
        self.assertEqual(u8(1) >> 1, 0)
        self.assertEqual(u8(5) & 3, 1)
        self.assertEqual(u8(5) ^ 3, 6)
        self.assertEqual(u8(5) | 3, 7)

        if not USING_NUMPY:
            with self.assertRaises(ZeroDivisionError):
                u8(0) % 0
            with self.assertRaises(ZeroDivisionError):
                u8(0) / 0  # Numpy will implicitly cast to float, unfortunately.

            self.assertEqual(u8(15) / 2, 7)
            self.assertEqual(u8(255) << 65, 254)

        self.assertEqual(unpack_u8(b"\x00"), 0)
        self.assertEqual(unpack_u8(b"\xff"), 255)
        with self.assertRaises(ValueError):
            unpack_u8(b"")
        self.assertEqual(pack_u8(u8(0)), b"\x00")
        self.assertEqual(pack_u8(u8(255)), b"\xff")

    def test_u16(self) -> None:
        self.assertEqual(u16(0), 0)
        self.assertEqual(u16(65535), 65535)

        self.assertTrue(u16(4) < 5)
        self.assertTrue(u16(4) <= 5)
        self.assertTrue(u16(5) <= 5)
        self.assertTrue(u16(5) == 5)
        self.assertTrue(u16(5) != 6)
        self.assertTrue(u16(5) >= 5)
        self.assertTrue(u16(5) >= 4)
        self.assertTrue(u16(5) > 4)

        with self.assertRaises(OverflowError):
            u16(65536)
        with self.assertRaises(OverflowError):
            u16(-1)

        self.assertIsInstance(u16(5) + 1, u16)

        self.assertEqual(u16(65535) + 1, 0)
        self.assertEqual(u16(0) - 1, 65535)
        self.assertEqual(u16(32768) * 2, 0)
        self.assertEqual(u16(65535) * 2, 65534)
        self.assertEqual(u16(15) % 4, 3)
        self.assertEqual(u16(15) // 2, 7)
        self.assertEqual(-u16(5), 65531)
        self.assertEqual(~u16(5), 65530)
        self.assertEqual(u16(65535) << 1, 65534)
        self.assertEqual(u16(1) >> 1, 0)
        self.assertEqual(u16(5) & 3, 1)
        self.assertEqual(u16(5) ^ 3, 6)
        self.assertEqual(u16(5) | 3, 7)

        if not USING_NUMPY:
            with self.assertRaises(ZeroDivisionError):
                u16(0) % 0
            with self.assertRaises(ZeroDivisionError):
                u16(0) / 0

            self.assertEqual(u16(15) / 2, 7)
            self.assertEqual(u16(65535) << 65, 65534)

        self.assertEqual(unpack_u16(b"\x00\x00"), 0)
        self.assertEqual(unpack_u16(b"\x80\x00"), 32768)
        self.assertEqual(unpack_u16(b"\xff\xff"), 65535)
        with self.assertRaises(ValueError):
            unpack_u16(b"")
        with self.assertRaises(ValueError):
            unpack_u16(b"\x00")
        self.assertEqual(pack_u16(u16(0)), b"\x00\x00")
        self.assertEqual(pack_u16(u16(65535)), b"\xff\xff")

    def test_u32(self) -> None:
        self.assertEqual(u32(0), 0)
        self.assertEqual(u32(4294967295), 4294967295)

        self.assertTrue(u32(4) < 5)
        self.assertTrue(u32(4) <= 5)
        self.assertTrue(u32(5) <= 5)
        self.assertTrue(u32(5) == 5)
        self.assertTrue(u32(5) != 6)
        self.assertTrue(u32(5) >= 5)
        self.assertTrue(u32(5) >= 4)
        self.assertTrue(u32(5) > 4)

        with self.assertRaises(OverflowError):
            u32(4294967296)
        with self.assertRaises(OverflowError):
            u32(-1)

        self.assertIsInstance(u32(5) + 1, u32)

        self.assertEqual(u32(4294967295) + 1, 0)
        self.assertEqual(u32(0) - 1, 4294967295)
        self.assertEqual(u32(2147483648) * 2, 0)
        self.assertEqual(u32(4294967295) * 2, 4294967294)
        self.assertEqual(u32(15) % 4, 3)
        self.assertEqual(u32(15) // 2, 7)
        self.assertEqual(-u32(5), 4294967291)
        self.assertEqual(~u32(5), 4294967290)
        self.assertEqual(u32(4294967295) << 1, 4294967294)
        self.assertEqual(u32(1) >> 1, 0)
        self.assertEqual(u32(5) & 3, 1)
        self.assertEqual(u32(5) ^ 3, 6)
        self.assertEqual(u32(5) | 3, 7)

        if not USING_NUMPY:
            with self.assertRaises(ZeroDivisionError):
                u32(0) % 0
            with self.assertRaises(ZeroDivisionError):
                u32(0) / 0

            self.assertEqual(u32(15) / 2, 7)
            self.assertEqual(u32(4294967295) << 65, 4294967294)

        self.assertEqual(unpack_u32(b"\x00\x00\x00\x00"), 0)
        self.assertEqual(unpack_u32(b"\x80\x00\x00\x00"), 2147483648)
        self.assertEqual(unpack_u32(b"\xff\xff\xff\xff"), 4294967295)
        with self.assertRaises(ValueError):
            unpack_u32(b"")
        with self.assertRaises(ValueError):
            unpack_u32(b"\x00\x00\x00")
        self.assertEqual(pack_u32(u32(0)), b"\x00\x00\x00\x00")
        self.assertEqual(pack_u32(u32(4294967295)), b"\xff\xff\xff\xff")

    def test_u64(self) -> None:
        self.assertEqual(u64(0), 0)
        self.assertEqual(u64(18446744073709551615), 18446744073709551615)

        self.assertTrue(u64(4) < 5)
        self.assertTrue(u64(4) <= 5)
        self.assertTrue(u64(5) <= 5)
        self.assertTrue(u64(5) == 5)
        self.assertTrue(u64(5) != 6)
        self.assertTrue(u64(5) >= 5)
        self.assertTrue(u64(5) >= 4)
        self.assertTrue(u64(5) > 4)

        with self.assertRaises(OverflowError):
            u64(18446744073709551616)
        with self.assertRaises(OverflowError):
            u64(-1)

        self.assertIsInstance(u64(5) + 1, u64)

        self.assertEqual(u64(18446744073709551615) + 1, 0)
        self.assertEqual(u64(0) - 1, 18446744073709551615)
        self.assertEqual(u64(9223372036854775808) * 2, 0)
        self.assertEqual(u64(18446744073709551615) * 2, 18446744073709551614)
        self.assertEqual(u64(15) % 4, 3)
        self.assertEqual(u64(15) // 2, 7)
        self.assertEqual(-u64(5), 18446744073709551611)
        self.assertEqual(~u64(5), 18446744073709551610)
        self.assertEqual(u64(18446744073709551615) << 1, 18446744073709551614)
        self.assertEqual(u64(1) >> 1, 0)
        self.assertEqual(u64(5) & 3, 1)
        self.assertEqual(u64(5) ^ 3, 6)
        self.assertEqual(u64(5) | 3, 7)

        if not USING_NUMPY:
            with self.assertRaises(ZeroDivisionError):
                u64(0) % 0
            with self.assertRaises(ZeroDivisionError):
                u64(0) / 0

            self.assertEqual(u64(15) / 2, 7)
            self.assertEqual(u64(18446744073709551615) << 65, 18446744073709551614)

        self.assertEqual(unpack_u64(b"\x00\x00\x00\x00\x00\x00\x00\x00"), 0)
        self.assertEqual(unpack_u64(b"\x80\x00\x00\x00\x00\x00\x00\x00"), 9223372036854775808)
        self.assertEqual(unpack_u64(b"\xff\xff\xff\xff\xff\xff\xff\xff"), 18446744073709551615)
        with self.assertRaises(ValueError):
            unpack_u64(b"")
        with self.assertRaises(ValueError):
            unpack_u64(b"\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(pack_u64(u64(0)), b"\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(pack_u64(u64(18446744073709551615)), b"\xff\xff\xff\xff\xff\xff\xff\xff")

    def test_i8(self) -> None:
        self.assertEqual(i8(-128), -128)
        self.assertEqual(i8(0), 0)
        self.assertEqual(i8(127), 127)

        self.assertTrue(i8(4) < 5)
        self.assertTrue(i8(4) <= 5)
        self.assertTrue(i8(5) <= 5)
        self.assertTrue(i8(5) == 5)
        self.assertTrue(i8(5) != 6)
        self.assertTrue(i8(5) >= 5)
        self.assertTrue(i8(5) >= 4)
        self.assertTrue(i8(5) > 4)

        with self.assertRaises(OverflowError):
            i8(128)
        with self.assertRaises(OverflowError):
            i8(-129)

        self.assertIsInstance(i8(5) + 1, i8)

        self.assertEqual(i8(127) + 1, -128)
        self.assertEqual(i8(-128) - 1, 127)
        self.assertEqual(i8(64) * 2, -128)
        self.assertEqual(i8(127) * 2, -2)
        self.assertEqual(i8(15) % 4, 3)
        self.assertEqual(i8(15) // 2, 7)
        self.assertEqual(-i8(5), -5)
        self.assertEqual(~i8(5), -6)
        self.assertEqual(i8(127) << 1, -2)
        self.assertEqual(i8(-128) >> 1, -64)
        self.assertEqual(i8(5) & 3, 1)
        self.assertEqual(i8(5) ^ 3, 6)
        self.assertEqual(i8(5) | 3, 7)

        if not USING_NUMPY:
            with self.assertRaises(ZeroDivisionError):
                i8(0) % 0
            with self.assertRaises(ZeroDivisionError):
                i8(0) / 0

            self.assertEqual(i8(15) / 2, 7)
            self.assertEqual(i8(127) << 65, -2)

        self.assertEqual(unpack_i8(b"\x00"), 0)
        self.assertEqual(unpack_i8(b"\x7f"), 127)
        self.assertEqual(unpack_i8(b"\x80"), -128)
        self.assertEqual(unpack_i8(b"\xff"), -1)
        with self.assertRaises(ValueError):
            unpack_i8(b"")
        self.assertEqual(pack_i8(i8(0)), b"\x00")
        self.assertEqual(pack_i8(i8(127)), b"\x7f")
        self.assertEqual(pack_i8(i8(-128)), b"\x80")
        self.assertEqual(pack_i8(i8(-1)), b"\xff")

    def test_i16(self) -> None:
        self.assertEqual(i16(-32768), -32768)
        self.assertEqual(i16(0), 0)
        self.assertEqual(i16(32767), 32767)

        self.assertTrue(i16(4) < 5)
        self.assertTrue(i16(4) <= 5)
        self.assertTrue(i16(5) <= 5)
        self.assertTrue(i16(5) == 5)
        self.assertTrue(i16(5) != 6)
        self.assertTrue(i16(5) >= 5)
        self.assertTrue(i16(5) >= 4)
        self.assertTrue(i16(5) > 4)

        with self.assertRaises(OverflowError):
            i16(32768)
        with self.assertRaises(OverflowError):
            i16(-32769)

        self.assertIsInstance(i16(5) + 1, i16)

        self.assertEqual(i16(32767) + 1, -32768)
        self.assertEqual(i16(-32768) - 1, 32767)
        self.assertEqual(i16(16384) * 2, -32768)
        self.assertEqual(i16(32767) * 2, -2)
        self.assertEqual(i16(15) % 4, 3)
        self.assertEqual(i16(15) // 2, 7)
        self.assertEqual(-i16(5), -5)
        self.assertEqual(~i16(5), -6)
        self.assertEqual(i16(32767) << 1, -2)
        self.assertEqual(i16(-32768) >> 1, -16384)
        self.assertEqual(i16(5) & 3, 1)
        self.assertEqual(i16(5) ^ 3, 6)
        self.assertEqual(i16(5) | 3, 7)

        if not USING_NUMPY:
            with self.assertRaises(ZeroDivisionError):
                i16(0) % 0
            with self.assertRaises(ZeroDivisionError):
                i16(0) / 0

            self.assertEqual(i16(15) / 2, 7)
            self.assertEqual(i16(32767) << 65, -2)

        self.assertEqual(unpack_i16(b"\x00\x00"), 0)
        self.assertEqual(unpack_i16(b"\x7f\xff"), 32767)
        self.assertEqual(unpack_i16(b"\x80\x00"), -32768)
        self.assertEqual(unpack_i16(b"\xff\xff"), -1)
        with self.assertRaises(ValueError):
            unpack_i16(b"")
        with self.assertRaises(ValueError):
            unpack_i16(b"\x00")
        self.assertEqual(pack_i16(i16(0)), b"\x00\x00")
        self.assertEqual(pack_i16(i16(32767)), b"\x7f\xff")
        self.assertEqual(pack_i16(i16(-32768)), b"\x80\x00")
        self.assertEqual(pack_i16(i16(-1)), b"\xff\xff")

    def test_i32(self) -> None:
        self.assertEqual(i32(-2147483648), -2147483648)
        self.assertEqual(i32(0), 0)
        self.assertEqual(i32(2147483647), 2147483647)

        self.assertTrue(i32(4) < 5)
        self.assertTrue(i32(4) <= 5)
        self.assertTrue(i32(5) <= 5)
        self.assertTrue(i32(5) == 5)
        self.assertTrue(i32(5) != 6)
        self.assertTrue(i32(5) >= 5)
        self.assertTrue(i32(5) >= 4)
        self.assertTrue(i32(5) > 4)

        with self.assertRaises(OverflowError):
            i32(2147483648)
        with self.assertRaises(OverflowError):
            i32(-2147483649)

        self.assertIsInstance(i32(5) + 1, i32)

        self.assertEqual(i32(2147483647) + 1, -2147483648)
        self.assertEqual(i32(-2147483648) - 1, 2147483647)
        self.assertEqual(i32(1073741824) * 2, -2147483648)
        self.assertEqual(i32(2147483647) * 2, -2)
        self.assertEqual(i32(15) % 4, 3)
        self.assertEqual(i32(15) // 2, 7)
        self.assertEqual(-i32(5), -5)
        self.assertEqual(~i32(5), -6)
        self.assertEqual(i32(2147483647) << 1, -2)
        self.assertEqual(i32(-2147483648) >> 1, -1073741824)
        self.assertEqual(i32(5) & 3, 1)
        self.assertEqual(i32(5) ^ 3, 6)
        self.assertEqual(i32(5) | 3, 7)

        if not USING_NUMPY:
            with self.assertRaises(ZeroDivisionError):
                i32(0) % 0
            with self.assertRaises(ZeroDivisionError):
                i32(0) / 0

            self.assertEqual(i32(15) / 2, 7)
            self.assertEqual(i32(2147483647) << 65, -2)

        self.assertEqual(unpack_i32(b"\x00\x00\x00\x00"), 0)
        self.assertEqual(unpack_i32(b"\x7f\xff\xff\xff"), 2147483647)
        self.assertEqual(unpack_i32(b"\x80\x00\x00\x00"), -2147483648)
        self.assertEqual(unpack_i32(b"\xff\xff\xff\xff"), -1)
        with self.assertRaises(ValueError):
            unpack_i32(b"")
        with self.assertRaises(ValueError):
            unpack_i32(b"\x00\x00\x00")
        self.assertEqual(pack_i32(i32(0)), b"\x00\x00\x00\x00")
        self.assertEqual(pack_i32(i32(2147483647)), b"\x7f\xff\xff\xff")
        self.assertEqual(pack_i32(i32(-2147483648)), b"\x80\x00\x00\x00")
        self.assertEqual(pack_i32(i32(-1)), b"\xff\xff\xff\xff")

    def test_i64(self) -> None:
        self.assertEqual(i64(-9223372036854775808), -9223372036854775808)
        self.assertEqual(i64(0), 0)
        self.assertEqual(i64(9223372036854775807), 9223372036854775807)

        self.assertTrue(i64(4) < 5)
        self.assertTrue(i64(4) <= 5)
        self.assertTrue(i64(5) <= 5)
        self.assertTrue(i64(5) == 5)
        self.assertTrue(i64(5) != 6)
        self.assertTrue(i64(5) >= 5)
        self.assertTrue(i64(5) >= 4)
        self.assertTrue(i64(5) > 4)

        with self.assertRaises(OverflowError):
            i64(9223372036854775808)
        with self.assertRaises(OverflowError):
            i64(-9223372036854775809)

        self.assertIsInstance(i64(5) + 1, i64)

        self.assertEqual(i64(9223372036854775807) + 1, -9223372036854775808)
        self.assertEqual(i64(-9223372036854775808) - 1, 9223372036854775807)
        self.assertEqual(i64(4611686018427387904) * 2, -9223372036854775808)
        self.assertEqual(i64(9223372036854775807) * 2, -2)
        self.assertEqual(i64(15) % 4, 3)
        self.assertEqual(i64(15) // 2, 7)
        self.assertEqual(-i64(5), -5)
        self.assertEqual(~i64(5), -6)
        self.assertEqual(i64(9223372036854775807) << 1, -2)
        self.assertEqual(i64(-9223372036854775808) >> 1, -4611686018427387904)
        self.assertEqual(i64(5) & 3, 1)
        self.assertEqual(i64(5) ^ 3, 6)
        self.assertEqual(i64(5) | 3, 7)

        if not USING_NUMPY:
            with self.assertRaises(ZeroDivisionError):
                i64(0) % 0
            with self.assertRaises(ZeroDivisionError):
                i64(0) / 0

            self.assertEqual(i64(15) / 2, 7)
            self.assertEqual(i64(9223372036854775807) << 65, -2)

        self.assertEqual(unpack_i64(b"\x00\x00\x00\x00\x00\x00\x00\x00"), 0)
        self.assertEqual(unpack_i64(b"\x7f\xff\xff\xff\xff\xff\xff\xff"), 9223372036854775807)
        self.assertEqual(unpack_i64(b"\x80\x00\x00\x00\x00\x00\x00\x00"), -9223372036854775808)
        self.assertEqual(unpack_i64(b"\xff\xff\xff\xff\xff\xff\xff\xff"), -1)
        with self.assertRaises(ValueError):
            unpack_i64(b"")
        with self.assertRaises(ValueError):
            unpack_i64(b"\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(pack_i64(i64(0)), b"\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(pack_i64(i64(9223372036854775807)), b"\x7f\xff\xff\xff\xff\xff\xff\xff")
        self.assertEqual(pack_i64(i64(-9223372036854775808)), b"\x80\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(pack_i64(i64(-1)), b"\xff\xff\xff\xff\xff\xff\xff\xff")

    def test_f32(self) -> None:
        # TODO: Add more tests for infinities, NaNs, subnormals, etc...
        self.assertEqual(f32(0), 0)
        self.assertEqual(f32(1.0), 1.0)
        self.assertEqual(f32(-1.0), -1.0)

        self.assertEqual(f32(1.4e-45), 1.401298464324817e-45)  # Float min value.
        self.assertEqual(f32(3.4028235e38), 3.4028234663852886e38)  # Float max value.

        self.assertEqual(f32(1.0000001) + f32(1e-8) - f32(1.0000001), 0)

    def test_f64(self) -> None:
        # TODO: Above.
        self.assertEqual(f64(0), 0)
        self.assertEqual(f64(1.0), 1.0)
        self.assertEqual(f64(-1.0), -1.0)

        self.assertEqual(f64(4.9e-324), 4.9e-324)
        self.assertEqual(f64(1.7976931348623157e308), 1.7976931348623157e308)

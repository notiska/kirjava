#!/usr/bin/env python3

import unittest
from io import BytesIO
from os import SEEK_SET

from kirjava.backend import *
from kirjava.jvm.fmt.constants import *
from kirjava.jvm.fmt.pool import ConstPool
from kirjava.jvm.version import Version


class TestConstants(unittest.TestCase):

    _DEFAULTS = {
        # ConstIndex:        (1,),
        UTF8Info:          (b"test",),
        IntegerInfo:       (i32(1),),
        FloatInfo:         (f32(1.0),),
        LongInfo:          (i64(1),),
        DoubleInfo:        (f64(1.0),),
        StringInfo:        (UTF8Info(b"test"),),
        ClassInfo:         (UTF8Info(b"Test"),),
        FieldrefInfo:      (ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"test"), UTF8Info(b"()V"),),),
        MethodrefInfo:     (ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"test"), UTF8Info(b"()V"),),),
        InterfaceMethodrefInfo: (
            ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"test"), UTF8Info(b"()V"),),
        ),
        NameAndTypeInfo:   (UTF8Info(b"test"), UTF8Info(b"()V"),),
        MethodHandleInfo: (
            MethodHandleInfo.INVOKE_STATIC, MethodrefInfo(
                ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"testMethod2"), UTF8Info(b"()V"),),
            ),
        ),
        MethodTypeInfo:    (UTF8Info(b"()V"),),
        DynamicInfo:       (0, NameAndTypeInfo(UTF8Info(b"test"), UTF8Info(b"()V"),)),
        InvokeDynamicInfo: (0, NameAndTypeInfo(UTF8Info(b"test"), UTF8Info(b"()V"),)),
        ModuleInfo:        (UTF8Info(b"test"),),
        PackageInfo:       (UTF8Info(b"test"),),
    }

    def setUp(self) -> None:
        self.pool = ConstPool()

    def test_abc_attrs(self) -> None:
        for subclass in ConstInfo.__subclasses__():
            with self.subTest(subclass.__name__):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest("Missing default init values for %r." % subclass)
                info = subclass(*init)  # type: ignore[arg-type]
                self.assertIsInstance(info.tag, int)
                self.assertIsInstance(info.wide, bool)
                self.assertIsInstance(info.since, Version)
                self.assertIsInstance(info.loadable, bool)

    def test_repr_str_eq_copy(self) -> None:
        for subclass in ConstInfo.__subclasses__():
            with self.subTest(subclass.__name__):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest("Missing default init values for %r." % subclass)
                info_no_index = subclass(*init)  # type: ignore[arg-type]

                print(repr(info_no_index), str(info_no_index), end=" ")
                info_index = info_no_index.copy()
                info_index.index = 2
                print(repr(info_index), str(info_index))

                self.assertEqual(info_no_index, info_no_index)
                self.assertEqual(info_no_index, info_index)

                self.assertEqual(repr(info_no_index), repr(info_index).replace("index=%i, " % info_index.index, ""))
                self.assertEqual(str(info_no_index), str(info_index).replace("#%i:" % info_index.index, ""))

    def test_symmetric_read_write(self) -> None:
        for subclass in ConstInfo.__subclasses__():
            with self.subTest(subclass.__name__):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest("Missing default init values for %r." % subclass)
                info_init = subclass(*init)  # type: ignore[arg-type]

                data = BytesIO()
                info_init.write(data, self.pool)
                data_first = data.getvalue()
                data.seek(0, SEEK_SET)

                info_read = ConstInfo.read(data, self.pool)
                self.assertEqual(info_init, info_read)
                if data.read():
                    self.fail("Instruction underread.")

                data = BytesIO()
                info_read.write(data, self.pool)
                self.assertEqual(data_first, data.getvalue())

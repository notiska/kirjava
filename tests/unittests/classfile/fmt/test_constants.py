#!/usr/bin/env python3

from __future__ import annotations

import copy
import unittest
from io import BytesIO
from os import SEEK_SET

from kirjava.backend import *
from kirjava.classfile.desc import *
from kirjava.classfile.fmt.constants import *
from kirjava.classfile.fmt.pool import ConstPool
from kirjava.classfile.version import Version
from kirjava.model.types import int_array_t, Array, Class as ClassType
from kirjava.model.values.constants import (
    Double, Integer, Float, Long, String, MethodHandle, MethodType, Class as ClassConst,
)


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
        FieldrefInfo:      (ClassInfo(UTF8Info(b"Test")), NameAndTypeInfo(UTF8Info(b"test"), UTF8Info(b"I"),),),
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

    _MH_KINDS = [
        (MethodHandleInfo.GET_FIELD, FieldrefInfo),
        (MethodHandleInfo.GET_STATIC, FieldrefInfo),
        (MethodHandleInfo.PUT_FIELD, FieldrefInfo),
        (MethodHandleInfo.PUT_STATIC, FieldrefInfo),
        (MethodHandleInfo.INVOKE_VIRTUAL, MethodrefInfo),
        (MethodHandleInfo.INVOKE_STATIC, MethodrefInfo),
        (MethodHandleInfo.INVOKE_SPECIAL, MethodrefInfo),
        (MethodHandleInfo.NEW_INVOKE_SPECIAL, MethodrefInfo),
        (MethodHandleInfo.INVOKE_INTERFACE, InterfaceMethodrefInfo),
    ]

    def setUp(self) -> None:
        self.pool = ConstPool()

    def test_abc_attrs(self) -> None:
        for subclass in ConstInfo.__subclasses__():
            with self.subTest(subclass.__name__):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest(f"Missing default init values for {subclass!r}.")
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
                    self.skipTest(f"Missing default init values for {subclass!r}.")
                info_no_index = subclass(*init)  # type: ignore[arg-type]

                print(repr(info_no_index), str(info_no_index), end=" ")
                info_index = copy.copy(info_no_index)
                info_index.index = 2
                print(repr(info_index), str(info_index))

                self.assertEqual(info_no_index, info_no_index)
                self.assertEqual(info_no_index, info_index)
                self.assertIsNot(info_no_index, info_index)

                info_deepcopy = copy.deepcopy(info_index)
                self.assertEqual(info_deepcopy, info_index)
                self.assertEqual(info_deepcopy, info_no_index)
                self.assertIsNot(info_deepcopy, info_index)
                self.assertIsNot(info_deepcopy, info_no_index)

                self.assertEqual(repr(info_no_index), repr(info_index).replace(f"index={info_index.index}, ", ""))
                self.assertEqual(str(info_no_index), str(info_index).replace(f"#{info_index.index}:", ""))

    # TODO: Test deref?

    def test_symmetric_read_write(self) -> None:
        for subclass in ConstInfo.__subclasses__():
            with self.subTest(subclass.__name__):
                init = self._DEFAULTS.get(subclass)
                if init is None:
                    self.skipTest(f"Missing default init values for {subclass!r}.")
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

    def test_cant_lift(self) -> None:
        with self.assertRaises(TypeError):
            ConstIndex(0).lift().unwrap()
        with self.assertRaises(TypeError):
            UTF8Info(*self._DEFAULTS[UTF8Info]).lift().unwrap()  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            FieldrefInfo(*self._DEFAULTS[FieldrefInfo]).lift().unwrap()  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            MethodrefInfo(*self._DEFAULTS[MethodrefInfo]).lift().unwrap()  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            InterfaceMethodrefInfo(*self._DEFAULTS[InterfaceMethodrefInfo]).lift().unwrap()  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            NameAndTypeInfo(*self._DEFAULTS[NameAndTypeInfo]).lift().unwrap()  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            InvokeDynamicInfo(*self._DEFAULTS[InvokeDynamicInfo]).lift().unwrap()  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            ModuleInfo(*self._DEFAULTS[ModuleInfo]).lift().unwrap()  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            PackageInfo(*self._DEFAULTS[PackageInfo]).lift().unwrap()  # type: ignore[arg-type]

    def test_integer_lift(self) -> None:
        info = IntegerInfo(i32(0))
        lifted = info.lift().unwrap()

        self.assertIsInstance(lifted, Integer)
        self.assertEqual(lifted.info, info)
        self.assertEqual(lifted.value, info.value)

    def test_float_lift(self) -> None:
        info = FloatInfo(f32(0.0))
        lifted = info.lift().unwrap()

        self.assertIsInstance(lifted, Float)
        self.assertEqual(lifted.info, info)
        self.assertEqual(lifted.value, info.value)

    def test_long_lift(self) -> None:
        info = LongInfo(i64(0))
        lifted = info.lift().unwrap()

        self.assertIsInstance(lifted, Long)
        self.assertEqual(lifted.info, info)
        self.assertEqual(lifted.value, info.value)

    def test_double_lift(self) -> None:
        info = DoubleInfo(f64(0.0))
        lifted = info.lift().unwrap()

        self.assertIsInstance(lifted, Double)
        self.assertEqual(lifted.info, info)
        self.assertEqual(lifted.value, info.value)

    def test_class_lift(self) -> None:
        info = ClassInfo(*self._DEFAULTS[ClassInfo])  # type: ignore[arg-type]
        lifted = info.lift().unwrap()

        self.assertIsInstance(lifted, ClassConst)
        self.assertEqual(lifted.info, info)
        assert isinstance(info.name, UTF8Info)
        self.assertEqual(lifted.name, info.name.decode())

        with self.assertRaises(TypeError):
            ClassInfo(ConstIndex(0)).lift().unwrap()
        with self.assertRaises(TypeError):
            ClassInfo(IntegerInfo(i32(0))).lift().unwrap()

        self.assertEqual(ClassInfo(UTF8Info(b"I")).lift().unwrap().ref_type, ClassType("I"))
        self.assertEqual(ClassInfo(UTF8Info(b"[I")).lift().unwrap().ref_type, int_array_t)
        self.assertEqual(ClassInfo(UTF8Info(b"LI")).lift().unwrap().ref_type, ClassType("LI"))
        self.assertEqual(ClassInfo(UTF8Info(b"LI;")).lift().unwrap().ref_type, ClassType("I"))
        self.assertEqual(ClassInfo(UTF8Info(b"[LI;")).lift().unwrap().ref_type, Array(ClassType("I")))

        with self.assertRaises(TypeError):
            ClassInfo(UTF8Info(b"[A")).lift().unwrap()
        with self.assertRaises(TypeError):
            ClassInfo(UTF8Info(b"[V")).lift().unwrap()

    def test_string_lift(self) -> None:
        info = StringInfo(*self._DEFAULTS[StringInfo])  # type: ignore[arg-type]
        lifted = info.lift().unwrap()

        self.assertIsInstance(lifted, String)
        self.assertEqual(lifted.info, info)
        assert isinstance(info.value, UTF8Info)
        self.assertEqual(lifted.value, info.value.decode())

        with self.assertRaises(TypeError):
            StringInfo(ConstIndex(0)).lift().unwrap()
        with self.assertRaises(TypeError):
            StringInfo(IntegerInfo(i32(0))).lift().unwrap()

    def test_method_handle_lift(self) -> None:
        for (kind, ref_type) in self._MH_KINDS:
            with self.subTest(MethodHandleInfo._KINDS[kind]):
                info = MethodHandleInfo(kind, ref_type(*self._DEFAULTS[ref_type]))  # type: ignore[arg-type]
                lifted = info.lift().unwrap()

                self.assertIsInstance(lifted, MethodHandle)
                self.assertEqual(lifted.info, info)
                self.assertEqual(lifted.kind.value, info.kind)
                assert isinstance(info.ref, (FieldrefInfo, MethodrefInfo, InterfaceMethodrefInfo))
                self.assertEqual(lifted.class_, info.ref.class_.lift().unwrap())

                if ref_type is FieldrefInfo:
                    arg_types = ()
                    # Mypy stuff...
                    assert isinstance(info.ref, FieldrefInfo)
                    assert isinstance(info.ref.name_and_type, NameAndTypeInfo)
                    assert isinstance(info.ref.name_and_type.descriptor, UTF8Info)
                    ret_type = parse_field_descriptor(info.ref.name_and_type.descriptor.decode()).unwrap()
                else:
                    assert isinstance(info.ref, (MethodrefInfo, InterfaceMethodrefInfo))
                    assert isinstance(info.ref.name_and_type, NameAndTypeInfo)
                    assert isinstance(info.ref.name_and_type.descriptor, UTF8Info)
                    arg_types, ret_type = parse_method_descriptor(info.ref.name_and_type.descriptor.decode()).unwrap()

                self.assertEqual(lifted.arg_types, arg_types)
                self.assertEqual(lifted.ret_type, ret_type)

        with self.assertRaises(TypeError):
            MethodHandleInfo(MethodHandleInfo.GET_FIELD, ConstIndex(0)).lift().unwrap()
        with self.assertRaises(TypeError):
            MethodHandleInfo(MethodHandleInfo.GET_FIELD, IntegerInfo(i32(0))).lift().unwrap()

        with self.assertRaises(ValueError):
            MethodHandleInfo(0, FieldrefInfo(*self._DEFAULTS[FieldrefInfo])).lift().unwrap()  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            MethodHandleInfo(10, FieldrefInfo(*self._DEFAULTS[FieldrefInfo])).lift().unwrap()  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            MethodHandleInfo(
                MethodHandleInfo.GET_FIELD,
                MethodrefInfo(*self._DEFAULTS[MethodrefInfo]),  # type: ignore[arg-type]
            ).lift().unwrap()
        with self.assertRaises(TypeError):
            MethodHandleInfo(
                MethodHandleInfo.GET_FIELD,
                InterfaceMethodrefInfo(*self._DEFAULTS[InterfaceMethodrefInfo]),  # type: ignore[arg-type]
            ).lift().unwrap()

    def test_method_type_lift(self) -> None:
        info = MethodTypeInfo(*self._DEFAULTS[MethodTypeInfo])  # type: ignore[arg-type]
        lifted = info.lift().unwrap()

        self.assertIsInstance(lifted, MethodType)
        self.assertEqual(lifted.info, info)
        assert isinstance(info.descriptor, UTF8Info)
        arg_types, ret_type = parse_method_descriptor(info.descriptor.decode()).unwrap()
        self.assertEqual(lifted.arg_types, arg_types)
        self.assertEqual(lifted.ret_type, ret_type)

        with self.assertRaises(TypeError):
            MethodTypeInfo(ConstIndex(0)).lift().unwrap()
        with self.assertRaises(TypeError):
            MethodTypeInfo(IntegerInfo(i32(0))).lift().unwrap()

    # TODO: Dynamic is a weird one, look into it further.

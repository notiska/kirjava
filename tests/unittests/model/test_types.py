#!/usr/bin/env python3

import unittest

from kirjava.model import types
from kirjava.model.types import *


class TestTypes(unittest.TestCase):

    def test_abc_attrs(self) -> None:
        for name in dir(types):
            type_ = getattr(types, name)
            if not isinstance(type_, Type):
                continue
            with self.subTest(str(type_)):
                self.assertIsInstance(type_.name, str)
                self.assertIsInstance(type_.wide, bool)
                self.assertIsInstance(type_.abstract, bool)

    def test_repr_str_eq_hash(self) -> None:
        for name in dir(types):
            type_ = getattr(types, name)
            if not isinstance(type_, Type):
                continue
            with self.subTest(str(type_)):
                self.assertEqual(type_, type_)
                self.assertEqual(hash(type_), hash(type_))
                print(str(type_), repr(type_))

    def test_eq_extended(self) -> None:
        self.assertNotEqual(primitive_t, reference_t)
        self.assertNotEqual(top_t, primitive_t)
        self.assertNotEqual(top_t, void_t)
        self.assertNotEqual(top_t, reserved_t)

        # All are integer types, though they should not be equal at this level.
        self.assertNotEqual(boolean_t, byte_t)
        self.assertNotEqual(boolean_t, char_t)
        self.assertNotEqual(boolean_t, short_t)
        self.assertNotEqual(boolean_t, int_t)

        self.assertEqual(return_address_t, ReturnAddress(0))
        self.assertNotEqual(ReturnAddress(0), ReturnAddress(1))

        # Base uninitialized should be assignable as it has no upper bound, so to speak.
        self.assertEqual(uninitialized_t, Uninitialized(0))
        self.assertNotEqual(Uninitialized(0), Uninitialized(1))
        # This should not work either, as uninitializedThis is treated differently.
        self.assertNotEqual(uninitialized_t, uninitialized_this_t)

        self.assertEqual(object_t, Class("java/lang/Object"))

        self.assertNotEqual(object_t, class_t)
        self.assertNotEqual(object_t, string_t)
        self.assertNotEqual(object_t, throwable_t)
        self.assertNotEqual(object_t, error_t)
        self.assertNotEqual(object_t, exception_t)

        # The type checker doesn't necessarily distinguish between interface types anc class types. Additionally, if an
        # interface is named exactly the same as a class, it's likely they are the same (different classloaders could
        # impact this though, of course).
        self.assertEqual(object_t, object_t.interface())

        self.assertNotEqual(null_t, object_t)
        self.assertNotEqual(null_t, reference_t)

        self.assertNotEqual(array_t, boolean_array_t)
        self.assertNotEqual(boolean_array_t, byte_array_t)
        self.assertNotEqual(boolean_array_t, char_array_t)
        self.assertNotEqual(boolean_array_t, short_array_t)
        self.assertNotEqual(boolean_array_t, int_array_t)
        self.assertNotEqual(boolean_array_t, long_array_t)
        self.assertNotEqual(boolean_array_t, float_array_t)
        self.assertNotEqual(boolean_array_t, double_array_t)

        self.assertEqual(Array(object_t), Array(object_t))
        self.assertNotEqual(Array(object_t), Array(class_t))
        self.assertEqual(Array.nested(object_t, 1), Array(object_t))
        self.assertEqual(Array.nested(object_t, 2), Array.nested(object_t, 2))
        self.assertNotEqual(Array.nested(object_t, 3), Array.nested(object_t, 2))

    def test_assignability(self) -> None:
        self.assertTrue(top_t.assignable(top_t))
        self.assertTrue(top_t.assignable(reserved_t))
        self.assertFalse(top_t.assignable(primitive_t))
        self.assertFalse(primitive_t.assignable(top_t))
        self.assertFalse(reference_t.assignable(top_t))

        self.assertTrue(primitive_t.assignable(void_t))  # Bit of a weird case here, tbh. Oh well.
        self.assertFalse(void_t.assignable(void_t))
        self.assertFalse(top_t.assignable(void_t))

        self.assertFalse(reserved_t.assignable(reserved_t))
        self.assertFalse(reserved_t.assignable(top_t))

        self.assertTrue(primitive_t.assignable(primitive_t))
        self.assertTrue(primitive_t.assignable(boolean_t))
        self.assertTrue(primitive_t.assignable(byte_t))
        self.assertTrue(primitive_t.assignable(int_t))
        self.assertTrue(primitive_t.assignable(long_t))
        self.assertTrue(primitive_t.assignable(float_t))
        self.assertTrue(primitive_t.assignable(double_t))
        self.assertFalse(primitive_t.assignable(reserved_t))
        self.assertFalse(primitive_t.assignable(object_t))
        self.assertFalse(primitive_t.assignable(null_t))
        self.assertFalse(primitive_t.assignable(array_t))
        self.assertFalse(primitive_t.assignable(boolean_array_t))

        self.assertFalse(boolean_t.assignable(int_t))
        self.assertFalse(byte_t.assignable(int_t))
        self.assertFalse(char_t.assignable(int_t))
        self.assertFalse(short_t.assignable(int_t))

        self.assertTrue(long_t.assignable(long_t))
        self.assertTrue(long_t.assignable(byte_t))
        self.assertTrue(long_t.assignable(int_t))
        self.assertFalse(int_t.assignable(long_t))
        self.assertFalse(long_t.assignable(boolean_t))

        self.assertTrue(float_t.assignable(float_t))
        self.assertTrue(float_t.assignable(byte_t))
        self.assertTrue(float_t.assignable(int_t))
        self.assertTrue(float_t.assignable(long_t))
        self.assertFalse(int_t.assignable(float_t))
        self.assertFalse(float_t.assignable(boolean_t))
        self.assertFalse(long_t.assignable(float_t))
        self.assertFalse(float_t.assignable(double_t))

        self.assertTrue(double_t.assignable(double_t))
        self.assertTrue(double_t.assignable(byte_t))
        self.assertTrue(double_t.assignable(int_t))
        self.assertTrue(double_t.assignable(long_t))
        self.assertTrue(double_t.assignable(float_t))
        self.assertFalse(int_t.assignable(double_t))
        self.assertFalse(double_t.assignable(boolean_t))
        self.assertFalse(long_t.assignable(double_t))

        self.assertTrue(return_address_t.assignable(return_address_t))
        self.assertTrue(return_address_t.assignable(ReturnAddress(0)))
        self.assertFalse(return_address_t.assignable(int_t))
        self.assertFalse(ReturnAddress(0).assignable(return_address_t))

        self.assertTrue(uninitialized_t.assignable(uninitialized_t))
        self.assertTrue(uninitialized_t.assignable(Uninitialized(0)))
        self.assertTrue(Uninitialized(0).assignable(Uninitialized(0)))
        self.assertFalse(Uninitialized(0).assignable(uninitialized_t))
        self.assertFalse(Uninitialized(0).assignable((Uninitialized(1))))
        self.assertFalse(uninitialized_t.assignable(uninitialized_this_t))

        self.assertTrue(uninitialized_this_t.assignable(uninitialized_this_t))
        self.assertFalse(uninitialized_this_t.assignable(uninitialized_t))

        self.assertTrue(object_t.assignable(object_t))
        self.assertTrue(object_t.assignable(Class("java/lang/Object")))
        self.assertTrue(object_t.assignable(class_t))
        self.assertTrue(object_t.assignable(string_t))
        self.assertTrue(object_t.assignable(throwable_t))
        self.assertTrue(object_t.assignable(error_t))
        self.assertTrue(object_t.assignable(exception_t))
        self.assertTrue(object_t.assignable(object_t.interface()))
        self.assertTrue(object_t.assignable(null_t))
        self.assertTrue(object_t.assignable(array_t))
        self.assertTrue(object_t.assignable(boolean_array_t))
        self.assertFalse(object_t.assignable(reference_t))
        self.assertFalse(object_t.assignable(uninitialized_t))
        self.assertFalse(object_t.assignable(uninitialized_this_t))

        self.assertTrue(class_t.assignable(class_t))
        self.assertTrue(class_t.assignable(Class("java/lang/Class")))
        self.assertFalse(class_t.assignable(object_t))
        self.assertFalse(class_t.assignable(string_t))

        self.assertTrue(null_t.assignable(null_t))
        self.assertFalse(null_t.assignable(object_t))
        self.assertFalse(null_t.assignable(array_t))

        self.assertTrue(array_t.assignable(array_t))
        self.assertTrue(array_t.assignable(null_t))
        self.assertTrue(array_t.assignable(boolean_array_t))
        self.assertTrue(array_t.assignable(byte_array_t))
        self.assertTrue(array_t.assignable(int_array_t))
        self.assertTrue(array_t.assignable(long_array_t))
        self.assertTrue(array_t.assignable(float_array_t))
        self.assertTrue(array_t.assignable(double_array_t))
        self.assertTrue(Array(object_t).assignable(Array(object_t)))
        self.assertTrue(Array(object_t).assignable(Array(class_t)))
        self.assertTrue(Array(object_t).assignable(Array.nested(class_t, 2)))
        self.assertTrue(Array(object_t).assignable(null_t))
        self.assertTrue(Array.nested(class_t, 2).assignable(null_t))
        self.assertFalse(int_array_t.assignable(array_t))
        self.assertFalse(int_array_t.assignable(byte_array_t))
        self.assertFalse(Array(object_t).assignable(int_array_t))
        self.assertFalse(Array(class_t).assignable(Array(object_t)))
        self.assertFalse(Array.nested(class_t, 2).assignable(Array(object_t)))

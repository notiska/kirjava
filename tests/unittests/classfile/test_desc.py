#!/usr/bin/env python3

from __future__ import annotations

import unittest

from kirjava.classfile.desc import *
from kirjava.model.types import *


class TestDescriptors(unittest.TestCase):

    # TODO: Also add tests with strict=False.

    def test_parse_reference(self) -> None:
        self.assertEqual(parse_reference("java/lang/Object").unwrap(), object_t)
        self.assertEqual(parse_reference("java/lang/String").unwrap(), string_t)
        self.assertEqual(parse_reference("java/lang/Integer").unwrap(), Class("java/lang/Integer"))
        self.assertEqual(parse_reference("I").unwrap(), Class("I"))

        self.assertEqual(parse_reference("Ljava/lang/Object").unwrap(), Class("Ljava/lang/Object"))

        self.assertEqual(parse_reference("Ljava/lang/Object;").unwrap(), object_t)
        self.assertEqual(parse_reference("Ljava/lang/String;").unwrap(), string_t)
        self.assertEqual(parse_reference("Ljava/lang/Integer;").unwrap(), Class("java/lang/Integer"))
        self.assertEqual(parse_reference("LI;").unwrap(), Class("I"))

        self.assertEqual(parse_reference("[Z").unwrap(), boolean_array_t)
        self.assertEqual(parse_reference("[I").unwrap(), int_array_t)
        self.assertEqual(parse_reference("[[I").unwrap(), Array(int_array_t))
        self.assertEqual(parse_reference("[Ljava/lang/Object;").unwrap(), Array(object_t))
        self.assertEqual(parse_reference("[[Ljava/lang/Object;").unwrap(), Array.nested(object_t, 2))

        with self.assertRaises(ValueError):
            parse_reference("").unwrap()
        with self.assertRaises(TypeError):
            parse_reference("[java/lang/Object").unwrap()
        with self.assertRaises(TypeError):
            parse_reference("[").unwrap()
        with self.assertRaises(TypeError):
            parse_reference("[[[[[[[[[[[[[[[[[[[[[[[[").unwrap()

    def test_parse_field_descriptor(self) -> None:
        self.assertEqual(parse_field_descriptor("I").unwrap(), int_t)
        self.assertEqual(parse_field_descriptor("B").unwrap(), byte_t)
        self.assertEqual(parse_field_descriptor("C").unwrap(), char_t)
        self.assertEqual(parse_field_descriptor("D").unwrap(), double_t)
        self.assertEqual(parse_field_descriptor("F").unwrap(), float_t)
        self.assertEqual(parse_field_descriptor("J").unwrap(), long_t)
        self.assertEqual(parse_field_descriptor("S").unwrap(), short_t)
        self.assertEqual(parse_field_descriptor("Z").unwrap(), boolean_t)
        self.assertEqual(parse_field_descriptor("Ljava/lang/Object;").unwrap(), object_t)
        self.assertEqual(parse_field_descriptor("[Ljava/lang/Object;").unwrap(), Array(object_t))

        with self.assertRaises(ValueError):
            parse_field_descriptor("").unwrap()
        with self.assertRaises(ValueError):
            parse_field_descriptor("II").unwrap()
        with self.assertRaises(ValueError):
            parse_field_descriptor("Ljava/lang/Object;;").unwrap()
        with self.assertRaises(TypeError):
            parse_field_descriptor("V").unwrap()
        with self.assertRaises(TypeError):
            parse_field_descriptor("[[V").unwrap()

    def test_parse_method_descriptor(self) -> None:
        self.assertEqual(parse_method_descriptor("()V").unwrap(), ((), void_t))
        self.assertEqual(parse_method_descriptor("(I)V").unwrap(), ((int_t,), void_t))
        self.assertEqual(parse_method_descriptor("(I)I").unwrap(), ((int_t,), int_t))
        self.assertEqual(parse_method_descriptor("(I)Z").unwrap(), ((int_t,), boolean_t))
        self.assertEqual(parse_method_descriptor("(I)D").unwrap(), ((int_t,), double_t))
        self.assertEqual(parse_method_descriptor("(I)F").unwrap(), ((int_t,), float_t))
        self.assertEqual(parse_method_descriptor("(I)J").unwrap(), ((int_t,), long_t))
        self.assertEqual(parse_method_descriptor("(I)S").unwrap(), ((int_t,), short_t))
        self.assertEqual(parse_method_descriptor("(I)C").unwrap(), ((int_t,), char_t))
        self.assertEqual(parse_method_descriptor("(Ljava/lang/Object;)V").unwrap(), ((object_t,), void_t))
        self.assertEqual(parse_method_descriptor(
            "(Ljava/lang/Object;)Ljava/lang/Object;").unwrap(), ((object_t,), object_t),
        )
        self.assertEqual(parse_method_descriptor("([Ljava/lang/Object;)V").unwrap(), ((Array(object_t),), void_t))
        self.assertEqual(parse_method_descriptor(
            "([Ljava/lang/Object;)[Ljava/lang/Object;").unwrap(), ((Array(object_t),), Array(object_t)),
        )

        with self.assertRaises(ValueError):
            parse_method_descriptor("").unwrap()
        with self.assertRaises(ValueError):
            parse_method_descriptor("(I").unwrap()
        with self.assertRaises(ValueError):
            parse_method_descriptor("I)").unwrap()
        with self.assertRaises(ValueError):
            parse_method_descriptor("V").unwrap()
        with self.assertRaises(ValueError):
            parse_method_descriptor("(())V").unwrap()
        with self.assertRaises(ValueError):
            parse_method_descriptor("(()I)V").unwrap()
        with self.assertRaises(ValueError):
            parse_method_descriptor("V()I").unwrap()
        with self.assertRaises(ValueError):
            parse_method_descriptor("()V()()()()()()(").unwrap()

        with self.assertRaises(TypeError):  # Kinda a weird one actually, but that's how the parser works so.
            parse_method_descriptor("()").unwrap()
        with self.assertRaises(TypeError):
            parse_method_descriptor("(Ljava/lang/Object;)[").unwrap()
        with self.assertRaises(TypeError):
            parse_method_descriptor("(Ljava/lang/Object;)[[[[[[[[").unwrap()
        with self.assertRaises(TypeError):
            parse_method_descriptor("(V)I").unwrap()
        with self.assertRaises(TypeError):
            parse_method_descriptor("(I)[V").unwrap()

    def test_to_descriptor(self) -> None:
        self.assertEqual(to_descriptor(int_t).unwrap(), "I")
        self.assertEqual(to_descriptor(byte_t).unwrap(), "B")
        self.assertEqual(to_descriptor(char_t).unwrap(), "C")
        self.assertEqual(to_descriptor(double_t).unwrap(), "D")
        self.assertEqual(to_descriptor(float_t).unwrap(), "F")
        self.assertEqual(to_descriptor(long_t).unwrap(), "J")
        self.assertEqual(to_descriptor(short_t).unwrap(), "S")
        self.assertEqual(to_descriptor(boolean_t).unwrap(), "Z")
        self.assertEqual(to_descriptor(object_t).unwrap(), "Ljava/lang/Object;")
        self.assertEqual(to_descriptor(Array(object_t)).unwrap(), "[Ljava/lang/Object;")
        self.assertEqual(to_descriptor(Array.nested(object_t, 2)).unwrap(), "[[Ljava/lang/Object;")
        self.assertEqual(to_descriptor(Array(int_t)).unwrap(), "[I")
        self.assertEqual(to_descriptor(Array.nested(int_t, 2)).unwrap(), "[[I")

        self.assertEqual(to_descriptor((int_t,), void_t).unwrap(), "(I)V")
        self.assertEqual(to_descriptor((int_t, int_t), void_t).unwrap(), "(II)V")
        self.assertEqual(to_descriptor((int_t,), int_t).unwrap(), "(I)I")
        self.assertEqual(to_descriptor((int_t,), boolean_t).unwrap(), "(I)Z")
        self.assertEqual(to_descriptor((object_t, int_t), void_t).unwrap(), "(Ljava/lang/Object;I)V")
        self.assertEqual(to_descriptor((Array(object_t),), void_t).unwrap(), "([Ljava/lang/Object;)V")

        # Yeah so unfortunately (or fortunately) we can do this without raising an exception. Might fix in the future,
        # doesn't matter too much right now though.
        self.assertEqual(to_descriptor((void_t,), int_t).unwrap(), "(V)I")
        self.assertEqual(to_descriptor(((object_t, int_t), int_t), void_t).unwrap(), "((Ljava/lang/Object;I)I)V")
        self.assertEqual(to_descriptor(object_t, (int_t, int_t), void_t).unwrap(), "Ljava/lang/Object;(II)V")

        with self.assertRaises(TypeError):
            to_descriptor(Invalid("abc")).unwrap()
        with self.assertRaises(TypeError):
            to_descriptor((int_t, Invalid("abc"))).unwrap()

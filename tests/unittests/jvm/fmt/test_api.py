#!/usr/bin/env python3

import unittest

from kirjava.backend import *
from kirjava.jvm.fmt.annotation import *
from kirjava.jvm.fmt.constants import *


# FIXME: If possible, could go through and find all classes that implement __getitem__, etc...

class TestIterablesMatchABC(unittest.TestCase):

    _DEFAULTS: dict[type, tuple[tuple, list]] = {
        Annotation: ((UTF8Info(b"TestAnno1"),), [
            Annotation.NamedElement(UTF8Info(b"test1"), ConstValue(ConstValue.KIND_INT, IntegerInfo(i32(1)))),
            Annotation.NamedElement(UTF8Info(b"test2"), ConstValue(ConstValue.KIND_LONG, LongInfo(i64(2)))),
            Annotation.NamedElement(UTF8Info(b"test3"), ConstValue(ConstValue.KIND_FLOAT, FloatInfo(f32(3.0)))),
            Annotation.NamedElement(UTF8Info(b"test4"), ConstValue(ConstValue.KIND_DOUBLE, DoubleInfo(f64(4.0)))),
        ]),
        ParameterAnnotations: ((), [
            Annotation(UTF8Info(b"TestAnno2")),
            Annotation(UTF8Info(b"TestAnno3")),
        ]),
        TypePath: ((), []),
        ArrayValue: ((), []),
        LocalVarTarget: ((), []),
    }

    def test_init(self) -> None:
        for class_, (args, iterable) in self._DEFAULTS.items():
            with self.subTest(class_.__name__):
                inst_no_args = class_(*args)
                inst_none_arg = class_(*args, None)
                self.assertEqual(len(inst_no_args), 0)
                self.assertEqual(len(inst_none_arg), 0)

                inst = class_(*args, iterable)
                self.assertEqual(len(inst), len(iterable))

    def test_casts(self) -> None:
        for class_ in self._DEFAULTS:
            with self.subTest(class_.__name__):
                args, iterable = self._DEFAULTS[class_]
                inst = class_(*args, iterable)

                self.assertIsInstance(list(inst), list)
                self.assertIsInstance(tuple(iterable), tuple)
                self.assertEqual(next(iter(iterable)), iterable[0])

                for index, value in enumerate(inst):
                    self.assertEqual(iterable[index], value)

    def test_repr_str(self) -> None:
        for class_ in self._DEFAULTS:
            with self.subTest(class_.__name__):
                args, iterable = self._DEFAULTS[class_]
                inst = class_(*args, iterable)

                print(repr(inst), str(inst))
                self.assertIn(repr(iterable), repr(inst))

    def test_get_set_del(self) -> None:
        for class_ in self._DEFAULTS:
            with self.subTest(class_.__name__):
                args, iterable = self._DEFAULTS[class_]
                inst = class_(*args, iterable)

                for index, value in enumerate(iterable):
                    self.assertEqual(inst[index], value)

                inst[0] = iterable[0]
                self.assertEqual(inst[0], iterable[0])

                del inst[0]
                self.assertEqual(len(inst), len(iterable) - 1)

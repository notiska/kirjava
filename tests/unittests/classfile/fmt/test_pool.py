#!/usr/bin/env python3

import unittest

from kirjava.classfile.fmt import ConstPool


class TestConstantPool(unittest.TestCase):

    # TODO: Check that all errors raise correctly too.

    def setUp(self) -> None:
        self.pool = ConstPool()

    def test_getitem(self) -> None:
        ...

    def test_setitem(self) -> None:
        ...

    def test_delitem(self) -> None:
        ...

    def test_clear(self) -> None:
        ...  # self.pool.clear()

    def test_add(self) -> None:
        ...

    def test_insert(self) -> None:
        ...

    def test_extend(self) -> None:
        ...

    def test_index(self) -> None:
        ...

    def test_pop(self) -> None:
        ...

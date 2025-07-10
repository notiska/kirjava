#!/usr/bin/env python3

import unittest

from kirjava.classfile.analysis import Frame
from kirjava.model.types import *


class TestFrame(unittest.TestCase):

    def test_pop(self) -> None:
        frame = Frame([reserved_t, double_t])
        self.assertEqual(frame.pop(double_t).unwrap(), double_t)
        self.assertEqual(frame.stack, [])

        frame = Frame([reserved_t, double_t])
        self.assertEqual(frame.pop(top_t).unwrap(), double_t)
        self.assertEqual(frame.stack, [reserved_t])

        frame = Frame([int_t, reserved_t, double_t])
        self.assertEqual(frame.pop(double_t).unwrap(), double_t)
        self.assertEqual(frame.stack, [int_t])

        frame = Frame([object_t, null_t, int_t, reserved_t, double_t])
        self.assertEqual(frame.pop(top_t).unwrap(), double_t)
        self.assertEqual(frame.pop(top_t).unwrap(), reserved_t)
        self.assertEqual(frame.pop(primitive_t).unwrap(), int_t)
        self.assertEqual(frame.pop(object_t).unwrap(), null_t)
        self.assertEqual(frame.pop(reference_t).unwrap(), object_t)

        with self.assertRaises(IndexError):
            Frame().pop(top_t).unwrap()
        with self.assertRaises(TypeError):
            Frame([int_t]).pop(float_t).unwrap()

    def test_push(self) -> None:
        frame = Frame()
        frame.push(int_t)
        self.assertEqual(frame.stack, [int_t])
        frame.push(double_t)
        self.assertEqual(frame.stack, [int_t, reserved_t, double_t])

    def test_get(self) -> None:
        frame = Frame([], {0: int_t, 1: double_t, 2: reserved_t, 3: null_t, 4: object_t})
        self.assertEqual(frame.load(0, int_t).unwrap(), int_t)
        self.assertEqual(frame.load(0, int_t).unwrap(), int_t)
        self.assertEqual(frame.load(0, primitive_t).unwrap(), int_t)
        self.assertEqual(frame.load(1, primitive_t).unwrap(), double_t)
        self.assertEqual(frame.load(2, top_t).unwrap(), reserved_t)
        self.assertEqual(frame.load(3, object_t).unwrap(), null_t)
        self.assertEqual(frame.load(4, reference_t).unwrap(), object_t)

        with self.assertRaises(IndexError):
            frame.load(5, top_t).unwrap()
        with self.assertRaises(TypeError):
            frame.load(4, int_t).unwrap()

    def test_set(self) -> None:
        frame = Frame()
        self.assertIsNone(frame.store(0, int_t).unwrap())
        self.assertEqual(frame.locals, {0: int_t})
        self.assertIsNone(frame.store(1, double_t).unwrap())
        self.assertEqual(frame.locals, {0: int_t, 1: double_t, 2: reserved_t})
        self.assertIsNone(frame.store(3, double_t).unwrap())
        self.assertEqual(frame.locals, {0: int_t, 1: double_t, 2: reserved_t, 3: double_t, 4: reserved_t})
        self.assertEqual(frame.store(3, null_t).unwrap(), double_t)
        self.assertEqual(frame.locals, {0: int_t, 1: double_t, 2: reserved_t, 3: null_t})

        with self.assertRaises(TypeError):
            frame.store(2, int_t).unwrap()

    def test_rload(self) -> None:
        ...  # TODO

    def test_rstore(self) -> None:
        ...  # TODO

    def test_dup(self) -> None:
        frame = Frame([int_t])
        self.assertEqual(frame.dup().unwrap(), int_t)
        self.assertEqual(frame.stack, [int_t, int_t])

        frame = Frame([null_t, int_t])
        self.assertEqual(frame.dup().unwrap(), int_t)
        self.assertEqual(frame.stack, [null_t, int_t, int_t])

        frame = Frame([ReturnAddress(5)])
        self.assertEqual(frame.dup().unwrap(), ReturnAddress(5))
        self.assertEqual(frame.stack, [ReturnAddress(5), ReturnAddress(5)])

        with self.assertRaises(IndexError):
            Frame().dup().unwrap()
        frame = Frame([reserved_t, double_t])
        with self.assertRaises(TypeError):
            frame.dup().unwrap()

    def test_dup_x1(self) -> None:
        frame = Frame([null_t, int_t])
        self.assertEqual(frame.dup_x1().unwrap(), int_t)
        self.assertEqual(frame.stack, [int_t, null_t, int_t])

        frame = Frame([object_t, null_t, int_t])
        self.assertEqual(frame.dup_x1().unwrap(), int_t)
        self.assertEqual(frame.stack, [object_t, int_t, null_t, int_t])

        frame = Frame([int_t, ReturnAddress(5)])
        self.assertEqual(frame.dup_x1().unwrap(), ReturnAddress(5))
        self.assertEqual(frame.stack, [ReturnAddress(5), int_t, ReturnAddress(5)])

        with self.assertRaises(IndexError):
            Frame().dup_x1().unwrap()
        with self.assertRaises(IndexError):
            Frame([int_t]).dup_x1().unwrap()
        frame = Frame([reserved_t, double_t])
        with self.assertRaises(TypeError):
            frame.dup_x1().unwrap()

    def test_dup_x2(self) -> None:
        frame = Frame([object_t, null_t, int_t])
        self.assertEqual(frame.dup_x2().unwrap(), int_t)
        self.assertEqual(frame.stack, [int_t, object_t, null_t, int_t])

        frame = Frame([reserved_t, double_t, int_t])
        self.assertEqual(frame.dup_x2().unwrap(), int_t)
        self.assertEqual(frame.stack, [int_t, reserved_t, double_t, int_t])

        frame = Frame([null_t, reserved_t, double_t, int_t])
        self.assertEqual(frame.dup_x2().unwrap(), int_t)
        self.assertEqual(frame.stack, [null_t, int_t, reserved_t, double_t, int_t])

        frame = Frame([null_t, int_t, ReturnAddress(5)])
        self.assertEqual(frame.dup_x2().unwrap(), ReturnAddress(5))
        self.assertEqual(frame.stack, [ReturnAddress(5), null_t, int_t, ReturnAddress(5)])

        with self.assertRaises(IndexError):
            Frame().dup_x2().unwrap()
        with self.assertRaises(IndexError):
            Frame([int_t]).dup_x2().unwrap()
        with self.assertRaises(IndexError):
            Frame([int_t, int_t]).dup_x2().unwrap()

        frame = Frame([int_t, reserved_t, double_t])
        with self.assertRaises(TypeError):
            frame.dup_x2().unwrap()
        frame = Frame([reserved_t, double_t, null_t, int_t])
        with self.assertRaises(TypeError):
            frame.dup_x2().unwrap()

    def test_dup2(self) -> None:
        frame = Frame([int_t, int_t])
        self.assertEqual(frame.dup2().unwrap(), (int_t, int_t))
        self.assertEqual(frame.stack, [int_t, int_t, int_t, int_t])

        frame = Frame([reserved_t, double_t])
        self.assertEqual(frame.dup2().unwrap(), (reserved_t, double_t))
        self.assertEqual(frame.stack, [reserved_t, double_t, reserved_t, double_t])

        frame = Frame([null_t, int_t, int_t])
        self.assertEqual(frame.dup2().unwrap(), (int_t, int_t))
        self.assertEqual(frame.stack, [null_t, int_t, int_t, int_t, int_t])

        frame = Frame([null_t, int_t, ReturnAddress(5)])
        self.assertEqual(frame.dup2().unwrap(), (int_t, ReturnAddress(5)))
        self.assertEqual(frame.stack, [null_t, int_t, ReturnAddress(5), int_t, ReturnAddress(5)])

        with self.assertRaises(IndexError):
            Frame().dup2().unwrap()
        with self.assertRaises(IndexError):
            Frame([int_t]).dup2().unwrap()
        frame = Frame([reserved_t, double_t, int_t])
        with self.assertRaises(TypeError):
            frame.dup2().unwrap()

    def test_dup2_x1(self) -> None:
        frame = Frame([null_t, int_t, int_t])
        self.assertEqual(frame.dup2_x1().unwrap(), (int_t, int_t))
        self.assertEqual(frame.stack, [int_t, int_t, null_t, int_t, int_t])

        frame = Frame([int_t, reserved_t, double_t])
        self.assertEqual(frame.dup2_x1().unwrap(), (reserved_t, double_t))
        self.assertEqual(frame.stack, [reserved_t, double_t, int_t, reserved_t, double_t])

        frame = Frame([object_t, null_t, int_t, int_t])
        self.assertEqual(frame.dup2_x1().unwrap(), (int_t, int_t))
        self.assertEqual(frame.stack, [object_t, int_t, int_t, null_t, int_t, int_t])

        frame = Frame([null_t, int_t, ReturnAddress(5)])
        self.assertEqual(frame.dup2_x1().unwrap(), (int_t, ReturnAddress(5)))
        self.assertEqual(frame.stack, [int_t, ReturnAddress(5), null_t, int_t, ReturnAddress(5)])

        with self.assertRaises(IndexError):
            Frame().dup2_x1().unwrap()
        with self.assertRaises(IndexError):
            Frame([int_t]).dup2_x1().unwrap()
        with self.assertRaises(IndexError):
            Frame([int_t, int_t]).dup2_x1().unwrap()

        frame = Frame([reserved_t, double_t, int_t])
        with self.assertRaises(TypeError):
            frame.dup2_x1().unwrap()
        frame = Frame([reserved_t, double_t, int_t, int_t])
        with self.assertRaises(TypeError):
            frame.dup2_x1().unwrap()

    def test_dup2_x2(self) -> None:
        frame = Frame([object_t, null_t, int_t, int_t])
        self.assertEqual(frame.dup2_x2().unwrap(), (int_t, int_t))
        self.assertEqual(frame.stack, [int_t, int_t, object_t, null_t, int_t, int_t])

        frame = Frame([null_t, int_t, reserved_t, double_t])
        self.assertEqual(frame.dup2_x2().unwrap(), (reserved_t, double_t))
        self.assertEqual(frame.stack, [reserved_t, double_t, null_t, int_t, reserved_t, double_t])

        frame = Frame([reserved_t, double_t, reserved_t, double_t])
        self.assertEqual(frame.dup2_x2().unwrap(), (reserved_t, double_t))
        self.assertEqual(frame.stack, [reserved_t, double_t, reserved_t, double_t, reserved_t, double_t])

        frame = Frame([float_t, object_t, null_t, int_t, int_t])
        self.assertEqual(frame.dup2_x2().unwrap(), (int_t, int_t))
        self.assertEqual(frame.stack, [float_t, int_t, int_t, object_t, null_t, int_t, int_t])

        frame = Frame([object_t, null_t, int_t, ReturnAddress(5)])
        self.assertEqual(frame.dup2_x2().unwrap(), (int_t, ReturnAddress(5)))
        self.assertEqual(frame.stack, [int_t, ReturnAddress(5), object_t, null_t, int_t, ReturnAddress(5)])

        with self.assertRaises(IndexError):
            Frame().dup2_x2().unwrap()
        with self.assertRaises(IndexError):
            Frame([int_t]).dup2_x2().unwrap()
        with self.assertRaises(IndexError):
            Frame([int_t, int_t]).dup2_x2().unwrap()
        with self.assertRaises(IndexError):
            Frame([int_t, int_t, int_t]).dup2_x2().unwrap()

        frame = Frame([int_t, reserved_t, double_t, int_t])
        with self.assertRaises(TypeError):
            frame.dup2_x2().unwrap()
        frame = Frame([reserved_t, double_t, int_t, int_t, int_t])
        with self.assertRaises(TypeError):
            frame.dup2_x2().unwrap()

    def test_swap(self) -> None:
        frame = Frame([float_t, int_t])
        self.assertEqual(frame.swap().unwrap(), (float_t, int_t))
        self.assertEqual(frame.stack, [int_t, float_t])

        frame = Frame([ReturnAddress(5), int_t])
        self.assertEqual(frame.swap().unwrap(), (ReturnAddress(5), int_t))
        self.assertEqual(frame.stack, [int_t, ReturnAddress(5)])

        with self.assertRaises(IndexError):
            Frame().swap().unwrap()
        with self.assertRaises(IndexError):
            Frame([int_t]).swap().unwrap()
        frame = Frame([reserved_t, double_t])
        with self.assertRaises(TypeError):
            frame.swap().unwrap()

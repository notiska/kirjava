#!/usr/bin/env python3

from __future__ import annotations

import inspect
import os
import unittest
from io import BytesIO
from typing import IO, Iterator

from kirjava.classfile.fmt import ClassFile


class TestClassFile(unittest.TestCase):

    def setUp(self) -> None:
        self.files = []

        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        classes = os.path.join(base, "classes/")
        # samples = os.path.join(base, "samples")

        if os.path.exists(classes):
            for root, dirs, files in os.walk(classes):
                for file in files:
                    if not file.endswith(".class"):
                        continue
                    self.files.append(os.path.join(root, file))

    def test_symmetric_read_write(self) -> None:
        if not self.files:
            self.skipTest("No test class files found.")

        for file in self.files:
            with self.subTest("Read file", file=file):
                stream: IO[bytes]  # mypy

                with open(file, "rb") as stream:
                    data = stream.read()
                cf, meta = ClassFile.read(BytesIO(data))
                stream = BytesIO()
                cf.write(stream)
                final = stream.getvalue()

                self.assertEqual(len(data), len(final))
                for index, (byte_a, byte_b) in enumerate(zip(data, final)):
                    if byte_a != byte_b:
                        self.fail(f"Byte mismatch at index {index}: {byte_a} != {byte_b}")

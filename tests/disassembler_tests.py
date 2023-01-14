#!/usr/bin/env python3

"""
Tests that the disassembler produces the correct output.
"""

import os
import unittest

import kirjava


class TestSimple(unittest.TestCase):
    """
    Simple disassembler tests.
    """

    def setUp(self) -> None:
        directory = os.path.dirname(__file__)

        with open(os.path.join(directory, "classes", "simple", "HelloWorld.class"), "rb") as stream:
            self.hello_world_class = kirjava.ClassFile.read(stream)

    def test_hello_world(self) -> None:
        """
        Disassembles the main method in the simple hello world class.
        """

        graph = kirjava.disassemble(self.hello_world_class.get_method("main"))

        self.assertEqual(0, len(graph.in_edges(graph.entry_block)))
        self.assertEqual(1, len(graph.out_edges(graph.entry_block)))

        self.assertEqual(graph.return_block, graph.out_edges(graph.entry_block)[0].to)

        self.assertEqual(3, len(graph.entry_block))

        self.assertEqual(kirjava.instructions.getstatic, graph.entry_block[0])
        self.assertEqual(kirjava.instructions.ldc, graph.entry_block[1])
        self.assertEqual(kirjava.instructions.invokevirtual, graph.entry_block[2])

    # TODO: Test invalid jumps
    # TODO: Test disassembler removes jump offsets

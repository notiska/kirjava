#!/usr/bin/env python3

from __future__ import annotations

import unittest

from kirjava.visitor import *


class TestVisitors(unittest.TestCase):

    def test_add_remove(self) -> None:
        """
        Tests that the add and remove methods work correctly.
        """

        visited = False

        class TestVisitable(Visitable):
            def visit(self, visitor: Visitor["TestVisitable"], visitors: Visitors) -> None:
                visitor.visit_start(self)
                visitor.visit_end(self)

        class TestVisitor(Visitor[TestVisitable]):
            type = TestVisitable

            def visit_start(self, inst: TestVisitable) -> None:
                nonlocal visited
                visited = True

        visitors = Visitors()
        visitor = TestVisitor()

        visitors.add(visitor)
        visitors.visit(TestVisitable())
        self.assertTrue(visited)
        visited = False
        visitors.remove(visitor)
        visitors.visit(TestVisitable())
        self.assertFalse(visited)

    def test_empty(self) -> None:
        """
        Tests that the visit code still runs with no visitors present.
        """

        visited = False

        class TestVisitable(Visitable):
            def visit(self, visitor: Visitor["TestVisitable"], visitors: Visitors) -> None:
                nonlocal visited
                visitor.visit_start(self)
                visited = True
                visitor.visit_end(self)

        Visitors().visit(TestVisitable())
        self.assertTrue(visited)

    def test_subclasses(self) -> None:
        """
        Tests that the visitors work correctly with subclassing.
        """

        visited_a = False
        visited_b = False

        class TestVisitableA(Visitable):
            def visit(self, visitor: Visitor["TestVisitableA"], visitors: Visitors) -> None:
                visitor.visit_start(self)
                visitor.visit_end(self)

        class TestVisitableB(TestVisitableA):
            def visit(self, visitor: Visitor["TestVisitableB"], visitors: Visitors) -> None:
                visitor.visit_start(self)
                visitor.visit_end(self)

        class TestVisitorA(Visitor[TestVisitableA]):
            type = TestVisitableA

            def visit_start(self, inst: TestVisitableA) -> None:
                nonlocal visited_a
                visited_a = True

        class TestVisitorB(Visitor[TestVisitableB]):
            type = TestVisitableB

            def visit_start(self, inst: TestVisitableB) -> None:
                nonlocal visited_b
                visited_b = True

        visitors = Visitors()
        visitors.add(TestVisitorA())
        visitors.add(TestVisitorB())

        visitors.visit(TestVisitableA())
        self.assertTrue(visited_a)
        self.assertFalse(visited_b)
        visited_a = False
        visitors.visit(TestVisitableB())
        self.assertTrue(visited_a)
        self.assertTrue(visited_b)

    def test_recursive_simple(self) -> None:
        """
        Tests that the visitors cannot be recursively visited, with a simple case.
        """

        class TestVisitable(Visitable):
            def visit(self, visitor: Visitor["TestVisitable"], visitors: Visitors) -> None:
                visitor.visit_start(self)
                visitors.visit(self)
                visitor.visit_end(self)

        with self.assertRaises(ValueError):
            Visitors().visit(TestVisitable())

    def test_recursive_complex(self) -> None:
        """
        Tests that the visitors cannot be recursively visited, with a more complex case.
        """

        class TestVisitableA(Visitable):

            next: "TestVisitableB"

            def visit(self, visitor: Visitor["TestVisitableA"], visitors: Visitors) -> None:
                visitor.visit_start(self)
                visitors.visit(self.next)
                visitor.visit_end(self)

        class TestVisitableB(Visitable):

            next: "TestVisitableC"

            def visit(self, visitor: Visitor["TestVisitableB"], visitors: Visitors) -> None:
                visitor.visit_start(self)
                visitors.visit(self.next)
                visitor.visit_end(self)

        class TestVisitableC(Visitable):

            next: TestVisitableA

            def visit(self, visitor: Visitor["TestVisitableC"], visitors: Visitors) -> None:
                visitor.visit_start(self)
                visitors.visit(self.next)
                visitor.visit_end(self)

        a = TestVisitableA()
        b = TestVisitableB()
        c = TestVisitableC()

        a.next = b
        b.next = c
        c.next = a

        with self.assertRaises(ValueError):
            Visitors().visit(a)

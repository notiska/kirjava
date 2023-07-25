#!/usr/bin/env python3

__all__ = (
    "InvokeExpression", "InvokeStaticExpression",
    "InvokeStatement", "InvokeStaticStatement",
)

"""
Invocation related IR expressions/statements.
"""

from typing import Iterable

from .cast import TypeCastExpression
from ...abc import Expression, Statement, Value
from ...constants import MethodRef
from ...types import Type


class InvokeExpression(Expression):
    """
    A virtual invocation expression.
    """

    __slots__ = ("target", "arguments", "reference")

    def __init__(self, target: Value, arguments: Iterable[Value], reference: MethodRef) -> None:
        """
        :param target: The instance to invoke the method on.
        :param arguments: The arguments to the method.
        :param reference: The reference to the method.
        """

        self.target = target
        self.arguments = tuple(arguments)
        self.reference = reference

    def __repr__(self) -> str:
        return "<InvokeExpression(target=%r, arguments=%r, reference=%r) at %x>" % (
            self.target, self.arguments, self.reference, id(self),
        )

    def __str__(self) -> str:
        if isinstance(self.target, TypeCastExpression):
            return "(%s).%s(%s)" % (self.target, self.reference.name, ", ".join(map(str, self.arguments)))
        return "%s.%s(%s)" % (self.target, self.reference.name, ", ".join(map(str, self.arguments)))

    def get_type(self) -> Type:
        return self.reference.return_type


class InvokeStaticExpression(Expression):
    ...  # TODO


class InvokeStatement(Statement):
    """
    A virtual invocation statement, either there is no return value or it isn't used.
    """

    __slots__ = ("target", "arguments", "reference")

    def __init__(self, target: Value, arguments: Iterable[Value], reference: MethodRef) -> None:
        """
        :param target: The instance to invoke the method on.
        :param arguments: The arguments to the method.
        :param reference: The reference to the method.
        """

        self.target = target
        self.arguments = tuple(arguments)
        self.reference = reference

    def __repr__(self) -> str:
        return "<InvokeStatement(target=%r, arguments=%r, reference=%r) at %x>" % (
            self.target, self.arguments, self.reference, id(self),
        )

    def __str__(self) -> str:
        if isinstance(self.target, TypeCastExpression):
            return "(%s).%s(%s)" % (self.target, self.reference.name, ", ".join(map(str, self.arguments)))
        return "%s.%s(%s)" % (self.target, self.reference.name, ", ".join(map(str, self.arguments)))


class InvokeStaticStatement(Statement):
    ...  # TODO

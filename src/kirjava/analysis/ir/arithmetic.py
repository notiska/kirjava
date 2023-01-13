#!/usr/bin/env python3

"""
Arithmetic related IR expressions, includes comparisons.
"""

from abc import ABC

from ...abc import Expression, Value
from ...types import BaseType


class UnaryExpression(Expression, ABC):
    """
    An expression that takes in one value.
    """

    def __init__(self, value: Value) -> None:
        """
        :param value: The value to operate on.
        """

        self.value = value

    def __repr__(self) -> str:
        return "<%s(value=%r) at %x>" % (self.__class__.__name__, self.value, id(self))

    def get_type(self) -> BaseType:
        return self.value.get_type()


class BinaryExpression(Expression, ABC):
    """
    An arithmetic expression that takes in two values.
    """

    def __init__(self, left: Value, right: Value) -> None:
        """
        :param left: The left value.
        :param right: The right value.
        """

        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return "<%s(left=%r, right=%r) at %x>" % (self.__class__.__name__, self.left, self.right, id(self))

    def get_type(self) -> BaseType:
        return self.left.get_type()  # TODO: Merge types


# ------------------------------ Arithmetic ------------------------------ #

class AdditionExpression(BinaryExpression):
    """
    Adds two values.
    """

    def __str__(self) -> str:
        return "%s + %s" % (self.left, self.right)


class SubtractionExpression(BinaryExpression):
    """
    Subtracts two values.
    """

    def __str__(self) -> str:
        return "%s - %s" % (self.left, self.right)


class MultiplicationExpression(BinaryExpression):
    """
    Multiplies two values.
    """

    def __str__(self) -> str:
        return "%s * %s" % (self.left, self.right)


class DivisionExpression(BinaryExpression):
    """
    Divides two values.
    """

    def __str__(self) -> str:
        return "%s / %s" % (self.left, self.right)


class ModuloExpression(BinaryExpression):
    """
    Gets the remainder of two values.
    """

    def __str__(self) -> str:
        return "%s %% %s" % (self.left, self.right)


class NegationExpression(UnaryExpression):
    """
    Negates a value.
    """

    def __str__(self) -> str:
        return "-%s" % self.value


class ShiftLeftExpression(BinaryExpression):
    """
    A binary shift left expression.
    """

    def __str__(self) -> str:
        return "%s << %s" % (self.left, self.right)


class ShiftRightExpression(BinaryExpression):
    """
    A binary shift right expression.
    """

    def __str__(self) -> str:
        return "%s >> %s" % (self.left, self.right)


class UnsignedShiftRightExpression(BinaryExpression):
    """
    A binary shift right expression, doesn't conserve the sign.
    """

    def __str__(self) -> str:
        return "%s >>> %s" % (self.left, self.right)


class BitwiseAndExpression(BinaryExpression):
    """
    A bitwise and between two values.
    """

    def __str__(self) -> str:
        return "%s & %s" % (self.left, self.right)


class BitwiseOrExpression(BinaryExpression):
    """
    A bitwise or between two values.
    """

    def __str__(self) -> str:
        return "%s | %s" % (self.left, self.right)


class BitwiseXorExpression(BinaryExpression):
    """
    A bitwise xor between two values.
    """

    def __str__(self) -> str:
        return "%s ^ %s" % (self.left, self.right)


# ------------------------------ Comparisons ------------------------------ #

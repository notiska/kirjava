#!/usr/bin/env python3

__all__ = (
    "UnaryExpression", "BinaryExpression",
    "AdditionExpression", "SubtractionExpression", "MultiplicationExpression", "DivisionExpression", "ModuloExpression",
    "NegationExpression",
    "ShiftLeftExpression", "ShiftRightExpression", "UnsignedShiftRightExpression",
    "BitwiseAndExpression", "BitwiseOrExpression", "BitwiseXorExpression",
)

"""
Arithmetic related IR expressions, includes comparisons.
"""

from ...abc import Expression, Value
from ...types import Type


class UnaryExpression(Expression):
    """
    An expression that takes in one value.
    """

    precedence: int = ...  # Higher means it binds earlier
    operator: str = ...

    def __init__(self, value: Value) -> None:
        """
        :param value: The value to operate on.
        """

        self.value = value

    def __repr__(self) -> str:
        return "<%s(value=%r) at %x>" % (type(self).__name__, self.value, id(self))

    def __str__(self) -> str:
        if (
            isinstance(self.value, BinaryExpression) or
            (isinstance(self.value, UnaryExpression) and self.value.precedence < self.precedence)
        ):
            return "%s(%s)" % (self.operator, self.value)
        return "%s%s" % (self.operator, self.value)

    def get_type(self) -> Type:
        return self.value.get_type()


class BinaryExpression(Expression):
    """
    An arithmetic expression that takes in two values.
    """

    precedence: int = ...
    operator: str = ...

    def __init__(self, left: Value, right: Value) -> None:
        """
        :param left: The left value.
        :param right: The right value.
        """

        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return "<%s(left=%r, right=%r) at %x>" % (type(self).__name__, self.left, self.right, id(self))

    def __str__(self) -> str:
        left = self.left
        right = self.right

        if isinstance(left, BinaryExpression) and left.precedence < self.precedence:
            left = "(%s)" % left
        if isinstance(right, BinaryExpression) and right.precedence < self.precedence:
            right = "(%s)" % right

        return "%s %s %s" % (left, self.operator, right)

    def get_type(self) -> Type:
        return self.left.get_type()  # TODO: Merge types


# ------------------------------ Arithmetic ------------------------------ #

class AdditionExpression(BinaryExpression):
    """
    Adds two values.
    """

    precedence: int = 2
    operator = "+"

    def __str__(self) -> str:
        return "%s + %s" % (self.left, self.right)


class SubtractionExpression(BinaryExpression):
    """
    Subtracts two values.
    """

    precedence: int = 2
    operator = "-"


class MultiplicationExpression(BinaryExpression):
    """
    Multiplies two values.
    """

    precedence: int = 3
    operator = "*"


class DivisionExpression(BinaryExpression):
    """
    Divides two values.
    """

    precedence: int = 3
    operator = "/"


class ModuloExpression(BinaryExpression):
    """
    Gets the remainder of two values.
    """

    precedence: int = 3
    operator = "%"


class NegationExpression(UnaryExpression):
    """
    Negates a value.
    """

    precedence: int = 5
    operator = "-"


class ShiftLeftExpression(BinaryExpression):
    """
    A binary shift left expression.
    """

    precedence = 1
    operator = "<<"


class ShiftRightExpression(BinaryExpression):
    """
    A binary shift right expression.
    """

    precedence = 1
    operator = ">>"


class UnsignedShiftRightExpression(BinaryExpression):
    """
    A binary shift right expression, doesn't conserve the sign.
    """

    precedence = 1
    operator = ">>>"


class BitwiseAndExpression(BinaryExpression):
    """
    A bitwise and between two values.
    """

    precedence = 0
    operator = "&"


class BitwiseOrExpression(BinaryExpression):
    """
    A bitwise or between two values.
    """

    precedence = 0
    operator = "|"


class BitwiseXorExpression(BinaryExpression):
    """
    A bitwise xor between two values.
    """

    precedence = 0
    operator = "^"


# ------------------------------ Comparisons ------------------------------ #

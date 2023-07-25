#!/usr/bin/env python3

__all__ = (
    "ArrayLoadExpression", "ArrayLengthExpression", "ArrayStoreStatement"
)

"""
Array related IR expressions/statements.
"""

from ... import types
from ...abc import Expression, Statement, Value
from ...types import Type


class ArrayLoadExpression(Expression):
    """
    Loads a value from an array.
    """

    def __init__(self, array: Value, index: Value) -> None:
        """
        :param array: The array to load from.
        :param index: The index to load from.
        """

        self.array = array
        self.index = index

    def __repr__(self) -> str:
        return "<ArrayLoadExpression(array=%r, index=%r) at %x>" % (self.array, self.index, id(self))

    def __str__(self) -> str:
        return "%s[%s]" % (self.array, self.index)

    def get_type(self) -> Type:
        return self.array.get_type().element


class ArrayLengthExpression(Expression):
    """
    Gets the length of an array.
    """

    def __init__(self, array: Value) -> None:
        """
        :param array: The array to get the length of.
        """

        self.array = array

    def __repr__(self) -> str:
        return "<ArrayLengthExpression(array=%r) at %x>" % (self.array, id(self))

    def __str__(self) -> str:
        return "%s.length" % self.array

    def get_type(self) -> Type:
        return types.int_t


class ArrayStoreStatement(Statement):
    """
    Stores a value in an array.
    """

    def __init__(self, array: Value, index: Value, value: Value) -> None:
        """
        :param array: The array to store in.
        :param index: The index to store in.
        :param value: The value to store.
        """

        self.array = array
        self.index = index
        self.value = value

    def __repr__(self) -> str:
        return "<ArrayStoreStatement(array=%r, index=%r, value=%r) at %x>" % (self.array, self.index, self.value, id(self))

    def __str__(self) -> str:
        return "%s[%s] = %s" % (self.array, self.index, self.value)

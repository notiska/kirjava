#!/usr/bin/env python3

__all__ = (
    "ValueCastExpression", "TypeCastExpression", "InstanceOfExpression",
)

"""
Type and value casting IR instructions.
"""

from .arithmetic import BinaryExpression
from ... import types
from ...abc import Expression, Value
from ...types import Primitive, Reference


class ValueCastExpression(Expression):
    """
    Casts a primitive value to another.
    """

    def __init__(self, value: Value, type_: Primitive) -> None:
        """
        :param value: The value to cast.
        :param type_: The type to cast the value to.
        """

        self.value = value
        self.type = type_

    def __repr__(self) -> str:
        return "<ValueCastExpression(value=%r, type=%s) at %x>" % (self.value, self.type, id(self))

    def __str__(self) -> str:
        if isinstance(self.value, BinaryExpression):
            return "(%s)(%s)" % (self.type, self.value)
        return "(%s)%s" % (self.type, self.value)

    def get_type(self) -> Primitive:
        return self.type


class TypeCastExpression(Expression):
    """
    Casts a reference type to another reference type.
    """

    def __init__(self, value: Value, type_: Reference) -> None:
        """
        :param value: The value being checked.
        :param type_: The type to check against.
        """

        self.value = value
        self.type = type_

    def __repr__(self) -> str:
        return "<TypeCastExpression(value=%r, type=%s) at %x>" % (self.value, self.type, id(self))

    def __str__(self) -> str:
        return "(%s)%s" % (self.type, self.value)

    def get_type(self) -> Reference:
        return self.type


class InstanceOfExpression(Expression):
    """
    Checks if a value is an instance of a type.
    """

    def __init__(self, value: Value, type_: Reference) -> None:
        """
        :param value: The value being checked.
        :param type_: The type to check against.
        """

        self.value = value
        self.type = type_

    def __repr__(self) -> str:
        return "<InstanceOfExpression(value=%r, type=%s) at %x>" % (self.value, self.type, id(self))

    def __str__(self) -> str:
        return "%s instanceof %s" % (self.value, self.type)

    def get_type(self) -> Primitive:
        return types.int_t

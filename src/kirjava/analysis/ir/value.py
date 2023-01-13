#!/usr/bin/env python3

"""
IR expressions that create values.
"""

from typing import Iterable

from ...abc import Constant, Expression, Value
from ...types import BaseType
from ...types.reference import ArrayType, ClassOrInterfaceType


class ConstantValue(Value):
    """
    A constant value.
    """

    def __init__(self, constant: Constant) -> None:
        """
        :param constant: The constant value.
        """

        self.constant = constant

    def __repr__(self) -> str:
        return "<ConstantValue(constant=%r) at %x>" % (self.constant, id(self))

    def __str__(self) -> str:
        return str(self.constant)

    def get_type(self) -> BaseType:
        return self.constant.get_type()


class NewExpression(Expression):
    """
    Creates a new object.
    """

    def __init__(self, type_: ClassOrInterfaceType) -> None:
        """
        :param type_: The type of the object to create.
        """

        self.type = type_

    def __repr__(self) -> str:
        return "<NewExpression(type=%s) at %x>" % (self.type, id(self))

    def __str__(self) -> str:
        return "new %s" % self.type

    def get_type(self) -> ClassOrInterfaceType:
        return self.type


class NewArrayExpression(Expression):
    """
    Creates a new array.
    """

    def __init__(self, type_: ArrayType, sizes: Iterable[Value]) -> None:
        """
        :param type_: The array type to initialise.
        :param sizes: The sizes to initialise the array with.
        """

        self.type = type_
        self.sizes = list(sizes)

    def __repr__(self) -> str:
        return "<NewArrayExpression(type=%s, sizes=%r) at %x>" % (self.type, self.sizes, id(self))

    def __str__(self) -> str:
        return "new %s%s" % (
            self.type.set_dimension(self.type.dimension - len(self.sizes)),
            "".join("[%s]" % size for size in self.sizes),
        )

    def get_type(self) -> ArrayType:
        return self.type

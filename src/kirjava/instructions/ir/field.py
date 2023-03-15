#!/usr/bin/env python3

"""
Field related IR expressions/statements.
"""

from .cast import TypeCastExpression
from ...abc import Expression, Statement, Value
from ...types import BaseType
from ...types.reference import ClassOrInterfaceType


class GetFieldExpression(Expression):
    """
    Gets a field, not static.
    """

    def __init__(self, instance: Value, name: str, type_: BaseType) -> None:
        """
        :param instance: The instance to get the field from.
        :param name: The name of the field to get.
        :param type_: The type of the field.
        """

        self.instance = instance
        self.name = name
        self.type = type_

    def __repr__(self) -> str:
        return "<GetFieldExpression(instance=%r, name=%r, type=%s) at %x>" % (
            self.instance, self.name, self.type, id(self),
        )

    def __str__(self) -> str:
        if isinstance(self.instance, TypeCastExpression):
            return "(%s).%s" % (self.instance, self.name)
        return "%s.%s" % (self.instance, self.name)

    def get_type(self) -> BaseType:
        return self.type


class GetStaticFieldExpression(Expression):
    """
    Gets a static field.
    """

    def __init__(self, class_: ClassOrInterfaceType, name: str, type_: BaseType) -> None:
        """
        :param class_: The class to get the field from.
        :param name: The name of the field.
        :param type_: The type of the field.
        """

        self.class_ = class_
        self.name = name
        self.type = type_

    def __repr__(self) -> str:
        return "<GetStaticFieldExpression(class=%s, name=%r, type=%s) at %x>" % (
            self.class_, self.name, self.type, id(self),
        )

    def __str__(self) -> str:
        return "%s.%s" % (self.class_, self.name)

    def get_type(self) -> BaseType:
        return self.type


class SetFieldStatement(Statement):
    """
    Sets a field, not static.
    """

    def __init__(self, instance: Value, name: str, value: Value) -> None:
        """
        :param instance: The instance to set the field on.
        :param name: The name of the field to set.
        :param value: The value to set the field to.
        """

        self.instance = instance
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        return "<SetFieldStatement(instance=%r, name=%r, value=%r) at %x>" % (
            self.instance, self.name, self.value, id(self),
        )

    def __str__(self) -> str:
        if isinstance(self.value, TypeCastExpression):
            return "(%s).%s = %s" % (self.instance, self.name, self.value)
        return "%s.%s = %s" % (self.instance, self.name, self.value)


class SetStaticFieldStatement(Statement):
    """
    Sets a static field.
    """

    def __init__(self, class_: ClassOrInterfaceType, name: str, value: Value) -> None:
        """
        :param class_: The class
        :param name: The name of the field to set.
        :param value: The value to set the field to.
        """

        self.class_ = class_
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        return "<SetStaticFieldStatement(class=%s, name=%r, value=%r) at %x>" % (
            self.class_, self.name, self.value, id(self),
        )

    def __str__(self) -> str:
        return "%s.%s = %s" % (self.class_, self.name, self.value)

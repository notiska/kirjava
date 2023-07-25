#!/usr/bin/env python3

__all__ = (
    "GetFieldExpression", "GetStaticFieldExpression", "SetFieldStatement", "SetStaticFieldStatement",
)

"""
Field related IR expressions/statements.
"""

from .cast import TypeCastExpression
from ...abc import Expression, Statement, Value
from ...constants import FieldRef
from ...types import Type


class GetFieldExpression(Expression):
    """
    Gets a field, not static.
    """

    def __init__(self, target: Value, reference: FieldRef) -> None:
        """
        :param target: The instance to get the field from.
        :param reference: The reference to the field.
        """

        self.target = target
        self.reference = reference

    def __repr__(self) -> str:
        return "<GetFieldExpression(target=%r, reference=%r) at %x>" % (
            self.target, self.reference, id(self),
        )

    def __str__(self) -> str:
        if isinstance(self.target, TypeCastExpression):
            return "(%s).%s" % (self.target, self.reference.name)
        return "%s.%s" % (self.target, self.reference.name)

    def get_type(self) -> Type:
        return self.reference.field_type


class GetStaticFieldExpression(Expression):
    """
    Gets a static field.
    """

    def __init__(self, reference: FieldRef) -> None:
        """
        :param reference: The reference to the field.
        """

        self.reference = reference

    def __repr__(self) -> str:
        return "<GetStaticFieldExpression(reference=%r) at %x>" % (self.reference, id(self))

    def __str__(self) -> str:
        return "%s.%s" % (self.reference.class_, self.reference.name)

    def get_type(self) -> Type:
        return self.reference.field_type


class SetFieldStatement(Statement):
    """
    Sets a field, not static.
    """

    def __init__(self, target: Value, value: Value, reference: FieldRef) -> None:
        """
        :param target: The instance to set the field on.
        :param value: The value to set the field to.
        :param reference: The reference to the field.
        """

        self.target = target
        self.value = value
        self.reference = reference

    def __repr__(self) -> str:
        return "<SetFieldStatement(target=%r, value=%r, reference=%r) at %x>" % (
            self.target, self.value, self.reference, id(self),
        )

    def __str__(self) -> str:
        if isinstance(self.value, TypeCastExpression):
            return "(%s).%s = %s" % (self.target, self.reference.name, self.value)
        return "%s.%s = %s" % (self.target, self.reference.name, self.value)


class SetStaticFieldStatement(Statement):
    """
    Sets a static field.
    """

    def __init__(self, value: Value, reference: FieldRef) -> None:
        """
        :param value: The value to set the field to.
        :param reference: The reference to the field.
        """

        self.value = value
        self.reference = reference

    def __repr__(self) -> str:
        return "<SetStaticFieldStatement(value=%r, reference=%r) at %x>" % (
            self.value, self.reference, id(self),
        )

    def __str__(self) -> str:
        return "%s.%s = %s" % (self.reference.class_, self.reference.name, self.value)

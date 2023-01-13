#!/usr/bin/env python3

"""
IR expressions and statements that reference the local variables.
"""

from ...abc import Expression, Statement, Value
from ...types import BaseType


class GetLocalExpression(Expression):
    """
    Gets the value from a local variable.
    """

    def __init__(self, index: int, value: Value) -> None:
        """
        :param index: The index of the local variable.
        :param value: The value that was in the local variable.
        """

        self.index = index
        self.value = value

    def __repr__(self) -> str:
        return "<GetLocalExpression(index=%i, value=%r) at %x>" % (self.index, self.value, id(self))

    def __str__(self) -> str:
        return "local_%i" % self.index

    def get_type(self) -> BaseType:
        return self.value.get_type()


class SetLocalStatement(Statement):
    """
    Sets a local variable.
    """

    def __init__(self, index: int, value: Value) -> None:
        """
        :param index: The index of the local variable to set.
        :param value: The value to set it to.
        """

        self.index = index
        self.value = value

    def __repr__(self) -> str:
        return "<SetLocalStatement(index=%i, value=%r) at %x>" % (self.index, self.value, id(self))

    def __str__(self) -> str:
        return "local_%i = %s" % (self.index, self.value)


# class IncrementLocalStatement(Statement):
#     """
#     Increments a given local variable.
#     """
#
#     def __init__(self, index: int, value: Value) -> None:
#         """
#         :param index: The index of the local variable to increment.
#         :param value: The value to increment the local variable by.
#         """
#
#         self.index = index
#         self.value = value
#
#     def __repr__(self) -> str:
#         return "<IncrementLocalStatement(index=%i, value=%r) at %x>" % (self.index, self.value, id(self))
#
#     def __str__(self) -> str:
#         return "local_%i += %s" % (self.index, self.value)

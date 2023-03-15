#!/usr/bin/env python3

__all__ = (
    "Value", "Expression", "Statement",
)

"""
Abstract base classes for the IR.
"""

import typing

from .. import types

if typing.TYPE_CHECKING:
    from ..types import BaseType
    from ..types.primitive import VoidType


class Value:
    """
    Any kind of value present in the IR.
    """

    def get_type(self) -> "BaseType":
        """
        :return: The output type of this value.
        """

        ...


class Expression(Value):
    """
    A base expression.
    """

    ...


class Statement(Expression):
    """
    A base statement.
    """

    def get_type(self) -> "VoidType":
        return types.void_t

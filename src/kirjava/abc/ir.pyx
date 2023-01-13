# cython: language=c
# cython: language_level=3

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


cdef class Value:
    """
    Any kind of value present in the IR.
    """

    def get_type(self) -> "BaseType":
        """
        :return: The output type of this value.
        """

        ...


cdef class Expression(Value):
    """
    A base expression.
    """

    ...


cdef class Statement(Expression):
    """
    A base statement.
    """

    def get_type(self) -> "VoidType":
        return types.void_t

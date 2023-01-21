# cython: language=c
# cython: language_level=3

__all__ = (
    "Constant",
)

import typing
from typing import Any

if typing.TYPE_CHECKING:
    from ..types import BaseType


cdef class Constant:
    """
    A Java constant (some piece of information that is constant).
    """

    property value:
        """
        The actual value of this constant.
        """

        def __get__(self) -> object:
            ...

    def __repr__(self) -> str:
        return "<%s(%r) at %x>" % (self.__class__.__name__, self.value, id(self))

    def __str__(self) -> str:
        return repr(self.value)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and other.value == self.value  # or other == self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def get_type(self) -> "BaseType":
        """
        :return: The type of this constant, if applicable.
        """

        raise TypeError("Cannot convert %r into a Java type." % self)  # By default

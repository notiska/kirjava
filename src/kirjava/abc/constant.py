#!/usr/bin/env python3

__all__ = (
    "Constant",
)

import typing
from typing import Any

if typing.TYPE_CHECKING:
    from ..types import BaseType


class Constant:
    """
    A Java constant (some piece of information that is constant).
    """

    def __init__(self, value: Any) -> None:
        self.value = value
        self._hash = hash(self.value)

    def __repr__(self) -> str:
        return "<%s(%r) at %x>" % (self.__class__.__name__, self.value, id(self))

    def __str__(self) -> str:
        return repr(self.value)

    def __eq__(self, other: Any) -> bool:
        return type(other) is type(self) and other.value == self.value  # or other == self.value

    def __hash__(self) -> int:
        return self._hash

    def get_type(self) -> "BaseType":
        """
        :return: The type of this constant, if applicable.
        """

        raise TypeError("Cannot convert %r into a Java type." % self)  # By default

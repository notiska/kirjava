#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Array", "Object",
)

"""
Models for reference values (objects).
"""

from typing import Iterable

from . import Value
from ..types import Array as ArrayType, Class


class Array(Value):
    """
    An array value.

    Used to store partial or complete information about an array.

    Attributes
    ----------
    size: Value
        The size of the array.
    elements: list[Value]
        The elements in the array.
    """

    __slots__ = ("type", "size", "elements")

    def __init__(self, type: ArrayType, size: Value, elements: Iterable[Value] | None = None) -> None:
        self.type = type
        self.size = size
        self.elements: list[Value] = []

        if elements is not None:
            self.elements.extend(elements)

    def __repr__(self) -> str:
        elements_str = ", ".join(map(str, self.elements))
        return f"<Array(type={self.type!s}, size={self.size}, elements=[{elements_str}])>"

    def __str__(self) -> str:
        return str(self.type)  # FIXME


class Object(Value):
    """
    An object value.

    Attributes
    ----------
    type: Class
        The type of this object.
    """

    __slots__ = ("type",)

    # TODO: We could also store information about (potential) fields and methods.

    def __init__(self, type: Class) -> None:
        self.type = type

    def __repr__(self) -> str:
        return f"<Object(type={self.type!s})>"

    def __str__(self) -> str:
        return self.type.name

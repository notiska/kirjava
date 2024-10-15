#!/usr/bin/env python3

__all__ = (
    "Array", "Object",
)

"""
Models for reference values (objects).
"""

from . import Value
from ..types import Array as ArrayType, Class


class Array(Value):
    """
    An array value.

    Used to store partial or complete information about an array.

    Attributes
    ----------
    sizes: tuple[Value, ...]
        The sizes of this array.
    """

    __slots__ = ("type", "sizes")

    # TODO: We could also store elements, to some degree.

    def __init__(self, type_: ArrayType, sizes: tuple[Value, ...]) -> None:
        self.type = type_
        self.sizes = sizes

    def __repr__(self) -> str:
        return f"<Array(type={self.type!s}, sizes={self.sizes!r})>"

    def __str__(self) -> str:
        sizes = []
        type_ = self.type
        for size in self.sizes:
            # Mypy issue again, the type is checked properly in the loop, though.
            type_ = type_.element  # type: ignore[attr-defined]
            sizes.append(f"[{size}]")
            if not isinstance(type_, ArrayType):
                break
        return f"{self.type!s}{"".join(sizes)}"


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

    def __init__(self, type_: Class) -> None:
        self.type = type_

    def __repr__(self) -> str:
        return f"<Object(type={self.type!s})>"

    def __str__(self) -> str:
        return self.type.name

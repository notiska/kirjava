#!/usr/bin/env python3

__all__ = (
    "constants", "objects", "variable",
    "Value",
)

import typing

if typing.TYPE_CHECKING:
    from ..types import Type


class Value:
    """
    A model value.

    Attributes
    ----------
    type: Type
        The type of value.

    Methods
    -------
    cast(self, type_: Type) -> Value
        Casts this value to another type.
    """

    __slots__ = ()

    type: "Type"

    def __repr__(self) -> str:
        return f"<Value(type={self.type!s})>"

    def cast(self, type_: "Type") -> "Value":
        """
        Casts this value to another type.

        Parameters
        ----------
        type_: Type
            The type to cast this value to.

        Returns
        -------
        Value
            The new value.

        Raises
        ------
        ValueError
            If this value cannot be cast to the given type.
        """

        raise ValueError(f"cannot cast {self!r} to {type_!s}")

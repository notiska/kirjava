#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "constants", "objects", "variable",
    "Value",
)

import typing

if typing.TYPE_CHECKING:
    from ..types import Type


class Value:
    """
    A value.

    Attributes
    ----------
    type: Type
        The type of this value.
    """

    __slots__ = ()

    type: "Type"

    def __repr__(self) -> str:
        raise NotImplementedError(f"repr() is not implemented for {type(self)!r}")

    def __str__(self) -> str:
        raise NotImplementedError(f"str() is not implemented for {type(self)!r}")

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError(f"== is not implemented for {type(self)!r}")

    # TODO
    # def cast(self, type_: "Type") -> "Value":
    #     """
    #     Casts this value to another type.

    #     Parameters
    #     ----------
    #     type_: Type
    #         The type to cast this value to.

    #     Returns
    #     -------
    #     Value
    #         The new value.

    #     Raises
    #     ------
    #     ValueError
    #         If this value cannot be cast to the given type.
    #     """

    #     raise ValueError(f"cannot cast {self!r} to {type_!s}")

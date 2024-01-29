#!/usr/bin/env python3

__all__ = (
    "Source", "Offset",
)

from typing import Any


class Source:
    """
    The source of a particular value (deliberately quite generic).
    """

    __slots__ = ()


class Offset(Source):
    """
    An instruction offset used in Uninitialized verification types.
    """

    __slots__ = ("offset",)

    def __init__(self, offset: int) -> None:
        self.offset = offset

    def __repr__(self) -> str:
        return "<Offset(%i)>" % self.offset

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Offset) and other.offset == self.offset

    def __hash__(self) -> int:
        return self.offset


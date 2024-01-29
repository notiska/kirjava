#!/usr/bin/env python3

__all__ = (
    "Constant",
)

import typing
from typing import Any, Optional

from . import Source

if typing.TYPE_CHECKING:
    from ..types import Type


class Constant(Source):
    """
    A Java constant (some piece of information that is constant).
    """

    __slots__ = ("value", "_hash")

    type: Optional["Type"] = None

    def __init__(self, value: Any) -> None:
        self.value = value
        self._hash = hash(self.value)

    def __repr__(self) -> str:
        return "<%s(%r)>" % (type(self).__name__, self.value)

    def __str__(self) -> str:
        return repr(self.value)

    def __eq__(self, other: Any) -> bool:
        return type(other) is type(self) and other.value == self.value  # or other == self.value

    def __hash__(self) -> int:
        return self._hash

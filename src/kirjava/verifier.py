#!/usr/bin/env python3

__all__ = (
    "Error", "VerifyError",
    "TypeChecker",
)

"""
Verifier implementation, verifies that graphs and/or methods are valid.
"""

import typing
from typing import Any, Iterable, List, Optional

from .abc import Source
from .types import top_t, Class, Type, Verification

if typing.TYPE_CHECKING:
    from .analysis import InsnGraph


def verify_graph(graph: "InsnGraph") -> None:
    """
    Verifies that the structure of a graph is valid.

    :param graph: The graph to verify.
    :raises VerifyError: If the graph is invalid.
    """

    ...


class Error:
    """
    An individual error.
    """

    __slots__ = ("message", "source", "_hash")

    def __init__(self, message: str, source: Optional[Source] = None) -> None:
        self.message = message
        self.source = source

        self._hash = hash((self.message, self.source))

    def __repr__(self) -> str:
        return "<Error(message=%r, source=%r)>" % (self.message, self.source)

    def __str__(self) -> str:
        if self.source is not None:
            return "%s: %s" % (self.source, self.message)
        return self.message

    def __eq__(self, other: Any) -> bool:
        return type(other) is Error and other.message == self.message and other.source == self.source

    def __hash__(self) -> int:
        return self._hash


class VerifyError(Exception):
    """
    Raised when verification fails.
    """

    __slots__ = ("errors",)

    def __init__(self, errors: Iterable[Error]) -> None:
        self.errors = tuple(errors)
        super().__init__("Verification failed with %i error(s)." % len(self.errors))

    def __repr__(self) -> str:
        return "<VerifyError(errors=%r)>" % (self.errors,)

    def __str__(self) -> str:
        return "\n".join(map(str, self.errors))


class TypeChecker:
    """
    A type checker implementation.
    """

    __slots__ = ("errors",)

    def __init__(self) -> None:
        self.errors: List[Error] = []

    def check(self, expected: Verification, actual: Type) -> bool:
        """
        Checks if the actual type matches the expected type.
        """

        return expected is actual or expected == actual

    def merge(self, type_a: Type, type_b: Type) -> Type:
        """
        Merges two types together.
        """

        if type_a is type_b:
            return type_a
        elif not type_a.mergeable(type_b):
            return top_t

        ...  # TODO: Proper reference type merging?

        return type_b

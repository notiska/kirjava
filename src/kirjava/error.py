#!/usr/bin/env python3

__all__ = (
    "ClassFormatError",
    "MergeError",
    "MergeDepthError",
    "MergeMissingLocalError",
    "UnresolvableSubroutineError",
)

"""
Various exceptions raised by kirjava.
"""

import typing
from typing import Optional

if typing.TYPE_CHECKING:
    from .abc import Edge
    from .analysis import Entry, RetEdge
    from .types import Type


class ClassFormatError(Exception):
    """
    Raised when a class file is malformed.
    """

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Malformed class file.")


# ---------------------------------------- Merge errors ---------------------------------------- #

class MergeError(Exception):
    """
    Raised when an illegal frame merge into the same block is attempted.
    """

    def __init__(self, edge: "Edge", message: Optional[str] = None) -> None:
        """
        :param edge: The edge that caused the issue.
        """

        super().__init__(message or ("Illegal frame merge at edge %s." % edge))

        self.edge = edge


class MergeDepthError(MergeError):
    """
    A merge error caused by inconsistent stack depths.
    """

    def __init__(self, edge: "Edge", actual: int, expected: int) -> None:
        """
        :param actual: The actual stack depth that was provided.
        :param expected: The stack depth that was expected.
        """

        super().__init__(
            edge,
            message="Illegal frame merge at edge %s: expected stack depth %i, got %i." % (
                edge, expected, actual,
            ),
        )

        self.actual = actual
        self.expected = expected


class MergeMissingLocalError(MergeError):
    """
    A merge error caused by a local present in one frame not being present in the other.
    """

    def __init__(self, edge: "Edge", index: int, expected: "Type") -> None:
        """
        :param index: The index of the missing local.
        :param expected: The expected type of the missing local.
        """

        super().__init__(
            edge,
            message="Illegal frame merge at edge %s: missing local at index %i, expected type %s." % (
                edge, index, expected,
            ),
        )

        self.index = index
        self.expected = expected


# ---------------------------------------- Subroutine resolution errors ---------------------------------------- #

class UnresolvableSubroutineError(Exception):
    """
    Raised when a subroutine cannot be resolved.
    """

    def __init__(self, edge: "RetEdge", message: Optional[str] = None) -> None:
        super().__init__(message or "Could not resolve subroutine origin at edge %s." % edge)

        self.edge = edge


class NotAReturnAddressError(UnresolvableSubroutineError):
    """
    Raised when the local at the return index is not a return address.
    """

    def __init__(self, edge: "RetEdge", actual: "Entry") -> None:
        super().__init__(
            edge,
            message="Could not resolve subroutine origin at edge %s: expected type returnAddress, got %s." % (
                edge, actual,
            ),
        )

        self.actual = actual


class NotASubroutineError(UnresolvableSubroutineError):
    """
    Raised when the subroutine origin (the jsr edge) just doesn't exist.
    """

    def __init__(self, edge: "RetEdge", origin: "Source") -> None:
        super().__init__(
            edge,
            message="Could not resolve subroutine origin at edge %s: origin %s is not valid." % (
                edge, origin,
            ),
        )

        self.origin = origin
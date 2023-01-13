#!/usr/bin/env python3

__all__ = (
    "VerifyError", "Error",
    "NoTypeChecker", "BasicTypeChecker", "FullTypeChecker",
)

"""
A bytecode verifier implementation.
"""

from enum import Enum
from typing import Any, List, Union

from ._types import *
from ..abc import Source


class Error:
    """
    An error that has occurred during the bytecode analysis, typically due to invalid bytecode.
    """

    __slots__ = ("type", "source", "messages")

    def __init__(self, type_: "Error.Type", source: Union[Source, None], *messages: object) -> None:
        """
        :param type_: The type of error.
        :param source: The source of the error (typically an instruction).
        :param message: Information about the error that occurred.
        """

        self.type = type_
        self.source = source
        self.messages = messages

    def __repr__(self) -> str:
        return "<Error(type=%r, source=%r, messages=%r) at %x>" % (self.type, self.source, self.messages, id(self))

    def __str__(self) -> str:
        if self.source is None:
            return "error %r: %r" % (self.type.value, ", ".join(map(str, self.messages)))
        return "error %r at %s: %r" % (self.type.value, str(self.source), ", ".join(map(str, self.messages)))

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return other.__class__ is Error and other.source == self.source and other.messages == self.messages

    class Type(Enum):
        """
        The type of error, for more specific error handling.
        """

        INVALID_TYPE = "invalid type"
        INVALID_CONSTANT = "invalid constant"
        INVALID_INSTRUCTION = "invalid instruction"

        INVALID_BLOCK = "invalid block"
        INVALID_EDGE = "invalid edge"

        STACK_UNDERFLOW = "stack underflow"
        STACK_OVERFLOW = "stack overflow"
        UNKNOWN_LOCAL = "unknown local"

        INVALID_STACK_MERGE = "invalid stack merge"
        INVALID_LOCALS_MERGE = "invalid locals merge"


class VerifyError(Exception):
    """
    An exception to throw when verification fails.
    """

    def __init__(self, errors: List[Error]) -> None:
        self.errors = []

        for error in errors:
            if not error in self.errors:
                self.errors.append(error)

        super().__init__("%i verification error(s)" % len(self.errors))

    def __repr__(self) -> str:
        return "<VerifyError(errors=%i) at %x>" % (len(self.errors), id(self))

    def __str__(self) -> str:
        return "%i verification error(s):\n%s" % (
            len(self.errors), "\n".join(" - %s" % error for error in self.errors),
        )

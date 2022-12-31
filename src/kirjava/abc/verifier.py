#!/usr/bin/env python3

__all__ = (
    "VerifyError", "Error", "TypeChecker", "Verifier", "NoTypeChecker",
)

"""
A bytecode verifier implementation.
"""

import typing
from abc import abstractmethod, ABC
from typing import Any, List, Tuple, Union

from . import Source

if typing.TYPE_CHECKING:
    from ..types import VerificationType


class VerifyError(Exception):
    """
    An exception to throw when verification fails.
    """

    def __init__(self, errors: List["Error"]) -> None:
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


class Error:
    """
    An error that has occurred during the bytecode analysis, typically due to invalid bytecode.
    """

    def __init__(self, source: Union[Source, None], *messages: Tuple[object, ...]) -> None:
        """
        :param source: The source of the error (typically an instruction).
        :param message: Information about the error that occurred.
        """

        self.source = source
        self.messages = messages

    def __repr__(self) -> str:
        return "<Error(source=%r, messages=%r) at %x>" % (self.source, self.message, id(self))

    def __str__(self) -> str:
        if self.source is None:
            return "error: %r" % (", ".join(map(str, self.messages)))
        return "error at %r: %r" % (str(self.source), ", ".join(map(str, self.messages)))

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return other.__class__ is Error and other.source == self.source and other.messages == self.messages


class TypeChecker(ABC):
    """
    The abstract base class for a type checker implementation. Type checkers are responsible for checking if
    verification types can be merged or if they match certain requirements. It is also responsible for merging them.
    """

    @abstractmethod
    def check_merge(self, expected: Union["VerificationType", None], actual: "VerificationType") -> bool:
        """
        Checks if the two provided types can be merged (AKA are assignable).

        :param expected: The expected type that we should have.
        :param actual: The actual type that we've been given.
        :return: Can the types be merged?
        """

        ...

    @abstractmethod
    def check_reference(self, actual: "VerificationType") -> bool:
        """
        Checks that the provided type is a reference type.

        :param actual: The type to check.
        :return: Is the type a reference type?
        """

        ...

    @abstractmethod
    def check_array(self, actual: "VerificationType") -> bool:
        """
        Checks that the provided type is an array type.

        :param actual: The type to check.
        :return: Is the type assignable to an array type?
        """

        ...

    @abstractmethod
    def check_category(self, actual: "VerificationType", category: int = 2) -> bool:
        """
        Checks that a given type is of a certain category (internal size).

        :param actual: The type to check.
        :param category: The expected category of type.
        :return: Is the type of the correct category?
        """

        ...

    @abstractmethod
    def merge(self, expected: Union["VerificationType", None], actual: "VerificationType") -> "VerificationType":
        """
        Merges the two provided types.

        :param expected: The expected type that we should have.
        :param actual: The actual type that we've been given.
        :return: The merged type.
        """

        ...


class Verifier(ABC):
    """
    The abstract base class for a bytecode verifier implementation.
    """

    ...


class NoTypeChecker(TypeChecker):
    """
    A type checker that does nothing (for no verification).
    """

    def check_merge(self, expected: Union["VerificationType", None], actual: "VerificationType") -> bool:
        return True  # Always assignable

    def check_reference(self, actual: "VerificationType") -> bool:
        return True

    def check_array(self, actual: "VerificationType") -> bool:
        return True

    def check_category(self, actual: "VerificationType", category: int = 2) -> bool:
        return True

    def merge(self, expected: Union["VerificationType", None], actual: "VerificationType") -> "VerificationType":
        return actual  # Assume that the actual type is always correct

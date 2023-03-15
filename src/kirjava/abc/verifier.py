#!/usr/bin/env python3

__all__ = (
    "TypeChecker",
)

"""
Classfile verifier abstract classes.
"""

import typing
from typing import Optional

if typing.TYPE_CHECKING:
    from ..types import VerificationType


class TypeChecker:
    """
    The abstract base class for a type checker implementation. Type checkers are responsible for checking if
    verification types can be merged or if they match certain requirements. It is also responsible for merging them.
    """

    def check_merge(self, expected: Optional["VerificationType"], actual: "VerificationType") -> bool:
        """
        Checks if the two provided types can be merged (AKA are assignable).

        :param expected: The expected type that we should have.
        :param actual: The actual type that we've been given.
        :return: Can the types be merged?
        """

        ...

    def check_reference(self, actual: "VerificationType") -> bool:
        """
        Checks that the provided type is a reference type.

        :param actual: The type to check.
        :return: Is the type a reference type?
        """

        ...

    def check_class(self, actual: "VerificationType") -> bool:
        """
        Checks that the provided type is a class type.

        :param actual: The type to check.
        :return: Is the type assignable to a class type?
        """

        ...

    def check_array(self, actual: "VerificationType") -> bool:
        """
        Checks that the provided type is an array type.

        :param actual: The type to check.
        :return: Is the type assignable to an array type?
        """

        ...

    def check_category(self, actual: "VerificationType", category: int = 2) -> bool:
        """
        Checks that a given type is of a certain category (internal size).

        :param actual: The type to check.
        :param category: The expected category of type.
        :return: Is the type of the correct category?
        """

        ...

    def merge(
            self,
            expected: Optional["VerificationType"],
            actual: "VerificationType",
            *,
            fallback: Optional["VerificationType"] = None,
    ) -> "VerificationType":
        """
        Merges the two provided types.

        :param expected: The expected type that we should have.
        :param actual: The actual type that we've been given.
        :param fallback: A fallback type to use if a merged type could not be determined.
        :return: The merged type.
        """

        ...

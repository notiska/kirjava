#!/usr/bin/env python3

__all__ = (
    "VerifyError", "Error", "Verifier",
)

import typing
from enum import Enum
from typing import Any, Iterable, Optional, Tuple

from ..abc.source import Source
from ..abc.verifier import TypeChecker

if typing.TYPE_CHECKING:
    from ..types import VerificationType


class VerifyError(Exception):
    """
    An exception to throw when verification fails.
    """

    def __init__(self, errors: Iterable["Error"]) -> None:
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
    An error that has occurred during verification.
    """

    def __init__(self, type_: "Error.Type", source: Optional[Source], *messages: object) -> None:
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
        return type(other) is Error and other.source == self.source and other.messages == self.messages

    # ------------------------------ Classes ------------------------------ #

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


class Verifier:
    """
    A verifier, performs certain checks to make sure the classfile is valid and reports any errors.
    """

    @property
    def errors(self) -> Tuple[Error, ...]:
        """
        A copy of the errors reported by this verifier. Not mutable.
        """

        return tuple(self._errors)

    @property
    def has_errors(self) -> bool:
        """
        Does this verifier have errors?
        """

        return bool(self._errors)

    def __init__(self, checker: TypeChecker) -> None:
        """
        :param checker: The type checker implementation this verifier uses.
        """

        self.checker = checker
        self._errors: List[Error] = []

    def raise_(self) -> None:
        """
        Raises an exception if there are verify errors, otherwise, does nothing.
        """

        if self._errors:
            raise VerifyError(self._errors)

    # ------------------------------ Errors ------------------------------ #

    def report(self, error: Error) -> None:
        """
        Reports the provided error.

        :param error: The error to report.
        """

        if not error in self._errors:
            self._errors.append(error)

    def report_invalid_type(
            self,
            source: Optional[Source],
            expected: "VerificationType",
            actual: "VerificationType",
            origin: Optional[Source] = None,
    ) -> None:
        """
        Reports an "invalid type" error.

        :param source: The source that is reporting the error.
        :param expected: The type that was expected.
        :param actual: The type that was actually provided.
        :param origin: The original source of the actual type, if applicable.
        """

        if origin is not None:
            error = Error(
                Error.Type.INVALID_TYPE, source, "expected type %s" % expected, "got %s (via %s)" % (actual, origin),
            )
        else:
            error = Error(Error.Type.INVALID_TYPE, source, "expected type %s" % expected, "got %s" % actual)

        if not error in self._errors:
            self._errors.append(error)

    def report_expected_reference_type(
            self, source: Optional[Source], actual: "VerificationType", origin: Optional[Source],
    ) -> None:
        """
        Reports that a reference type was expected, but not provided.

        :param source: The source that is reporting the error.
        :param actual: The actual type that was provided.
        :param origin: The origin of the actual type.
        """

        if origin is not None:
            error = Error(
                Error.Type.INVALID_TYPE, source, "expected reference type", "got %s (via %s)" % (actual, origin),
            )
        else:
            error = Error(Error.Type.INVALID_TYPE, source, "expected reference type", "got %s" % actual)

        if not error in self._errors:
            self._errors.append(error)

    def report_invalid_type_category(
            self, source: Optional[Source], category: int, actual: "VerificationType", origin: Optional[Source],
    ) -> None:
        """
        Reports that a type does not meet the given category requirements.

        :param source: The source reporting the error.
        :param category: The expected category of the type.
        :param actual: The actual type that was provided.
        :param origin: The origin of the type, if applicable.
        """

        if origin is not None:
            error = Error(
                Error.Type.INVALID_TYPE, source, "expected category %i type" % category, "got %s (via %s)" % (actual, origin),
            )
        else:
            error = Error(Error.Type.INVALID_TYPE, source, "expected category %i type" % category, "got %s" % actual)

        if not error in self._errors:
            self._errors.append(error)

    def report_unknown_local(self, source: Optional[Source], index: int) -> None:
        """
        Reports that a local access was invalid.

        :param source: The source reporting the error.
        :param index: The index of the local that could not be accessed.
        """

        error = Error(Error.Type.UNKNOWN_LOCAL, source, "unknown local at index %i" % index)
        if not error in self._errors:
            self._errors.append(error)

    def report_stack_underflow(self, source: Optional[Source], entries: int) -> None:
        """
        Reports a "stack underflow" error.

        :param source: The source reporting the error.
        :param entries: The number of entries that we underflowed by.
        """

        # FIXME: ^^ grammar check lol

        error = Error(Error.Type.STACK_UNDERFLOW, source, "%i entries" % entries)
        if not error in self._errors:
            self._errors.append(error)

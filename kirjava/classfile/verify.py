#!/usr/bin/env python3

__all__ = (
    "Verifier",
)

import typing
from threading import RLock
from typing import Callable, Optional

if typing.TYPE_CHECKING:
    from .fmt.classfile import ClassFile


class Verifier:
    """
    Class file validity verifier implementation.

    Attributes
    ----------
    check_utf8_null_bytes: bool
        Checks for null bytes in UTF8 constants.
    check_const_vers: bool
        Checks that all constants can exist in the current class file version.
    check_const_types: bool
        Checks that all constants are of the correct type.
    check_access_flags: bool
        Checks that all access flags are valid.
    check_attr_data: bool
        Checks that all attributes are valid.
    check_attr_vers: bool
        Checks that all attributes can exist in the current class file version.
    check_attr_locs: bool
        Checks that all attributes are in the correct locations.
    """

    __slots__ = (
        "check_utf8_null_bytes", "check_const_vers", "check_const_types",
        "check_access_flags",
        "check_attr_data", "check_attr_vers", "check_attr_locs",

        "_errors", "_lock",
    )

    # TODO: Qualified name checks, everywhere.

    def __init__(
            self,
            check_utf8_null_bytes: bool = True,
            check_const_vers:      bool = True,
            check_const_types:     bool = True,
            check_access_flags:    bool = True,
            check_attr_data:       bool = False,
            check_attr_vers:       bool = True,
            check_attr_locs:       bool = True,
    ) -> None:
        self.check_utf8_null_bytes = check_utf8_null_bytes
        self.check_const_vers = check_const_vers
        self.check_const_types = check_const_types

        self.check_access_flags = check_access_flags

        self.check_attr_data = check_attr_data
        self.check_attr_vers = check_attr_vers
        self.check_attr_locs = check_attr_locs

        self._errors: list[Verifier.Error] = []
        self._lock = RLock()

    def verify(self, cf: "ClassFile") -> list["Verifier.Error"]:
        """
        Verifies the class file and returns all collected errors, if any.

        Parameters
        ----------
        cf: ClassFile
            The class file to verify.

        Returns
        -------
        list[Verifier.Error]
            All collected errors.
        """

        with self._lock:  # Thread safety, because "the future is multithreaded".
            self._errors.clear()
            cf.verify(self)
            return self._errors.copy()

    def fatal(self, element: object, message: str, **data: object) -> None:
        """
        Reports a fatal error.
        See `Verifier.Error` for more information.
        """

        with self._lock:
            self._errors.append(Verifier.Error(element, message, fatal=True, **data))

    def error(self, element: object, message: str, **data: object) -> None:
        """
        Reports a non-fatal error.
        See `Verifier.Error` for more information.
        """

        with self._lock:
            self._errors.append(Verifier.Error(element, message, fatal=False, **data))

    # ------------------------------ Classes ------------------------------ #

    class Error:
        """
        Information about a verification error.

        Attributes
        ----------
        element: object
            The element that the error occurred in.
        message: str
            The error message.
        fatal: bool
            Whether this error is integral to the correct parsing of the class file.
        data: dict[str, object]
            Any other data associated with the error.
        """

        __slots__ = ("element", "message", "fatal", "data")

        def __init__(self, element: object, message: str, fatal: bool = True, **data: object) -> None:
            self.element = element
            self.message = message
            self.fatal = fatal
            self.data = data

        def __repr__(self) -> str:
            return (
                f"<Verifier.Error(element={self.element!r}, message={self.message!r}, fatal={self.fatal}, "
                f"data={self.data!r})>"
            )

        def __str__(self) -> str:
            fatal_str = "fatal" if self.fatal else "error"
            return f"{self.element!s} ({fatal_str}): {self.message!s}"

        def __eq__(self, other: object) -> bool:
            return (
                isinstance(other, Verifier.Error) and
                self.element == other.element and
                self.message == other.message and
                self.fatal == other.fatal and
                self.data == other.data
            )

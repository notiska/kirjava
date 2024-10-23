#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    # "ok", "err", "meta",
    "T", "Result", "Ok", "Err",
)

"""
Rust-like results, with added metadata.
Mainly for internal usage.
"""

import logging
import sys
import weakref
from logging import Filter, Logger, LogRecord
from types import TracebackType
from typing import Any, Generic, TypeVar

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

T = TypeVar("T")


# TODO: Waiting for generic functions, I guess...

# def ok(value: T) -> "Result[T]":
#     """
#     Shorthand for creating a result with a valid value.
#     """

#     return Result[T](value)


# def err(error: Exception) -> "Result[T]":
#     """
#     Shorthand for creating a result with an error.
#     """

#     return Result[T]().err(error)


# def meta(name: str, element: object | None = None) -> "Result[T]":
#     """
#     Shorthand for creating a result with metadata info.

#     Parameters
#     ----------
#     name: str
#         The name to attribute any logging to.
#     element: object | None
#         The element creating the result.
#     """

#     return Result[T](name=name, element=element)


class _ResultFilter(Filter):
    """
    A logging `Filter` used to obtain log records for results.
    Not a logging `Handler` as we want to catch the records early.
    """

    __slots__ = ("_result",)

    def __init__(self, result: "Result[T]") -> None:
        super().__init__("_result")
        self._result = weakref.proxy(result)

    def filter(self, record: LogRecord) -> LogRecord:
        self._result._messages.append(record)
        return record


class Result(Generic[T]):
    """
    A result, may contain a value or an error.

    Attributes
    ----------
    value: T | None
        The actual value of the result, may be `None` if there was en error.
    element: object | None
        The element responsible for the metadata. May not necessarily be the value
        of the result.

    Methods
    -------
    meta(name: str, element: object | None = None) -> Self
        Creates a result with metadata info.

    ok(self, value: T) -> Self
        Sets the value of this result.
    err(self, error: Exception, *, reraise: bool = False) -> Self
        Adds an error to this result.
    debug(self, message: str, *args: object) -> None
        Adds a debug message to this result.
    info(self, message: str, *args: object) -> None
        Adds an info message to this result.
    warn(self, message: str, *args: object) -> None
        Adds a warning message to this result.
    reraise(self) -> None
        Re-raises the last error.
    unwrap(self) -> T
        Unwraps this result directly, raising an exception if not present.
    unwrap_into(self, parent: Result[object], default: T | None = None, reraise: bool = False) -> T
        Unwraps this result, adding any errors and/or metadata to a parent result.
    unwrap_or(self, default: T) -> T
        Unwraps this result directly, can raise an exception.
    """

    __slots__ = (
        "__weakref__",
        "_value", "_errors",
        # Metadata stuff.
        "_logger", "_filter", "element", "_messages",
    )

    @classmethod
    def meta(cls, name: str, element: object | None = None) -> Self:
        """
        Creates a result with metadata info.

        Parameters
        ----------
        name: str
            The name to attribute any logging to.
        element: object | None
            The element creating the result.
        """

        return cls(name=name, element=element)

    @property
    def value(self) -> T | None:
        return self._value

    def __init__(self, *, name: str | None = None, element: object | None = None) -> None:
        self._value: T | None = None
        self._errors: list[Exception] = []

        self._logger: Logger | None
        self._filter: _ResultFilter | None
        if name is not None:
            self._logger = logging.getLogger(name)
            self._filter = _ResultFilter(self)
            self._logger.addFilter(self._filter)
        else:
            self._logger = None
            self._filter = None
        self.element = element
        self._messages: list[LogRecord] = []

    def __del__(self) -> None:
        if self._logger is not None and self._filter is not None:
            self._logger.removeFilter(self._filter)

    def __repr__(self) -> str:
        return f"<Result(value={self._value!r})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Result) and self._value == other._value

    def __bool__(self) -> bool:
        return self._value is not None

    def __enter__(self) -> Self:
        return self

    def __exit__(
            self, exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
    ) -> bool:
        if isinstance(exc_value, Exception):
            self._errors.append(exc_value)
            return True
        # print(exc_value, traceback)
        return False

    def ok(self, value: T) -> Self:
        """
        Sets the value of this result.

        If `element` is `None`, then it will also be set to the value.
        """

        if self._value is not None:
            raise ValueError(f"{self!r} already has a valid value")
        self._value = value
        if self.element is not None:
            self.element = value
        return self

    def err(self, error: Exception, *, reraise: bool = False) -> Self:
        """
        Adds an error to this result.

        Parameters
        ----------
        error: Exception
            The error that occurred.
        reraise: bool
            Whether to re-raise the error after noting it down.

        Raises
        ------
        Exception
            If `reraise=True`, the provided error.
        """

        self._errors.append(error)
        if reraise:
            raise error
        return self

    # Wouldn't normally do "Any", but unfortunately it's required here.
    def debug(self, text: str, *args: object, **kwargs: Any) -> None:
        """
        Adds a debug message to this result.
        """

        if self._logger is not None:
            self._logger.debug(text, *args, **kwargs)

    def info(self, text: str, *args: object, **kwargs: Any) -> None:
        """
        Adds an info message to this result.
        """

        if self._logger is not None:
            self._logger.info(text, *args, **kwargs)

    def warn(self, text: str, *args: object, **kwargs: Any) -> None:
        """
        Adds a warning message to this result.
        """

        if self._logger is not None:
            self._logger.warning(text, *args, **kwargs)

    def reraise(self) -> None:
        """
        Re-raises the last error.

        Raises
        ------
        Exception
            If there were any errors, the last one that occurred.
        """

        if self._errors:
            raise self._errors[-1]

    def unwrap(self) -> T:
        """
        Unwraps this result directly, raising an exception if not present.

        Raises
        ------
        Exception
            If no value is present, the last error that occurred.
        ValueError
            If no value is present and there are no errors.
        """

        if self._value is not None:
            return self._value
        elif self._errors:
            raise self._errors[-1]
        raise ValueError("failed to unwrap result, no value present")

    def unwrap_into(self, parent: Result[Any], default: T | None = None, *, reraise: bool = False) -> T:
        """
        Unwraps this result, adding any errors and/or metadata to a parent result.

        Additionally, a default may be provided.

        Parameters
        ----------
        parent: Result[Any]
            The parent result to add any metadata to.
        default: T | None
            The default value to use if not value is present.
            If `None`, an exception is thrown.
        reraise: bool
            Re-raises the last error that occurred.

        Raises
        ------
        Exception
            If `reraise=True` and there is an error present.
        ValueError
            If no value and no default are present.
        """

        # FIXME: Rather than this, add some kind of metadata object to the parent that includes the element, name and
        #        messages.
        parent._errors.extend(self._errors)
        parent._messages.extend(self._messages)

        if self._value is not None:
            return self._value
        elif default is not None:
            return default

        if reraise and self._errors:  # FIXME: Perhaps some other failure state?
            # It does actually make more sense to re-raise the last error in this case, as we're assuming that the first
            # errors were probably added through .err().
            raise self._errors[-1]
        raise ValueError("failed to unwrap result, no value present and no default provided")

    def unwrap_or(self, default: T) -> T:
        """
        Unwraps this result or returns a default if no value is present.

        Parameters
        ----------
        default: T
            The default value to use if no value is present.
        """

        if self._value is not None:
            return self._value
        return default


class Ok(Result[T]):
    """
    Shorthand for creating a valid result.
    """

    def __init__(self, value: T, *, name: str | None = None, element: object | None = None) -> None:
        super().__init__(name=name, element=element or value)
        self._value = value


class Err(Result[T]):
    """
    Shorthand for creating an error result.
    """

    def __init__(self, error: Exception, *, name: str | None = None, element: object | None = None) -> None:
        super().__init__(name=name, element=element)
        self._errors.append(error)

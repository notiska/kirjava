#!/usr/bin/env python3

__all__ = (
    "Message", "Metadata",
)

"""
Metadata and messages used throughout the pipeline.
"""

import logging
from typing import Iterator


class Message:
    """
    An informative and structured message.

    Attributes
    ----------
    level: int
        The log level of this message.
    name: str
        The structured, unique name of the message.
    message: str
        The human-readable message.
    args: tuple[object, ...]
        The message formatting arguments.
    data: dict[str, object]
        Additional data.
    children: list[Message]
        Child messages.
    """

    __slots__ = ("level", "name", "message", "args", "data")

    def __init__(self, level: int, name: str, message: str, *args: object, **data: object) -> None:
        self.level = level
        self.name = name
        self.message = message
        self.args = args
        self.data = data

    def __repr__(self) -> str:
        return (
            f"<Message(level={logging.getLevelName(self.level)}, name={self.name!r}, "
            f"message={self.message % self.args!r})>"
        )

    def __str__(self) -> str:
        return f"{self.name}: {self.message % self.args}"


class Metadata:
    """
    Metadata information.

    Parameters
    ----------
    warnings: bool
        Whether this metadata contains any warnings.
    errors: bool
        Whether this metadata contains any errors.
    name: str
        The structured name of this metadata.
    element: object
        The element that this metadata belongs to.
    messages: list[Message]
        All messages added to this metadata.
    children: list[Metadata]
        Child metadata.

    Methods
    -------
    walk(self, level: int = logging.WARNING) -> Iterator[Message]
        Walks through all messages in this metadata and its children.
    has(self, name: str) -> bool
        Checks if this metadata contains a certain message.
    debug(self, name: str, message: str, *args: object) -> Message
        Adds a debug message to this metadata.
    info(self, name: str, message: str, *args: object) -> Message
        Adds an info message to this metadata.
    warn(self, name: str, message: str, *args: object) -> Message
        Adds a warning message to this metadata.
    error(self, name: str, message: str, *args: object) -> Message
        Adds an error message to this metadata.
    critical(self, name: str, message: str, *args: object) -> Message
        Adds a critical error message to this metadata.
    add(self, meta: Metadata) -> None
        Adds a child to this metadata.
    """

    __slots__ = ("name", "element", "messages", "children", "_logger")

    @property
    def warnings(self) -> bool:
        for message in self.messages:
            if message.level == logging.WARNING:
                return True
        for child in self.children:
            if child.warnings:
                return True
        return False

    @property
    def errors(self) -> bool:
        for message in self.messages:
            if message.level >= logging.ERROR:  # Include critical too.
                return True
        for child in self.children:
            if child.errors:
                return True
        return False

    def __init__(self, name: str, element: object | None = None) -> None:
        self.name = name
        self.element = element

        self.messages: list[Message] = []
        self.children: list[Metadata] = []

        if not name.startswith("kirjava."):
            name = "kirjava." + name
        self._logger = logging.getLogger(name)

    def __repr__(self) -> str:
        return f"<Metadata(name={self.name!r}, element={self.element!s}, messages={self.messages!r})>"

    # TODO: More comprehensive API.

    def walk(self, level: int = logging.WARNING) -> Iterator[tuple["Metadata", Message]]:
        """
        Walks through all messages in this metadata and its children.

        Parameters
        ----------
        level: int
            The minimum log level of messages.
        """

        for message in self.messages:
            if message.level >= level:
                yield self, message
        for child in self.children:
            yield from child.walk(level)

    def has(self, name: str) -> bool:
        """
        Checks if this metadata contains a certain message.

        Parameters
        ----------
        name: str
            The name of the message to check for.
        """

        for message in self.messages:
            if message.name == name:
                return True
        return False

    # ------------------------------ Logging API ------------------------------ #

    def debug(self, name: str, text: str, *args: object) -> Message:
        """
        Adds a debug message to this metadata.
        """

        message = Message(logging.DEBUG, name, text, *args)
        self.messages.append(message)
        self._logger.debug(text, *args)
        return message

    def info(self, name: str, text: str, *args: object) -> Message:
        """
        Adds an info message to this metadata.
        """

        message = Message(logging.INFO, name, text, *args)
        self.messages.append(message)
        self._logger.info(text, *args)
        return message

    def warn(self, name: str, text: str, *args: object) -> Message:
        """
        Adds a warning message to this metadata.
        """

        message = Message(logging.WARNING, name, text, *args)
        self.messages.append(message)
        self._logger.warning(text, *args)
        return message

    def error(self, name: str, text: str, *args: object) -> Message:
        """
        Adds an error message to this metadata.
        """

        message = Message(logging.ERROR, name, text, *args)
        self.messages.append(message)
        self._logger.error(text, *args)
        return message

    def critical(self, name: str, text: str, *args: object) -> Message:
        """
        Adds a critical error message to this metadata.
        """

        message = Message(logging.CRITICAL, name, text, *args)
        self.messages.append(message)
        self._logger.critical(text, *args)
        return message

    def add(self, meta: "Metadata") -> None:
        """
        Adds a child to this metadata.
        """

        if not meta.messages and not meta.children:  # No point in adding empty child metadata.
            return
        self.children.append(meta)

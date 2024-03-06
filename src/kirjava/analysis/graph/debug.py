#!/usr/bin/env python3

__all__ = (
    "LineNumber", "LocalVariable",
)

"""
Extra JVM debug information.
"""

from typing import Any

from ...instructions import _ReservedInstruction


class LineNumber(_ReservedInstruction):
    """
    A line number marker.
    """

    __slots__ = ("line_number",)

    def __init__(self, line_number: int) -> None:
        """
        :param line_number: The line number.
        """

        self.line_number = line_number

    def __repr__(self) -> str:
        return "<LineNumber(line_number=%i) at %x>" % (self.line_number, id(self))

    def __str__(self) -> str:
        return "line %i" % self.line_number

    def __eq__(self, other: Any) -> bool:
        return type(other) is LineNumber and other.line_number == self.line_number

    def __hash__(self) -> int:
        return self.line_number


class LocalVariable(_ReservedInstruction):
    """
    Information about a local variable.
    """

    __slot__ = ("index", "name", "descriptor", "signature", "_hash")

    def __init__(self, index: int, name: str, descriptor: str, signature: str | None = None) -> None:
        """
        :param index: The index of the local variable.
        :param name: The name of the local variable.
        :param descriptor: The descriptor of the local variable.
        """

        self.index = index
        self.name = name
        self.descriptor = descriptor
        self.signature = signature

        self._hash = hash((index, name, descriptor, signature))

    def __repr__(self) -> str:
        return "<LocalVariable(index=%i, name=%r, descriptor=%r, signature=%r) at %x>" % (
            self.index, self.name, self.descriptor, self.signature, id(self),
        )

    def __eq__(self, other: Any) -> bool:
        return (
            type(other) is LocalVariable and
            other.index == self.index and
            other.name == self.name and
            other.descriptor == self.descriptor and
            other.signature == self.signature
        )

    def __hash__(self) -> int:
        return self._hash

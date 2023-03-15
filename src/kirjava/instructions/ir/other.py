#!/usr/bin/env python3

"""
IR expressions/statements that are not unique enough to fit into their own categories.
"""

from typing import Iterable, Optional

from ...abc import Statement, Value


class CompoundStatement(Statement):
    """
    Multiple statements in a row.
    """

    def __init__(self, statements: Iterable[Statement]) -> None:
        """
        :param statements: The statements.
        """

        self.statements = list(statements)

    def __repr__(self) -> str:
        return "<CompoundStatement(%r) at %x>" % (self.statements, id(self))

    def __str__(self) -> str:
        return "\n".join(map(str, self.statements))


class ThrowStatement(Statement):
    """
    A throw statement.
    """

    def __init__(self, value: Value) -> None:
        self.value = value

    def __repr__(self) -> str:
        return "<ThrowStatement(value=%r) at %x>" % (self.value, id(self))

    def __str__(self) -> str:
        return "throw %s" % self.value


class ReturnStatement(Statement):
    """
    Returns a value from the method.
    """

    def __init__(self, value: Optional[Value] = None) -> None:
        """
        :param value: The value to return, None if there is no return value.
        """

        self.value = value

    def __repr__(self) -> str:
        return "<ReturnStatement(value=%r) at %x>" % (self.value, id(self))

    def __str__(self) -> str:
        if self.value is None:
            return "return"
        return "return %s" % self.value


class MonitorEnterStatement(Statement):
    """
    Enters an object monitor.
    """

    def __init__(self, object_: Value) -> None:
        """
        :param object_: The object to enter.
        """

        self.object = object_

    def __repr__(self) -> str:
        return "<MonitorEnterStatement(object=%r) at %x>" % (self.object, id(self))

    def __str__(self) -> str:
        return "monitorenter (%s)" % self.object


class MonitorExitStatement(Statement):
    """
    Exits an object monitor.
    """

    def __init__(self, object_: Value) -> None:
        """
        :param object_: The object to exit.
        """

        self.object = object_

    def __repr__(self) -> str:
        return "<MonitorExitStatement(object=%r) at %x>" % (self.object, id(self))

    def __str__(self) -> str:
        return "monitorexit (%s)" % self.object

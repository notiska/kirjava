#!/usr/bin/env python3

__all__ = (
    "PhiExpression",
    "AssignExpression", "DeclareStatement", "AssignStatement",
    "GetLocalExpression", "SetLocalStatement",
)

"""
IR variables and variable-related expressions/statements.
"""

from typing import Iterable, Optional

from ...abc import Expression, Statement, Value
# from ...analysis.ir.variable import Variable
from ...constants import Integer
from ...types import Primitive, Type


class PhiExpression(Expression):
    """
    A phi function expression.
    """

    def __init__(self, type_: Type, variables: Iterable["Variable"]) -> None:
        """
        :param type_: The merged type of the variables.
        :param variables: The variables that this phi function merges.
        """

        self.type = type_
        self.variables = list(variables)

    def __repr__(self) -> str:
        return "<PhiExpression(type=%s, variables=%r) at %x>" % (self.type, self.variables, id(self))

    def __str__(self) -> str:
        return "phi(%s)" % ", ".join(map(str, self.variables))

    def get_type(self) -> Type:
        return self.type


class AssignExpression(Expression):
    """
    An assignment expression.
    """

    def __init__(self, target: "Variable", value: Value) -> None:
        """
        :param target: The target variable to assign to.
        :param value: The value to assign.
        """

        self.target = target
        self.value = value

    def __repr__(self) -> str:
        return "<AssignExpression(target=%r, value=%r) at %x>" % (self.target, self.value, id(self))

    def __str__(self) -> str:
        return "%s = %s" % (self.target, self.value)

    def get_type(self) -> Type:
        return self.value.get_type()


class GetLocalExpression(Expression):
    """
    Indicates that a value has been obtained from a JVM local.
    """

    def __init__(self, index: int, value: Value) -> None:
        """
        :param index: The index of the local.
        :param value: The value obtained from the local.
        """

        self.index = index
        self.value = value

    def __repr__(self) -> str:
        return "<GetLocalExpression(index=%r, value=%r) at %x>" % (self.index, self.value, id(self))

    def __str__(self) -> str:
        return "getlocal(%i)" % self.index

    def get_type(self) -> Type:
        return self.value.get_type()


# ------------------------------ Statements ------------------------------ #

class DeclareStatement(Statement):
    """
    A variable declaration statement.
    """

    def __init__(self, target: "Variable", value: Optional[Value] = None) -> None:
        """
        :param target: The target variable to declare.
        :param value: The value to assign to the variable, if any.
        """

        self.target = target
        self.value = value

    def __repr__(self) -> str:
        return "<DeclareStatement(target=%r, value=%r) at %x>" % (self.target, self.value, id(self))

    def __str__(self) -> str:
        if self.value is not None:
            type_ = self.value.get_type()
            if isinstance(type_, Primitive):
                return "%s %s = %s" % (type_, self.target, self.value)
            return "var %s = %s" % (self.target, self.value)
        return "var %s" % self.target


class AssignStatement(Statement):
    """
    An assignment statement.
    """

    _INTEGER_1  = Integer(1)
    _INTEGER_M1 = Integer(-1)

    def __init__(self, target: "Variable", value: Value) -> None:
        """
        :param target: The target variable to assign to.
        :param value: The value to assign.
        """

        self.target = target
        self.value = value

    def __repr__(self) -> str:
        return "<AssignStatement(target=%r, value=%r) at %x>" % (self.target, self.value, id(self))

    def __str__(self) -> str:
        # if isinstance(self.value, BinaryExpression) and type(self.value.left) is Local:
        #     if type(self.value) is AdditionExpression and type(self.value.right) is ConstantValue:
        #         if self.value.right.constant == self._INTEGER_1:
        #             return "++%s" % self.target
        #         elif self.value.right.constant == self._INTEGER_M1:
        #             return "--%s" % self.target
        #     return "%s %s= %s" % (self.target, self.value.operator, self.value.right)
        return "%s = %s" % (self.target, self.value)


class SetLocalStatement(Statement):
    """
    Indicates that a value has been assigned to a JVM local.
    """

    def __init__(self, index: int, value: Value) -> None:
        """
        :param index: The index of the local.
        :param value: The value assigned to the local.
        """

        self.index = index
        self.value = value

    def __repr__(self) -> str:
        return "<SetLocalStatement(index=%r, value=%r) at %x>" % (self.index, self.value, id(self))

    def __str__(self) -> str:
        return "setlocal(%i, %s)" % (self.index, self.value)

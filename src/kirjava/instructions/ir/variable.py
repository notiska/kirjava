#!/usr/bin/env python3

"""
IR variables and variable-related expressions/statements.
"""

from typing import Iterable, Union

from .arithmetic import AdditionExpression, BinaryExpression
from .value import ConstantValue
from ...abc import Expression, Statement, Value
from ...analysis.ir.variable import Local, Variable
from ...classfile.constants import Integer
from ...types import BaseType, PrimitiveType


class PhiExpression(Expression):
    """
    A phi function expression.
    """

    def __init__(self, type_: BaseType, variables: Iterable[Variable]) -> None:
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

    def get_type(self) -> BaseType:
        return self.type


class AssignExpression(Expression):
    """
    An assignment expression.
    """

    def __init__(self, target: Variable, value: Value) -> None:
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

    def get_type(self) -> BaseType:
        return self.value.get_type()


# ------------------------------ Statements ------------------------------ #

class DeclareStatement(Statement):
    """
    A variable declaration statement.
    """

    def __init__(self, target: Variable, value: Union[Value, None] = None) -> None:
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
            if isinstance(type_, PrimitiveType):
                return "%s %s = %s" % (type_, self.target, self.value)
            return "var %s = %s" % (self.target, self.value)
        return "var %s" % self.target


class AssignStatement(Statement):
    """
    An assignment statement.
    """

    _INTEGER_1  = Integer(1)
    _INTEGER_M1 = Integer(-1)

    def __init__(self, target: Variable, value: Value) -> None:
        """
        :param target: The target variable to assign to.
        :param value: The value to assign.
        """

        self.target = target
        self.value = value

    def __repr__(self) -> str:
        return "<AssignStatement(target=%r, value=%r) at %x>" % (self.target, self.value, id(self))

    def __str__(self) -> str:
        if isinstance(self.value, BinaryExpression) and type(self.value.left) is Local:
            if type(self.value) is AdditionExpression and type(self.value.right) is ConstantValue:
                if self.value.right.constant == self._INTEGER_1:
                    return "++%s" % self.target
                elif self.value.right.constant == self._INTEGER_M1:
                    return "--%s" % self.target
            return "%s %s= %s" % (self.target, self.value.operator, self.value.right)
        return "%s = %s" % (self.target, self.value)

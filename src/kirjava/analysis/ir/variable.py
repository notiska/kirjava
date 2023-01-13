#!/usr/bin/env python3

"""
IR variables and variable-related expressions/statements.
"""

from typing import Any, Iterable, Union

from ...abc import Expression, Statement, Value
from ...types import BaseType
from ...types.reference import ClassOrInterfaceType


# ------------------------------ Variables ------------------------------ #

class Variable(Value):
    """
    An IR variable.
    """

    def __init__(self, id_: int, type_: BaseType) -> None:
        """
        :param id_: The unique ID of this variable, for faster hashing.
        :param type_: The type of this variable.
        """

        self.id = id_
        self.type = type_

    def __repr__(self) -> str:
        return "<Variable(id=%i) at %x>" % (self.id, id(self))

    def __str__(self) -> str:
        return "var_%i" % self.id

    def __eq__(self, other: Any) -> bool:
        return other.__class__ is self.__class__ and other.id == self.id

    def __hash__(self) -> int:
        return hash((8530224966147402853, self.id))

    def get_type(self) -> BaseType:
        return self.type


class This(Variable):
    """
    A variable that simply represents the this class.
    """

    def __init__(self, type_: ClassOrInterfaceType) -> None:
        super().__init__(0, type_)

    def __repr__(self) -> str:
        return "<This(class=%r) at %x>" % (self._type, id(self))

    def __str__(self) -> str:
        return "this"

    def __eq__(self, other: Any) -> bool:
        return other.__class__ is This

    def __hash__(self) -> int:
        return 1952999795


class Parameter(Variable):
    """
    A parameter passed to the method, for keeping track of.
    """

    def __init__(self, index: int, type_: BaseType) -> None:
        """
        :param index: The index of the local variable representing the parameter.
        """

        super().__init__(index, type_)

    def __repr__(self) -> str:
        return "<Parameter(index=%i) at %x>" % (self.id, id(self))

    def __str__(self) -> str:
        return "param_%i" % self.id

    def __hash__(self) -> int:
        return hash((7021781891505481074, self.id))


# ------------------------------ Expressions ------------------------------ #

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
            return "var %s = %s" % (self.target, self.value)
        return "var %s" % self.target


class AssignStatement(Statement):
    """
    An assignment statement.
    """

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
        return "%s = %s" % (self.target, self.value)

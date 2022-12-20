#!/usr/bin/env python3

"""
IR variables.
"""

from typing import Any

from .abc import Expression
from ...types import BaseType
from ...types.reference import ClassOrInterfaceType


class Variable(Expression):
    """
    An IR variable.
    """

    __slots__ = ("id", "_type")

    @property
    def type(self) -> BaseType:
        return self._type

    def __init__(self, id_: int, type_: BaseType) -> None:
        """
        :param id_: The unique ID of this variable, for faster hashing.
        :param type_: The type of this variable.
        """

        self.id = id_
        self._type = type_

    def __repr__(self) -> str:
        return "<Variable(id=%i) at %x>" % (self.id, id(self))

    def __str__(self) -> str:
        return "var_%i" % self.id

    def __eq__(self, other: Any) -> bool:
        return other.__class__ == self.__class__ and other.id == self.id

    def __hash__(self) -> int:
        return self.id


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
        return isinstance(other, This)

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
        return 7021781891505481074 + self.id

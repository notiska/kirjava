#!/usr/bin/env python3

"""
IR variables.
"""

from typing import Any, Dict, Optional

from ...abc import Value
from ...types import BaseType
from ...types.reference import ClassOrInterfaceType


class Scope:
    """
    A variable scope.
    """

    @property
    def variable_id(self) -> int:
        self._variable_id += 1
        return self._variable_id

    def __init__(self, parent: Optional["Scope"] = None) -> None:
        """
        :param parent: The parent scope to this scope.
        """

        self.parent = parent
        self.declared: Dict[int, Variable] = {}

        self._variable_id = -1  # We increment before we return, so the first ID will be 0

    def declare(self, variable: "Variable") -> bool:
        """
        Declares a variable in this scope.

        :param variable: The variable to define.
        :return: Was the variable declared or does it already exist?
        """

        declared = self.declared.get(variable.id, None)
        if declared is not None:
            if variable.type == declared.type:  # Correct types?
                return False
            ...  # TODO: Exception?
        self.declared[variable.id] = variable
        return True

    def lookup(self, id_: int) -> "Variable":
        """
        Looks up a variable with the provided ID.

        :param id_: The ID of the variable.
        :return: The variable, if not found, a LookupError is raised.
        """

        variable = self.declared.get(id_, None)
        if variable is not None:
            return variable

        if self.parent is not None:
            return self.parent.lookup(id_)
        raise LookupError("Couldn't find a variable with ID %i." % id_)


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
        return type(other) is self.__class__ and other.id == self.id

    def __hash__(self) -> int:
        return hash((8530224966147402853, self.id))

    def get_type(self) -> BaseType:
        return self.type


class This(Variable):
    """
    A variable that simply represents the this class.
    """

    def __init__(self, type_: ClassOrInterfaceType) -> None:
        super().__init__(-1, type_)

    def __repr__(self) -> str:
        return "<This(class=%s) at %x>" % (self.type, id(self))

    def __str__(self) -> str:
        return "this"

    def __eq__(self, other: Any) -> bool:
        return type(other) is This

    def __hash__(self) -> int:
        return 1952999795


class Super(Variable):
    """
    A variable that represents the super "instance" of this instance.
    """

    def __init__(self, type_: ClassOrInterfaceType) -> None:
        super().__init__(-2, type_)

    def __repr__(self) -> str:
        return "<Super(class=%s) at %x>" % (self.type, id(self))

    def __str__(self) -> str:
        return "super"

    def __eq__(self, other: Any) -> bool:
        return type(other) is Super

    def __hash__(self) -> int:
        return 495891539314


class Local(Variable):
    """
    An actual Java local variable.
    """

    def __init__(self, id_: int, index: int, type_: BaseType) -> None:
        """
        :param index: The index of the local variable.
        """

        super().__init__(id_, type_)

        self.index = index

    def __repr__(self) -> str:
        return "<Local(index=%i) at %x>" % (self.id, id(self))

    def __str__(self) -> str:
        return "local_%i" % self.id

    def __hash__(self) -> int:
        return hash((465725251948, self.id))


class Parameter(Local):
    """
    A parameter passed to the method, for keeping track of.
    """

    def __repr__(self) -> str:
        return "<Parameter(index=%i) at %x>" % (self.id, id(self))

    def __str__(self) -> str:
        return "param_%i" % self.id

    def __hash__(self) -> int:
        return hash((7021781891505481074, self.id))

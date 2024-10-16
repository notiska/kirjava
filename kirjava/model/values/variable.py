#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Variable", "This", "Super",
)

import typing

from . import Value

if typing.TYPE_CHECKING:
    from ..types import Class, Type


class Variable(Value):  # TODO: Names, is it a local, etc...
    """
    A variable.

    Attributes
    ----------
    ID_THIS: int
        The ID of the `this` variable.
    ID_SUPER: int
        The ID of the `super` variable.

    type: Type
        The type of the variable.
    id: int
        The unique identifier of the variable within its scope.
    """

    __slots__ = ("type", "id")

    ID_THIS  = 0
    ID_SUPER = -1

    def __init__(self, type_: "Type", id_: int) -> None:
        self.type = type_
        self.id = id_

    def __repr__(self) -> str:
        return f"<Variable(type={self.type!s}, id={self.id})"

    def __str__(self) -> str:
        return f"var_{self.id}"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Variable) and self.id == other.id

    def __hash__(self) -> int:
        return self.id


class This(Variable):

    __slots__ = ()

    def __init__(self, type_: "Class") -> None:
        super().__init__(type_, Variable.ID_THIS)

    def __repr__(self) -> str:
        return f"<This(type={self.type!s})>"

    def __str__(self) -> str:
        return "this"

    def __eq__(self, other: object) -> bool:
        return type(other) is This


class Super(Variable):

    __slots__ = ()

    def __init__(self, type_: "Class") -> None:
        super().__init__(type_, Variable.ID_SUPER)

    def __repr__(self) -> str:
        return f"<Super(type={self.type!s})>"

    def __str__(self) -> str:
        return "super"

    def __eq__(self, other: object) -> bool:
        return type(other) is Super

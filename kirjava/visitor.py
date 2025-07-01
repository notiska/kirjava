#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Visitable", "Visitor", "Visitors",
)

"""
The generic visitor API.
"""

from collections import defaultdict
from typing import Any, Generic, Iterable

from ._compat import TypeVar, Self

T = TypeVar("T", bound="Visitable")


class Visitable:
    """
    A "visitable" interface for instances that can be visited.
    """

    __slots__ = ()

    def visit(self, visitor: "Visitor[Self]", visitors: "Visitors") -> None:
        """
        Visits this instance.

        Parameters
        ----------
        visitor: Visitor[type[Self]]
            The specific visitor being invoked.
        visitors: Visitor
            The `Visitors` object, for invoking nested visitable objects.
        """

        raise NotImplementedError(f"visit() is not implemented for {type(self)!r}")


class Visitor(Generic[T]):
    """
    A generic visitor class.

    Attributes
    ----------
    type: T
        The type that the visitor will be listening to.

    Methods
    -------
    visit_start(self, inst: T) -> None
        Called at the start of visiting the type.
    visit_end(self) -> None
        Called at the end of visiting the type.
    """

    __slots__ = ()

    type: type[T]

    def visit_start(self, inst: T) -> None:
        """
        Called at the start of visiting the type.

        Parameters
        ----------
        inst: T
            The instance being visited.
        """

        ...

    def visit_end(self, inst: T) -> None:
        """
        Called at the end of visiting the type.

        Parameters
        ----------
        inst: T
            The instance being visited.
        """

        ...


class Visitors:
    """
    A collection of visitors.

    Attributes
    ----------
    stack: tuple[Visitable, ...]
        An unmodifiable copy of the stack of instances that are currently being
        visited.

    Methods
    -------
    visit(self, inst: Visitable) -> None
        Visits the provided instance.
    """

    __slots__ = ("visitors", "_stack", "_dummy")

    # _cache: dict[type[Visitable], list[Visitor[Visitable]]] = {}

    @property
    def stack(self) -> tuple[Visitable, ...]:
        return tuple(self._stack)

    def __init__(self) -> None:
        self.visitors: dict[type[Visitable], list[Visitor[Visitable]]] = defaultdict(list)
        self._stack: list[Visitable] = []
        # self._visited: set[Visitable] = set()
        self._dummy = Visitors.Dummy()

    def __repr__(self) -> str:
        return f"<Visitors(visitors={self.visitors!r})>"

    def __getitem__(self, key: type[Visitable]) -> list[Visitor[Visitable]]:
        return self.visitors[key]

    def __setitem__(self, key: type[Visitable], value: Iterable[Visitable]) -> None:
        self.visitors[key].extend(value)

    def __delitem__(self, key: type[Visitable]) -> None:
        del self.visitors[key]

    def visit(self, inst: Visitable) -> None:
        """
        Visits the provided instance.

        Parameters
        ----------
        inst: Any
            The instance to visit.
        """

        if inst in self.stack:
            raise ValueError(f"recursive visit call on {inst!r}")

        self._stack.append(inst)
        try:
            for cls in type(inst).__mro__:
                if cls is Visitable:  # FIXME: Weird MRO possible?
                    break
                visitors = self.visitors.get(cls)
                if not visitors:
                    # TODO: Could also use this to verify that both visit_start() and visit_end() are called?
                    visitors = [self._dummy]
                    # del self.visitors[cls]  # Don't want to actually add this visitor to the list.
                for visitor in visitors:
                    inst.visit(visitor, self)
        finally:
            self._stack.pop()

    def add(self, visitor: Visitor[Any]) -> None:
        """
        Adds a visitor to this collection.
        """

        self.visitors[visitor.type].append(visitor)

    def remove(self, visitor: Visitor[Any]) -> None:
        """
        Removes the provided visitor from this collection.
        """

        visitors = self.visitors.get(visitor.type)
        if not visitors:
            return
        try:
            visitors.remove(visitor)
        except ValueError:
            ...

    class Dummy(Visitor[Visitable]):
        """
        A dummy visitor that does nothing.
        """

        type = Visitable

        def visit_start(self, inst: Visitable) -> None:
            ...

        def visit_end(self, inst: Visitable) -> None:
            ...

#!/usr/bin/env python3

from __future__ import annotations

"""
Value constraints.
"""

# TODO

from typing import Any, Generic

from ..._compat import TypeVar
from ...model.values import Constant, Value

T = TypeVar("T", bound=Constant)


class Constraint(Value):
    """
    Any type of value constraint.
    """

    __slots__ = ()


class Range(Generic[T], Constraint):
    """
    A range constraint.
    """

    __slots__ = ("_start", "_stop", "_step", "_hash")

    def __init__(self, start: T, stop: T, step: T) -> None:
        self._start = start
        self._stop = stop  # TODO: Inclusive flags?
        self._step = step
        self._hash = hash((start, stop, step))

    def __contains__(self, other: Any) -> bool:
        return other >= self._start and other <= self._stop and not other % self._step

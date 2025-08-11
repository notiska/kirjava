#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "assemble",
)

"""
The JVM bytecode assembler.
"""

import typing

from ..fmt import ClassFile, MethodInfo
from ..._compat import TypeVar
from ...backend import Result

if typing.TYPE_CHECKING:
    from . import Graph

T = TypeVar("T", bound="Graph")


def assemble(graph: T, method: MethodInfo, cf: ClassFile | None) -> Result[T]:
    """
    JVM bytecode assembler.

    Parameters
    ----------
    graph: T
        The graph assemble from.
    method: MethodInfo
        The method to assemble.
    cf: ClassFile | None
        The class file that the method belongs to.
    """

    with Result[T].meta(__name__) as result:
        ...  # graph.blocks

    return result

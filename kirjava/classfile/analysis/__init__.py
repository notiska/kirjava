#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "frame",
    "Frame",
    "Analysis",
)

"""
Various analysis functionality for JVM bytecode.
"""

import typing
from collections import defaultdict

from . import frame
from ._analyse import *
from .frame import *
from ..._compat import Self
from ...backend import Result

if typing.TYPE_CHECKING:
    from ..graph import Graph


class Analysis:
    """
    Method JVM bytecode analysis information.

    Methods
    -------
    analyse(graph: Graph) -> Result[Self]
        Performs an analysis pass on the provided JVM CFG.
    """

    __slots__ = ()

    @classmethod
    def analyse(cls, graph: "Graph") -> Result[Self]:
        """
        Performs an analysis pass on the provided JVM CFG.
        """

        return analyse(cls(), graph)

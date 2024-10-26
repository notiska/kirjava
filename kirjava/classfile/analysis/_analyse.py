#!/usr/bin/env python3

__all__ = (
    "analyse",
)

import operator
import typing
from collections import defaultdict
from typing import TypeVar

from ...backend import Result

if typing.TYPE_CHECKING:
    from . import Analysis
    from ..graph import Graph
    from ...model.class_ import *

T = TypeVar("T", bound="Analysis")


def analyse(analysis: T, graph: "Graph") -> Result[T]:
    """
    Performs an analysis pass on the provided JVM CFG.
    """

    with Result[T].meta(__name__) as result:
        ...
    return result

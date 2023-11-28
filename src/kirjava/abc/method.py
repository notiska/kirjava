#!/usr/bin/env python3

__all__ = (
    "Method",
)

"""
Java method abstraction.
"""

import typing
import weakref
from typing import Iterable

from ..types import Type

if typing.TYPE_CHECKING:
    from .class_ import Class


class Method:
    """
    An abstract representation of a Java method.
    """

    __slots__ = ("__weakref__", "class_",)

    is_public: bool
    is_private: bool
    is_protected: bool
    is_static: bool
    is_final: bool
    is_synchronized: bool
    is_bridge: bool
    is_varargs: bool
    is_native: bool
    is_abstract: bool
    is_strict: bool
    is_synthetic: bool

    name: str
    argument_types: tuple[Type, ...]
    return_type: Type

    def __init__(self, class_: "Class") -> None:
        """
        :param class_: The class that this method belongs to.
        """

        self.class_ = weakref.proxy(class_)

#!/usr/bin/env python3

__all__ = (
    "Field",
)

"""
Java field abstraction.
"""

import typing
import weakref

from ..types import Type

if typing.TYPE_CHECKING:
    from .class_ import Class


class Field:
    """
    An abstract representation of a Java field.
    """

    __slots__ = ("__weakref__", "class_",)

    is_public: bool
    is_private: bool
    is_protected: bool
    is_static: bool
    is_final: bool
    is_volatile: bool
    is_transient: bool
    is_synthetic: bool
    is_enum: bool

    name: str
    type: Type

    def __init__(self, class_: "Class") -> None:
        """
        :param class_: The class that this field belongs to.
        """

        self.class_ = weakref.proxy(class_)

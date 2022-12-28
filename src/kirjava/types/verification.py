#!/usr/bin/env python3

"""
Verification types.
"""

import typing
from typing import Any, Union

from . import BaseType, ReferenceType, VerificationType
from ..abc import Constant

if typing.TYPE_CHECKING:
    from .reference import ClassOrInterfaceType


class Top(VerificationType):
    """
    Top verification type.
    """
    
    def __repr__(self) -> str:
        return "<Top() at %r>" % id(self)
        
    def __str__(self) -> str:
        return "top"
        
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Top)  # FIXME: Speed improvements: other is self?

    def __hash__(self) -> int:
        return 7630704

    def can_merge(self, other: VerificationType) -> bool:
        return True  # Top extends all other verification types


class Null(Constant, VerificationType):  # Yes, it's a constant too, cos compatibility reasons :p
    """
    Used to denote a null reference in Java.
    """

    def __init__(self) -> None:
        super().__init__(None)

    def __repr__(self) -> str:
        return "<Null() at %x>" % id(self)

    def __str__(self) -> str:
        return "null"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Null)

    def __hash__(self) -> int:
        return 1853189228

    def get_type(self) -> BaseType:
        return self  # Hacky since this is a VerificationType, but whatever

    def can_merge(self, other: VerificationType) -> bool:
        # Delegate the call to the other type, reference types should be ok with this
        return other == self or isinstance(other, ReferenceType)


class This(VerificationType):
    """
    Direct reference to the this class for simpler code.
    """

    __slots__ = ("class_",)

    def __init__(self, class_: Union["ClassOrInterfaceType", None] = None) -> None:
        """
        :param class_: The this class reference, for easier access.
        """

        self.class_ = class_

    def __repr__(self) -> str:
        return "<This(class=%r) at %x>" % (self.class_, id(self))

    def __str__(self) -> str:
        return "this"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, This) and (self.class_ is None or other.class_ is None or other.class_ == self.class_)

    def __hash__(self) -> int:
        return 1952999795

    def can_merge(self, other: VerificationType) -> bool:
        return other == self or self.class_.can_merge(other)


class Uninitialized(VerificationType):
    """
    Used to denote that an uninitialized variable in Java.
    """

    __slots__ = ("offset", "class_")

    def __init__(self, offset: int = -1, class_: Union["ClassOrInterfaceType", None] = None) -> None:
        """
        :param offset: The bytecode offset to the new instruction that created this type.
        :param class_: The class that is uninitialised, if applicable, otherwise None.
        """

        self.offset = offset
        self.class_ = class_  # Yeah obviously not possible with the StackMapTable, but very useful elsewhere

    def __repr__(self) -> str:
        args = {}
        if self.offset >= 0:
            args["offset"] = self.offset
        if self.class_ is not None:
            args["class"] = self.class_
        return "<%s(%s) at %x>" % (
            self.__class__.__name__, ", ".join(["%s=%r" % item for item in args.items()]), id(self),
        )

    def __str__(self) -> str:
        string = "uninitialized"
        if self.class_ is not None:
            string += " " + str(self.class_)
        if self.offset >= 0:
            string += " (offset %i)" % self.offset 
        return string

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Uninitialized) and other.offset == self.offset and other.class_ == self.class_

    def __hash__(self) -> int:
        return hash((8388342899208250724, self.offset, self.class_))

    def can_merge(self, other: VerificationType) -> bool:
        return isinstance(other, Uninitialized) or isinstance(other, Null)


class UninitializedThis(Uninitialized):
    """
    Used to denote an uninitialized this verification type.
    """

    def __init__(self, class_: Union["ClassOrInterfaceType", None] = None) -> None:
        super().__init__(-1, class_)

    def __str__(self) -> str:
        return "uninitializedThis"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, UninitializedThis) and (
            self.class_ is None or other.class_ is None or other.class_ == self.class_
        )

    def __hash__(self) -> int:
        return 7600498803265268083

    def can_merge(self, other: VerificationType) -> bool:
        return other == self or isinstance(other, Null)

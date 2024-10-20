#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "ClassFileVisitor", "FieldInfoVisitor", "MethodInfoVisitor",
)

"""
The visitor API for JVM class files.
"""

import typing

if typing.TYPE_CHECKING:
    from .fmt import AttributeInfo, ClassFile, ConstPool, FieldInfo, MethodInfo

# TODO: A more comprehensive visitor API.


class ClassFileVisitor:
    """
    A visitor for a JVM class file.

    Methods
    -------
    visit_start(self, cf: ClassFile)
        Called at the start of visiting a class file.
    visit_pool(self, pool: ConstPool)
        Called when visiting the class file constant pool.
    visit_field(self, field: FieldInfo)
        Called when visiting a field in the class.
    visit_method(self, method: MethodInfo)
        Called when visiting a method in the class.
    visit_attribute(self, attribute: AttributeInfo)
        Called when visiting an attribute of any type in the class.
    visit_end(self, cf: ClassFile)
        Called at the end of visiting a class file.
    """

    __slots__ = ()

    def visit_start(self, cf: "ClassFile") -> None:
        """
        Called at the start of visiting a class file.
        """

        raise NotImplementedError(f"visit_start() is not implemented for {type(self)!r}")

    def visit_pool(self, pool: "ConstPool") -> None:
        """
        Called when visiting the class file constant pool.
        """

        raise NotImplementedError(f"visit_pool() is not implemented for {type(self)!r}")

    def visit_field(self, field: "FieldInfo") -> None:
        """
        Called when visiting a field in the class.
        """

        raise NotImplementedError(f"visit_field() is not implemented for {type(self)!r}")

    def visit_method(self, method: "MethodInfo") -> None:
        """
        Called when visiting a method in the class.
        """

        raise NotImplementedError(f"visit_method() is not implemented for {type(self)!r}")

    def visit_attribute(self, attribute: "AttributeInfo") -> None:
        """
        Called when visiting an attribute of any type in the class.
        """

        raise NotImplementedError(f"visit_attribute() is not implemented for {type(self)!r}")

    def visit_end(self, cf: "ClassFile") -> None:
        """
        Called at the end of visiting a class file.
        """

        raise NotImplementedError(f"visit_end() is not implemented for {type(self)!r}")


class FieldInfoVisitor:
    """
    A visitor for fields in a class file.

    Methods
    -------
    visit_start(self, field: FieldInfo) -> None
        Called at the start of visiting a field.
    visit_attribute(self, field: FieldInfo) -> None
        Called when visiting an attribute of any type in the field.
    visit_end(self, field: FieldInfo) -> None
        Called at the end of visiting a field.
    """

    __slots__ = ()

    def visit_start(self, field: "FieldInfo") -> None:
        """
        Called at the start of visiting a field.
        """

        raise NotImplementedError(f"visit_start() is not implemented for {type(self)!r}")

    def visit_attribute(self, attribute: "AttributeInfo") -> None:
        """
        Called when visiting an attribute of any type in the field.
        """

        raise NotImplementedError(f"visit_attribute() is not implemented for {type(self)!r}")

    def visit_end(self, field: "FieldInfo") -> None:
        """
        Called at the end of visiting a field.
        """

        raise NotImplementedError(f"visit_end() is not implemented for {type(self)!r}")


class MethodInfoVisitor:
    """
    A visitor for methods in a class file.

    Methods
    -------
    visit_start(self, method: MethodInfo) -> None
        Called at the start of visiting a method.
    visit_attribute(self, attribute: AttributeInfo) -> None
        Called when visiting an attribute of any type in the method.
    visit_end(self, method: MethodInfo) -> None
        Called at the end of visiting a method.
    """

    __slots__ = ()

    def visit_start(self, method: "MethodInfo") -> None:
        """
        Called at the start of visiting a method.
        """

        raise NotImplementedError(f"visit_start() is not implemented for {type(self)!r}")

    def visit_attribute(self, attribute: "AttributeInfo") -> None:
        """
        Called when visiting an attribute of any type in the method.
        """

        raise NotImplementedError(f"visit_attribute() is not implemented for {type(self)!r}")

    def visit_end(self, method: "MethodInfo") -> None:
        """
        Called at the end of visiting a method.
        """

        raise NotImplementedError(f"visit_end() is not implemented for {type(self)!r}")

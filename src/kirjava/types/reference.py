#!/usr/bin/env python3

"""
Java reference types.
"""

from typing import Any, Iterable, Optional, Union

from . import BaseType, ReferenceType, TypeArgument, TypeArgumentList, TypeBound, VerificationType


class ClassOrInterfaceType(ReferenceType, VerificationType):
    """
    Either a Java class or interface.
    """

    __slots__ = ("name", "type_arguments", "inner_name", "inner_type_arguments")

    def __init__(
            self,
            name: str,
            type_arguments: Optional[Iterable[TypeArgument]] = None,
            inner_name: Optional[str] = None,
            inner_type_arguments: Optional[Iterable[TypeArgument]] = None,
    ) -> None:
        """
        :param name: The name of the class.
        :param type_arguments: Any generic type arguments given for the class.
        :param inner_name: The name of the inner classes, if this is one.
        :param inner_type_arguments: The type arguments of the inner class, if this is one.
        """

        if type_arguments is None:
            type_arguments = ()
        if inner_type_arguments is None:
            inner_type_arguments = ()

        self.name = name
        self.type_arguments = TypeArgumentList(type_arguments)
        self.inner_name = inner_name
        self.inner_type_arguments = TypeArgumentList(inner_type_arguments)

    def __repr__(self) -> str:
        if not self.type_arguments and self.inner_name is None:
            return "<ClassOrInterfaceType(%r) at %x>" % (self.name, id(self))
        elif self.inner_name is None:
            return "<ClassOrInterfaceType(name=%s, type_arguments=%s) at %x>" % (self.name, self.type_arguments, id(self))

        return "<ClassOrInterfaceType(name=%s, inner_name=%s, type_arguments=%r, inner_type_arguments=%r) at %x>" % (
            self.name, self.inner_name, self.type_arguments, self.inner_type_arguments, id(self),
        )

    def __str__(self) -> str:  # Yeah, wow
        if not self.type_arguments and self.inner_name is None:
            return self.name
        elif self.type_arguments and self.inner_name is None:
            return "%s%s" % (self.name, self.type_arguments)
        elif not self.type_arguments:
            if not self.inner_type_arguments:
                return "%s.%s" % (self.name, self.inner_name)
            return "%s.%s%s" % (self.name, self.inner_name, self.inner_type_arguments)

        if not self.inner_type_arguments:
            return "%s%s.%s" % (self.name, self.type_arguments, self.inner_name)
        return "%s%s.%s%s" % (self.name, self.type_arguments, self.inner_name, self.inner_type_arguments)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        elif type(other) is ClassOrInterfaceType:
            return (
                other.name == self.name and 
                # Do we both have type arguments, and are they the same?
                ((not other.type_arguments or not self.type_arguments) or
                 other.type_arguments == self.type_arguments) and
                # Same deal as above, except with the inner class
                other.inner_name == self.inner_name and
                ((not other.inner_type_arguments or not self.inner_type_arguments) or
                 other.inner_type_arguments == self.inner_type_arguments)
            )
        elif type(other) is str:
            return other == self.name

        return False

    def __hash__(self) -> int:
        return hash((self.name, self.type_arguments, self.inner_name, self.inner_type_arguments))

    def to_verification_type(self) -> VerificationType:
        return ClassOrInterfaceType(self.name)  # Remove any generic data

    def can_merge(self, other: VerificationType) -> bool:
        return isinstance(other, ClassOrInterfaceType) or other.can_merge(self)

    def rename(self, name: str) -> "ClassOrInterfaceType":
        if name == self.name:
            return self

        return ClassOrInterfaceType(
            name,
            self.type_arguments.arguments,
            self.inner_name,
            self.inner_type_arguments.arguments,
        )


class ArrayType(ReferenceType, VerificationType):
    """
    A reference to an array.
    """

    __slots__ = ("element_type", "dimension")

    def __init__(self, element_type: Union[BaseType, VerificationType], dimension: int = 1) -> None:
        """
        :param element_type: The type of element in the array.
        :param dimension: The dimension of the array.
        """

        self.element_type = element_type
        self.dimension = dimension

    def __repr__(self) -> str:
        return "<ArrayType(element_type=%r, dimension=%i) at %x>" % (self.element_type, self.dimension, id(self))

    def __str__(self) -> str:
        return str(self.element_type) + ("[]" * self.dimension)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return type(other) is ArrayType and other.dimension == self.dimension and other.element_type == self.element_type

    def __hash__(self) -> int:
        return hash((self.element_type, self.dimension))

    def to_verification_type(self) -> VerificationType:
        if type(self.element_type) is ClassOrInterfaceType:  # Strip any signature info, if necessary
            return ArrayType(self.element_type.to_verification_type(), self.dimension)
        return self

    def can_merge(self, other: VerificationType) -> bool:
        return isinstance(other, ArrayType) or isinstance(other, ClassOrInterfaceType) or other.can_merge(self)

    def set_dimension(self, dimension: int) -> "ArrayType":
        """
        Sets the dimension in this array type to the given value. If the dimension <= 0, it will return the element type.

        :param dimension: The new dimension of the array type.
        :return: The copied array type with the new dimension, or other.
        """

        if dimension <= 0:
            return self.element_type
        elif dimension == self.dimension:
            return self
        return ArrayType(self.element_type, dimension)

    def set_dim(self, dimension: int) -> "ArrayType":
        """
        Sets the dimension in this array type to the given value. If the dimension <= 0, it will return the element type.

        :param dimension: The new dimension of the array type.
        :return: The coped array type with the new dimension, or other.
        """

        return self.set_dimension(dimension)

    def rename(self, name: str) -> "ArrayType":
        if not isinstance(self.element_type, ReferenceType):
            return self
        return ArrayType(self.element_type.rename(name), self.dimension)


class TypeVariable(ReferenceType, TypeBound):
    """
    A generic type variable identifier.
    """

    __slots__ = ("identifier",)

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def __repr__(self) -> str:
        return "<TypeVariable(%r) at %x>" % (self.identifier, id(self))

    def __str__(self) -> str:
        return self.identifier

    def __eq__(self, other: Any) -> bool:
        if type(other) is TypeVariable:
            return other.identifier == self.identifier
        elif type(other) is str:
            return other == self.identifier

        return False

    def __hash__(self) -> int:
        return hash(self.identifier)

    def to_verification_type(self) -> VerificationType:
        raise TypeError("Cannot create verification type from %r." % self)

    def rename(self, name: str) -> "TypeVariable":
        return self

#!/usr/bin/env python3

"""
Java reference types.
"""

from typing import Any, List, Union

from . import BaseType, ReferenceType, TypeArgument, TypeArgumentList, TypeBound, VerificationType


class ClassOrInterfaceType(ReferenceType, VerificationType):
    """
    Either a Java class or interface.
    """

    __slots__ = ("name", "type_arguments", "inner_name", "inner_type_arguments")

    def __init__(
            self,
            name: str,
            type_arguments: Union[List[TypeArgument], None] = None,
            inner_name: Union[str, None] = None,
            inner_type_arguments: Union[List[TypeArgument], None] = None,
    ) -> None:
        """
        :param name: The name of the class.
        :param type_arguments: Any generic type arguments given for the class.
        :param inner_name: The name of the inner classes, if this is one.
        :param inner_type_arguments: The type arguments of the inner class, if this is one.
        """
        
        self.name = name
        self.type_arguments = TypeArgumentList()
        self.inner_name = inner_name
        self.inner_type_arguments = TypeArgumentList()

        if type_arguments is not None:
            self.type_arguments.extend(type_arguments)
        if inner_type_arguments is not None:
            self.inner_type_arguments.extend(inner_type_arguments)

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
        if isinstance(other, str):
            return other == self.name
        elif isinstance(other, ClassOrInterfaceType):
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
            
        return False

    def __hash__(self) -> int:
        return hash((self.name, self.type_arguments, self.inner_name, self.inner_type_arguments))

    def to_verification_type(self) -> VerificationType:
        return ClassOrInterfaceType(self.name)  # Remove any generic data

    def can_merge(self, other: VerificationType) -> bool:
        return isinstance(other, ClassOrInterfaceType) or other.can_merge(self)


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
        return isinstance(other, ArrayType) and other.dimension == self.dimension and other.element_type == self.element_type

    def __hash__(self) -> int:
        return hash((self.element_type, self.dimension))

    def to_verification_type(self) -> VerificationType:
        if isinstance(self.element_type, ClassOrInterfaceType):  # Strip any signature info, if necessary
            return ArrayType(self.element_type.to_verification_type(), self.dimension)
        return self

    def can_merge(self, other: VerificationType) -> bool:
        return isinstance(other, ArrayType) or isinstance(other, ClassOrInterfaceType) or other.can_merge(self)


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
        if isinstance(other, str):
            return other == self.identifier
        elif isinstance(other, TypeVariable):
            return other.identifier == self.identifier

        return False

    def __hash__(self) -> int:
        return hash(self.identifier)

    def to_verification_type(self) -> VerificationType:
        raise TypeError("Cannot create verification type from %r." % self)

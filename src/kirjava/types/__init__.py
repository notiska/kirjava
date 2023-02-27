#!/usr/bin/env python3

__all__ = (
    "class_", "array",
    "void_t",
    "byte_t", "short_t", "char_t", "bool_t",
    "int_t", "long_t",
    "float_t", "double_t",
    "return_address_t",
    "object_t", "cloneable_t", "serializable_t", 
    "throwable_t", "exception_t",
    "string_t",
    "abstractmethoderror_t",
    "arithmeticexception_t",
    "arrayindexoutofboundsexception_t",
    "arraystoreexception_t",
    "classcastexception_t",
    "illegalaccesserror_t",
    "illegalmonitorstateexception_t",
    "incompatibleclasschangeerror_t",
    "negativearraysizeexception_t",
    "nullpointerexception_t",
    "unsatisfiedlinkerror_t",
    "byte_array_t", "short_array_t", "int_array_t",
    "long_array_t",
    "char_array_t",
    "float_array_t", "double_array_t",
    "bool_array_t",
    "object_array_t",
    "string_array_t",
    "top_t", "null_t",
    "this_t", "uninit_this_t",
    "VerificationType", "BaseType", "PrimitiveType", "ReferenceType",
    "ArrayType", "ClassOrInterfaceType",
)

"""
JVM types, (somewhat loosely) from the Oracle specification.
"""

from abc import ABC, abstractmethod
from typing import Any, Iterable


class VerificationType(ABC):
    """
    A verification type as seen in the stack map table.
    """

    __slots__ = ()

    internal_size = 1

    @abstractmethod
    def can_merge(self, other: "VerificationType") -> bool:
        """
        :return: Can this type merge with the other given type?
        """

        ...


class BaseType(ABC):
    """
    A base Java type.
    """

    internal_size = 1  # For wide types

    @abstractmethod
    def to_verification_type(self) -> VerificationType:
        """
        Converts this base type into a verification type.
        
        :return: The verification type.
        """

        ...


class TypeBound(ABC):
    """
    Something that bounds type variables.
    """

    ...


class TypeArgument(ABC):
    """
    A type parameter is used to declare a type variable for generics.
    """

    ...


class TypeArgumentList:
    """
    A list of type arguments.
    """

    __slots__ = ("arguments",)

    def __init__(self, arguments: Iterable[TypeArgument]) -> None:
        """
        :param arguments: The type arguments.
        """

        self.arguments = tuple(arguments)

    def __repr__(self) -> str:
        return "<TypeArgumentList(arguments=%r) at %x>" % (self.arguments, id(self))

    def __str__(self) -> str:
        return "<%s>" % (", ".join(map(str, self.arguments)))

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        return isinstance(other, TypeArgumentList) and other.arguments == self.arguments

    def __hash__(self) -> int:
        return hash(self.arguments)

    def __bool__(self) -> bool:
        return bool(self.arguments)


class InvalidType(BaseType):
    """
    Used when parsing descriptors, indicates that an invalid descriptor is present.
    """

    __slots__ = ("descriptor",)

    name = "invalid"

    def __init__(self, descriptor: str) -> None:
        self.descriptor = descriptor

    def __repr__(self) -> str:
        return "<InvalidType(%r) at %x>" % (self.descriptor, id(self))

    def __str__(self) -> str:
        return "invalid"

    def __eq__(self, other: Any) -> bool:
        return type(other) is InvalidType and other.descriptor == self.descriptor

    def __hash__(self) -> int:
        return hash(self.descriptor)

    def to_verification_type(self) -> VerificationType:
        raise TypeError("Cannot create verification type from %r." % self)


class PrimitiveType(BaseType, ABC):
    """
    A Java primitive type.
    """

    name = "base"
    byte_size = 1

    def __repr__(self) -> str:
        return "<%s() at %x>" % (self.__class__.__name__, id(self))

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: Any) -> bool:
        return other is self or type(other) is self.__class__


class ReferenceType(BaseType, ABC):
    """
    A Java reference type.
    """

    def __repr__(self) -> str:
        return "<%s() at %x>" % (self.__class__.__name__, id(self))

    def __eq__(self, other: Any) -> bool:
        return other is self or type(other) is self.__class__

    @abstractmethod
    def rename(self, name: str) -> "ReferenceType":
        """
        Returns the renamed reference type. This may vary based on the reference type in question, some many not change
        at all.

        :param name: The new name.
        :return: The new reference type, renamed (if applicable).
        """

        ...


from .primitive import *
from .reference import *

# Aliases for easier API usage
array = ArrayType
class_ = ClassOrInterfaceType

# ------------------------------ Primitives ------------------------------ #

void_t = VoidType()

byte_t = ByteType()
short_t = ShortType()
int_t = IntegerType()

long_t = LongType()

char_t = CharacterType()

float_t = FloatType()
double_t = DoubleType()

bool_t = BooleanType()

return_address_t = ReturnAddressType()


# ------------------------------ Reference ------------------------------ #

# Bases
object_t = ClassOrInterfaceType("java/lang/Object")
class_t = ClassOrInterfaceType("java/lang/Class")

throwable_t = ClassOrInterfaceType("java/lang/Throwable")
exception_t = ClassOrInterfaceType("java/lang/Exception")

cloneable_t = ClassOrInterfaceType("java/lang/Cloneable")
serializable_t = ClassOrInterfaceType("java/io/Serializable")

string_t = ClassOrInterfaceType("java/lang/String")

# Exceptions
abstractmethoderror_t = ClassOrInterfaceType("java/lang/AbstractMethodError")
arithmeticexception_t = ClassOrInterfaceType("java/lang/ArithmeticException")
arrayindexoutofboundsexception_t = ClassOrInterfaceType("java/lang/ArrayIndexOutOfBoundsException")  # Lollll idk
arraystoreexception_t = ClassOrInterfaceType("java/lang/ArrayStoreException")
classcastexception_t = ClassOrInterfaceType("java/lang/ClassCastException")
illegalaccesserror_t = ClassOrInterfaceType("java/lang/IllegalAccessError")
illegalmonitorstateexception_t = ClassOrInterfaceType("java/lang/IllegalMonitorStateException")
incompatibleclasschangeerror_t = ClassOrInterfaceType("java/lang/IncompatibleClassChangeError")
negativearraysizeexception_t = ClassOrInterfaceType("java/lang/NegativeArraySizeException")
nullpointerexception_t = ClassOrInterfaceType("java/lang/NullPointerException")
unsatisfiedlinkerror_t = ClassOrInterfaceType("java/lang/UnsatisfiedLinkError")

# Arrays
byte_array_t = ArrayType(byte_t)
short_array_t = ArrayType(short_t)
int_array_t = ArrayType(int_t)

long_array_t = ArrayType(long_t)

char_array_t = ArrayType(char_t)

float_array_t = ArrayType(float_t)
double_array_t = ArrayType(double_t)

bool_array_t = ArrayType(bool_t)

object_array_t = ArrayType(object_t)
class_array_t = ArrayType(class_t)
string_array_t = ArrayType(string_t)

# ------------------------------ Verification ------------------------------ #

from .verification import *

top_t = Top()
null_t = Null()
this_t = This()
# uninit_t = Uninitialized()
uninit_this_t = UninitializedThis()

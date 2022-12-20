#!/usr/bin/env python3

"""
Primitive Java types.
"""

from abc import ABC

from . import PrimitiveType, VerificationType


class VoidType(PrimitiveType):
    """
    (EVIL!!!) Represents a void type.
    """

    __slots__ = ()

    name = "void"

    def __hash__(self) -> int:
        return 8534155699062141029

    def to_verification_type(self) -> VerificationType:
        raise TypeError("Cannot create verification type from %r." % self)


class NumericType(PrimitiveType, ABC):
    """
    Represents a numeric type in Java.
    """

    __slots__ = ()


class IntegralType(NumericType, ABC):
    """
    Represents bytes, shorts, ints, longs (and chars).
    """

    ...


class FloatingPointType(NumericType, ABC):
    """
    Represents any floating point type.
    """

    ...


class ByteType(IntegralType):
    """
    An 8-bit signed integer, default value is 0.
    """

    name = "byte"
    byte_size = 1

    def __hash__(self) -> int:
        return 7095830666993561701

    def to_verification_type(self) -> "IntegerType":
        return IntegerType()  # All this stuff on the bytecode level is just an integer


class ShortType(IntegralType):
    """
    A 16-bit signed integer, default value is 0.
    """

    name = "short"
    byte_size = 2

    def __hash__(self) -> int:
        return 7525359346855276645

    def to_verification_type(self) -> "IntegerType":
        return IntegerType()


class IntegerType(IntegralType, VerificationType):
    """
    A 32-bit signed integer, default value is 0.
    """

    name = "int"
    byte_size = 4

    def __hash__(self) -> int:
        return 7306920462686711909

    def to_verification_type(self) -> "IntegerType":
        return self  # Nothing really to do here

    def can_merge(self, other: VerificationType) -> bool:
        return other == self


class LongType(IntegralType, VerificationType):
    """
    A 64-bit signed integer, default value is 0.
    """

    name = "long"
    byte_size = 8
    internal_size = 2

    def __hash__(self) -> int:
        return 7306920462686711909

    def to_verification_type(self) -> "LongType":
        return self

    def can_merge(self, other: VerificationType) -> bool:
        return other == self


class CharacterType(IntegralType):
    """
    A single unicode character represented by a 16-bit unsigned integer.
    """

    name = "char"
    byte_size = 2

    def __hash__(self) -> int:
        return 7166464449308094565

    def to_verification_type(self) -> IntegerType:
        return IntegerType()


class FloatType(FloatingPointType, VerificationType):
    """
    A 32-bit floating point number, default value is +0.
    """

    name = "float"
    byte_size = 4

    def __hash__(self) -> int:
        return 7813571031309316197

    def to_verification_type(self) -> "FloatType":
        return self

    def can_merge(self, other: VerificationType) -> bool:
        return other == self


class DoubleType(FloatingPointType, VerificationType):
    """
    A 64-bit floating point number, default value is +0.
    """

    name = "double"
    byte_size = 8
    internal_size = 2

    def __hash__(self) -> int:
        return 8458442233156825189

    def to_verification_type(self) -> "DoubleType":
        return self

    def can_merge(self, other: VerificationType) -> bool:
        return other == self


class BooleanType(PrimitiveType):
    """
    A boolean type, default value is false.
    """

    name = "boolean"
    byte_size = 1

    def __hash__(self) -> int:
        return 7810756255772405861

    def to_verification_type(self) -> IntegerType:
        return IntegerType()


class ReturnAddressType(PrimitiveType, VerificationType):
    """
    A 16-bit signed integer, representing a bytecode offset, this has no actual type in the Java language.
    """

    name = "returnAddress"
    byte_size = 2

    def __hash__(self) -> int:
        return 8243121632684109925

    def to_verification_type(self) -> "ReturnAddressType":
        return self  # Might not be applicable the StackMapTable but is still required

    def can_merge(self, other: VerificationType) -> bool:
        return other == self

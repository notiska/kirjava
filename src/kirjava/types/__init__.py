#!/usr/bin/env python3

__all__ = (
    "descriptor", "signature",

    "primitive_t",
    "reference_t",
    "top_t",
    "void_t", "reserved_t",

    "boolean_t", "byte_t", "short_t", "char_t", "int_t", "long_t",
    "float_t", "double_t",
    "return_address_t",

    "uninitialized_t", "uninitialized_this_t",

    "object_t", "class_t", "throwable_t", "string_t",
    "method_type_t", "method_handle_t",

    "boxed_boolean_t", "boxed_byte_t", "boxed_short_t", "boxed_char_t", "boxed_int_t", "boxed_long_t",
    "boxed_float_t", "boxed_double_t",

    "null_t",

    "array_t",
    "boolean_array_t",
    "byte_array_t", "short_array_t", "char_array_t", "int_array_t", "long_array_t",
    "float_array_t", "double_array_t",

    "Type", "Invalid", "Verification",
    "Primitive", "Reference",
    "OneWord", "TwoWord",
    "ReturnAddress",
    "Uninitialized",
    "Array", "Class", "Interface",
)

"""
JVM, verification and (some) JLS types.
 - https://docs.oracle.com/javase/specs/jvms/se20/html/jvms-2.html#jvms-2.2
 - https://docs.oracle.com/javase/specs/jvms/se20/html/jvms-4.html#jvms-4.10.1.2
"""

from functools import cached_property
from typing import Any, Optional
from weakref import WeakValueDictionary

from ..abc import Source


class Type:
    """
    Base type class.
    """

    __slots__ = ("__weakref__", "name", "wide", "abstract", "_hash")

    def __init__(self, name: str, *, wide: bool = False, abstract: bool = False) -> None:
        self.name = name
        self.wide = wide
        self.abstract = abstract

        self._hash = hash((name, wide, abstract))

    def __repr__(self) -> str:
        return "<%s(name=%r)>" % (type(self).__name__, self.name)

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __hash__(self) -> int:
        return self._hash

    def mergeable(self, other: "Type") -> bool:
        """
        :return: Can this type be merged with the other type?
        """

        # top_t.mergeable(int_t) -> True
        # int_t.mergeable(top_t) -> False
        return self == other or (self.abstract and type(other) is not type(self) and isinstance(other, type(self)))

    def as_vtype(self) -> "Verification":
        """
        :return: The verification type corresponding to this type.
        """

        raise TypeError("Cannot convert %r to a verification type." % self)


class Invalid(Type):
    """
    A way of representing invalid/raw descriptors.
    """

    __slots__ = ("descriptor",)

    def __init__(self, descriptor: str) -> None:
        super().__init__("invalid")
        self.descriptor = descriptor

    def __repr__(self) -> str:
        return "<Invalid(descriptor=%r)>" % self.descriptor

    def mergeable(self, other: Type) -> bool:
        return False


class Verification(Type):
    """
    Verification types. These are used in the bytecode verifier, and (may) not actually exist.
    """

    __slots__ = ()

    def as_vtype(self) -> "Verification":
        return self


class Primitive(Verification):
    """
    Primitive types.
    """

    __slots__ = ("boxed",)

    def __init__(self, name: str, boxed: Optional[Type] = None, *, wide: bool = False, abstract: bool = False) -> None:
        super().__init__(name, wide=wide)
        self.boxed = boxed


class Reference(Verification):
    """
    Reference types.
    """

    __slots__ = ()


# Verification type hierarchy:
#
#                              top
#                  ____________/\____________
#                 /                          \
#                /                            \
#             oneWord                       twoWord
#            /   |   \                     /       \
#           /    |    \                   /         \
#         int  float  reference        long        double
#                      /     \
#                     /       \_____________
#                    /                      \
#                   /                        \
#            uninitialized                    +------------------+
#             /         \                     |  Java reference  |
#            /           \                    |  type hierarchy  |
# uninitializedThis  uninitialized(Offset)    +------------------+
#                                                      |
#                                                      |
#                                                     null


class _Top(Verification):
    """
    The top type. Used for the bytecode verifier.
    """

    __slots__ = ()


class OneWord(_Top):
    """
    A one-word type. Used for the bytecode verifier.
    """

    __slots__ = ()

    def __init__(self, name: str = "oneWord", *, wide: bool = False, abstract: bool = False) -> None:
        super().__init__(name, wide=False, abstract=abstract)


class TwoWord(_Top):
    """
    A two-word type. Used for the bytecode verifier.
    """

    __slots__ = ()

    def __init__(self, name: str = "twoWord", *, wide: bool = True, abstract: bool = False) -> None:
        super().__init__(name, wide=True, abstract=abstract)


class _Integer(Primitive, OneWord):
    """
    Integer types, these include types that under-the-hood are integers.
    """

    __slots__ = ()

    def mergeable(self, other: "Type") -> bool:
        # byte_t.mergeable(int_t) -> True
        # int_t.mergeable(byte_t) -> False
        return other is int_t  # self is int_t and isinstance(other, _Integer)

    def as_vtype(self) -> "_Integer":
        return int_t


class _Long(Primitive, TwoWord):
    """
    The long type.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("long", Class("java/lang/Long"))


class _Float(Primitive, OneWord):
    """
    The float (32-bit) type.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("float", Class("java/lang/Float"))


class _Double(Primitive, TwoWord):
    """
    The double (64-bit) type.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("double", Class("java/lang/Double"))


class ReturnAddress(Primitive, OneWord):
    """
    A returnAddress type. Deprecated now.
    """

    __slots__ = ("source",)

    def __init__(self, source: Optional[Source]) -> None:
        super().__init__("returnAddress")
        self.source = source

        self._hash = hash((self._hash, self.source))

    def __repr__(self) -> str:
        return "<ReturnAddress(source=%r)>" % self.source

    def __eq__(self, other: Any) -> bool:
        return type(other) is ReturnAddress and self.source == other.source

    def __hash__(self) -> int:
        return self._hash

    def mergeable(self, other: "Type") -> bool:
        return type(other) is ReturnAddress and (self.source is None or self.source == other.source)


class Uninitialized(Reference, OneWord):
    """
    An uninitialized reference type.
    """

    __slots__ = ("source",)

    # _cached: WeakValueDictionary[Source, "Uninitialized"] = WeakValueDictionary()
    #
    # def __new__(cls, source: Optional[Source]) -> "Uninitialized":
    #     if source is None:
    #         return super().__new__(cls)
    #
    #     cached = cls._cached.get(source)
    #     if cached is not None:
    #         return cached
    #
    #     self = super().__new__(cls)
    #     cls._cached[source] = self
    #     return self

    def __init__(self, source: Optional[Source]) -> None:
        super().__init__("uninitialized")
        self.source = source

        self._hash = hash((self._hash, self.source))

    def __repr__(self) -> str:
        return "<Uninitialized(source=%r)>" % self.source

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Uninitialized) and (self.source is None or self.source == other.source)

    def __hash__(self) -> int:
        return self._hash


class _UninitializedThis(Uninitialized):  # Not fully true to the spec, note.
    """
    An uninitialized reference type for the current class.
    """

    __slots__ = ()

    # def __new__(cls) -> "_UninitializedThis":
    #     return super().__new__(cls, None)

    def __init__(self) -> None:
        super().__init__(None)
        self.name = "uninitializedThis"

        self._hash = hash(self.name)

    def __eq__(self, other: Any) -> bool:
        return type(other) is _UninitializedThis

    def __hash__(self) -> int:
        return self._hash


class _JavaReference(Reference, OneWord):
    """
    A Java reference type, i.e. it exists within the actual Java type hierarchy.
    """

    __slots__ = ()

    def mergeable(self, other: Type) -> bool:
        return isinstance(other, _JavaReference)


class Array(_JavaReference):
    """
    An array type.
    """

    __slots__ = ("__dict__", "element")

    _cached: WeakValueDictionary[Type, "Array"] = WeakValueDictionary()

    @classmethod
    def from_dimension(cls, element: Type, dimension: int) -> "Array":
        """
        Creates an array type from a dimension and element type.

        :param element: The element type.
        :param dimension: The dimension.
        :return: The array type.
        """

        if not dimension:
            raise ValueError("Invalid dimension 0.")

        type_ = cls(element)
        for _ in range(dimension - 1):
            type_ = cls(type_)
        return type_

    @cached_property  # Possible because we know this is immutable.
    def lowest_element(self) -> Type:
        """
        :return: The lowest element type of this array type.
        """

        element = self.element
        while type(element) is Array:
            element = element.element

        return element

    @cached_property
    def dimensions(self) -> int:
        """
        :return: The dimensions of this array type.
        """

        dimension = 1

        element = self.element
        while type(element) is Array:
            dimension += 1
            element = element.element

        return dimension

    @cached_property
    def primitive(self) -> bool:
        """
        :return: Is this array type a primitive array type?
        """

        return isinstance(self.element, Primitive)  # and not self.element.abstract

    def __new__(cls, element: Type) -> "Array":
        cached = cls._cached.get(element)
        if cached is not None:
            return cached

        self = super().__new__(cls)
        self._cached[element] = self
        return self

    def __init__(self, element: Type) -> None:
        super().__init__(element.name + "[]", abstract=element.abstract)
        self.element = element

        self._hash = hash((self._hash, self.element))

    def __repr__(self) -> str:
        return "<Array(element=%r)>" % self.element

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Array) and self.element == other.element

    def __hash__(self) -> int:
        return self._hash

    # We won't get into specifics here as it causes issues in the assembler. It's notable that arrays can just be
    # generified to java/lang/Object, making this technically valid. If a more precise comparison is needed the element
    # field is accessible.
    # def mergeable(self, other: Type) -> bool:
    #     if isinstance(other, Array):
    #         return self.element.mergeable(other.element)
    #     return super().mergeable(other)


class Class(_JavaReference):
    """
    A class type.
    """

    __slots__ = ()

    _cached: WeakValueDictionary[str, "Class"] = WeakValueDictionary()

    def __new__(cls, name: str) -> "Class":
        cached = cls._cached.get(name)
        if cached is not None:
            return cached

        self = super().__new__(cls)
        cls._cached[name] = self
        return self

    def as_interface(self) -> "Interface":
        return Interface(self.name)


# Although this is distinct from a class according to the spec, it's not always possible to distinguish between a class
# and an interface if we have an incomplete class hierarchy, so in terms of types, we treat them almost the same.
class Interface(Class):
    """
    An interface type.
    """

    __slots__ = ()

    _cached: WeakValueDictionary[str, "Interface"] = WeakValueDictionary()

    def __new__(cls, name: str) -> "Interface":
        cached = cls._cached.get(name)
        if cached is not None:
            return cached

        self = super().__new__(cls, name)
        cls._cached[name] = self
        return self

    def as_interface(self) -> "Interface":
        return self


# Another slight inaccuracy as this should really extend (Array, Class, Interface). That's not done here to avoid all
# the extra attributes that this would gain. Instead, we just emulate the behaviour with the mergeable method.
class _Null(_JavaReference):
    """
    The null type.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("null")
        self._hash = hash(self.name)

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __hash__(self) -> int:
        return self._hash

    def mergeable(self, other: Type) -> bool:
        return self is other or isinstance(other, _JavaReference)


primitive_t = Primitive("primitive", abstract=True)
reference_t = Reference("reference", abstract=True)

top_t = _Top("top", abstract=True)

void_t = Primitive("void")
# The second half of a long or double. Not a Primitive as we want to be able to merge it into a top type in certain
# cases (https://discord.com/channels/443258489146572810/887649798918909972/1118900676764897280). Credits to xxDark for
# this insight.
reserved_t = OneWord("__reserved")

# Integer types
boolean_t = _Integer("boolean", Class("java/lang/Boolean"))
byte_t    = _Integer("byte",    Class("java/lang/Byte"))
char_t    = _Integer("char",    Class("java/lang/Character"))
short_t   = _Integer("short",   Class("java/lang/Short"))
int_t     = _Integer("int",     Class("java/lang/Integer"))

long_t  = _Long()

float_t = _Float()
double_t = _Double()

return_address_t = ReturnAddress(None)

uninitialized_t = Uninitialized(None)
uninitialized_this_t = _UninitializedThis()

# Important class types
object_t    = Class("java/lang/Object")
class_t     = Class("java/lang/Class")
throwable_t = Class("java/lang/Throwable")
string_t    = Class("java/lang/String")

method_type_t   = Class("java/lang/invoke/MethodType")
method_handle_t = Class("java/lang/invoke/MethodHandle")

# Boxed primitive types
boxed_boolean_t = boolean_t.boxed
boxed_byte_t    = byte_t.boxed
boxed_char_t    = char_t.boxed
boxed_short_t   = short_t.boxed
boxed_int_t     = int_t.boxed
boxed_long_t    = long_t.boxed
boxed_float_t   = float_t.boxed
boxed_double_t  = double_t.boxed

null_t = _Null()

array_t = Array(top_t)

# Basic array types
boolean_array_t = Array(boolean_t)
byte_array_t    = Array(byte_t)
char_array_t    = Array(char_t)
short_array_t   = Array(short_t)
int_array_t     = Array(int_t)
long_array_t    = Array(long_t)
float_array_t   = Array(float_t)
double_array_t  = Array(double_t)

from . import descriptor, signature

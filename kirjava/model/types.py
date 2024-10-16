#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "primitive_t",
    "reference_t",
    "top_t",
    "void_t", "reserved_t",

    "boolean_t", "byte_t", "short_t", "char_t", "int_t", "long_t",
    "float_t", "double_t",
    "return_address_t",

    "uninitialized_t", "uninitialized_this_t",

    "object_t", "class_t", "string_t", "throwable_t", "error_t", "exception_t",
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
    "Top", "OneWord", "TwoWord",
    "ReturnAddress",
    "Uninitialized",
    "Array", "Class", "Interface",
)

from functools import cached_property
from weakref import WeakValueDictionary


class Type:
    """
    The base type class.

    Attributes
    ----------
    name: str
        The name of this type.
    wide: bool
        Whether this type takes up two words.
    abstract: bool
        Whether this type actually exists in the JVM type hierarchy.

    Methods
    -------
    assignable(self, other: Type) -> bool
        Checks if a value of this type is assignable to a value of the provided type.
    verification(self) -> Verification
        Returns the verification type that represents this type.
    """

    __slots__ = ()

    name: str
    wide: bool
    abstract: bool

    def __repr__(self) -> str:
        raise NotImplementedError(f"repr() is not implemented for {type(self)!r}")

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError(f"== is not implemented for {type(self)!r}")

    def __hash__(self) -> int:
        raise NotImplementedError(f"hash() is not implemented for {type(self)!r}")

    def assignable(self, other: "Type") -> bool:
        """
        Checks if another type is assignable to this type.

        The assumption is that this type acts as the l-value.
        This is such that:
         - `top_t.assignable(int_t) -> False`
         - `int_t.assignable(top_t) -> True`
        Or, in pseudocode:
         - `top x; int y; x = y;` is valid.
         - `int x; top y; x = y;` is not valid.
        """

        raise NotImplementedError(f"assignable() is not implemented for {type(self)!r}")

    def verification(self) -> "Verification":
        """
        Returns the verification type that represents this type.

        Raises
        ------
        ValueError
            If a verification type does not exist for this type.
        """

        raise ValueError(f"cannot make verification type from {self!r}")


class Invalid(Type):
    """
    A way of representing invalid/raw descriptors.

    Attributes
    ----------
    descriptor: str
        The invalid descriptor that this type represents.
    """

    __slots__ = ("_descriptor", "_hash")

    name = "invalid"
    wide = False
    abstract = False

    @property
    def descriptor(self) -> str:
        return self._descriptor

    def __init__(self, descriptor: str) -> None:
        self._descriptor = descriptor
        self._hash = hash((Invalid, descriptor))

    def __repr__(self) -> str:
        return f"<Invalid(descriptor={self._descriptor!r})>"

    def __str__(self) -> str:
        return f"invalid<{self._descriptor!r}>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Invalid) and self._descriptor == other._descriptor

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        return False  # Invalid types shouldn't be assignable to anything, even themselves.


class Verification(Type):
    """
    A verification type.

    These are used in the bytecode verifier, and may or may not actually exist.
    """

    __slots__ = ()

    def verification(self) -> "Verification":
        return self


class Primitive(Verification):
    """
    A primitive type.

    Attributes
    ----------
    boxed: Type | None
        The boxed type that Java would use to store this primitive.
    """

    __slots__ = ("_boxed",)

    @property
    def boxed(self) -> Type | None:
        return self._boxed

    def __init__(self, boxed: Type | None = None) -> None:
        self._boxed = boxed

    def __repr__(self) -> str:
        if self.boxed is not None:
            return f"<Primitive(name={self.name!r}, boxed={self.boxed!s})>"
        return f"<Primitive(name={self.name!r})>"


class Reference(Verification):
    """
    A reference type.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return f"<Reference(name={self.name!r}>"


class _Primitive(Primitive):
    """
    Primitive type for direct usage.
    """

    __slots__ = ("_hash",)

    name = "primitive"
    wide = False  # Not necessarily true, but not much we can do about it.
    abstract = True

    def __init__(self) -> None:
        super().__init__()
        self._hash = id(self)

    def __repr__(self) -> str:
        # Another trick to avoid references to internal classes. This is simply to give the appearance of outside
        # consistency.
        return "<Primitive>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Primitive)

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        return isinstance(other, Primitive)


class _Reference(Reference):
    """
    Reference type for direct usage.
    """

    __slots__ = ("_hash",)

    name = "reference"
    wide = False  # Not necessarily true, but not much we can do about it.
    abstract = True

    def __init__(self) -> None:
        self._hash = id(self)

    def __repr__(self) -> str:
        return "<Reference>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Reference)

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        return isinstance(other, Reference)


class _Void(Primitive):
    """
    A void type.

    Although this cannot be used as a concrete type, it is still required to
    represent method return types.
    """

    __slots__ = ("_hash",)

    name = "void"
    wide = False
    abstract = False

    def __init__(self) -> None:
        super().__init__(Class("java/lang/Void"))  # Technically true, but only used for reflection.
        self._hash = id(self)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Void)

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        return False  # This is a check that should never happen in the first place.


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

class Top(Verification):
    """
    A top type.

    Represents the parent of all verification types.
    """

    __slots__ = ()

    abstract = True


class _Top(Top):
    """
    Top type for direct usage.
    """

    __slots__ = ("_hash",)

    name = "top"
    wide = False
    abstract = True

    def __init__(self) -> None:
        self._hash = id(self)

    def __repr__(self) -> str:
        return "<Top>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Top)

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        return isinstance(other, Top)


class OneWord(Top):
    """
    A one-word type.

    Used by the bytecode verifier.
    """

    __slots__ = ()

    wide = False

    def __repr__(self) -> str:
        return f"<OneWord(name={self.name!r}>"

    def assignable(self, other: Type) -> bool:
        return isinstance(other, OneWord)


class TwoWord(Top):
    """
    A two-word type.

    Used by the bytecode verifier.
    """

    __slots__ = ()

    wide = True

    def __repr__(self) -> str:
        return f"<TwoWord(name={self.name!r}>"

    def assignable(self, other: Type) -> bool:
        return isinstance(other, TwoWord)


class _Reserved(OneWord):
    """
    The second half of a long or double.

    Not a Primitive as we want to be able to merge it into a top type in certain
    cases.
    https://discord.com/channels/443258489146572810/887649798918909972/1118900676764897280
    Credits to xxDark for this insight.
    """

    __slots__ = ("_hash",)

    name = "reserved"
    abstract = False

    def __init__(self) -> None:
        self._hash = id(self)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Reserved)

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        # There shouldn't be a comparison where this has to happen. The assignability check should rather be on the wide
        # type itself, so if this happens, it should always be incorrect.
        return False


class _Integer(Primitive, OneWord):
    """
    An integer type.

    This can represent 32-bit integers or any type that is actually an integer at the
    JVM level (i.e. byte, char...).
    """

    __slots__ = ("_name", "_width", "_hash")

    abstract = False

    @property  # type: ignore[override]
    def name(self) -> str:
        return self._name

    def __init__(self, name: str, width: int, boxed: Type | None) -> None:
        super().__init__(boxed)
        self._name = name
        self._width = width
        self._hash = id(self)

    def __repr__(self) -> str:
        return f"<Primitive(name={self.name!r})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Integer) and self._width == other._width

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        if not isinstance(other, _Integer):
            return False
        elif other._width < 0:
            return False
        return self._width >= other._width

    def verification(self) -> "_Integer":
        return int_t


class _Long(Primitive, TwoWord):
    """
    A long (64-bit integer) type.
    """

    __slots__ = ("_hash",)

    name = "long"
    abstract = False

    def __init__(self) -> None:
        super().__init__(Class("java/lang/Long"))
        self._hash = id(self)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Long)

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        if isinstance(other, _Integer):
            return other._width > 0
        return other is self


class _Float(Primitive, OneWord):
    """
    A 32-bit float type.
    """

    __slots__ = ("_hash",)

    name = "float"
    abstract = False

    def __init__(self) -> None:
        super().__init__(Class("java/lang/Float"))
        self._hash = id(self)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Float)

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        if isinstance(other, _Integer):
            return other._width > 0
        return other is self or isinstance(other, _Long)


class _Double(Primitive, TwoWord):
    """
    A double (64-bit float) type.
    """

    __slots__ = ("_hash",)

    name = "double"
    abstract = False

    def __init__(self) -> None:
        super().__init__(Class("java/lang/Double"))
        self._hash = id(self)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Double)

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        if isinstance(other, _Integer):
            return other._width > 0
        return self == other or isinstance(other, (_Float, _Long))


class ReturnAddress(Primitive, OneWord):
    """
    A returnAddress type.

    Attributes
    ----------
    source: object | None
        The source of this return address.
        Used to indicate where to jump back to.
    """

    __slots__ = ("_source", "_hash")

    name = "returnAddress"
    abstract = False

    @property
    def source(self) -> object | None:
        return self.source

    def __init__(self, source: object | None) -> None:
        super().__init__(None)
        self._source = source
        self._hash = hash((ReturnAddress, source))

    def __repr__(self) -> str:
        if self._source is not None:
            return f"<ReturnAddress(source={self._source!s})>"
        return "<ReturnAddress>"

    def __str__(self) -> str:
        if self._source is not None:
            return f"returnAddress<{self._source!s}>"
        return "returnAddress"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ReturnAddress) and (self._source is None or self._source == other._source)

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        return self == other


class Uninitialized(Reference, OneWord):
    """
    An uninitialized reference type.

    Attributes
    ----------
    source: object | None
        The source of this uninitialised type.
        Used to indicate the type of the initialised value.
    """

    __slots__ = ("_source", "_hash")

    name = "uninitialized"
    abstract = False

    @property
    def source(self) -> object | None:
        return self._source

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

    def __init__(self, source: object | None) -> None:
        self._source = source
        self._hash = hash((Uninitialized, source))

    def __repr__(self) -> str:
        return f"<Uninitialized(source={self._source!s})>"

    def __str__(self) -> str:
        if self._source is not None:
            return f"uninitialized<{self._source!s}>"
        return "uninitialized"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Uninitialized) and (self._source is None or self._source == other._source)

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        return self == other


class _UninitializedThis(Uninitialized):  # Not fully true to the spec, note.
    """
    An uninitialized reference type for the current class.
    """

    __slots__ = ()

    name = "uninitializedThis"

    def __init__(self) -> None:
        super().__init__(None)
        self._hash = id(self)

    def __str__(self) -> str:
        return "uninitializedThis"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _UninitializedThis)

    def __hash__(self) -> int:
        return self._hash


class _JavaReference(Reference, OneWord):
    """
    A Java reference type.

    These types concretely exist within the JVM type hierarchy.
    """

    __slots__ = ()


class Array(_JavaReference):
    """
    An array type.

    Attributes
    ----------
    element: Type
        The element type of this array.
    dimension: int
        The dimensions of this array (i.e. `4` would mean `[[[[I` in an int array).
    lowest: Type
        The lowest element type of this array, if multidimensional.
    primitive: bool
        Whether this represents a primitive array type.

    Methods
    -------
    nested(element: Type, dimension: int) -> Array
        Creates a nested array type from the provided element type and dimension.
    """

    __slots__ = (
        "__weakref__",
        "_name", "_abstract", "_element", "_hash",
    )

    _cached: WeakValueDictionary[Type, "Array"] = WeakValueDictionary()

    @classmethod
    def nested(cls, element: Type, dimension: int) -> "Array":
        """
        Creates a nested array type from the provided element type and dimension.

        Parameters
        ----------
        element: Type
            The innermost element type of this array.
        dimension: int
            The dimensionality of this array.

        Raises
        ------
        ValueError
            If an invalid dimension was provided.
        """

        if dimension <= 0:
            raise ValueError(f"invalid dimension {dimension} for array type")
        type_ = cls(element)
        for _ in range(dimension - 1):
            type_ = cls(type_)
        return type_

    @property  # type: ignore[override]
    def name(self) -> str:
        return self._name

    @property  # type: ignore[override]
    def abstract(self) -> bool:
        return self._abstract

    @property
    def element(self) -> Type:
        return self._element

    @cached_property
    def dimension(self) -> int:
        dimension = 1
        element = self._element
        while isinstance(element, Array):
            dimension += 1
            element = element._element
        return dimension

    @cached_property  # Possible because we know this is immutable.
    def lowest(self) -> Type:
        element = self._element
        while isinstance(element, Array):
            element = element._element
        return element

    @cached_property
    def primitive(self) -> bool:
        return isinstance(self._element, Primitive)  # and not self.element.abstract

    def __new__(cls, element: Type) -> "Array":
        cached = cls._cached.get(element)
        if cached is not None:
            return cached

        self = super().__new__(cls)
        self._cached[element] = self
        return self

    def __init__(self, element: Type) -> None:
        self._name = element.name + "[]"
        self._abstract = element.abstract
        self._element = element

        self._hash = hash((Array, element))

    def __repr__(self) -> str:
        return f"<Array(element={self._element!r})>"

    def __str__(self) -> str:
        return self._name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Array) and self._element == other._element

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        if isinstance(other, Array):
            return not isinstance(self._element, Primitive) and self._element.assignable(other._element)
        return isinstance(other, _Null)


class Class(_JavaReference):
    """
    A class type.

    Methods
    -------
    interface(self) -> Interface
        Creates an interface type from this class.
    """

    __slots__ = ("__weakref__", "_name", "_hash")

    abstract = False

    _cached: WeakValueDictionary[str, "Class"] = WeakValueDictionary()

    @property  # type: ignore[override]
    def name(self) -> str:
        return self._name

    def __new__(cls, name: str) -> "Class":
        cached = cls._cached.get(name)
        if cached is not None:
            return cached

        self = super().__new__(cls)
        cls._cached[name] = self
        return self

    def __init__(self, name: str) -> None:
        self._name = name
        self._hash = hash((Class, name))

    def __repr__(self) -> str:
        return f"<Class(name={self._name!r})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Class) and self._name == other._name

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        if self is object_t:
            return isinstance(other, _JavaReference)
        elif isinstance(other, Class):
            # Narrowing this down is not our responsibility here. The most basic check we'll do is if we're
            # java/lang/Object. Further checks require hierarchy knowledge, which we don't have here.
            return self._name == other._name or isinstance(other, _Null)
        return False

    def interface(self) -> "Interface":
        """
        Creates an interface type from this class.
        """

        return Interface(self._name)


# Although this is distinct from a class according to the spec, it's not always possible to distinguish between a class
# and an interface if we have an incomplete class hierarchy, so in terms of types, we treat them almost the same.
class Interface(Class):
    """
    An interface type.
    """

    __slots__ = ()

    _cached: WeakValueDictionary[str, "Interface"] = WeakValueDictionary()  # type: ignore[assignment]

    def __new__(cls, name: str) -> "Interface":
        cached = cls._cached.get(name)
        if cached is not None:
            return cached

        # Yeah this is actually correct, not sure why mypy is complaining here. Could be a bug?
        self: Interface = super().__new__(cls, name)  # type: ignore[assignment]
        cls._cached[name] = self
        return self

    def __repr__(self) -> str:
        return f"<Interface(name={self._name!r})>"

    def interface(self) -> "Interface":
        return self


# Another slight inaccuracy as this should really extend (Array, Class, Interface). That's not done here to avoid all
# the extra attributes that this would gain. Instead, we just emulate the behaviour with the assignable method.
class _Null(_JavaReference):
    """
    A null type.
    """

    __slots__ = ("_hash",)

    name = "null"
    abstract = False

    def __init__(self) -> None:
        self._hash = id(self)

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return self._hash

    def assignable(self, other: Type) -> bool:
        return isinstance(other, _Null)


primitive_t = _Primitive()
reference_t = _Reference()

top_t = _Top()

void_t = _Void()
reserved_t = _Reserved()

# Integer types.
# Boolean width is -1 to ensure that it cannot be assigned to by any integer type.
boolean_t = _Integer("boolean", -1, Class("java/lang/Boolean"))
byte_t    = _Integer("byte",    1, Class("java/lang/Byte"))
char_t    = _Integer("char",    2, Class("java/lang/Character"))
short_t   = _Integer("short",   2, Class("java/lang/Short"))
int_t     = _Integer("int",     4, Class("java/lang/Integer"))

long_t  = _Long()

float_t = _Float()
double_t = _Double()

return_address_t = ReturnAddress(None)

uninitialized_t = Uninitialized(None)
uninitialized_this_t = _UninitializedThis()

# Important class types.
object_t    = Class("java/lang/Object")
class_t     = Class("java/lang/Class")
string_t    = Class("java/lang/String")
throwable_t = Class("java/lang/Throwable")
error_t     = Class("java/lang/Error")
exception_t = Class("java/lang/Exception")

method_type_t   = Class("java/lang/invoke/MethodType")
method_handle_t = Class("java/lang/invoke/MethodHandle")

# Boxed primitive types.
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

# Basic array types.
boolean_array_t = Array(boolean_t)
byte_array_t    = Array(byte_t)
char_array_t    = Array(char_t)
short_array_t   = Array(short_t)
int_array_t     = Array(int_t)
long_array_t    = Array(long_t)
float_array_t   = Array(float_t)
double_array_t  = Array(double_t)

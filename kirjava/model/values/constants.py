#!/usr/bin/env python3

__all__ = (
    "Constant",
    "Null", "Index",
    "Integer", "Float", "Long", "Double",
    "Class", "String",
    "MethodHandle", "MethodType",
)

"""
Models for constant values.
"""

import numpy as np  # TODO: Support multiple backends.

from . import Value
# Mypy gets confused if we do import * because `Class` is also defined in types, so yea...
from ..types import (
    byte_t, char_t, class_t, double_t, float_t, int_t, long_t, method_handle_t, method_type_t, null_t, short_t,
    string_t, top_t,
    Primitive, Reference, Type,
)
# from ..types.descriptor import parse_reference
from ...pretty import pretty_repr


class Constant(Value):
    """
    A constant value.

    Attributes
    ----------
    type: Type
        The type that this constant represents.
    """

    __slots__ = ()

    type: Type


class Null(Constant):
    """
    A null constant.
    """

    __slots__ = ()

    type = null_t

    def __repr__(self) -> str:
        return "<Null>"

    def __str__(self) -> str:
        return "null"


class Index(Constant):
    """
    Represents an unloadable/unresolvable CP index.
    """

    __slots__ = ("index",)

    type = top_t

    def __init__(self, index: int) -> None:
        self.index = index

    def __repr__(self) -> str:
        return "<Index(index=%i)>" % self.index

    def __str__(self) -> str:
        return "cpindex(#%i)" % self.index


class Integer(Constant):
    """
    A 32-bit integer constant.

    Attributes
    ----------
    value: np.int32
        The integer value of this constant.
    """

    __slots__ = ("value",)

    type = int_t

    def __init__(self, value: int | np.int32) -> None:
        if not isinstance(value, np.int32):
            value = np.int32(value)
        self.value = value

    def __repr__(self) -> str:
        return "<Integer(value=%s)>" % self.value

    def __str__(self) -> str:
        return "%si" % self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Integer) and bool(self.value == other.value)  # STUPID NUMPY BOOLS!!

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Integer) or bool(self.value != other.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Integer):
            raise TypeError("'<' not supported between %r and %r" % (Integer, type(other)))
        return bool(self.value < other.value)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Integer):
            raise TypeError("'>=' not supported between %r and %r" % (Integer, type(other)))
        return bool(self.value >= other.value)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Integer):
            raise TypeError("'>' not supported between %r and %r" % (Integer, type(other)))
        return bool(self.value > other.value)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Integer):
            raise TypeError("'<=' not supported between %r and %r" % (Integer, type(other)))
        return bool(self.value <= other.value)

    def __neg__(self) -> "Integer":
        return Integer(-self.value)

    def __add__(self, other: object) -> "Integer":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for +: %r and %r" % (Integer, type(other)))
        return Integer(self.value + other.value)

    def __sub__(self, other: object) -> "Integer":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for -: %r and %r" % (Integer, type(other)))
        return Integer(self.value - other.value)

    def __mul__(self, other: object) -> "Integer":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for *: %r and %r" % (Integer, type(other)))
        return Integer(self.value * other.value)

    def __truediv__(self, other: object) -> "Integer":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for /: %r and %r" % (Integer, type(other)))
        if not other.value:
            raise ZeroDivisionError("integer division by zero")
        return Integer(self.value // other.value)

    def __mod__(self, other: object) -> "Integer":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Integer, type(other)))
        if not other.value:
            raise ZeroDivisionError("integer modulo by zero")
        return Integer(self.value % other.value)

    def __lshift__(self, other: object) -> "Integer":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for <<: %r and %r" % (Integer, type(other)))
        return Integer(self.value << (other.value % 32))

    def __rshift__(self, other: object) -> "Integer":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for >>: %r and %r" % (Integer, type(other)))
        return Integer(self.value >> (other.value % 32))

    def __and__(self, other: object) -> "Integer":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for &: %r and %r" % (Integer, type(other)))
        return Integer(self.value & other.value)

    def __or__(self, other: object) -> "Integer":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for |: %r and %r" % (Integer, type(other)))
        return Integer(self.value | other.value)

    def __xor__(self, other: object) -> "Integer":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for ^: %r and %r" % (Integer, type(other)))
        return Integer(self.value ^ other.value)

    def vcast(self, type_: Primitive) -> Value:
        if type_ is int_t:
            return self
        elif type_ is float_t:
            return Float(np.float32(self.value))
        elif type_ is long_t:
            return Long(np.int64(self.value))
        elif type_ is double_t:
            return Double(np.float64(self.value))
        # TODO: Test that these are all working correctly.
        elif type_ is byte_t:
            return Integer(np.int32(np.int8(self.value)))
        elif type_ is char_t:
            return Integer(np.int32(np.uint16(self.value)))
        elif type_ is short_t:
            return Integer(np.int32(np.int16(self.value)))
        raise ValueError("cannot cast %r to %s" % (self, type_))

    def ushr(self, other: Value) -> "Integer":
        if not isinstance(other, Integer):
            raise ValueError("cannot unsigned shift right %r by %r" % (self, other))
        return Integer(np.int32(np.uint32(self.value) >> np.uint8(other.value % 32)))


class Float(Constant):
    """
    A 32-bit float constant.

    Attributes
    ----------
    value: np.float32
        The float value of this constant.
    """

    __slots__ = ("value",)

    type = float_t

    def __init__(self, value: float | np.float32) -> None:
        if not isinstance(value, np.float32):
            value = np.float32(value)
        self.value = value

    def __repr__(self) -> str:
        return "<Float(value=%s)>" % self.value

    def __str__(self) -> str:
        # return "%f" % _unpack_f(_pack_i(self.value))
        return "%sf" % self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Float) and bool(self.value == other.value)

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Float) or bool(self.value != other.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Float):
            raise TypeError("'<' not supported between %r and %r" % (Float, type(other)))
        return bool(self.value < other.value)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Float):
            raise TypeError("'>=' not supported between %r and %r" % (Float, type(other)))
        return bool(self.value >= other.value)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Float):
            raise TypeError("'>' not supported between %r and %r" % (Float, type(other)))
        return bool(self.value > other.value)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Float):
            raise TypeError("'<=' not supported between %r and %r" % (Float, type(other)))
        return bool(self.value <= other.value)

    def __neg__(self) -> "Float":
        return Float(-self.value)

    def __add__(self, other: object) -> "Float":
        if not isinstance(other, Float):
            raise TypeError("unsupported operand type(s) for +: %r and %r" % (Float, type(other)))
        return Float(self.value + other.value)

    def __sub__(self, other: object) -> "Float":
        if not isinstance(other, Float):
            raise TypeError("unsupported operand type(s) for -: %r and %r" % (Float, type(other)))
        return Float(self.value - other.value)

    def __mul__(self, other: object) -> "Float":
        if not isinstance(other, Float):
            raise TypeError("unsupported operand type(s) for *: %r and %r" % (Float, type(other)))
        return Float(self.value * other.value)

    def __truediv__(self, other: object) -> "Float":
        if not isinstance(other, Float):
            raise TypeError("unsupported operand type(s) for /: %r and %r" % (Float, type(other)))
        return Float(self.value / other.value)

    def __mod__(self, other: object) -> "Float":
        if not isinstance(other, Float):
            raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Float, type(other)))
        return Float(self.value % other.value)

    def vcast(self, type_: Primitive) -> Value:
        if type_ is int_t:
            return Integer(min(max(int(self.value), -0x80000000), 0x7fffffff))
        elif type_ is float_t:
            return self
        elif type_ is long_t:
            return Long(min(max(int(self.value), -0x8000000000000000), 0x7fffffffffffffff))
        elif type_ is double_t:
            return Double(np.float64(self.value))
        raise ValueError("cannot cast %r to %s" % (self, type_))


class Long(Constant):
    """
    A 64-bit long constant.

    Attributes
    ----------
    value: np.int64
        The integer value of this constant.
    """

    __slots__ = ("value",)

    type = long_t

    def __init__(self, value: int | np.int64) -> None:
        if not isinstance(value, np.int64):
            value = np.int64(value)
        self.value = value

    def __repr__(self) -> str:
        return "<Long(value=%s)>" % self.value

    def __str__(self) -> str:
        return "%sL" % self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Long) and bool(self.value == other.value)

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Long) or bool(self.value != other.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Long):
            raise TypeError("'<' not supported between %r and %r" % (Long, type(other)))
        return bool(self.value < other.value)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Long):
            raise TypeError("'>=' not supported between %r and %r" % (Long, type(other)))
        return bool(self.value >= other.value)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Long):
            raise TypeError("'>' not supported between %r and %r" % (Long, type(other)))
        return bool(self.value > other.value)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Long):
            raise TypeError("'<=' not supported between %r and %r" % (Long, type(other)))
        return bool(self.value <= other.value)

    def __neg__(self) -> "Long":
        return Long(-self.value)

    def __add__(self, other: object) -> "Long":
        if not isinstance(other, Long):
            raise TypeError("unsupported operand type(s) for +: %r and %r" % (Long, type(other)))
        return Long(self.value + other.value)

    def __sub__(self, other: object) -> "Long":
        if not isinstance(other, Long):
            raise TypeError("unsupported operand type(s) for -: %r and %r" % (Long, type(other)))
        return Long(self.value - other.value)

    def __mul__(self, other: object) -> "Long":
        if not isinstance(other, Long):
            raise TypeError("unsupported operand type(s) for *: %r and %r" % (Long, type(other)))
        return Long(self.value * other.value)

    def __truediv__(self, other: object) -> "Long":
        if not isinstance(other, Long):
            raise TypeError("unsupported operand type(s) for /: %r and %r" % (Long, type(other)))
        if not other.value:
            raise ZeroDivisionError("integer division by zero")
        return Long(self.value // other.value)

    def __mod__(self, other: object) -> "Long":
        if not isinstance(other, Long):
            raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Long, type(other)))
        if not other.value:
            raise ZeroDivisionError("integer modulo by zero")
        return Long(self.value % other.value)

    def __lshift__(self, other: object) -> "Long":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for <<: %r and %r" % (Long, type(other)))
        return Long(self.value << (other.value % 64))

    def __rshift__(self, other: object) -> "Long":
        if not isinstance(other, Integer):
            raise TypeError("unsupported operand type(s) for >>: %r and %r" % (Long, type(other)))
        return Long(self.value >> (other.value % 64))

    def __and__(self, other: object) -> "Long":
        if not isinstance(other, Long):
            raise TypeError("unsupported operand type(s) for &: %r and %r" % (Long, type(other)))
        return Long(self.value & other.value)

    def __or__(self, other: object) -> "Long":
        if not isinstance(other, Long):
            raise TypeError("unsupported operand type(s) for |: %r and %r" % (Long, type(other)))
        return Long(self.value | other.value)

    def __xor__(self, other: object) -> "Long":
        if not isinstance(other, Long):
            raise TypeError("unsupported operand type(s) for ^: %r and %r" % (Long, type(other)))
        return Long(self.value ^ other.value)

    def vcast(self, type_: Primitive) -> Value:
        if type_ is int_t:
            return Integer(np.int32(self.value))
        elif type_ is long_t:
            return self
        elif type_ is float_t:
            return Float(np.float32(self.value))
        elif type_ is double_t:
            return Double(np.float64(self.value))
        raise ValueError("cannot cast %r to %s" % (self, type_))

    def ushr(self, other: Value) -> "Long":
        if not isinstance(other, Integer):
            raise ValueError("cannot unsigned shift right %r by %r" % (self, other))
        return Long(np.int64(np.uint64(self.value) >> np.uint8(other.value % 64)))


class Double(Constant):
    """
    A 64-bit double constant.

    Attributes
    ----------
    value: np.float64
        The float value of this constant.
    """

    __slots__ = ("value",)

    type = double_t

    def __init__(self, value: float | np.float64) -> None:
        if not isinstance(value, np.float64):
            value = np.float64(value)
        self.value = value

    def __repr__(self) -> str:
        return "<Double(value=%s)>" % self.value

    def __str__(self) -> str:
        # return "%f" % _unpack_d(_pack_q(self.value))
        return "%sD" % self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Double) and bool(self.value == other.value)

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Double) or bool(self.value != other.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Double):
            raise TypeError("'<' not supported between %r and %r" % (Double, type(other)))
        return bool(self.value < other.value)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Double):
            raise TypeError("'>=' not supported between %r and %r" % (Double, type(other)))
        return bool(self.value >= other.value)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Double):
            raise TypeError("'>' not supported between %r and %r" % (Double, type(other)))
        return bool(self.value > other.value)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Double):
            raise TypeError("'<=' not supported between %r and %r" % (Double, type(other)))
        return bool(self.value <= other.value)

    def __neg__(self) -> "Double":
        return Double(-self.value)

    def __add__(self, other: object) -> "Double":
        if not isinstance(other, Double):
            raise TypeError("unsupported operand type(s) for +: %r and %r" % (Double, type(other)))
        return Double(self.value + other.value)

    def __sub__(self, other: object) -> "Double":
        if not isinstance(other, Double):
            raise TypeError("unsupported operand type(s) for -: %r and %r" % (Double, type(other)))
        return Double(self.value - other.value)

    def __mul__(self, other: object) -> "Double":
        if not isinstance(other, Double):
            raise TypeError("unsupported operand type(s) for *: %r and %r" % (Double, type(other)))
        return Double(self.value * other.value)

    def __truediv__(self, other: object) -> "Double":
        if not isinstance(other, Double):
            raise TypeError("unsupported operand type(s) for /: %r and %r" % (Double, type(other)))
        return Double(self.value / other.value)

    def __mod__(self, other: object) -> "Double":
        if not isinstance(other, Double):
            raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Double, type(other)))
        return Double(self.value % other.value)

    def vcast(self, type_: Primitive) -> Value:
        if type_ is int_t:
            return Integer(min(max(int(self.value), -0x80000000), 0x7fffffff))
        elif type_ is float_t:
            return Float(np.float32(self.value))
        elif type_ is long_t:
            return Long(min(max(int(self.value), -0x8000000000000000), 0x7fffffffffffffff))
        elif type_ is double_t:
            return self
        raise ValueError("cannot cast %r to %s" % (self, type_))


# Class is "defined" already (as we import * from types), which I'm not going to rewrite just to make mypy happy. It
# would require at least 2 lines of imports...
class Class(Constant):  # type: ignore[no-redef]
    """
    A class constant.

    Attributes
    ----------
    name: str
        The name of the class.

    Methods
    -------
    as_rtype(self) -> Reference
        Gets the reference type that this constant represents.
    """

    __slots__ = ("name",)

    type = class_t

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return "<Class(name=%r)>" % pretty_repr(self.name)

    def __str__(self) -> str:
        return "CLASS(%s)" % pretty_repr(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Class) and self.name == other.name

    def as_rtype(self) -> Reference:
        """
        Gets the reference type that this constant represents.

        Returns
        -------
        Reference
            The representative reference type.
        """

        # https://github.com/ItzSomebody/stopdecompilingmyjava/blob/master/decompiler-tool-bugs/entry-007/entry.md
        # return parse_reference(self.name)
        raise NotImplementedError("as_rtype() is not implemented for %r" % type(self))


class String(Constant):
    """
    A string constant.

    Attributes
    ----------
    value: str
        The string value.
    """

    __slots__ = ("value",)

    type = string_t

    # TODO: String constants might escape the method, could be modified via reflection.

    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return "<String(value=%r)>" % pretty_repr(self.value)

    def __str__(self) -> str:
        return "\"%s\"" % pretty_repr(self.value).replace("\"", "\\\"")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, String) and self.value == other.value


class MethodHandle(Constant):
    """
    A method handle constant.

    Attributes
    ----------
    kind: int
        The kind of method handle.
    class_: Class
        The class containing the referenced field/method.
    name: str
        The name of the referenced field/method.
    descriptor: str
        The descriptor of the referenced field/method.
    """

    __slots__ = ("kind", "class_", "name", "descriptor")

    type = method_handle_t

    def __init__(self, kind: int, class_: Class, name: str, descriptor: str) -> None:
        self.kind = kind
        self.class_ = class_
        self.name = name
        self.descriptor = descriptor

    def __repr__(self) -> str:
        return "<MethodHandle(kind=%i, class_=%s, name=%r, descriptor=%r)>" % (
            self.kind, self.class_, self.name, self.descriptor,
        )


class MethodType(Constant):
    """
    A method type constant.

    Attributes
    ----------
    descriptor: str
        The method descriptor.
    """

    __slots__ = ("descriptor",)

    type = method_type_t

    def __init__(self, descriptor: str) -> None:
        self.descriptor = descriptor

    def __repr__(self) -> str:
        return "<MethodType(descriptor=%r)>" % pretty_repr(self.descriptor)

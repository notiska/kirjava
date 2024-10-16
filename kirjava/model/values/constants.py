#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Constant",
    "Null",
    "Integer", "Float", "Long", "Double",
    "Class", "String",
    "MethodHandle", "MethodType",
)

"""
Models for constant values.
"""

from . import Value
# Mypy gets confused if we do import * because `Class` is also defined in types, so yea...
from ..types import (
    byte_t, char_t, class_t, double_t, float_t, int_t, long_t, method_handle_t, method_type_t, null_t, short_t,
    string_t, top_t,
    Primitive, Reference, Type,
)
# from ..types.descriptor import parse_reference
from ...backend import f32, f64, i32, i64
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
        return f"<Index(index={self.index})>"

    def __str__(self) -> str:
        return f"cpindex(#{self.index})"


class Integer(Constant):
    """
    A 32-bit integer constant.

    Attributes
    ----------
    value: i32
        The integer value of this constant.
    """

    __slots__ = ("value",)

    type = int_t

    def __init__(self, value: i32) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"<Integer(value={self.value!r})>"

    def __str__(self) -> str:
        return f"{self.value!s}i"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Integer) and self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Integer) or self.value != other.value

    # FIXME: All arithmetic and comparisons.

    # def __lt__(self, other: object) -> bool:
    #     if not isinstance(other, Integer):
    #         raise TypeError("'<' not supported between %r and %r" % (Integer, type(other)))
    #     return bool(self.value < other.value)

    # def __ge__(self, other: object) -> bool:
    #     if not isinstance(other, Integer):
    #         raise TypeError("'>=' not supported between %r and %r" % (Integer, type(other)))
    #     return bool(self.value >= other.value)

    # def __gt__(self, other: object) -> bool:
    #     if not isinstance(other, Integer):
    #         raise TypeError("'>' not supported between %r and %r" % (Integer, type(other)))
    #     return bool(self.value > other.value)

    # def __le__(self, other: object) -> bool:
    #     if not isinstance(other, Integer):
    #         raise TypeError("'<=' not supported between %r and %r" % (Integer, type(other)))
    #     return bool(self.value <= other.value)

    # def __neg__(self) -> "Integer":
    #     return Integer(-self.value)

    # def __add__(self, other: object) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for +: %r and %r" % (Integer, type(other)))
    #     return Integer(self.value + other.value)

    # def __sub__(self, other: object) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for -: %r and %r" % (Integer, type(other)))
    #     return Integer(self.value - other.value)

    # def __mul__(self, other: object) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for *: %r and %r" % (Integer, type(other)))
    #     return Integer(self.value * other.value)

    # def __truediv__(self, other: object) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for /: %r and %r" % (Integer, type(other)))
    #     if not other.value:
    #         raise ZeroDivisionError("integer division by zero")
    #     return Integer(self.value // other.value)

    # def __mod__(self, other: object) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Integer, type(other)))
    #     if not other.value:
    #         raise ZeroDivisionError("integer modulo by zero")
    #     return Integer(self.value % other.value)

    # def __lshift__(self, other: object) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for <<: %r and %r" % (Integer, type(other)))
    #     return Integer(self.value << (other.value % 32))

    # def __rshift__(self, other: object) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for >>: %r and %r" % (Integer, type(other)))
    #     return Integer(self.value >> (other.value % 32))

    # def __and__(self, other: object) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for &: %r and %r" % (Integer, type(other)))
    #     return Integer(self.value & other.value)

    # def __or__(self, other: object) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for |: %r and %r" % (Integer, type(other)))
    #     return Integer(self.value | other.value)

    # def __xor__(self, other: object) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for ^: %r and %r" % (Integer, type(other)))
    #     return Integer(self.value ^ other.value)

    # def vcast(self, type_: Primitive) -> Value:
    #     if type_ is int_t:
    #         return self
    #     elif type_ is float_t:
    #         return Float(f32(self.value))
    #     elif type_ is long_t:
    #         return Long(i64(self.value))
    #     elif type_ is double_t:
    #         return Double(f64(self.value))
    #     # FIXME: Below.
    #     # elif type_ is byte_t:
    #     #     return Integer(i32(i8(self.value)))
    #     # elif type_ is char_t:
    #     #     return Integer(i32(u8(self.value)))
    #     # elif type_ is short_t:
    #     #     return Integer(i32(i16(self.value)))
    #     raise ValueError("cannot cast %r to %s" % (self, type_))

    # def ushr(self, other: Value) -> "Integer":
    #     if not isinstance(other, Integer):
    #         raise ValueError("cannot unsigned shift right %r by %r" % (self, other))
    #     return Integer(np.int32(np.uint32(self.value) >> np.uint8(other.value % 32)))


class Float(Constant):
    """
    A 32-bit float constant.

    Attributes
    ----------
    value: f32
        The float value of this constant.
    """

    __slots__ = ("value",)

    type = float_t

    def __init__(self, value: f32) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"<Float(value={self.value!r})>"

    def __str__(self) -> str:
        # return "%f" % _unpack_f(_pack_i(self.value))
        return f"{self.value!s}f"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Float) and self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Float) or self.value != other.value

    # def __lt__(self, other: object) -> bool:
    #     if not isinstance(other, Float):
    #         raise TypeError("'<' not supported between %r and %r" % (Float, type(other)))
    #     return bool(self.value < other.value)

    # def __ge__(self, other: object) -> bool:
    #     if not isinstance(other, Float):
    #         raise TypeError("'>=' not supported between %r and %r" % (Float, type(other)))
    #     return bool(self.value >= other.value)

    # def __gt__(self, other: object) -> bool:
    #     if not isinstance(other, Float):
    #         raise TypeError("'>' not supported between %r and %r" % (Float, type(other)))
    #     return bool(self.value > other.value)

    # def __le__(self, other: object) -> bool:
    #     if not isinstance(other, Float):
    #         raise TypeError("'<=' not supported between %r and %r" % (Float, type(other)))
    #     return bool(self.value <= other.value)

    # def __neg__(self) -> "Float":
    #     return Float(-self.value)

    # def __add__(self, other: object) -> "Float":
    #     if not isinstance(other, Float):
    #         raise TypeError("unsupported operand type(s) for +: %r and %r" % (Float, type(other)))
    #     return Float(self.value + other.value)

    # def __sub__(self, other: object) -> "Float":
    #     if not isinstance(other, Float):
    #         raise TypeError("unsupported operand type(s) for -: %r and %r" % (Float, type(other)))
    #     return Float(self.value - other.value)

    # def __mul__(self, other: object) -> "Float":
    #     if not isinstance(other, Float):
    #         raise TypeError("unsupported operand type(s) for *: %r and %r" % (Float, type(other)))
    #     return Float(self.value * other.value)

    # def __truediv__(self, other: object) -> "Float":
    #     if not isinstance(other, Float):
    #         raise TypeError("unsupported operand type(s) for /: %r and %r" % (Float, type(other)))
    #     return Float(self.value / other.value)

    # def __mod__(self, other: object) -> "Float":
    #     if not isinstance(other, Float):
    #         raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Float, type(other)))
    #     return Float(self.value % other.value)

    # def vcast(self, type_: Primitive) -> Value:
    #     if type_ is int_t:
    #         return Integer(min(max(int(self.value), -0x80000000), 0x7fffffff))
    #     elif type_ is float_t:
    #         return self
    #     elif type_ is long_t:
    #         return Long(min(max(int(self.value), -0x8000000000000000), 0x7fffffffffffffff))
    #     elif type_ is double_t:
    #         return Double(np.float64(self.value))
    #     raise ValueError("cannot cast %r to %s" % (self, type_))


class Long(Constant):
    """
    A 64-bit long constant.

    Attributes
    ----------
    value: i64
        The integer value of this constant.
    """

    __slots__ = ("value",)

    type = long_t

    def __init__(self, value: i64) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"<Long(value={self.value!r})>"

    def __str__(self) -> str:
        return f"{self.value!s}L"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Long) and self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Long) or self.value != other.value

    # def __lt__(self, other: object) -> bool:
    #     if not isinstance(other, Long):
    #         raise TypeError("'<' not supported between %r and %r" % (Long, type(other)))
    #     return bool(self.value < other.value)

    # def __ge__(self, other: object) -> bool:
    #     if not isinstance(other, Long):
    #         raise TypeError("'>=' not supported between %r and %r" % (Long, type(other)))
    #     return bool(self.value >= other.value)

    # def __gt__(self, other: object) -> bool:
    #     if not isinstance(other, Long):
    #         raise TypeError("'>' not supported between %r and %r" % (Long, type(other)))
    #     return bool(self.value > other.value)

    # def __le__(self, other: object) -> bool:
    #     if not isinstance(other, Long):
    #         raise TypeError("'<=' not supported between %r and %r" % (Long, type(other)))
    #     return bool(self.value <= other.value)

    # def __neg__(self) -> "Long":
    #     return Long(-self.value)

    # def __add__(self, other: object) -> "Long":
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for +: %r and %r" % (Long, type(other)))
    #     return Long(self.value + other.value)

    # def __sub__(self, other: object) -> "Long":
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for -: %r and %r" % (Long, type(other)))
    #     return Long(self.value - other.value)

    # def __mul__(self, other: object) -> "Long":
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for *: %r and %r" % (Long, type(other)))
    #     return Long(self.value * other.value)

    # def __truediv__(self, other: object) -> "Long":
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for /: %r and %r" % (Long, type(other)))
    #     if not other.value:
    #         raise ZeroDivisionError("integer division by zero")
    #     return Long(self.value // other.value)

    # def __mod__(self, other: object) -> "Long":
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Long, type(other)))
    #     if not other.value:
    #         raise ZeroDivisionError("integer modulo by zero")
    #     return Long(self.value % other.value)

    # def __lshift__(self, other: object) -> "Long":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for <<: %r and %r" % (Long, type(other)))
    #     return Long(self.value << (other.value % 64))

    # def __rshift__(self, other: object) -> "Long":
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for >>: %r and %r" % (Long, type(other)))
    #     return Long(self.value >> (other.value % 64))

    # def __and__(self, other: object) -> "Long":
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for &: %r and %r" % (Long, type(other)))
    #     return Long(self.value & other.value)

    # def __or__(self, other: object) -> "Long":
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for |: %r and %r" % (Long, type(other)))
    #     return Long(self.value | other.value)

    # def __xor__(self, other: object) -> "Long":
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for ^: %r and %r" % (Long, type(other)))
    #     return Long(self.value ^ other.value)

    # def vcast(self, type_: Primitive) -> Value:
    #     if type_ is int_t:
    #         return Integer(np.int32(self.value))
    #     elif type_ is long_t:
    #         return self
    #     elif type_ is float_t:
    #         return Float(np.float32(self.value))
    #     elif type_ is double_t:
    #         return Double(np.float64(self.value))
    #     raise ValueError("cannot cast %r to %s" % (self, type_))

    # def ushr(self, other: Value) -> "Long":
    #     if not isinstance(other, Integer):
    #         raise ValueError("cannot unsigned shift right %r by %r" % (self, other))
    #     return Long(np.int64(np.uint64(self.value) >> np.uint8(other.value % 64)))


class Double(Constant):
    """
    A 64-bit double constant.

    Attributes
    ----------
    value: f64
        The float value of this constant.
    """

    __slots__ = ("value",)

    type = double_t

    def __init__(self, value: f64) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"<Double(value={self.value!r})>"

    def __str__(self) -> str:
        # return "%f" % _unpack_d(_pack_q(self.value))
        return f"{self.value!s}D"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Double) and self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Double) or self.value != other.value

    # def __lt__(self, other: object) -> bool:
    #     if not isinstance(other, Double):
    #         raise TypeError("'<' not supported between %r and %r" % (Double, type(other)))
    #     return bool(self.value < other.value)

    # def __ge__(self, other: object) -> bool:
    #     if not isinstance(other, Double):
    #         raise TypeError("'>=' not supported between %r and %r" % (Double, type(other)))
    #     return bool(self.value >= other.value)

    # def __gt__(self, other: object) -> bool:
    #     if not isinstance(other, Double):
    #         raise TypeError("'>' not supported between %r and %r" % (Double, type(other)))
    #     return bool(self.value > other.value)

    # def __le__(self, other: object) -> bool:
    #     if not isinstance(other, Double):
    #         raise TypeError("'<=' not supported between %r and %r" % (Double, type(other)))
    #     return bool(self.value <= other.value)

    # def __neg__(self) -> "Double":
    #     return Double(-self.value)

    # def __add__(self, other: object) -> "Double":
    #     if not isinstance(other, Double):
    #         raise TypeError("unsupported operand type(s) for +: %r and %r" % (Double, type(other)))
    #     return Double(self.value + other.value)

    # def __sub__(self, other: object) -> "Double":
    #     if not isinstance(other, Double):
    #         raise TypeError("unsupported operand type(s) for -: %r and %r" % (Double, type(other)))
    #     return Double(self.value - other.value)

    # def __mul__(self, other: object) -> "Double":
    #     if not isinstance(other, Double):
    #         raise TypeError("unsupported operand type(s) for *: %r and %r" % (Double, type(other)))
    #     return Double(self.value * other.value)

    # def __truediv__(self, other: object) -> "Double":
    #     if not isinstance(other, Double):
    #         raise TypeError("unsupported operand type(s) for /: %r and %r" % (Double, type(other)))
    #     return Double(self.value / other.value)

    # def __mod__(self, other: object) -> "Double":
    #     if not isinstance(other, Double):
    #         raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Double, type(other)))
    #     return Double(self.value % other.value)

    # def vcast(self, type_: Primitive) -> Value:
    #     if type_ is int_t:
    #         return Integer(min(max(int(self.value), -0x80000000), 0x7fffffff))
    #     elif type_ is float_t:
    #         return Float(np.float32(self.value))
    #     elif type_ is long_t:
    #         return Long(min(max(int(self.value), -0x8000000000000000), 0x7fffffffffffffff))
    #     elif type_ is double_t:
    #         return self
    #     raise ValueError("cannot cast %r to %s" % (self, type_))


class Class(Constant):  # FIXME: Separate constant for array classes.
    """
    A class constant.

    Attributes
    ----------
    name: str
        The name of the class.

    Methods
    -------
    as_type(self) -> Reference
        Returns the type that this constant represents.
    """

    __slots__ = ("name",)

    type = class_t

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"<Class(name={self.name!r})>"

    def __str__(self) -> str:
        return f"Class({self.name!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Class) and self.name == other.name

    def as_type(self) -> Reference:
        """
        Returns the type that this constant represents.
        """

        # https://github.com/ItzSomebody/stopdecompilingmyjava/blob/master/decompiler-tool-bugs/entry-007/entry.md
        # return parse_reference(self.name)
        raise NotImplementedError(f"as_type() is not implemented for {type(self)!r}")


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
        return f"<String(value={self.value!r})>"

    def __str__(self) -> str:
        return f"\"{self.value.replace("\"", "\\\"")}\""  # Python moment.

    def __eq__(self, other: object) -> bool:
        return isinstance(other, String) and self.value == other.value


class MethodHandle(Constant):  # FIXME: Could be done much better.
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
        return (
            f"<MethodHandle(kind={self.kind}, class_={self.class_!s}, name={self.name!r}, "
            f"descriptor={self.descriptor!r})>"
        )


class MethodType(Constant):  # FIXME: Could also be done better.
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
        return f"<MethodType(descriptor={self.descriptor!r})>"

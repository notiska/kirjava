#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Constant",
    "Null",
    "Boolean", "Byte", "Character", "Short",
    "Integer", "Float", "Long", "Double",
    "Class", "String",
    "MethodHandle", "MethodType",
)

"""
Models for constant values.
"""

from enum import Enum
from typing import Any, Generic, Iterable, SupportsFloat, SupportsInt

from . import Value
# Mypy gets confused if we do import * because `Class` is also defined in types, so yea...
from ..types import (
    boolean_t, byte_t, char_t, class_t, double_t, float_t, int_t, long_t,
    method_handle_t, method_type_t, null_t, short_t, string_t,
    Array, Class as ClassType, Reference, Type,
)
from ..._compat import TypeVar
from ...backend import f32, f64, i8, i16, i32, i64, u16

T = TypeVar("T", default=Any)


class Constant(Generic[T], Value):
    """
    A constant value.

    Attributes
    ----------
    info: T | None
        The constant info that this constant was generated from.
    """

    __slots__ = ("info",)

    def __init__(self) -> None:
        self.info: T | None = None

    def __hash__(self) -> int:
        raise NotImplementedError(f"hash() is not implemented for {type(self)!r}")


class Null(Constant[None]):
    """
    A null constant.
    """

    __slots__ = ()

    type = null_t

    def __repr__(self) -> str:
        return "<Null>"

    def __str__(self) -> str:
        return "null"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Null)

    def __hash__(self) -> int:
        return hash(Null)  # FIXME: A better hash value?


class Boolean(Constant[T]):
    """
    A boolean constant.

    Attributes
    ----------
    value: bool
        The value of this constant.

    Methods
    -------
    as_integer(self) -> Integer[T]
        Returns this constant as an integer constant.
    """

    __slots__ = ("_value", "_hash")

    type = boolean_t

    @property
    def value(self) -> bool:
        return self._value

    def __init__(self, value: bool) -> None:
        super().__init__()
        self._value = value
        self._hash = hash(value)

    def __repr__(self) -> str:
        if self.info is not None:
            return f"<Boolean(info={self.info!s}, value={self._value})>"
        return f"<Boolean(value={self._value})>"

    def __str__(self) -> str:
        return "true" if self._value else "false"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Boolean) and self._value == other._value

    def __hash__(self) -> int:
        return self._hash

    def as_integer(self) -> "Integer[T]":
        """
        Returns this constant as an integer constant.
        """

        integer = Integer(i32(self._value))
        integer.info = self.info
        return integer


class Byte(Constant[T]):
    """
    An 8-bit integer constant.

    Attributes
    ----------
    value: i8
        The value of this constant.

    Methods
    -------
    as_integer(self) -> Integer[T]
        Returns this constant as an integer constant.
    """

    __slots__ = ("_value", "_hash")

    type = byte_t

    @property
    def value(self) -> i8:
        return self._value

    def __init__(self, value: i8 | SupportsInt) -> None:
        super().__init__()
        if not isinstance(value, i8):
            value = i8(value)
        self._value = value
        self._hash = hash(value)

    def __repr__(self) -> str:
        if self.info is not None:
            return f"<Byte(info={self.info!s}, value={self._value!r})>"
        return f"<Byte(value={self._value!r})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Byte) and self._value == other._value

    def __hash__(self) -> int:
        return self._hash

    def as_integer(self) -> "Integer[T]":
        """
        Returns this constant as an integer constant.
        """

        integer = Integer(i32(self._value))
        integer.info = self.info
        return integer


class Character(Constant[T]):
    """
    A 16-bit unsigned integer constant.

    Attributes
    ----------
    value: u16
        The value of this constant.

    Methods
    -------
    as_integer(self) -> Integer[T]
        Returns this constant as an integer constant.
    """

    __slots__ = ("_value", "_hash")

    type = char_t

    @property
    def value(self) -> u16:
        return self._value

    def __init__(self, value: u16 | str | bytes | SupportsInt) -> None:
        super().__init__()
        if isinstance(value, (str, bytes)):
            value = u16(ord(value))
        elif not isinstance(value, u16):
            value = u16(value)
        self._value = value
        self._hash = hash(value)

    def __repr__(self) -> str:
        if self.info is not None:
            return f"<Character(info={self.info!s}, value={self._value!r})>"
        return f"<Character(value={self._value!r})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Character) and self._value == other._value

    def __hash__(self) -> int:
        return self._hash

    def as_integer(self) -> "Integer[T]":
        """
        Returns this constant as an integer constant.
        """

        integer = Integer(self._value)
        integer.info = self.info
        return integer


class Short(Constant[T]):
    """
    A 16-bit integer constant.

    Attributes
    ----------
    value: i16
        The value of this constant.

    Methods
    -------
    as_integer(self) -> Integer[T]
        Returns this constant as an integer constant.
    """

    __slots__ = ("_value", "_hash")

    type = short_t

    @property
    def value(self) -> i16:
        return self._value

    def __init__(self, value: i16 | SupportsInt) -> None:
        super().__init__()
        if not isinstance(value, i16):
            value = i16(value)
        self._value = value
        self._hash = hash(value)

    def __repr__(self) -> str:
        if self.info is not None:
            return f"<Short(info={self.info!s}, value={self._value!r})>"
        return f"<Short(value={self._value!r})>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Short) and self._value == other._value

    def __hash__(self) -> int:
        return self._hash

    def as_integer(self) -> "Integer[T]":
        """
        Returns this constant as an integer constant.
        """

        integer = Integer(self._value)
        integer.info = self.info
        return integer


class Integer(Constant[T]):
    """
    A 32-bit integer constant.

    Attributes
    ----------
    value: i32
        The value of this constant.

    Methods
    -------
    as_boolean(self) -> Boolean[T]
        Returns this constant as a boolean constant.
    as_byte(self) -> Byte[T]
        Returns this constant as a byte constant.
    as_character(self) -> Character[T]
        Returns this constant as a character constant.
    as_short(self) -> Short[T]
        Returns this constant as a short constant.
    """

    __slots__ = ("_value", "_hash")

    type = int_t

    @property
    def value(self) -> i32:
        return self._value

    def __init__(self, value: i32 | SupportsInt) -> None:
        super().__init__()
        if not isinstance(value, i32):
            value = i32(value)
        self._value = value
        self._hash = hash(value)

    def __repr__(self) -> str:
        if self.info is not None:
            return f"<Integer(info={self.info!s}, value={self._value!r})>"
        return f"<Integer(value={self._value!r})>"

    def __str__(self) -> str:
        return f"{self._value!s}i"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Integer) and self._value == other._value

    def __hash__(self) -> int:
        return self._hash

    def as_boolean(self) -> Boolean[T]:
        """
        Returns this constant as a boolean constant.
        """

        boolean = Boolean(bool(self._value))
        boolean.info = self.info
        return boolean

    def as_byte(self) -> Byte[T]:
        """
        Returns this constant as a byte constant.
        """

        byte = Byte(i8(self._value))  # FIXME: May raise I think? Would the JVM just truncate it?
        byte.info = self.info
        return byte

    def as_character(self) -> Character[T]:
        """
        Returns this constant as a character constant.
        """

        character = Character(u16(self._value))
        character.info = self.info
        return character

    def as_short(self) -> Short[T]:
        """
        Returns this constant as a short constant.
        """

        short = Short(i16(self._value))
        short.info = self.info
        return short


class Float(Constant[T]):
    """
    A 32-bit float constant.

    Attributes
    ----------
    value: f32
        The float value of this constant.
    """

    __slots__ = ("_value", "_hash")

    type = float_t

    @property
    def value(self) -> f32:
        return self._value

    def __init__(self, value: f32 | SupportsFloat) -> None:
        super().__init__()
        if not isinstance(value, f32):
            value = f32(value)
        self._value = value
        self._hash = hash(value)

    def __repr__(self) -> str:
        if self.info is not None:
            return f"<Float(info={self.info!s}, value={self._value!r})>"
        return f"<Float(value={self._value!r})>"

    def __str__(self) -> str:
        # return "%f" % _unpack_f(_pack_i(self.value))
        return f"{self._value!s}f"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Float) and self._value == other._value

    def __hash__(self) -> int:
        return self._hash


class Long(Constant[T]):
    """
    A 64-bit long constant.

    Attributes
    ----------
    value: i64
        The integer value of this constant.
    """

    __slots__ = ("_value", "_hash")

    type = long_t

    @property
    def value(self) -> i64:
        return self._value

    def __init__(self, value: i64 | SupportsInt) -> None:
        super().__init__()
        if not isinstance(value, i64):
            value = i64(value)
        self._value = value
        self._hash = hash(value)

    def __repr__(self) -> str:
        if self.info is not None:
            return f"<Long(info={self.info!s}, value={self._value!r})>"
        return f"<Long(value={self._value!r})>"

    def __str__(self) -> str:
        return f"{self._value!s}L"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Long) and self._value == other._value

    def __hash__(self) -> int:
        return self._hash


class Double(Constant[T]):
    """
    A 64-bit double constant.

    Attributes
    ----------
    value: f64
        The float value of this constant.
    """

    __slots__ = ("_value", "_hash")

    type = double_t

    @property
    def value(self) -> f64:
        return self._value

    def __init__(self, value: f64 | SupportsFloat) -> None:
        super().__init__()
        if not isinstance(value, f64):
            value = f64(value)
        self._value = value
        self._hash = hash(value)

    def __repr__(self) -> str:
        if self.info is not None:
            return f"<Double(info={self.info!s}, value={self._value!r})>"
        return f"<Double(value={self._value!r})>"

    def __str__(self) -> str:
        # return "%f" % _unpack_d(_pack_q(self.value))
        return f"{self._value!s}D"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Double) and self._value == other._value

    def __hash__(self) -> int:
        return self._hash


class Class(Constant[T]):
    """
    A class constant.

    Attributes
    ----------
    ref_type: Reference
        The reference type representation of this class constant.
    name: str
        The name of the class.
    array: bool
        Whether this is an array pseudo-class.
    """

    __slots__ = ("_ref_type", "_hash")

    type = class_t

    @property
    def ref_type(self) -> Reference:
        return self._ref_type

    @property
    def name(self) -> str:
        return self._ref_type.name

    @property
    def array(self) -> bool:
        return isinstance(self._ref_type, Array)

    def __init__(self, name_or_type: str | Reference) -> None:
        super().__init__()
        if isinstance(name_or_type, str):
            name_or_type = ClassType(name_or_type)
        self._ref_type = name_or_type
        self._hash = hash(name_or_type)

    def __repr__(self) -> str:
        if self.info is not None:
            return f"<Class(info={self.info!s}, name={self._ref_type.name!r})>"
        return f"<Class(name={self._ref_type.name!r})>"

    def __str__(self) -> str:
        return f"Class({self._ref_type.name!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Class) and self._ref_type == other._ref_type

    def __hash__(self) -> int:
        return self._hash


class String(Constant[T]):  # TODO: Note: string constants might escape the method, could be modified via reflection.
    """
    A string constant.

    Attributes
    ----------
    value: str
        The string value.
    """

    __slots__ = ("_value", "_hash")

    type = string_t

    @property
    def value(self) -> str:
        return self._value

    def __init__(self, value: str) -> None:
        super().__init__()
        self._value = value
        self._hash = hash(value)

    def __repr__(self) -> str:
        if self.info is not None:
            return f"<String(info={self.info!s}, value={self._value!r})>"
        return f"<String(value={self._value!r})>"

    def __str__(self) -> str:
        value_str = self._value.replace("\"", "\\\"")
        return f"\"{value_str}\""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, String) and self._value == other._value

    def __hash__(self) -> int:
        return self._hash


class MethodHandle(Constant[T]):
    """
    A method handle constant.

    Attributes
    ----------
    kind: MethodHandle.Kind
        The kind of method handle.
    class_: Class
        The class containing the referenced field/method.
    name: str
        The name of the referenced field/method.
    arg_types: tuple[Type, ...]
        The method handle argument types. If this method handle references a field,
        this will be empty.
    ret_type: Type
        The method handle return type.
    """

    __slots__ = ("_kind", "_class", "_name", "_arg_types", "_ret_type", "_hash")

    type = method_handle_t

    @property
    def kind(self) -> "MethodHandle.Kind":
        return self._kind

    @property
    def class_(self) -> Class:
        return self._class

    @property
    def name(self) -> str:
        return self._name

    @property
    def arg_types(self) -> tuple[Type, ...]:
        return self._arg_types

    @property
    def ret_type(self) -> Type:
        return self._ret_type

    def __init__(
        self, kind: "MethodHandle.Kind", class_: Class, name: str, arg_types: Iterable[Type], ret_type: Type,
    ) -> None:
        super().__init__()
        self._kind = kind
        self._class = class_
        self._name = name
        self._arg_types = tuple(arg_types)
        self._ret_type = ret_type
        self._hash = hash((kind, class_, name, self._arg_types, ret_type))

    def __repr__(self) -> str:
        arg_types_str = ", ".join(map(str, self._arg_types))
        if self.info is not None:
            return (
                f"<MethodHandle(info={self.info!s}, kind={self._kind!s}, class_={self._class!s}, name={self._name!r}, "
                f"arg_types=({arg_types_str}), ret_type={self._ret_type!s})>"
            )
        return (
            f"<MethodHandle(kind={self._kind!s}, class_={self._class!s}, name={self._name!r}, "
            f"arg_types=({arg_types_str}), ret_type={self._ret_type!s})>"
        )

    def __str__(self) -> str:
        # So this formatting does differ from how Java would print a method handle, as it provides more info (kind,
        # class and name rather than just arg and ret types). This is done because it's simply more useful.
        arg_types_str = ",".join(map(str, self._arg_types))
        return f"MethodHandle({self._kind.name},{self._class!s},{self._name!s},({arg_types_str}){self._ret_type!s})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, MethodHandle) and
            self._kind == other._kind and
            self._class == other._class and
            self._name == other._name and
            self._arg_types == other._arg_types and
            self._ret_type == other._ret_type
        )

    def __hash__(self) -> int:
        return self._hash

    class Kind(Enum):
        """
        The type of reference that a method handle refers to.
        """

        GET_FIELD          = 1
        GET_STATIC         = 2
        PUT_FIELD          = 3
        PUT_STATIC         = 4
        INVOKE_VIRTUAL     = 5
        INVOKE_STATIC      = 6
        INVOKE_SPECIAL     = 7
        NEW_INVOKE_SPECIAL = 8
        INVOKE_INTERFACE   = 9


class MethodType(Constant[T]):
    """
    A method type constant.

    Attributes
    ----------
    arg_types: tuple[Type, ...]
        The method argument types.
    ret_type: Type
        The method return type.
    """

    __slots__ = ("_arg_types", "_ret_type", "_hash")

    type = method_type_t

    @property
    def arg_types(self) -> tuple[Type, ...]:
        return self._arg_types

    @property
    def ret_type(self) -> Type:
        return self._ret_type

    def __init__(self, arg_types: Iterable[Type], ret_type: Type) -> None:
        super().__init__()
        self._arg_types = tuple(arg_types)
        self._ret_type = ret_type
        self._hash = hash((self._arg_types, ret_type))

    def __repr__(self) -> str:
        arg_types_str = ", ".join(map(str, self._arg_types))
        if self.info is not None:
            return f"<MethodType(info={self.info!s}, arg_types=({arg_types_str}), ret_type={self._ret_type!s})>"
        return f"<MethodType(arg_types=({arg_types_str}), ret_type={self._ret_type!s})>"

    def __str__(self) -> str:
        arg_types_str = ",".join(map(str, self._arg_types))
        return f"({arg_types_str}){self._ret_type!s}"  # Similarly formatted to actual Java.

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, MethodType) and
            self._arg_types == other._arg_types and
            self._ret_type == other._ret_type
        )

    def __hash__(self) -> int:
        return self._hash

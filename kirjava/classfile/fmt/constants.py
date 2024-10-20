#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "ConstInfo", "ConstIndex",

    "UTF8Info", "IntegerInfo", "FloatInfo",
    "LongInfo", "DoubleInfo", "ClassInfo",
    "StringInfo", "FieldrefInfo", "MethodrefInfo",
    "InterfaceMethodrefInfo", "NameAndTypeInfo", "MethodHandleInfo",
    "MethodTypeInfo", "DynamicInfo", "InvokeDynamicInfo",
    "ModuleInfo", "PackageInfo",
)

import sys
import typing
from copy import deepcopy
from typing import Any, IO

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .._desc import *
from .._struct import *
from ..version import *
from ...backend import *
from ...model.values.constants import *

if typing.TYPE_CHECKING:
    from .pool import ConstPool


# FIXME: It would be nice to have some external indication as to preferred type? Due to reasons attributes may have to
#        be marked as type `ConstInfo`, but ideally are i.e. `UTF8Info`. Could be done with generics?
class ConstInfo:
    """
    A cp_info struct/union.

    Attributes
    ----------
    tag: int
        The tag used to identify the type of constant pool entry.
    wide: bool
        Whether this constant type is considered to be "wide", meaning that it takes
        up two entries in the constant pool.
    since: Version
        The Java version that the constant was introduced in.
    loadable: bool
        Whether the constant can be loaded and pushed onto the operand stack.

    index: int | None
        The original, preserved index of the constant in the pool.
        Used to ensure original constant pool order, if necessary.

    Methods
    -------
    read(stream: IO[bytes], pool: ConstPool) -> ConstInfo
        Reads a constant info from a binary stream.
    lookup(tag: int) -> type[ConstInfo] | None
        Looks up a constant info type by tag.

    deref(self, pool: ConstPool) -> None
        Dereferences any indices in this constant.
    write(self, stream: IO[bytes], pool: ConstPool) -> None
        Writes the constant info to a binary stream.
    unwrap(self) -> Result[Any]
        Unwraps this constant info.
    """

    __slots__ = ("index",)

    tag: int
    wide: bool
    since: Version
    loadable: bool

    _cache: dict[int, type["ConstInfo"] | None] = {}

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        """
        Internal constant read.
        """

        raise NotImplementedError(f"_read() is not implemented for {cls!r}")

    @classmethod
    def lookup(cls, tag: int) -> type["ConstInfo"] | None:
        """
        Looks up a constant info type by tag.

        Parameters
        ----------
        tag: int
            The tag to look up.

        Returns
        -------
        type[ConstInfo] | None
            The constant info subclass, or `None` if not found.
        """

        for subclass in cls.__subclasses__():
            if subclass.tag == tag:
                return subclass
        return None

    @classmethod
    def read(cls, stream: IO[bytes], pool: "ConstPool") -> "ConstInfo":
        """
        Reads a constant info from a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        pool: ConstantPool
            The class file constant pool.
        """

        tag, = stream.read(1)
        subclass: type[ConstInfo] | None = cls._cache.get(tag)
        if subclass is None:
            subclass = cls.lookup(tag)
            cls._cache[tag] = subclass
        if subclass is None:
            raise ValueError(f"unknown constant pool tag {tag}")
        info = subclass._read(stream, pool)
        info.index = len(pool)
        return info

    # @staticmethod
    # def make(constant: object) -> "ConstInfo":
    #     """
    #     Creates a `ConstInfo` of the appropriate type given a Pythonic value.
    #
    #     Parameters
    #     ----------
    #     constant: object
    #         The Pythonic value of a constant, the type of which is used to determine
    #         the type of `ConstInfo` to create.
    #         In some circumstances, the value is also used, such as with
    #         differentiating `int`s from `long`s.
    #
    #     Raises
    #     ------
    #     ValueError
    #         If a `ConstInfo` cannot be created from provided value for whatever reason.
    #     """
    #
    #     if isinstance(constant, str):
    #         return UTF8Info(constant.encode("utf8").replace(b"\x00", b"\xc0\x80"))
    #
    #     elif isinstance(constant, bytes):
    #         return UTF8Info(constant)
    #
    #     elif isinstance(constant, int):
    #         if 0x7fffffff <= constant <= -0x80000000:
    #             return IntegerInfo(pack_i(constant))
    #         elif 0x7fffffffffffffff <= constant <= -0x8000000000000000:
    #             return LongInfo(pack_q(constant))
    #         raise ValueError("value is too large to convert into int and/or long constant")
    #
    #     elif isinstance(constant, float):
    #         return DoubleInfo(pack_d(constant))
    #
    #     # TODO: More...
    #
    #     raise ValueError("don't know how to convert %r into a constant" % constant)

    def __init__(self, index: int | None = None) -> None:
        self.index = index

    def __copy__(self) -> "ConstInfo":
        raise NotImplementedError(f"copy.copy() is not implemented for {type(self)!r}")

    # def __deepcopy__(self, memo: dict[int, object]) -> "ConstInfo":
    #     raise NotImplementedError("copy.deepcopy() is not implemented for %r" % type(self))

    def __repr__(self) -> str:
        raise NotImplementedError(f"repr() is not implemented for {type(self)!r}")

    def __str__(self) -> str:
        raise NotImplementedError(f"str() is not implemented for {type(self)!r}")

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError(f"== is not implemented for {type(self)!r}")

    # TODO: Descriptors, coercion/expectation.

    # def __get__(self, instance: object, owner: type) -> "ConstInfo":
    #     if instance is None:
    #         return self
    #     return instance.__dict__[self.__name__]

    # def __set__(self, instance: object, value: "ConstInfo") -> None:
    #     instance.__dict__[self.__name__] = value

    def deref(self, pool: "ConstPool") -> None:
        """
        Dereferences any indices in this constant.

        Parameters
        ----------
        pool: ConstPool
            The constant pool to dereference from.
        """

        raise NotImplementedError(f"deref() is not implemented for {type(self)!r}")

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        """
        Writes the constant info to a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        pool: ConstPool
            The class file constant pool.
        """

        raise NotImplementedError(f"write() is not implemented for {type(self)!r}")

    def unwrap(self) -> Result[Any]:
        """
        Unwraps this constant info.
        """

        return Err(ValueError(f"cannot unwrap constant {self!r}"))


class ConstIndex(ConstInfo):
    """
    A reference to an undefined index in the constant pool.

    Attributes
    ----------
    index: int
        The index being referenced.
    """

    __slots__ = ()

    tag = -1
    wide = False
    since = JAVA_1_1
    loadable = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        return cls(len(pool))  # Shouldn't really happen, though.

    def __init__(self, index: int) -> None:
        super().__init__(index)
        self.index: int

    def __copy__(self) -> "ConstIndex":
        return ConstIndex(self.index)

    def __repr__(self) -> str:
        return f"<ConstIndex(index={self.index})>"

    def __str__(self) -> str:
        return f"#{self.index}"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ConstIndex) and self.index == other.index

    def deref(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        ...


class UTF8Info(ConstInfo):
    """
    A CONSTANT_Utf8_info struct.

    Contains a constant UTF8 (M-UTF8) value.

    Attributes
    ----------
    value: bytes
        The bytes that make up the UTF8 string.

    Methods
    -------
    decode(self) -> str
        Decodes the UTF8 bytes into a string.
    """

    __slots__ = ("value",)

    tag = 1
    wide = False
    since = JAVA_1_0
    loadable = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        length, = unpack_H(stream.read(2))
        return cls(stream.read(length))

    def __init__(self, value: bytes) -> None:  # TODO: Automatic string encoding.
        super().__init__()
        self.value = value

    def __copy__(self) -> "UTF8Info":
        copy = UTF8Info(self.value)
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<UTF8Info(index={self.index}, value={self.value!r})>"
        return f"<UTF8Info(value={self.value!r})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:{self.decode()!r}"
        return repr(self.decode())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UTF8Info) and self.value == other.value

    def deref(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(UTF8Info.tag, len(self.value)))
        stream.write(self.value)

    def decode(self) -> str:
        """
        Decodes the UTF8 bytes into a string.
        """

        # TODO: Could implement the full M-UTF8 decoder.
        return self.value.replace(b"\xc0\x80", b"\x00").decode("utf8", "ignore")


class IntegerInfo(ConstInfo):
    """
    A CONSTANT_Integer_info struct.

    Represents a 32-bit numeric integer.

    Attributes
    ----------
    value: i32
        The integer value.
    """

    __slots__ = ("value",)

    tag = 3
    wide = False
    since = JAVA_1_0
    loadable = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        return cls(unpack_i32(stream.read(4)))

    def __init__(self, value: i32) -> None:
        super().__init__()
        self.value = value

    def __copy__(self) -> "IntegerInfo":
        copy = IntegerInfo(self.value)
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<IntegerInfo(index={self.index}, value={self.value!r})>"
        return f"<IntegerInfo(value={self.value!r})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:{self.value!s}i"
        return f"{self.value!s}i"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IntegerInfo) and self.value == other.value

    def deref(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((IntegerInfo.tag,)))
        stream.write(pack_i32(self.value))

    def unwrap(self) -> Result[Integer]:
        return Ok(Integer(self.value))


class FloatInfo(ConstInfo):
    """
    A CONSTANT_Float_info struct.

    Represents a 32-bit floating-point number.

    Attributes
    ----------
    value: f32
        The float value.
    """

    __slots__ = ("value",)

    tag = 4
    wide = False
    since = JAVA_1_0
    loadable = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        return cls(unpack_f32(stream.read(4)))

    def __init__(self, value: f32) -> None:
        super().__init__()
        self.value = value

    def __copy__(self) -> "FloatInfo":
        copy = FloatInfo(self.value)
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<FloatInfo(index={self.index}, value={self.value!r})>"
        return f"<FloatInfo(value={self.value!r})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:{self.value!s}f"
        return f"{self.value!s}f"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FloatInfo):
            return False
        if self.value == other.value:
            return True
        # FIXME: Will not resolve exact NaN matches though. Could cause issues.
        elif isnan(self.value) and isnan(other.value):  # Special case check, annoyingly.
            return True
        return False

    def deref(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((FloatInfo.tag,)))
        stream.write(pack_f32(self.value))

    def unwrap(self) -> Result[Float]:
        return Ok(Float(self.value))


class LongInfo(ConstInfo):
    """
    A CONSTANT_Long_info struct.

    Represents a 64-bit numeric integer.

    Attributes
    ----------
    value: np.int64
        The long value.
    """

    __slots__ = ("value",)

    tag = 5
    wide = True
    since = JAVA_1_0
    loadable = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        return cls(unpack_i64(stream.read(8)))

    def __init__(self, value: i64) -> None:
        super().__init__()
        self.value = value

    def __copy__(self) -> "LongInfo":
        copy = LongInfo(self.value)
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<LongInfo(index={self.index}, value={self.value!r})>"
        return f"<LongInfo(value={self.value!r})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:{self.value!s}L"
        return f"{self.value!s}L"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LongInfo) and self.value == other.value

    def deref(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((LongInfo.tag,)))
        stream.write(pack_i64(self.value))

    def unwrap(self) -> Result[Long]:
        return Ok(Long(self.value))


class DoubleInfo(ConstInfo):
    """
    A CONSTANT_Double_info struct.

    Represents a 64-bit floating-point number.

    Attributes
    ----------
    value: f64
        The double value.
    """

    __slots__ = ("value",)

    tag = 6
    wide = True
    since = JAVA_1_0
    loadable = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        return cls(unpack_f64(stream.read(8)))

    def __init__(self, value: f64) -> None:
        super().__init__()
        self.value = value

    def __copy__(self) -> "DoubleInfo":
        copy = DoubleInfo(self.value)
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<DoubleInfo(index={self.index}, value={self.value!r})>"
        return f"<DoubleInfo(value={self.value!r})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:{self.value!s}D"
        return f"{self.value!s}D"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DoubleInfo):
            return False
        if self.value == other.value:
            return True
        elif isnan(self.value) and isnan(other.value):
            return True
        return False

    def deref(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((DoubleInfo.tag,)))
        stream.write(pack_f64(self.value))

    def unwrap(self) -> Result[Double]:
        return Ok(Double(self.value))


class ClassInfo(ConstInfo):
    """
    A CONSTANT_Class_info struct.

    Represents a reference to a class or interface.

    Attributes
    ----------
    name: ConstInfo
        A UTF8 constant, used as the name of the class.
    """

    __slots__ = ("name",)

    tag = 7
    wide = False
    since = JAVA_1_0
    loadable = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, name: ConstInfo) -> None:
        super().__init__()
        self.name = name

    def __copy__(self) -> "ClassInfo":
        copy = ClassInfo(self.name)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "ClassInfo":
        copy = ClassInfo(deepcopy(self.name, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<ClassInfo(index={self.index}, name={self.name!s})>"
        return f"<ClassInfo(name={self.name!s})>"

    def __str__(self) -> str:
        # return pretty_repr(str(self.name))
        if self.index is not None:
            return f"#{self.index}:Class({self.name!s})"
        return f"Class({self.name!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ClassInfo) and self.name == other.name

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.name, ConstIndex):
            self.name = pool[self.name.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(ClassInfo.tag, pool.add(self.name)))

    def unwrap(self) -> Result[Class]:
        with Result[Class]() as result:
            if not isinstance(self.name, UTF8Info):
                return result.err(TypeError(f"name {self.name!s} is not a UTF8 constant"))
            # https://github.com/ItzSomebody/stopdecompilingmyjava/blob/master/decompiler-tool-bugs/entry-007/entry.md
            return result.ok(Class(parse_reference(self.name.decode())))
        return result


class StringInfo(ConstInfo):
    """
    A CONSTANT_String_info struct.

    Represents constant objects of type `java/lang/String`.

    Attributes
    ----------
    value: ConstInfo
        A UTF8 constant, used as the value of this string.
    """

    __slots__ = ("value",)

    tag = 8
    wide = False
    since = JAVA_1_0
    loadable = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, value: ConstInfo) -> None:
        super().__init__()
        self.value = value

    def __copy__(self) -> "StringInfo":
        copy = StringInfo(self.value)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "StringInfo":
        copy = StringInfo(deepcopy(self.value, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<StringInfo(index={self.index}, value={self.value!s})>"
        return f"<StringInfo(value={self.value!s})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:String({self.value!s})"
        return f"String({self.value!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StringInfo) and self.value == other.value

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.value, ConstIndex):
            self.value = pool[self.value.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(StringInfo.tag, pool.add(self.value)))

    def unwrap(self) -> Result[String]:
        with Result[String]() as result:
            if not isinstance(self.value, UTF8Info):
                return result.err(TypeError(f"value {self.value!s} is not a UTF8 constant"))
            return result.ok(String(self.value.decode()))
        return result


class FieldrefInfo(ConstInfo):
    """
    A CONSTANT_Fieldref_info struct.

    Represents a reference to a field.

    Attributes
    ----------
    class_: ConstInfo
        A class constant, used as the class containing the field.
    name_and_type: ConstInfo
        A name and type constant, used as the name of the field and the descriptor
        detailing the type of the field.
    """

    __slots__ = ("class_", "name_and_type")

    tag = 9
    wide = False
    since = JAVA_1_0
    loadable = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        class_index, nat_index = unpack_HH(stream.read(4))
        return cls(pool[class_index], pool[nat_index])

    def __init__(self, class_: ConstInfo, name_and_type: ConstInfo) -> None:
        super().__init__()
        self.class_ = class_
        self.name_and_type = name_and_type

    def __copy__(self) -> "FieldrefInfo":
        copy = FieldrefInfo(self.class_, self.name_and_type)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "FieldrefInfo":
        copy = FieldrefInfo(deepcopy(self.class_, memo), deepcopy(self.name_and_type, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<FieldrefInfo(index={self.index}, class_={self.class_!s}, name_and_type={self.name_and_type!s})>"
        return f"<FieldrefInfo(class_={self.class_!s}, name_and_type={self.name_and_type!s})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:Fieldref({self.class_!s}.{self.name_and_type!s})"
        return f"Fieldref({self.class_!s}.{self.name_and_type!s})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FieldrefInfo) and
            self.class_ == other.class_ and
            self.name_and_type == other.name_and_type
        )

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.class_, ConstIndex):
            self.class_ = pool[self.class_.index]
        if isinstance(self.name_and_type, ConstIndex):
            self.name_and_type = pool[self.name_and_type.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(FieldrefInfo.tag, pool.add(self.class_), pool.add(self.name_and_type)))


class MethodrefInfo(ConstInfo):
    """
    A CONSTANT_Methodref_info struct.

    Represents a reference to a method.

    Attributes
    ----------
    class_: ConstInfo
        A class constant, used as the class containing the method.
    name_and_type: ConstInfo
        A name and type constant, used as the name of the method and the descriptor
        detailing the argument and return types of the method.
    """

    __slots__ = ("class_", "name_and_type")

    tag = 10
    wide = False
    since = JAVA_1_0
    loadable = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        class_index, nat_index = unpack_HH(stream.read(4))
        return cls(pool[class_index], pool[nat_index])

    def __init__(self, class_: ConstInfo, name_and_type: ConstInfo) -> None:
        super().__init__()
        self.class_ = class_
        self.name_and_type = name_and_type

    def __copy__(self) -> "MethodrefInfo":
        copy = MethodrefInfo(self.class_, self.name_and_type)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "MethodrefInfo":
        copy = MethodrefInfo(deepcopy(self.class_, memo), deepcopy(self.name_and_type, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<MethodrefInfo(index={self.index}, class_={self.class_!s}, name_and_type={self.name_and_type!s})>"
        return f"<MethodrefInfo(class_={self.class_!s}, name_and_type={self.name_and_type!s})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:Methodref({self.class_!s}.{self.name_and_type!s})"
        return f"Methodref({self.class_!s}.{self.name_and_type!s})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, MethodrefInfo) and
            self.class_ == other.class_ and
            self.name_and_type == other.name_and_type
        )

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.class_, ConstIndex):
            self.class_ = pool[self.class_.index]
        if isinstance(self.name_and_type, ConstIndex):
            self.name_and_type = pool[self.name_and_type.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(MethodrefInfo.tag, pool.add(self.class_), pool.add(self.name_and_type)))


class InterfaceMethodrefInfo(ConstInfo):
    """
    A CONSTANT_InterfaceMethodref_info struct.

    Represents a reference to an interface method.

    Attributes
    ----------
    class_: ConstInfo
        A class constant, used as the interface containing the method.
    name_and_type: ConstInfo
        A name and type constant, used as the name of the method and the descriptor
        detailing the argument and return types of the method.
    """

    __slots__ = ("class_", "name_and_type")

    tag = 11
    wide = False
    since = JAVA_1_0
    loadable = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        class_index, nat_index = unpack_HH(stream.read(4))
        return cls(pool[class_index], pool[nat_index])

    def __init__(self, class_: ConstInfo, name_and_type: ConstInfo) -> None:
        super().__init__()
        self.class_ = class_
        self.name_and_type = name_and_type

    def __copy__(self) -> "InterfaceMethodrefInfo":
        copy = InterfaceMethodrefInfo(self.class_, self.name_and_type)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "InterfaceMethodrefInfo":
        copy = InterfaceMethodrefInfo(deepcopy(self.class_, memo), deepcopy(self.name_and_type, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return (
                f"<InterfaceMethodrefInfo(index={self.index}, class_={self.class_!s}, "
                f"name_and_type={self.name_and_type!s})>"
            )
        return f"<InterfaceMethodrefInfo(class_={self.class_!s}, name_and_type={self.name_and_type!s})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:InterfaceMethodref({self.class_!s}.{self.name_and_type!s})"
        return f"InterfaceMethodref({self.class_!s}.{self.name_and_type!s})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, InterfaceMethodrefInfo) and
            self.class_ == other.class_ and
            self.name_and_type == other.name_and_type
        )

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.class_, ConstIndex):
            self.class_ = pool[self.class_.index]
        if isinstance(self.name_and_type, ConstIndex):
            self.name_and_type = pool[self.name_and_type.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(InterfaceMethodrefInfo.tag, pool.add(self.class_), pool.add(self.name_and_type)))


class NameAndTypeInfo(ConstInfo):
    """
    A CONSTANT_NameAndType_info struct.

    Represents a name and descriptor pair.

    Attributes
    ----------
    name: ConstInfo
        A UTF8 constant, used as the name.
    descriptor: ConstInfo
        A UTF8 constant, used as the descriptor.
    """

    __slots__ = ("name", "descriptor")

    tag = 12
    wide = False
    since = JAVA_1_0
    loadable = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        name_index, desc_index = unpack_HH(stream.read(4))
        return cls(pool[name_index], pool[desc_index])

    def __init__(self, name: ConstInfo, descriptor: ConstInfo) -> None:
        super().__init__()
        self.name = name
        self.descriptor = descriptor

    def __copy__(self) -> "NameAndTypeInfo":
        copy = NameAndTypeInfo(self.name, self.descriptor)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "NameAndTypeInfo":
        copy = NameAndTypeInfo(deepcopy(self.name, memo), deepcopy(self.descriptor, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<NameAndTypeInfo(index={self.index}, name={self.name!s}, descriptor={self.descriptor!s})>"
        return f"<NameAndTypeInfo(name={self.name!s}, descriptor={self.descriptor!s})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:NameAndType({self.name!s}:{self.descriptor!s})"
        return f"NameAndType({self.name!s}:{self.descriptor!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NameAndTypeInfo) and self.name == other.name and self.descriptor == other.descriptor

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.name, ConstIndex):
            self.name = pool[self.name.index]
        if isinstance(self.descriptor, ConstIndex):
            self.descriptor = pool[self.descriptor.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(NameAndTypeInfo.tag, pool.add(self.name), pool.add(self.descriptor)))


class MethodHandleInfo(ConstInfo):
    """
    A CONSTANT_MethodHandle_info primitive.

    This represents a method handle.

    Attributes
    ----------
    GET_FIELD: int
        A constant denoting a `REF_getField` reference kind.
        Generic interpretation: `getfield C.f:T`
    GET_STATIC: int
        A constant denoting a `REF_getStatic` reference kind.
        Generic interpretation: `getstatic C.f:T`
    PUT_FIELD: int
        A constant denoting a `REF_putField` reference kind.
        Generic interpretation: `putfield C.f:T`
    PUT_STATIC: int
        A constant denoting a `REF_putStatic` reference kind.
        Generic interpretation: `putstatic C.f:T`
    INVOKE_VIRTUAL: int
        A constant denoting a `REF_invokeVirtual` reference kind.
        Generic interpretation: `invokevirtual C.m:(A*)T`
    INVOKE_STATIC: int
        A constant denoting a `REF_invokeStatic` reference kind.
        Generic interpretation: `invokestatic C.m:(A*)T`
    INVOKE_SPECIAL: int
        A constant denoting a `REF_invokeSpecial` reference kind.
        Generic interpretation: `invokespecial C.m:(A*)T`
    NEW_INVOKE_SPECIAL: int
        A constant denoting a `REF_newInvokeSpecial` reference kind.
        Generic interpretation: `new C; dup; invokespecial C.<init>:(A*)V`
    INVOKE_INTERFACE: int
        A constant denoting a `REF_invokeInterface` reference kind.
        Generic interpretation: `invokeinterface C.m:(A*)T`

    kind: int
        The kind of reference.
    ref: ConstInfo
        A field, method or interface method reference constant, used as the target
        of this method handle.
    """

    __slots__ = ("kind", "ref")

    GET_FIELD          = 1
    GET_STATIC         = 2
    PUT_FIELD          = 3
    PUT_STATIC         = 4
    INVOKE_VIRTUAL     = 5
    INVOKE_STATIC      = 6
    INVOKE_SPECIAL     = 7
    NEW_INVOKE_SPECIAL = 8
    INVOKE_INTERFACE   = 9

    _KINDS = {
        GET_FIELD:          "GET_FIELD",
        GET_STATIC:         "GET_STATIC",
        PUT_FIELD:          "PUT_FIELD",
        PUT_STATIC:         "PUT_STATIC",
        INVOKE_VIRTUAL:     "INVOKE_VIRTUAL",
        INVOKE_STATIC:      "INVOKE_STATIC",
        INVOKE_SPECIAL:     "INVOKE_SPEICAL",
        NEW_INVOKE_SPECIAL: "NEW_INVOKE_SPECIAL",
        INVOKE_INTERFACE:   "INVOKE_INTERFACE",
    }

    tag = 15
    wide = False
    since = JAVA_7
    loadable = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        kind, index = unpack_BH(stream.read(3))
        return cls(kind, pool[index])

    def __init__(self, kind: int, ref: ConstInfo) -> None:
        super().__init__()
        self.kind = kind
        self.ref = ref

    def __copy__(self) -> "MethodHandleInfo":
        copy = MethodHandleInfo(self.kind, self.ref)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "MethodHandleInfo":
        copy = MethodHandleInfo(self.kind, deepcopy(self.ref, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        kind_str = MethodHandleInfo._KINDS.get(self.kind) or str(self.kind)
        if self.index is not None:
            return f"<MethodHandleInfo(index={self.index}, kind={kind_str}, ref={self.ref!s})>"
        return f"<MethodHandleInfo(kind={kind_str}, ref={self.ref!s})>"

    def __str__(self) -> str:
        kind_str = MethodHandleInfo._KINDS.get(self.kind) or str(self.kind)
        if self.index is not None:
            return f"#{self.index}:MethodHandle({kind_str},{self.ref!s})"
        return f"MethodHandle({kind_str},{self.ref!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MethodHandleInfo) and self.kind == other.kind and self.ref == other.ref

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.ref, ConstIndex):
            self.ref = pool[self.ref.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BBH(MethodHandleInfo.tag, self.kind, pool.add(self.ref)))

    def unwrap(self) -> Result[MethodHandle]:
        with Result[MethodHandle]() as result:
            field = False

            if self.kind in (
                MethodHandleInfo.GET_FIELD, MethodHandleInfo.GET_STATIC,
                MethodHandleInfo.PUT_FIELD, MethodHandleInfo.PUT_STATIC
            ):
                if not isinstance(self.ref, FieldrefInfo):
                    return result.err(TypeError(f"reference {self.ref!s} is not a field reference"))
                field = True
            elif self.kind in (MethodHandleInfo.INVOKE_VIRTUAL, MethodHandleInfo.NEW_INVOKE_SPECIAL):
                if not isinstance(self.ref, MethodrefInfo):
                    return result.err(TypeError(f"reference {self.ref!s} is not a method reference"))
            elif self.kind in (
                MethodHandleInfo.INVOKE_STATIC, MethodHandleInfo.INVOKE_SPECIAL, MethodHandleInfo.INVOKE_INTERFACE,
            ):
                # Note that Java 8 and below does not allow this to be an interface method, but we can't check the
                # version so we'll just be generous in this case.
                if not isinstance(self.ref, (MethodrefInfo, InterfaceMethodrefInfo)):
                    return result.err(TypeError(f"reference {self.ref!s} is not a method or interface method reference"))
            else:
                return result.err(ValueError(f"reference kind {self.kind} is not valid"))

            class_ = self.ref.class_
            name_and_type = self.ref.name_and_type

            if not isinstance(class_, ClassInfo):
                return result.err(TypeError(f"reference class {class_!s} is not a class constant"))
            if not isinstance(name_and_type, NameAndTypeInfo):
                return result.err(TypeError(f"reference name and type {name_and_type!s} is not a name and type constant"))

            name = name_and_type.name
            descriptor = name_and_type.descriptor

            if not isinstance(name, UTF8Info):
                return result.err(TypeError(f"reference name {name!s} is not a UTF8 constant"))
            if not isinstance(descriptor, UTF8Info):
                return result.err(TypeError(f"reference descriptor {descriptor!s} is not a UTF8 constant"))

            if not field:
                arg_types, ret_type = parse_method_descriptor(descriptor.decode())
            else:
                arg_types = ()
                ret_type = parse_field_descriptor(descriptor.decode())

            return result.ok(MethodHandle(
                MethodHandle.Kind(self.kind), class_.unwrap().unwrap_into(result), name.decode(), arg_types, ret_type,
            ))
        return result


class MethodTypeInfo(ConstInfo):
    """
    A CONSTANT_MethodType_info struct.

    Attributes
    ----------
    descriptor: ConstInfo
        A UTF8 constant used as the descriptor representing the argument and return
        types of a method.
    """

    __slots__ = ("descriptor",)

    tag = 16
    wide = False
    since = JAVA_7
    loadable = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, descriptor: ConstInfo) -> None:
        super().__init__()
        self.descriptor = descriptor

    def __copy__(self) -> "MethodTypeInfo":
        copy = MethodTypeInfo(self.descriptor)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "MethodTypeInfo":
        copy = MethodTypeInfo(deepcopy(self.descriptor, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<MethodTypeInfo(index={self.index}, descriptor={self.descriptor!s})>"
        return f"<MethodTypeInfo(descriptor={self.descriptor!s})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:MethodType({self.descriptor!s})"
        return f"MethodType({self.descriptor!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MethodTypeInfo) and self.descriptor == other.descriptor

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.descriptor, ConstIndex):
            self.descriptor = pool[self.descriptor.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(MethodTypeInfo.tag, pool.add(self.descriptor)))

    def unwrap(self) -> Result[MethodType]:
        with Result[MethodType]() as result:
            if not isinstance(self.descriptor, UTF8Info):
                return result.err(TypeError(f"descriptor {self.descriptor!s} is not a UTF8 constant"))
            return result.ok(MethodType(*parse_method_descriptor(self.descriptor.decode())))
        return result


class DynamicInfo(ConstInfo):
    """
    A CONSTANT_Dynamic_info struct.

    Represents a dynamically computed constant.

    Attributes
    ----------
    attr_index: int
        The index of the bootstrap method in the `BootstrapMethods` attribute.
    name_and_type: ConstInfo
        A name and type constant, used as the name and descriptor of the entity to
        be computed.
    """

    __slots__ = ("attr_index", "name_and_type")

    tag = 17
    wide = False
    since = JAVA_11
    loadable = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        attr_index, nat_index = unpack_HH(stream.read(4))
        return cls(attr_index, pool[nat_index])

    def __init__(self, attr_index: int, name_and_type: ConstInfo) -> None:
        super().__init__()
        self.attr_index = attr_index
        self.name_and_type = name_and_type

    def __copy__(self) -> "DynamicInfo":
        copy = DynamicInfo(self.attr_index, self.name_and_type)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "DynamicInfo":
        copy = DynamicInfo(self.attr_index, deepcopy(self.name_and_type, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return (
                f"<DynamicInfo(index={self.index}, attr_index={self.attr_index}, name_and_type={self.name_and_type!s})>"
            )
        return f"<DynamicInfo(attr_index={self.attr_index}, name_and_type={self.name_and_type!s})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:Dynamic(#{self.attr_index},{self.name_and_type!s})"
        return f"Dynamic(#{self.attr_index},{self.name_and_type!s})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, DynamicInfo) and
            self.attr_index == other.attr_index and
            self.name_and_type == other.name_and_type
        )

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.name_and_type, ConstIndex):
            self.name_and_type = pool[self.name_and_type.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(DynamicInfo.tag, self.attr_index, pool.add(self.name_and_type)))


class InvokeDynamicInfo(ConstInfo):
    """
    A CONSTANT_InvokeDynamic_info struct.

    Represents a dynamically computed callsite of type `java/lang/invoke/CallSite`.

    Attributes
    ----------
    attr_index: int
        The index of the bootstrap method in the `BootstrapMethods` attribute.
    name_and_type: ConstInfo
        A name and type constant, used as the name and descriptor of the method to
        be invoked at this call site.
    """

    __slots__ = ("attr_index", "name_and_type")

    tag = 18
    wide = False
    since = JAVA_7
    loadable = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        attr_index, nat_index = unpack_HH(stream.read(4))
        return cls(attr_index, pool[nat_index])

    def __init__(self, attr_index: int, name_and_type: ConstInfo) -> None:
        super().__init__()
        self.attr_index = attr_index
        self.name_and_type = name_and_type

    def __copy__(self) -> "InvokeDynamicInfo":
        copy = InvokeDynamicInfo(self.attr_index, self.name_and_type)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "InvokeDynamicInfo":
        copy = InvokeDynamicInfo(self.attr_index, deepcopy(self.name_and_type, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return (
                f"<InvokeDynamicInfo(index={self.index}, attr_index={self.attr_index}, "
                f"name_and_type={self.name_and_type!s})>"
            )
        return f"<InvokeDynamicInfo(attr_index={self.attr_index}, name_and_type={self.name_and_type!s})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:InvokeDynamic(#{self.attr_index},{self.name_and_type!s})"
        return f"InvokeDynamic(#{self.attr_index},{self.name_and_type!s})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, InvokeDynamicInfo) and
            self.attr_index == other.attr_index and
            self.name_and_type == other.name_and_type
        )

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.name_and_type, ConstIndex):
            self.name_and_type = pool[self.name_and_type.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(InvokeDynamicInfo.tag, self.attr_index, pool.add(self.name_and_type)))


class ModuleInfo(ConstInfo):
    """
    A CONSTANT_Module_info struct.

    Attributes
    ----------
    name: ConstInfo
        A UTF8 constant, used as the name of the module.
    """

    __slots__ = ("name",)

    tag = 19
    wide = False
    since = JAVA_9
    loadable = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, name: ConstInfo) -> None:
        super().__init__()
        self.name = name

    def __copy__(self) -> "ModuleInfo":
        copy = ModuleInfo(self.name)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "ModuleInfo":
        copy = ModuleInfo(deepcopy(self.name, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<ModuleInfo(index={self.index}, name={self.name!s})>"
        return f"<ModuleInfo(name={self.name!s})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:Module({self.name!s})"
        return f"Module({self.name!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ModuleInfo) and self.name == other.name

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.name, ConstIndex):
            self.name = pool[self.name.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(ModuleInfo.tag, pool.add(self.name)))


class PackageInfo(ConstInfo):
    """
    A CONSTANT_Package_info struct.

    Attributes
    ----------
    name: ConstInfo
        A UTF8 constant, used as the name of the package.
    """

    __slots__ = ("name",)

    tag = 20
    wide = False
    since = JAVA_9
    loadable = False

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, name: ConstInfo) -> None:
        super().__init__()
        self.name = name

    def __copy__(self) -> "PackageInfo":
        copy = PackageInfo(self.name)
        copy.index = self.index
        return copy

    def __deepcopy__(self, memo: dict[int, object]) -> "PackageInfo":
        copy = PackageInfo(deepcopy(self.name, memo))
        copy.index = self.index
        return copy

    def __repr__(self) -> str:
        if self.index is not None:
            return f"<PackageInfo(index={self.index}, name={self.name!s})>"
        return f"<PackageInfo(name={self.name!s})>"

    def __str__(self) -> str:
        if self.index is not None:
            return f"#{self.index}:Package({self.name!s})"
        return f"Package({self.name!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PackageInfo) and self.name == other.name

    def deref(self, pool: "ConstPool") -> None:
        if isinstance(self.name, ConstIndex):
            self.name = pool[self.name.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(PackageInfo.tag, pool.add(self.name)))

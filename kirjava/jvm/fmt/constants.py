#!/usr/bin/env python3

__all__ = (
    "ConstInfo", "ConstIndex",

    "UTF8Info", "IntegerInfo", "FloatInfo",
    "LongInfo", "DoubleInfo", "ClassInfo",
    "StringInfo", "FieldrefInfo", "MethodrefInfo",
    "InterfaceMethodrefInfo", "NameAndTypeInfo", "MethodHandleInfo",
    "MethodTypeInfo", "DynamicInfo", "InvokeDynamicInfo",
    "ModuleInfo", "PackageInfo",
)

import typing
from functools import cache
from typing import IO

from .._struct import *
from ..version import *
from ...backend import *
from ...model.values.constants import *

if typing.TYPE_CHECKING:
    from .pool import ConstPool
    from ..verify import Verifier


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

    copy(self) -> ConstInfo
        Creates a copy of this cosntant.
    populate(self, pool: ConstPool) -> None
        Dereferences any indices in the constant.
    write(self, stream: IO[bytes], pool: ConstPool) -> None
        Writes the constant info to a binary stream.
    verify(self, verifier: Verifier) -> None
        Verifies that the constant is valid.
    unwrap(self) -> Constant
        Unwraps this constant info into a model constant.
    """

    __slots__ = ("index",)

    tag: int
    wide: bool
    since: Version
    loadable: bool

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "ConstInfo":
        """
        Internal constant read.
        """

        raise NotImplementedError("_read() is not implemented for %r" % cls)

    @classmethod
    @cache
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
        subclass: type[ConstInfo] | None = ConstInfo.lookup(tag)
        if subclass is None:
            raise ValueError("unknown constant pool tag %i" % tag)
        info = subclass._read(stream, pool)
        info.index = pool.maximum
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

    def __repr__(self) -> str:
        raise NotImplementedError("repr() is not implemented for %r" % type(self))

    def __str__(self) -> str:
        raise NotImplementedError("str() is not implemented for %r" % type(self))

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError("== is not implemented for %r" % type(self))

    # TODO: Descriptors, coercion/expectation.

    # def __get__(self, instance: object, owner: type) -> "ConstInfo":
    #     if instance is None:
    #         return self
    #     return instance.__dict__[self.__name__]

    # def __set__(self, instance: object, value: "ConstInfo") -> None:
    #     instance.__dict__[self.__name__] = value

    def copy(self) -> "ConstInfo":
        """
        Creates a copy of this constant.
        """

        raise NotImplementedError("copy() is not implemented for %r" % type(self))

    def populate(self, pool: "ConstPool") -> None:
        """
        Dereferences any indices in the constant.

        Parameters
        ----------
        pool: ConstPool
            The constant pool to dereference from.
        """

        raise NotImplementedError("populate() is not implemented for %r" % type(self))

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

        raise NotImplementedError("write() is not implemented for %r" % type(self))

    def verify(self, verifier: "Verifier") -> None:
        """
        Verifies that the constant is valid.

        Parameters
        ----------
        verifier: Verifier
            The verifier to use and report to.
        """

        raise NotImplementedError("verify() is not implemented for %r" % type(self))

    def unwrap(self) -> Constant:
        """
        Unwraps this constant info.

        Returns
        -------
        Constant
            The unwrapped `Constant`.

        Raises
        ------
        ValueError
            If this constant info cannot be unwrapped.
        """

        raise ValueError("cannot unwrap constant %r" % self)


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "ConstIndex":
        return cls(pool.maximum)  # Shouldn't really happen, though.

    def __init__(self, index: int) -> None:
        super().__init__(index)
        self.index: int

    def __repr__(self) -> str:
        return "<ConstIndex(index=%i)>" % self.index

    def __str__(self) -> str:
        return "#%i" % self.index

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ConstIndex) and self.index == other.index

    def copy(self) -> "ConstIndex":
        return ConstIndex(self.index)

    def populate(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        ...

    def verify(self, verifier: "Verifier") -> None:
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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "UTF8Info":
        length, = unpack_H(stream.read(2))
        return cls(stream.read(length))

    def __init__(self, value: bytes) -> None:  # TODO: Automatic string encoding.
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        if self.index is not None:
            return "<UTF8Info(index=%i, value=%r)>" % (self.index, self.value)
        return "<UTF8Info(value=%r)>" % self.value

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:%r" % (self.index, self.decode())
        return repr(self.decode())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UTF8Info) and self.value == other.value

    def copy(self) -> "UTF8Info":
        copy = UTF8Info(self.value)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(UTF8Info.tag, len(self.value)))
        stream.write(self.value)

    def verify(self, verifier: "Verifier") -> None:
        if len(self.value) > 65535:
            verifier.fatal(self, "utf8 constant is too long")
        if verifier.check_utf8_null_bytes and b"\x00" in self.value:
            verifier.fatal(self, "null bytes in utf8 constant")

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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "IntegerInfo":
        return cls(unpack_i32(stream.read(4)))

    def __init__(self, value: i32) -> None:
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        if self.index is not None:
            return "<IntegerInfo(index=%i, value=%r)>" % (self.index, self.value)
        return "<IntegerInfo(value=%r)>" % self.value

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:%si" % (self.index, self.value)
        return "%si" % self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IntegerInfo) and self.value == other.value

    def copy(self) -> "IntegerInfo":
        copy = IntegerInfo(self.value)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((IntegerInfo.tag,)))
        stream.write(pack_i32(self.value))

    def verify(self, verifier: "Verifier") -> None:
        ...

    def unwrap(self) -> Integer:
        return Integer(self.value)


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "FloatInfo":
        return cls(unpack_f32(stream.read(4)))

    def __init__(self, value: f32) -> None:
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        if self.index is not None:
            return "<FloatInfo(index=%i, value=%r)>" % (self.index, self.value)
        return "<FloatInfo(value=%r)>" % self.value

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:%sf" % (self.index, self.value)
        return "%sf" % self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FloatInfo):
            return False
        if self.value == other.value:
            return True
        # FIXME: Will not resolve exact NaN matches though. Could cause issues.
        elif isnan(self.value) and isnan(other.value):  # Special case check, annoyingly.
            return True
        return False

    def copy(self) -> "FloatInfo":
        copy = FloatInfo(self.value)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((FloatInfo.tag,)))
        stream.write(pack_f32(self.value))

    def verify(self, verifier: "Verifier") -> None:
        ...

    def unwrap(self) -> Float:
        return Float(self.value)


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "LongInfo":
        return cls(unpack_i64(stream.read(8)))

    def __init__(self, value: i64) -> None:
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        if self.index is not None:
            return "<LongInfo(index=%i, value=%r)>" % (self.index, self.value)
        return "<LongInfo(value=%r)>" % self.value

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:%sl" % (self.index, self.value)
        return "%sl" % self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LongInfo) and self.value == other.value

    def copy(self) -> "LongInfo":
        copy = LongInfo(self.value)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((LongInfo.tag,)))
        stream.write(pack_i64(self.value))

    def verify(self, verifier: "Verifier") -> None:
        ...

    def unwrap(self) -> Long:
        return Long(self.value)


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "DoubleInfo":
        return cls(unpack_f64(stream.read(8)))

    def __init__(self, value: f64) -> None:
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        if self.index is not None:
            return "<DoubleInfo(index=%i, value=%r)>" % (self.index, self.value)
        return "<DoubleInfo(value=%r)>" % self.value

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:%sd" % (self.index, self.value)
        return "%sd" % self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DoubleInfo):
            return False
        if self.value == other.value:
            return True
        elif isnan(self.value) and isnan(other.value):
            return True
        return False

    def copy(self) -> "DoubleInfo":
        copy = DoubleInfo(self.value)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        ...

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(bytes((DoubleInfo.tag,)))
        stream.write(pack_f64(self.value))

    def verify(self, verifier: "Verifier") -> None:
        ...

    def unwrap(self) -> Double:
        return Double(self.value)


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "ClassInfo":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, name: ConstInfo) -> None:
        super().__init__()
        self.name = name

    def __repr__(self) -> str:
        if self.index is not None:
            return "<ClassInfo(index=%i, name=%s)>" % (self.index, self.name)
        return "<ClassInfo(name=%s)>" % self.name

    def __str__(self) -> str:
        # return pretty_repr(str(self.name))
        if self.index is not None:
            return "#%i:Class(%s)" % (self.index, self.name)
        return "Class(%s)" % self.name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ClassInfo) and self.name == other.name

    def copy(self) -> "ClassInfo":
        copy = ClassInfo(self.name)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.name, ConstIndex):
            self.name = pool[self.name.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(ClassInfo.tag, pool.add(self.name)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types and not isinstance(self.name, UTF8Info):
            verifier.fatal(self, "name is not a UTF8 constant")

    def unwrap(self) -> Class:
        if not isinstance(self.name, UTF8Info):
            raise ValueError("%r name is not a UTF8 constant" % self)
        return Class(self.name.decode())


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "StringInfo":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, value: ConstInfo) -> None:
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        if self.index is not None:
            return "<StringInfo(index=%i, value=%s)>" % (self.index, self.value)
        return "<StringInfo(value=%s)>" % self.value

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:String(%s)" % (self.index, self.value)
        return "String(%s)" % self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StringInfo) and self.value == other.value

    def copy(self) -> "StringInfo":
        copy = StringInfo(self.value)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.value, ConstIndex):
            self.value = pool[self.value.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(StringInfo.tag, pool.add(self.value)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types and not isinstance(self.value, UTF8Info):
            verifier.fatal(self, "value is not a UTF8 constant")

    def unwrap(self) -> String:
        if not isinstance(self.value, UTF8Info):
            raise ValueError("%r value is not a UTF8 constant" % self)
        return String(self.value.decode())


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "FieldrefInfo":
        class_index, nat_index = unpack_HH(stream.read(4))
        return cls(pool[class_index], pool[nat_index])

    def __init__(self, class_: ConstInfo, name_and_type: ConstInfo) -> None:
        super().__init__()
        self.class_ = class_
        self.name_and_type = name_and_type

    def __repr__(self) -> str:
        if self.index is not None:
            return "<FieldrefInfo(index=%i, class_=%s, name_and_type=%s)>" % (
                self.index, self.class_, self.name_and_type,
            )
        return "<FieldrefInfo(class_=%s, name_and_type=%s)>" % (self.class_, self.name_and_type)

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:Fieldref(%s.%s)" % (self.index, self.class_, self.name_and_type)
        return "Fieldref(%s.%s)" % (self.class_, self.name_and_type)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FieldrefInfo) and
            self.class_ == other.class_ and
            self.name_and_type == other.name_and_type
        )

    def copy(self) -> "FieldrefInfo":
        copy = FieldrefInfo(self.class_, self.name_and_type)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.class_, ConstIndex):
            self.class_ = pool[self.class_.index]
        if isinstance(self.name_and_type, ConstIndex):
            self.name_and_type = pool[self.name_and_type.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(FieldrefInfo.tag, pool.add(self.class_), pool.add(self.name_and_type)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types:
            if not isinstance(self.class_, ClassInfo):
                verifier.fatal(self, "class is not a class constant")
            if not isinstance(self.name_and_type, NameAndTypeInfo):
                verifier.fatal(self, "name and type is not a name and type constant")


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "MethodrefInfo":
        class_index, nat_index = unpack_HH(stream.read(4))
        return cls(pool[class_index], pool[nat_index])

    def __init__(self, class_: ConstInfo, name_and_type: ConstInfo) -> None:
        super().__init__()
        self.class_ = class_
        self.name_and_type = name_and_type

    def __repr__(self) -> str:
        if self.index is not None:
            return "<MethodrefInfo(index=%i, class_=%s, name_and_type=%s)>" % (
                self.index, self.class_, self.name_and_type,
            )
        return "<MethodrefInfo(class_=%s, name_and_type=%s)>" % (self.class_, self.name_and_type)

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:Methodref(%s.%s)" % (self.index, self.class_, self.name_and_type)
        return "Methodref(%s.%s)" % (self.class_, self.name_and_type)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, MethodrefInfo) and
            self.class_ == other.class_ and
            self.name_and_type == other.name_and_type
        )

    def copy(self) -> "MethodrefInfo":
        copy = MethodrefInfo(self.class_, self.name_and_type)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.class_, ConstIndex):
            self.class_ = pool[self.class_.index]
        if isinstance(self.name_and_type, ConstIndex):
            self.name_and_type = pool[self.name_and_type.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(MethodrefInfo.tag, pool.add(self.class_), pool.add(self.name_and_type)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types:
            if not isinstance(self.class_, ClassInfo):
                verifier.fatal(self, "class is not a class constant")
            if not isinstance(self.name_and_type, NameAndTypeInfo):
                verifier.fatal(self, "name and type is not a name and type constant")


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "InterfaceMethodrefInfo":
        class_index, nat_index = unpack_HH(stream.read(4))
        return cls(pool[class_index], pool[nat_index])

    def __init__(self, class_: ConstInfo, name_and_type: ConstInfo) -> None:
        super().__init__()
        self.class_ = class_
        self.name_and_type = name_and_type

    def __repr__(self) -> str:
        if self.index is not None:
            return "<InterfaceMethodrefInfo(index=%i, class_=%s, name_and_type=%s)>" % (
                self.index, self.class_, self.name_and_type,
            )
        return "<InterfaceMethodrefInfo(class_=%s, name_and_type=%s)>" % (self.class_, self.name_and_type)

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:InterfaceMethodref(%s.%s)" % (self.index, self.class_, self.name_and_type)
        return "InterfaceMethodref(%s.%s)" % (self.class_, self.name_and_type)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, InterfaceMethodrefInfo) and
            self.class_ == other.class_ and
            self.name_and_type == other.name_and_type
        )

    def copy(self) -> "InterfaceMethodrefInfo":
        copy = InterfaceMethodrefInfo(self.class_, self.name_and_type)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.class_, ConstIndex):
            self.class_ = pool[self.class_.index]
        if isinstance(self.name_and_type, ConstIndex):
            self.name_and_type = pool[self.name_and_type.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(InterfaceMethodrefInfo.tag, pool.add(self.class_), pool.add(self.name_and_type)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types:
            if not isinstance(self.class_, ClassInfo):
                verifier.fatal(self, "class is not a class constant")
            if not isinstance(self.name_and_type, NameAndTypeInfo):
                verifier.fatal(self, "name and type is not a name and type constant")


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "NameAndTypeInfo":
        name_index, desc_index = unpack_HH(stream.read(4))
        return cls(pool[name_index], pool[desc_index])

    def __init__(self, name: ConstInfo, descriptor: ConstInfo) -> None:
        super().__init__()
        self.name = name
        self.descriptor = descriptor

    def __repr__(self) -> str:
        if self.index is not None:
            return "<NameAndTypeInfo(index=%i, name=%s, descriptor=%s)>" % (
                self.index, self.name, self.descriptor,
            )
        return "<NameAndTypeInfo(name=%s, descriptor=%s)>" % (self.name, self.descriptor)

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:NameAndType(%s:%s)" % (self.index, self.name, self.descriptor)
        return "NameAndType(%s:%s)" % (self.name, self.descriptor)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NameAndTypeInfo) and self.name == other.name and self.descriptor == other.descriptor

    def copy(self) -> "NameAndTypeInfo":
        copy = NameAndTypeInfo(self.name, self.descriptor)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.name, ConstIndex):
            self.name = pool[self.name.index]
        if isinstance(self.descriptor, ConstIndex):
            self.descriptor = pool[self.descriptor.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(NameAndTypeInfo.tag, pool.add(self.name), pool.add(self.descriptor)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types:
            if not isinstance(self.name, UTF8Info):
                verifier.fatal(self, "name is not a UTF8 constant")
            if not isinstance(self.descriptor, UTF8Info):
                verifier.fatal(self, "descriptor is not a UTF8 constant")


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

    tag = 15
    wide = False
    since = JAVA_7
    loadable = True

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "MethodHandleInfo":
        kind, index = unpack_BH(stream.read(3))
        return cls(kind, pool[index])

    def __init__(self, kind: int, ref: ConstInfo) -> None:
        super().__init__()
        self.kind = kind
        self.ref = ref

    def __repr__(self) -> str:
        if self.index is not None:
            return "<MethodHandleInfo(index=%i, kind=%i, ref=%s)>" % (self.index, self.kind, self.ref)
        return "<MethodHandleInfo(kind=%i, ref=%s)>" % (self.kind, self.ref)

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:MethodHandle(%i,%s)" % (self.index, self.kind, self.ref)
        return "MethodHandle(%i,%s)" % (self.kind, self.ref)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MethodHandleInfo) and self.kind == other.kind and self.ref == other.ref

    def copy(self) -> "MethodHandleInfo":
        copy = MethodHandleInfo(self.kind, self.ref)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.ref, ConstIndex):
            self.ref = pool[self.ref.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BBH(MethodHandleInfo.tag, self.kind, pool.add(self.ref)))

    def verify(self, verifier: "Verifier") -> None:
        # This method is a handful lol, read carefully if you dare.

        if self.kind in (
            MethodHandleInfo.GET_FIELD, MethodHandleInfo.GET_STATIC,
            MethodHandleInfo.PUT_FIELD, MethodHandleInfo.PUT_STATIC,
        ):
            if verifier.check_const_types and not isinstance(self.ref, FieldrefInfo):
                verifier.fatal(self, "reference is not a field reference")

        elif self.kind in (
            MethodHandleInfo.INVOKE_VIRTUAL, MethodHandleInfo.INVOKE_STATIC, MethodHandleInfo.INVOKE_SPECIAL,
        ):
            if isinstance(self.ref, MethodrefInfo) or isinstance(self.ref, InterfaceMethodrefInfo):
                if (
                    isinstance(self.ref.name_and_type, NameAndTypeInfo) and
                    isinstance(self.ref.name_and_type.name, UTF8Info) and
                    self.ref.name_and_type.name.value in (b"<init>", b"<clinit>")
                ):
                    verifier.fatal(self, "invalid method reference name")
                # FIXME: Below, need to check version.
                # if (
                #     verifier.check_const_types and
                #     verifier.cf.major < 52 and  # Java SE 8.
                #     not isinstance(self.reference, MethodrefInfo)
                # ):
                #     verifier.fatal(self, "reference is not a method reference")
            elif verifier.check_const_types:
                verifier.fatal(self, "reference is not a method reference or an interface method reference")

        elif self.kind == MethodHandleInfo.NEW_INVOKE_SPECIAL:
            if isinstance(self.ref, MethodrefInfo):
                if (
                    isinstance(self.ref.name_and_type, NameAndTypeInfo) and
                    isinstance(self.ref.name_and_type.name, UTF8Info) and
                    self.ref.name_and_type.name.value != b"<init>"
                ):
                    verifier.fatal(self, "invalid method reference name")
            elif verifier.check_const_types:
                verifier.fatal(self, "reference is not a method reference")

        elif self.kind == MethodHandleInfo.INVOKE_INTERFACE:
            if verifier.check_const_types and not isinstance(self.ref, InterfaceMethodrefInfo):
                verifier.fatal(self, "reference is not an interface method reference")

        else:
            verifier.fatal(self, "kind is not a valid method handle kind")

    # TODO
    # def unwrap(self) -> MethodHandle:
    #     if self.reference_kind in range(self.REF_GET_FIELD, self.REF_PUT_STATIC + 1):
    #         if not isinstance(self.reference_index.info, ConstantFieldrefInfo):
    #             raise ValueError("%r reference index is not a field reference" % self)
    #         reference = self.reference_index.info
    #
    #     elif self.reference_kind in (self.REF_INVOKE_VIRTUAL, self.REF_NEW_INVOKE_SPECIAL):
    #         if not isinstance(self.reference_index.info, ConstantMethodrefInfo):
    #             raise ValueError("%r reference index is not a method reference" % self)
    #         reference = self.reference_index.info
    #
    #     elif self.reference_kind in (self.REF_INVOKE_STATIC, self.REF_INVOKE_SPECIAL, self.REF_INVOKE_INTERFACE):
    #         # FIXME: Version 52.0 and below does not allow all this.
    #         if (
    #             not isinstance(self.reference_index.info, ConstantMethodrefInfo) and
    #             not isinstance(self.reference_index.info, ConstantInterfaceMethodrefInfo)
    #         ):
    #             raise ValueError("%r reference index is not an method/interface method reference" % self)
    #         reference = self.reference_index.info
    #
    #     else:
    #         raise ValueError("%r reference kind is not a valid method handle kind" % self)
    #
    #     if not isinstance(reference.class_index.info, ConstantClassInfo):
    #         raise ValueError("%r reference index class index is not a class reference" % self)
    #     if not isinstance(reference.name_and_type_index.info, ConstantNameAndTypeInfo):
    #         raise ValueError("%r reference index name and type index is not a name and type reference" % self)
    #     name_and_type = reference.name_and_type_index.info
    #
    #     if not isinstance(name_and_type.name_index.info, ConstantUTF8Info):
    #         raise ValueError("%r name and type name index is not a UTF8 constant" % self)
    #     if not isinstance(name_and_type.descriptor_index.info, ConstantUTF8Info):
    #         raise ValueError("%r name and type descriptor index is not a UTF8 constant" % self)
    #
    #     return MethodHandle(
    #         self.reference_kind,
    #         reference.class_index.info.unwrap(),
    #         str(name_and_type.name_index), str(name_and_type.descriptor_index),
    #     )


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "MethodTypeInfo":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, descriptor: ConstInfo) -> None:
        super().__init__()
        self.descriptor = descriptor

    def __repr__(self) -> str:
        if self.index is not None:
            return "<MethodTypeInfo(index=%i, descriptor=%s)>" % (self.index, self.descriptor)
        return "<MethodTypeInfo(descriptor=%s)>" % self.descriptor

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:MethodType(%s)" % (self.index, self.descriptor)
        return "MethodType(%s)" % self.descriptor

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MethodTypeInfo) and self.descriptor == other.descriptor

    def copy(self) -> "MethodTypeInfo":
        copy = MethodTypeInfo(self.descriptor)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.descriptor, ConstIndex):
            self.descriptor = pool[self.descriptor.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(MethodTypeInfo.tag, pool.add(self.descriptor)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types and not isinstance(self.descriptor, UTF8Info):
            verifier.fatal(self, "descriptor is not a UTF8 constant")

    def unwrap(self) -> MethodType:
        if not isinstance(self.descriptor, UTF8Info):
            raise ValueError("%r descriptor index is not a UTF8 constant" % self)
        # TODO: Parse descriptor.
        return MethodType(self.descriptor.decode())


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "DynamicInfo":
        attr_index, nat_index = unpack_HH(stream.read(4))
        return cls(attr_index, pool[nat_index])

    def __init__(self, attr_index: int, name_and_type: ConstInfo) -> None:
        super().__init__()
        self.attr_index = attr_index
        self.name_and_type = name_and_type

    def __repr__(self) -> str:
        if self.index is not None:
            return "<DynamicInfo(index=%i, attr_index=%i, name_and_type=%s)>" % (
                self.index, self.attr_index, self.name_and_type
            )
        return "<DynamicInfo(attr_index=%i, name_and_type=%s)>" % (self.attr_index, self.name_and_type)

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:Dynamic(#%i,%s)" % (self.index, self.attr_index, self.name_and_type)
        return "Dynamic(#%i,%s)" % (self.attr_index, self.name_and_type)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, DynamicInfo) and
            self.attr_index == other.attr_index and
            self.name_and_type == other.name_and_type
        )

    def copy(self) -> "DynamicInfo":
        copy = DynamicInfo(self.attr_index, self.name_and_type)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.name_and_type, ConstIndex):
            self.name_and_type = pool[self.name_and_type.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(DynamicInfo.tag, self.attr_index, pool.add(self.name_and_type)))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.attr_index <= 65535):
            verifier.fatal(self, "invalid bootstrap index")
        if verifier.check_const_types and not isinstance(self.name_and_type, NameAndTypeInfo):
            verifier.fatal(self, "name and type is not a name and type constant")

        # TODO: Good solution for this, will cause circular import otherwise.
        # for attribute in verifier.classfile.attributes:
        #     if not isinstance(attribute, BootstrapMethodsAttribute):
        #         continue


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "InvokeDynamicInfo":
        attr_index, nat_index = unpack_HH(stream.read(4))
        return cls(attr_index, pool[nat_index])

    def __init__(self, attr_index: int, name_and_type: ConstInfo) -> None:
        super().__init__()
        self.attr_index = attr_index
        self.name_and_type = name_and_type

    def __repr__(self) -> str:
        if self.index is not None:
            return "<InvokeDynamicInfo(index=%i, attr_index=%i, name_and_type=%s)>" % (
                self.index, self.attr_index, self.name_and_type,
            )
        return "<InvokeDynamicInfo(attr_index=%i, name_and_type=%s)>" % (self.attr_index, self.name_and_type)

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:InvokeDynamic(#%i,%s)" % (self.index, self.attr_index, self.name_and_type)
        return "InvokeDynamic(#%i,%s)" % (self.attr_index, self.name_and_type)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, InvokeDynamicInfo) and
            self.attr_index == other.attr_index and
            self.name_and_type == other.name_and_type
        )

    def copy(self) -> "InvokeDynamicInfo":
        copy = InvokeDynamicInfo(self.attr_index, self.name_and_type)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.name_and_type, ConstIndex):
            self.name_and_type = pool[self.name_and_type.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(InvokeDynamicInfo.tag, self.attr_index, pool.add(self.name_and_type)))

    def verify(self, verifier: "Verifier") -> None:
        if not (0 <= self.attr_index <= 65535):
            verifier.fatal(self, "invalid bootstrap index")
        if verifier.check_const_types and not isinstance(self.name_and_type, NameAndTypeInfo):
            verifier.fatal(self, "name and type is not a name and type constant")

        # TODO: See above.


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "ModuleInfo":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, name: ConstInfo) -> None:
        super().__init__()
        self.name = name

    def __repr__(self) -> str:
        if self.index is not None:
            return "<ModuleInfo(index=%i, name=%s)>" % (self.index, self.name)
        return "<ModuleInfo(name=%s)>" % self.name

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:Module(%s)" % (self.index, self.name)
        return "Module(%s)" % self.name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ModuleInfo) and self.name == other.name

    def copy(self) -> "ModuleInfo":
        copy = ModuleInfo(self.name)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.name, ConstIndex):
            self.name = pool[self.name.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(ModuleInfo.tag, pool.add(self.name)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types and not isinstance(self.name, UTF8Info):
            verifier.fatal(self, "name is not a UTF8 constant")


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
    def _read(cls, stream: IO[bytes], pool: "ConstPool") -> "PackageInfo":
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, name: ConstInfo) -> None:
        super().__init__()
        self.name = name

    def __repr__(self) -> str:
        if self.index is not None:
            return "<PackageInfo(index=%i, name=%s)>" % (self.index, self.name)
        return "<PackageInfo(name=%s)>" % self.name

    def __str__(self) -> str:
        if self.index is not None:
            return "#%i:Package(%s)" % (self.index, self.name)
        return "Package(%s)" % self.name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PackageInfo) and self.name == other.name

    def copy(self) -> "PackageInfo":
        copy = PackageInfo(self.name)
        copy.index = self.index
        return copy

    def populate(self, pool: "ConstPool") -> None:
        if isinstance(self.name, ConstIndex):
            self.name = pool[self.name.index]

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(PackageInfo.tag, pool.add(self.name)))

    def verify(self, verifier: "Verifier") -> None:
        if verifier.check_const_types and not isinstance(self.name, UTF8Info):
            verifier.fatal(self, "name is not a UTF8 constant")

#!/usr/bin/env python3

__all__ = (
    "Null",
    "ConstantInfo",
    "UTF8",
    "Integer",
    "Float",
    "Long",
    "Double",
    "Class",
    "String",
    "FieldRef",
    "MethodRef",
    "InterfaceMethodRef",
    "NameAndType",
    "MethodHandle",
    "MethodType",
    "Dynamic",
    "InvokeDynamic",
    "Module",
    "Package",
)

import typing
from typing import Any, IO, Optional, Union

from ._struct import *
from .abc import Constant
from .version import Version
from .types import (
    descriptor,
    class_t, double_t, float_t, int_t, long_t, method_handle_t, method_type_t, null_t, string_t,
    Class as ClassType, Reference
)

if typing.TYPE_CHECKING:
    from .classfile import ClassFile


class Null(Constant):
    """
    The null constant.
    """

    __slots__ = ()

    type = null_t

    def __init__(self) -> None:
        super().__init__(None)

    def __repr__(self) -> str:
        return "<Null()>"

    def __str__(self) -> str:
        return "null"


class ConstantInfo(Constant):
    """
    Represents a value in the constant pool.
    """

    __slots__ = ()

    tag = -1
    wide = False
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Union["ConstantInfo", Any]:
        """
        Reads this constant type from the provided buffer.

        :param buffer: The binary data buffer.
        :return: Either the constant, or info that can be used to dereference it.
        """

        ...

    @classmethod
    def dereference(cls, lookups: dict[int, "ConstantInfo"], info: Any) -> Optional["ConstantInfo"]:
        """
        Dereferences this constant from the provided information.

        :param lookups: The constant lookups that have already been computed.
        :param info: The info that was read from the constant pool.
        :return: The dereferenced constant, or None if it can't yet be dereferenced.
        """

        ...

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Writes this constant type to the provided buffer.

        :param class_file: The class file that the constant belongs to.
        :param buffer: The binary data buffer.
        """

        ...


class UTF8(ConstantInfo):
    """
    An MUTF-8 constant.
    """

    __slots__ = ()

    tag = 1
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "UTF8":
        return cls(buffer.read(
            unpack_H(buffer.read(2))[0],
        ).replace(b"\xc0\x80", b"\x00").decode("utf-8", errors="ignore"))

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to dereference UTF8 constant.")

    def __init__(self, value: str) -> None:
        """
        :param value: The decoded string value.
        """

        # TODO: Would be nice to be able to use bytes instead of decoding it.
        super().__init__(value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        value = self.value.encode("utf-8").replace(b"\x00", b"\xc0\x80")
        buffer.write(pack_H(len(value)))
        buffer.write(value)


class Integer(ConstantInfo):
    """
    A 32-bit signed integer constant.
    """

    __slots__ = ()

    type = int_t
    tag = 3
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "Integer":
        return cls(unpack_i(buffer.read(4))[0])

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to dereference integer constant.")

    def __init__(self, value: int) -> None:
        """
        :param value: The integer value of this constant.
        """

        super().__init__(value)

    # def __add__(self, other: Any) -> Integer:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for +: %r and %r" % (Integer, type(other)))
    #     return Integer(<int>self.value + (<Integer>other).value)

    # def __sub__(self, other: Any) -> Integer:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for -: %r and %r" % (Integer, type(other)))
    #     return Integer(<int>self.value - (<Integer>other).value)

    # def __mul__(self, other: Any) -> Integer:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for *: %r and %r" % (Integer, type(other)))
    #     return Integer(<int>self.value * (<Integer>other).value)

    # def __truediv__(self, other: Any) -> Integer:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for /: %r and %r" % (Integer, type(other)))
    #     return Integer(<int>self.value / (<Integer>other).value)

    # def __mod__(self, other: Any) -> Integer:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Integer, type(other)))
    #     return Integer(<int>self.value % (<Integer>other).value)

    # def __lshift__(self, other: Any) -> Integer:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for <<: %r and %r" % (Integer, type(other)))
    #     return Integer(<int>self.value << (<Integer>other).value)

    # def __rshift__(self, other: Any) -> Integer:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for >>: %r and %r" % (Integer, type(other)))
    #     return Integer(<int>self.value >> (<Integer>other).value)

    # def __and__(self, other: Any) -> Integer:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for &: %r and %r" % (Integer, type(other)))
    #     return Integer(<int>self.value & (<Integer>other).value)

    # def __or__(self, other: Any) -> Integer:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for |: %r and %r" % (Integer, type(other)))
    #     return Integer(<int>self.value | (<Integer>other).value)

    # def __xor__(self, other) -> Integer:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for &: %r and %r" % (Integer, type(other)))
    #     return Integer(<int>self.value ^ (<Integer>other).value)

    # def __neg__(self) -> Integer:
    #     return Integer(-self.value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_i(self.value))


class Float(ConstantInfo):
    """
    A 32-bit float constant.
    """

    __slots__ = ()

    type = float_t
    tag = 4
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "Float":
        return cls(unpack_f(buffer.read(4))[0])

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to dereference float constant.")

    def __init__(self, value: float) -> None:
        """
        :param value: The floating point value of this constant.
        """

        super().__init__(value)

    # def __add__(self, other: Any) -> Float:
    #     if not isinstance(other, Float):
    #         raise TypeError("unsupported operand type(s) for +: %r and %r" % (Float, type(other)))
    #     return Float(<float>self.value + (<Float>other).value)

    # def __sub__(self, other: Any) -> Float:
    #     if not isinstance(other, Float):
    #         raise TypeError("unsupported operand type(s) for -: %r and %r" % (Float, type(other)))
    #     return Float(<float>self.value - (<Float>other).value)

    # def __mul__(self, other: Any) -> Float:
    #     if not isinstance(other, Float):
    #         raise TypeError("unsupported operand type(s) for *: %r and %r" % (Float, type(other)))
    #     return Float(<float>self.value * (<Float>other).value)

    # def __truediv__(self, other: Any) -> Float:
    #     if not isinstance(other, Float):
    #         raise TypeError("unsupported operand type(s) for /: %r and %r" % (Float, type(other)))
    #     return Float(<float>self.value / (<Float>other).value)

    # def __mod__(self, other: Any) -> Float:
    #     if not isinstance(other, Float):
    #         raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Float, type(other)))
    #     return Float(<float>self.value % (<Float>other).value)

    # def __neg__(self) -> Float:
    #     return Float(-self.value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_f(self.value))


class Long(ConstantInfo):
    """
    A 64-bit signed integer constant.
    """

    __slots__ = ()

    type = long_t
    tag = 5
    wide = True
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "Long":
        return cls(unpack_q(buffer.read(8))[0])

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to dereference long constant.")

    def __init__(self, value: int) -> None:
        """
        :param value: The integer value of this constant.
        """

        super().__init__(value)

    # def __add__(self, other: Any) -> Long:
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for +: %r and %r" % (Long, type(other)))
    #     return Long(<long long>self.value + (<Long>other).value)

    # def __sub__(self, other: Any) -> Long:
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for -: %r and %r" % (Long, type(other)))
    #     return Long(<long long>self.value - (<Long>other).value)

    # def __mul__(self, other: Any) -> Long:
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for *: %r and %r" % (Long, type(other)))
    #     return Long(<long long>self.value * (<Long>other).value)

    # def __truediv__(self, other: Any) -> Long:
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for /: %r and %r" % (Long, type(other)))
    #     return Long(<long long>self.value / (<Long>other).value)

    # def __mod__(self, other: Any) -> Long:
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Long, type(other)))
    #     return Long(<long long>self.value % (<Long>other).value)

    # def __lshift__(self, other: Any) -> Long:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for <<: %r and %r" % (Long, type(other)))
    #     return Long(<long long>self.value << (<Integer>other).value)

    # def __rshift__(self, other: Any) -> Long:
    #     if not isinstance(other, Integer):
    #         raise TypeError("unsupported operand type(s) for >>: %r and %r" % (Long, type(other)))
    #     return Long(<long long>self.value >> (<Integer>other).value)

    # def __and__(self, other: Any) -> Long:
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for &: %r and %r" % (Long, type(other)))
    #     return Long(<long long>self.value & (<Long>other).value)

    # def __or__(self, other: Any) -> Long:
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for |: %r and %r" % (Long, type(other)))
    #     return Long(<long long>self.value | (<Long>other).value)

    # def __xor__(self, other) -> Long:
    #     if not isinstance(other, Long):
    #         raise TypeError("unsupported operand type(s) for &: %r and %r" % (Long, type(other)))
    #     return Long(<long long>self.value ^ (<Long>other).value)

    # def __neg__(self) -> Long:
    #     return Long(-self.value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_q(self.value))


class Double(ConstantInfo):
    """
    A 64-bit float constant.
    """

    __slots__ = ()

    type = double_t
    tag = 6
    wide = True
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "Double":
        return cls(unpack_d(buffer.read(8))[0])

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to dereference double constant.")

    def __init__(self, value: float) -> None:
        """
        :param value: The floating point value of this constant.
        """

        super().__init__(value)

    # def __add__(self, other: Any) -> Double:
    #     if not isinstance(other, Double):
    #         raise TypeError("unsupported operand type(s) for +: %r and %r" % (Double, type(other)))
    #     return Double(<double>self.value + (<Double>other).value)

    # def __sub__(self, other: Any) -> Double:
    #     if not isinstance(other, Double):
    #         raise TypeError("unsupported operand type(s) for -: %r and %r" % (Double, type(other)))
    #     return Double(<double>self.value - (<Double>other).value)

    # def __mul__(self, other: Any) -> Double:
    #     if not isinstance(other, Double):
    #         raise TypeError("unsupported operand type(s) for *: %r and %r" % (Double, type(other)))
    #     return Double(<double>self.value * (<Double>other).value)

    # def __truediv__(self, other: Any) -> Double:
    #     if not isinstance(other, Double):
    #         raise TypeError("unsupported operand type(s) for /: %r and %r" % (Double, type(other)))
    #     return Double(<double>self.value / (<Double>other).value)

    # def __mod__(self, other: Any) -> Double:
    #     if not isinstance(other, Double):
    #         raise TypeError("unsupported operand type(s) for %%: %r and %r" % (Double, type(other)))
    #     return Double(<double>self.value % (<Double>other).value)

    # def __neg__(self) -> Double:
    #     return Double(-self.value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_d(self.value))


class Class(ConstantInfo):
    """
    A class constant.
    """

    __slots__ = ("name", "class_type")

    type = class_t
    tag = 7
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> int:
        return unpack_H(buffer.read(2))[0]

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: int) -> "Class":
        name = lookups.get(info)
        if type(name) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(name)))
        return cls(name.value)

    def __init__(self, name_or_type: str | Reference) -> None:
        """
        :param name_or_type: The name value of the class or a reference type.
        """

        if type(name_or_type) is str:
            self.name = name_or_type
            self.class_type = descriptor.parse_field_descriptor(name_or_type, force_read=True, reference_only=True)
        elif isinstance(name_or_type, Reference):
            if isinstance(name_or_type, ClassType):
                self.name = name_or_type.name
            else:
                self.name = descriptor.to_descriptor(name_or_type)
            self.class_type = name_or_type
        else:
            raise TypeError("Expected type %r or %r, got %r." % (str, Reference, type(name_or_type)))

        super().__init__(self.name)

    def __repr__(self) -> str:
        return "<Class(name=%r) at %x>" % (self.name, id(self))

    def __str__(self) -> str:
        return self.name

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add_utf8(self.name)))


class String(ConstantInfo):
    """
    A string constant.
    """

    __slots__ = ()

    type = string_t
    tag = 8
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> int:
        return unpack_H(buffer.read(2))[0]

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: int) -> "String":
        value = lookups.get(info)
        if type(value) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(value)))
        return cls(value.value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add_utf8(self.value)))


class FieldRef(ConstantInfo):
    """
    A reference to a field.
    """

    __slots__ = ("class_", "name", "descriptor", "field_type")

    tag = 9
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: tuple[int, int]) -> Optional["FieldRef"]:
        class_ = lookups.get(info[0])
        if class_ is None:
            return None
        elif type(class_) is not Class:
            raise TypeError("Expected type %r, got %r." % (Class, type(class_)))
        name_and_type: NameAndType | None = lookups.get(info[1])
        if name_and_type is None:
            return None
        elif type(name_and_type) is not NameAndType:
            raise TypeError("Expected type %r, got %r." % (NameAndType, type(name_and_type)))

        # Initialising the class like this is hacky, but it's faster than passing the values to the constructor as we
        # already know what types the arguments are.
        field_ref = cls.__new__(cls)

        field_ref.value = (class_, name_and_type.name, name_and_type.descriptor)
        field_ref._hash = hash(field_ref.value)

        field_ref.class_ = class_
        field_ref.name = name_and_type.name
        field_ref.descriptor = name_and_type.descriptor
        field_ref.field_type = descriptor.parse_field_descriptor(name_and_type.descriptor, do_raise=False)

        return field_ref

    def __init__(self, class_: "_argument.ClassConstant", name: str, descriptor_: "_argument.FieldDescriptor") -> None:
        """
        :param class_: The class that the field belongs to.
        :param name: The name of the field.
        :param descriptor_: The field type, if already parsed from the descriptor.
        """

        self.class_ = _argument.get_class_constant(class_)
        self.name = name
        self.field_type = _argument.get_field_descriptor(descriptor_)

        if type(descriptor_) is str:
            self.descriptor = descriptor_
        else:
            self.descriptor = descriptor.to_descriptor(self.field_type)

        super().__init__((self.class_, name, self.descriptor))

    def __repr__(self) -> str:
        return "<FieldRef(class=%s, name=%r, descriptor=%r) at %x>" % (
            self.class_.name, self.name, self.descriptor, id(self),
        )

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_HH(
            class_file.constant_pool.add(self.class_), 
            class_file.constant_pool.add(NameAndType(self.name, self.descriptor)),
        ))

    def __str__(self) -> str:
        return "%s.%s:%s" % (self.class_, self.name, self.descriptor)


class MethodRef(ConstantInfo):
    """
    A reference to a method.
    """

    __slots__ = ("class_", "name", "descriptor", "argument_types", "return_type")

    tag = 10
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: tuple[int, int]) -> Optional["MethodRef"]:
        class_ = lookups.get(info[0])
        if class_ is None:
            return None
        elif type(class_) is not Class:
            raise TypeError("Expected type %r, got %r." % (Class, type(class_)))
        name_and_type: NameAndType | None = lookups.get(info[1])
        if name_and_type is None:
            return None
        elif type(name_and_type) is not NameAndType:
            raise TypeError("Expected type %r, got %r." % (NameAndType, type(name_and_type)))

        method_ref = cls.__new__(cls)

        method_ref.value = (class_, name_and_type.name, name_and_type.descriptor)
        method_ref._hash = hash(method_ref.value)

        method_ref.class_ = class_
        method_ref.name = name_and_type.name
        method_ref.descriptor = name_and_type.descriptor

        type_ = descriptor.parse_method_descriptor(name_and_type.descriptor, do_raise=False)
        if type(type_) is tuple and len(type_) == 2:
            method_ref.argument_types, method_ref.return_type = type_
        else:
            method_ref.argument_types = (type_,)
            method_ref.return_type = type_

        return method_ref

    def __init__(self, class_: "_argument.ClassConstant", name: str, *descriptor_: "_argument.MethodDescriptor") -> None:
        """
        :param class_: The class that the method belongs to.
        :param name: The name of the method.
        :param descriptor_: The method descriptor.
        """

        self.class_ = _argument.get_class_constant(class_)
        self.name = name
        self.argument_types, self.return_type = _argument.get_method_descriptor(*descriptor_)

        if type(descriptor_) is str:
            self.descriptor = descriptor_
        else:
            self.descriptor = descriptor.to_descriptor(self.argument_types, self.return_type)

        super().__init__((self.class_, name, self.descriptor))

    def __repr__(self) -> str:
        return "<%s(class=%s, name=%r, descriptor=%r) at %x>" % (
            type(self).__name__, self.class_.name, self.name, self.descriptor, id(self),
        )

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_HH(
            class_file.constant_pool.add(self.class_),
            class_file.constant_pool.add(NameAndType(self.name, self.descriptor)),
        ))

    def __str__(self) -> str:
        return "%s.%s:%s" % (self.class_, self.name, self.descriptor)


class InterfaceMethodRef(MethodRef):
    """
    A reference to an interface method.
    """

    __slots__ = ()

    tag = 11
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: tuple[int, int]) -> Optional["InterfaceMethodRef"]:
        class_ = lookups.get(info[0])
        if class_ is None:
            return None
        elif type(class_) is not Class:
            raise TypeError("Expected type %r, got %r." % (Class, type(class_)))
        name_and_type: NameAndType | None = lookups.get(info[1])
        if name_and_type is None:
            return None
        elif type(name_and_type) is not NameAndType:
            raise TypeError("Expected type %r, got %r." % (NameAndType, type(name_and_type)))

        method_ref = cls.__new__(cls)

        method_ref.value = (class_, name_and_type.name, name_and_type.descriptor)
        method_ref._hash = hash(method_ref.value)

        method_ref.class_ = class_
        method_ref.name = name_and_type.name
        method_ref.descriptor = name_and_type.descriptor

        type_ = descriptor.parse_method_descriptor(name_and_type.descriptor, do_raise=False)
        if type(type_) is tuple and len(type_) == 2:
            method_ref.argument_types, method_ref.return_type = type_
        else:
            method_ref.argument_types = (type_,)
            method_ref.return_type = type_

        return method_ref


class NameAndType(ConstantInfo):
    """
    A name and type constant.
    """

    __slots__ = ("name", "descriptor")

    tag = 12
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: tuple[int, int]) -> "NameAndType":
        name = lookups.get(info[0])
        if type(name) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(name)))
        descriptor_ = lookups.get(info[1])
        if type(descriptor_) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(descriptor_)))
        return cls(name.value, descriptor_.value)

    def __init__(self, name: str, descriptor_: str) -> None:
        """
        :param name: The name.
        :param descriptor_: The type descriptor.
        """

        super().__init__((name, descriptor_))

        self.name = name
        self.descriptor = descriptor_

    def __repr__(self) -> str:
        return "<NameAndType(name=%r, descriptor=%s) at %x>" % (self.name, self.descriptor, id(self))

    def __str__(self) -> str:
        return "%s:%s" % (self.name, self.descriptor)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_HH(
            class_file.constant_pool.add_utf8(self.name), class_file.constant_pool.add_utf8(self.descriptor),
        ))


class MethodHandle(ConstantInfo):
    """
    A constant used to represent a method handle.
    """

    __slots__ = ("reference_kind", "reference")

    type = method_handle_t
    tag = 15
    since = Version(51, 0)

    REF_GET_FIELD          = 1
    REF_GET_STATIC         = 2
    REF_PUT_FIELD          = 3
    REF_PUT_STATIC         = 4
    REF_INVOKE_VIRTUAL     = 5
    REF_INVOKE_STATIC      = 6
    REF_INVOKE_SPECIAL     = 7
    REF_NEW_INVOKE_SPECIAL = 8
    REF_INVOKE_INTERFACE   = 9

    @classmethod
    def read(cls, buffer: IO[bytes]) -> tuple[int, int]:
        return unpack_BH(buffer.read(3))

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: tuple[int, int]) -> Optional["MethodHandle"]:
        reference: FieldRef | MethodRef | None = lookups.get(info[1])
        if reference is None:
            return None
        elif type(reference) is not FieldRef and not isinstance(reference, MethodRef):
            raise TypeError("Expected type %r or %r, got %r." % (FieldRef, MethodRef, type(reference)))
        return cls(info[0], reference)

    def __init__(self, reference_kind: int, reference: FieldRef | MethodRef | InterfaceMethodRef) -> None:
        """
        :param reference_kind: The type of reference.
        :param reference: The reference itself.
        """

        super().__init__((reference_kind, reference))

        self.reference_kind = reference_kind
        self.reference = reference

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_BH(self.reference_kind, class_file.constant_pool.add(self.reference)))


class MethodType(ConstantInfo):
    """
    A constant used to represent the descriptor of a method.
    """

    __slots__ = ("descriptor", "argument_types", "return_type")

    type = method_type_t
    tag = 16
    since = Version(51, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> int:
        return unpack_H(buffer.read(2))[0]

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: int) -> "MethodType":
        descriptor = lookups.get(info)
        if type(descriptor) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(descriptor)))
        return cls(descriptor.value)

    def __init__(self, *descriptor_: "_argument.MethodDescriptor") -> None:
        """
        :param descriptor_: The method descriptor.
        """

        self.argument_types, self.return_type = _argument.get_method_descriptor(*descriptor_)
        if type(descriptor_) is str:
            self.descriptor = descriptor_
        else:
            self.descriptor = descriptor.to_descriptor(self.argument_types, self.return_type)

        super().__init__(self.descriptor)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add_utf8(self.descriptor)))


class Dynamic(ConstantInfo):
    """
    Represents a dynamically computed constant.
    """

    __slots__ = ("bootstrap_method_attr_index", "name", "descriptor", "constant_type")

    tag = 17
    since = Version(55, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: tuple[int, int]) -> Optional["Dynamic"]:
        name_and_type: NameAndType | None = lookups.get(info[1])
        if name_and_type is None:  # Can't dereference it yet
            return None
        elif type(name_and_type) is not NameAndType:
            raise TypeError("Expected type %r, got %r." % (NameAndType, type(name_and_type)))

        dynamic = cls.__new__(cls)

        dynamic.value = (info[0], name_and_type.name, name_and_type.descriptor)
        dynamic._hash = hash(dynamic.value)

        dynamic.bootstrap_method_attr_index, _ = info
        dynamic.name = name_and_type.name
        dynamic.descriptor = name_and_type.descriptor
        dynamic.constant_type = descriptor.parse_field_descriptor(dynamic.descriptor, do_raise=False)

        return dynamic

    def __init__(self, bootstrap_method_attr_index: int, name: str, descriptor_: "_argument.FieldDescriptor") -> None:
        """
        :param bootstrap_method_attr_index: The corresponding index in the bootstrap methods attribute.
        """

        self.bootstrap_method_attr_index = bootstrap_method_attr_index
        self.name = name
        self.constant_type = _argument.get_field_descriptor(descriptor_)

        if type(descriptor_) is str:
            self.descriptor = descriptor_
        else:
            self.descriptor = descriptor.to_descriptor(self.type)

        super().__init__((bootstrap_method_attr_index, name, self.descriptor))

    def __repr__(self) -> str:
        return "<Dynamic(bootstrap_method_attr_index=%i, name=%r, descriptor=%s) at %x>" % (
            self.bootstrap_method_attr_index, self.name, self.descriptor, id(self),
        )

    def __str__(self) -> str:
        return "#%i:%s:%s" % (self.bootstrap_method_attr_index, self.name, self.descriptor)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_HH(
            self.bootstrap_method_attr_index,
            class_file.constant_pool.add(NameAndType(self.name, self.descriptor)),
        ))


class InvokeDynamic(ConstantInfo):
    """
    A constant used to reference an entity (field, method, interface method) dynamically.
    """

    __slots__ = ("bootstrap_method_attr_index", "name", "descriptor", "argument_types", "return_type")

    tag = 18
    since = Version(51, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: tuple[int, int]) -> Optional["InvokeDynamic"]:
        name_and_type: NameAndType | None = lookups.get(info[1])
        if name_and_type is None:  # Can't dereference it yet
            return None
        elif type(name_and_type) is not NameAndType:
            raise TypeError("Expected type %r, got %r." % (NameAndType, type(name_and_type)))

        invoke_dynamic = cls.__new__(cls)

        invoke_dynamic.value = (info[0], name_and_type.name, name_and_type.descriptor)
        invoke_dynamic._hash = hash(invoke_dynamic.value)

        invoke_dynamic.bootstrap_method_attr_index, _ = info
        invoke_dynamic.name = name_and_type.name
        invoke_dynamic.descriptor = name_and_type.descriptor

        type_ = descriptor.parse_method_descriptor(invoke_dynamic.descriptor, do_raise=False)
        if type(type_) is tuple and len(type_) == 2:
            invoke_dynamic.argument_types, invoke_dynamic.return_type = type_
        else:
            invoke_dynamic.argument_types = (type_,)
            invoke_dynamic.return_type = type_

        return invoke_dynamic

    def __init__(self, bootstrap_method_attr_index: int, name: str, *descriptor_: "_argument.MethodDescriptor") -> None:
        """
        :param bootstrap_method_attr_index: The corresponding index in the bootstrap methods attribute.
        """

        self.bootstrap_method_attr_index = bootstrap_method_attr_index
        self.name = name
        self.argument_types, self.return_type = _argument.get_method_descriptor(*descriptor_)

        if descriptor_ and type(descriptor_[0]) is str:
            self.descriptor, *_ = descriptor_
        else:
            self.descriptor = descriptor.to_descriptor(self.argument_types, self.return_type)

        super().__init__((bootstrap_method_attr_index, name, descriptor_))

    def __repr__(self) -> str:
        return "<InvokeDynamic(bootstrap_method_attr_index=%i, name=%r, descriptor=%s) at %x>" % (
            self.bootstrap_method_attr_index, self.name, self.descriptor, id(self),
        )

    def __str__(self) -> str:
        return "#%i:%s:%s" % (self.bootstrap_method_attr_index, self.name, self.descriptor)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_HH(
            self.bootstrap_method_attr_index,
            class_file.constant_pool.add(NameAndType(self.name, self.descriptor)),
        ))


class Module(ConstantInfo):
    """
    A constant that is used to represent a module.
    """

    __slots__ = ("name",)

    tag = 19
    since = Version(53, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> int:
        return unpack_H(buffer.read(2))[0]

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: int) -> "Module":
        name = lookups.get(info)
        if type(name) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(name)))
        return cls(name.value)

    def __init__(self, name: str) -> None:
        """
        :param name: The name of the module.
        """

        super().__init__(name)

        self.name = name

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add_utf8(self.name)))


class Package(ConstantInfo):
    """
    A constant that is used to represent a package exported or opened by a module.
    """

    __slots__ = ("name",)

    tag = 20
    since = Version(53, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> int:
        return unpack_H(buffer.read(2))[0]

    @classmethod
    def dereference(cls, lookups: dict[int, ConstantInfo], info: int) -> "Package":
        name = lookups.get(info)
        if type(name) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(name)))
        return cls(name.value)

    def __init__(self, name: str) -> None:
        """
        :param name: The name of the package.
        """

        super().__init__(name)

        self.name = name

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add_utf8(self.name)))


CONSTANTS = (
    UTF8,
    Integer,
    Float,
    Long,
    Double,
    Class,
    String,
    FieldRef,
    MethodRef,
    InterfaceMethodRef,
    NameAndType,
    MethodHandle,
    MethodType,
    Dynamic,
    InvokeDynamic,
    Module,
    Package,
)

_constant_map = {constant.tag: constant for constant in CONSTANTS}

from . import _argument

#!/usr/bin/env python3

import logging
import typing
from typing import Any, Callable, Dict, IO, List, Optional, Tuple, Type, Union

from ._struct import *
from ..abc.constant import Constant
from ..version import Version

if typing.TYPE_CHECKING:
    from . import ClassFile
    from ..types.primitive import IntegerType, LongType, FloatType, DoubleType

logger = logging.getLogger("kirjava.classfile.constants")


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
    def dereference(cls, lookups: Dict[int, "ConstantInfo"], info: Any) -> Optional["ConstantInfo"]:
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


class Index(ConstantInfo):
    """
    A special type of constant that represents an invalid index in the constant pool.
    """

    __slots__ = ("index",)

    @property
    def value(self) -> int:
        return self.index

    @classmethod
    def read(cls, buffer: IO[bytes]) -> None:
        raise Exception("Tried to read index type.")

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to dereference index type.")

    def __init__(self, index: int) -> None:
        """
        :param index: The constant pool index.
        """

        super().__init__(index)

        self.index = index

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
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
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to derefence UTF8 constant.")

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

    tag = 3
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "Integer":
        return cls(unpack_i(buffer.read(4))[0])

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to derefence integer constant.")

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

    def get_type(self) -> "IntegerType":
        return types.int_t


class Float(ConstantInfo):
    """
    A 32-bit float constant.
    """

    __slots__ = ()

    tag = 4
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "Float":
        return cls(unpack_f(buffer.read(4))[0])

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to derefence float constant.")

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

    def get_type(self) -> "FloatType":
        return types.float_t


class Long(ConstantInfo):
    """
    A 64-bit signed integer constant.
    """

    __slots__ = ()

    tag = 5
    wide = True
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "Long":
        return cls(unpack_q(buffer.read(8))[0])

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to derefence long constant.")

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

    def get_type(self) -> "LongType":
        return types.long_t


class Double(ConstantInfo):
    """
    A 64-bit float constant.
    """

    __slots__ = ()

    tag = 6
    wide = True
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "Double":
        return cls(unpack_d(buffer.read(8))[0])

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Any) -> None:
        raise Exception("Tried to derefence double constant.")

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

    def get_type(self) -> "DoubleType":
        return types.double_t


class Class(ConstantInfo):
    """
    A class constant.
    """

    __slots__ = ("name", "type")

    tag = 7
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> int:
        return unpack_H(buffer.read(2))[0]

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: int) -> "Class":
        name = lookups.get(info)
        if type(name) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(name)))
        return cls(name.value)

    def __init__(self, name: str) -> None:
        """
        :param name: The name value of the class.
        """

        super().__init__(name)

        self.name = name

        if name.startswith("["):  # Array type
            self.type = descriptor.parse_field_descriptor(name)
        else:
            self.type = ClassOrInterfaceType(name)

    def __repr__(self) -> str:
        return "<Class(name=%r) at %x>" % (self.name, id(self))

    def __str__(self) -> str:
        return self.name

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add_utf8(self.name)))

    def get_type(self) -> "ClassOrInterfaceType":
        return types.class_t


class String(ConstantInfo):
    """
    A string constant.
    """

    __slots__ = ()

    tag = 8
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> int:
        return unpack_H(buffer.read(2))[0]

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: int) -> "String":
        value = lookups.get(info)
        if type(value) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(value)))
        return cls(value.value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add_utf8(self.value)))

    def get_type(self) -> "ClassOrInterfaceType":
        return types.string_t


class FieldRef(ConstantInfo):
    """
    A reference to a field.
    """

    __slots__ = ("class_", "name_and_type")

    tag = 9
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Tuple[int, int]) -> Optional["FieldRef"]:
        class_ = lookups.get(info[0])
        if class_ is None:
            return None
        elif type(class_) is not Class:
            raise TypeError("Expected type %r, got %r." % (Class, type(class_)))
        name_and_type = lookups.get(info[1])
        if name_and_type is None:
            return None
        elif type(name_and_type) is not NameAndType:
            raise TypeError("Expected type %r, got %r." % (NameAndType, type(name_and_type)))
        return cls(class_, name_and_type)

    def __init__(self, class_: Class, name_and_type: "NameAndType") -> None:
        """
        :param class_: The class that the field belongs to.
        :param name_and_type: The name and type of the field.
        """

        super().__init__((class_, name_and_type))

        self.class_ = class_
        self.name_and_type = name_and_type

    def __repr__(self) -> str:
        return "<FieldRef(class=%s, name=%r, descriptor=%r) at %x>" % (
            self.class_.name, self.name_and_type.name, self.name_and_type.descriptor, id(self),
        )

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_HH(
            class_file.constant_pool.add(self.class_), class_file.constant_pool.add(self.name_and_type),
        ))

    def __str__(self) -> str:
        return "%s.%s" % (self.class_, self.name_and_type)


class MethodRef(ConstantInfo):
    """
    A reference to a method.
    """

    __slots__ = ("class_", "name_and_type")

    tag = 10
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Tuple[int, int]) -> Optional["MethodRef"]:
        class_ = lookups.get(info[0])
        if class_ is None:
            return None
        elif type(class_) is not Class:
            raise TypeError("Expected type %r, got %r." % (Class, type(class_)))
        name_and_type = lookups.get(info[1])
        if name_and_type is None:
            return None
        elif type(name_and_type) is not NameAndType:
            raise TypeError("Expected type %r, got %r." % (NameAndType, type(name_and_type)))
        return cls(class_, name_and_type)

    def __init__(self, class_: Class, name_and_type: "NameAndType") -> None:
        """
        :param class_: The class that the method belongs to.
        :param name_and_type: The name and type of the field.
        """

        super().__init__((class_, name_and_type))

        self.class_ = class_
        self.name_and_type = name_and_type

    def __repr__(self) -> str:
        return "<%s(class=%s, name=%r, descriptor=%r) at %x>" % (
            self.__class__.__name__, self.class_.name, self.name_and_type.name,
            self.name_and_type.descriptor, id(self),
        )

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_HH(
            class_file.constant_pool.add(self.class_), class_file.constant_pool.add(self.name_and_type),
        ))

    def __str__(self) -> str:
        return "%s.%s" % (self.class_, self.name_and_type)


class InterfaceMethodRef(MethodRef):
    """
    A reference to an interface method.
    """

    tag = 11
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Tuple[int, int]) -> Optional["InterfaceMethodRef"]:
        class_ = lookups.get(info[0])
        if class_ is None:
            return None
        elif type(class_) is not Class:
            raise TypeError("Expected type %r, got %r." % (Class, type(class_)))
        name_and_type = lookups.get(info[1])
        if name_and_type is None:
            return None
        elif type(name_and_type) is not NameAndType:
            raise TypeError("Expected type %r, got %r." % (NameAndType, type(name_and_type)))
        return cls(class_, name_and_type)


class NameAndType(ConstantInfo):
    """
    A name and type constant.
    """

    __slots__ = ("name", "descriptor")

    tag = 12
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Tuple[int, int]) -> "NameAndType":
        name = lookups.get(info[0])
        if type(name) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(name)))
        descriptor = lookups.get(info[1])
        if type(descriptor) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(descriptor)))
        return cls(name.value, descriptor.value)

    def __init__(self, name: str, descriptor_: str) -> None:
        """
        :param name: The name.
        :param descriptor_: The type descriptor.
        """

        super().__init__((name, descriptor_))

        self.name = name
        self.descriptor = descriptor_
        # TODO: Parse type descriptor

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

    tag = 15
    since = Version(51, 0)

    REF_GET_FIELD = 1
    REF_GET_STATIC = 2
    REF_PUT_FIELD = 3
    REF_PUT_STATIC = 4
    REF_INVOKE_VIRTUAL = 5
    REF_INVOKE_STATIC = 6
    REF_INVOKE_SPECIAL = 7
    REF_NEW_INVOKE_SPECIAL = 8
    REF_INVOKE_INTERFACE = 9

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Tuple[int, int]:
        return unpack_BH(buffer.read(3))

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Tuple[int, int]) -> Optional["MethodHandle"]:
        reference = lookups.get(info[1])
        if reference is None:
            return None
        elif type(reference) is not FieldRef and not isinstance(reference, MethodRef):
            raise TypeError("Expected type %r or %r, got %r." % (FieldRef, MethodRef, type(reference)))
        return cls(info[0], reference)

    def __init__(self, reference_kind: int, reference: Union[FieldRef, MethodRef, InterfaceMethodRef]) -> None:
        """
        :param reference_kind: The type of reference.
        :param reference: The reference itself.
        """

        super().__init__((reference_kind, reference))

        self.reference_kind = reference_kind
        self.reference = reference

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_BH(self.reference_kind, class_file.constant_pool.add(self.reference)))

    def get_type(self) -> "ClassOrInterfaceType":
        return ClassOrInterfaceType("java/lang/invoke/MethodHandle")


class MethodType(ConstantInfo):
    """
    A constant used to represent the descriptor of a method.
    """

    __slots__ = ("descriptor", "argument_types", "return_type")

    tag = 16
    since = Version(51, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> int:
        return unpack_H(buffer.read(2))[0]

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: int) -> "MethodType":
        descriptor = lookups.get(info)
        if type(descriptor) is not UTF8:
            raise TypeError("Expected type %r, got %r." % (UTF8, type(descriptor)))
        return cls(descriptor.value)

    def __init__(self, descriptor_: str) -> None:
        """
        :param descriptor_: The method descriptor.
        """

        super().__init__(descriptor_)

        self.descriptor = descriptor_
        self.argument_types, self.return_type = descriptor.parse_method_descriptor(descriptor_, do_raise=False)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add_utf8(self.descriptor)))

    def get_type(self) -> "ClassOrInterfaceType":
        return ClassOrInterfaceType("java/lang/invoke/MethodType")


class Dynamic(ConstantInfo):
    """
    Represents a dynamically computed constant.
    """

    __slots__ = ("bootstrap_method_attr_index", "name_and_type")

    tag = 17
    since = Version(55, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Tuple[int, int]) -> Optional["Dynamic"]:
        name_and_type = lookups.get(info[1])
        if name_and_type is None:  # Can't dereference it yet
            return None
        elif type(name_and_type) is not NameAndType:
            raise TypeError("Expected type %r, got %r." % (NameAndType, type(name_and_type)))
        return cls(info[0], name_and_type)

    def __init__(self, bootstrap_method_attr_index: int, name_and_type: NameAndType) -> None:
        """
        :param bootstrap_method_attr_index: The corresponding index in the bootstrap methods attribute.
        :param name_and_type: Not sure, need to revisit the spec to improve this documentation :p.
        """

        super().__init__((bootstrap_method_attr_index, name_and_type))

        self.bootstrap_method_attr_index = bootstrap_method_attr_index
        self.name_and_type = name_and_type

    def __repr__(self) -> str:
        return "<%s(bootstrap_method_attr_index=%i, name=%r, descriptor=%s) at %x>" % (
            self.__class__.__name__, self.bootstrap_method_attr_index, self.name_and_type.name,
            self.name_and_type.descriptor, id(self),
        )

    def __str__(self) -> str:
        return "#%i:%s" % (self.bootstrap_method_attr_index, self.name_and_type)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_HH(self.bootstrap_method_attr_index, class_file.constant_pool.add(self.name_and_type)))


class InvokeDynamic(Dynamic):
    """
    A constant used to reference an entity (field, method, interface method) dynamically.
    """

    __slots__ = ()

    tag = 18
    since = Version(51, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Tuple[int, int]:
        return unpack_HH(buffer.read(4))

    @classmethod
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: Tuple[int, int]) -> Optional["InvokeDynamic"]:
        name_and_type = lookups.get(info[1])
        if name_and_type is None:  # Can't dereference it yet
            return None
        elif type(name_and_type) is not NameAndType:
            raise TypeError("Expected type %r, got %r." % (NameAndType, type(name_and_type)))
        return cls(info[0], name_and_type)


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
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: int) -> "Module":
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
    def dereference(cls, lookups: Dict[int, ConstantInfo], info: int) -> "Package":
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


class ConstantPool:
    """
    The constant pool structure.
    """

    __slots__ = ("_index", "_forward_entries", "_backward_entries")

    @classmethod
    def read(cls, version: Version, buffer: IO[bytes]) -> "ConstantPool":
        """
        Reads a constant pool from a buffer.

        :param version: The version of the classfile.
        :param buffer: The binary buffer to read from.
        :return: The constant pool that was read.
        """

        constant_pool = cls()

        constants_count, = unpack_H(buffer.read(2))
        # logger.debug("Reading %i constant pool entries..." % (constants_count - 1))

        uncomputed = []  # Constants we haven't computed yet
        offset = 1  # The constant pool starts at offset 1

        while offset < constants_count:
            tag, = buffer.read(1)
            constant = _constant_map.get(tag)
            if constant is None:
                raise ValueError("Unknown constant tag: %i." % tag)
            if constant.since > version:
                raise ValueError("Constant %r is not supported in version %s." % (constant, version))

            info = constant.read(buffer)

            if isinstance(info, ConstantInfo):
                constant_pool._forward_entries[offset] = info
                constant_pool._backward_entries[info] = offset
            else:
                uncomputed.append((offset, constant, info))

            offset += 1
            if constant.wide:
                offset += 1

        constant_pool._index = offset

        # FIXME: Could cause an infinite loop, check for this
        while uncomputed:
            offset, constant, info = uncomputed.pop(0)
            value = constant.dereference(constant_pool._forward_entries, info)
            if value is None:
                uncomputed.append((offset, constant, info))
                continue

            constant_pool._forward_entries[offset] = value
            constant_pool._backward_entries[value] = offset

        return constant_pool

    @property
    def entries(self) -> Dict[int, ConstantInfo]:
        """
        :return: A dictionary containing the forward entries in the pool.
        """

        return self._forward_entries.copy()

    def __init__(self) -> None:
        self._index = 1

        self._forward_entries: Dict[int, ConstantInfo] = {}
        self._backward_entries: Dict[ConstantInfo, int] = {}

    def __repr__(self) -> str:
        return "<ConstantPool(size=%i) at %x>" % (len(self), id(self))

    def __len__(self) -> int:
        return len(self._forward_entries)

    def __contains__(self, item: Any) -> bool:
        if type(item) is int:
            return item in self._forward_entries
        elif isinstance(item, ConstantInfo):
            return item in self._backward_entries

        return False

    def __getitem__(self, item: Any) -> Union[ConstantInfo, int]:
        if type(item) is int:
            constant = self._forward_entries.get(item)
            if constant is not None:
                return constant
            return Index(item)

        elif isinstance(item, ConstantInfo):
            if type(item) is Index:
                return item.value
            return self._backward_entries[item]

        raise TypeError("Type %r is not a valid index for %r." % (type(item), self))

    def __setitem__(self, index: int, item: Any) -> None:
        if isinstance(item, ConstantInfo):
            if type(item) is Index:
                return  # Nothing to do here

            self._forward_entries[index] = item
            self._backward_entries[item] = index

            if index >= self._index:
                self._index = index + 1
                if item.wide:
                    self._index += 1

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Writes this constant pool to a buffer.

        :param class_file: The class file that this constant pool belongs to.
        :param buffer: The binary buffer to write to.
        """

        start = buffer.tell()
        buffer.write(b"\x00\x00")  # Placeholder bytes so we can seek back to them

        offset = 1
        while offset < self._index:
            constant = self._forward_entries[offset]
            buffer.write(bytes((constant.tag,)))
            constant.write(class_file, buffer)

            offset += 1
            if constant.wide:
                offset += 1

        # Now overwrite the old placeholder bytes with the max offset
        current = buffer.tell()

        buffer.seek(start)
        buffer.write(pack_H(offset))
        buffer.seek(current)

    # ------------------------------ Public API ------------------------------ #

    def get(self, index: int, default: Optional[ConstantInfo] = None, do_raise: bool = False) -> ConstantInfo:
        """
        Gets the constant at a given index.

        :param index: The index of the constant.
        :param default: The default value to get if the constant doesn't exist.
        :param do_raise: Raises an error if the index is invalid.
        :return: The constant at that index.
        """

        constant = self._forward_entries.get(index)
        if constant is not None:
            return constant
        if default is not None:
            return default

        if do_raise:
            raise IndexError("Constant pool index %i is not defined." % index)

        return Index(index)

    def get_utf8(self, index: int, default: Optional[str] = None, *, do_raise: bool = True) -> str:
        """
        Gets a UTF-8 value at the given index.

        :param index: The index of the constant.
        :param default: The value to default to if not found.
        :param do_raise: Should we raise an exception if the index is invalid?
        :return: The UTF-8 value of the constant.
        """

        constant = self._forward_entries.get(index)
        if constant is None:
            if not do_raise or default is not None:
                return default
            raise ValueError("Index %i not in constant pool." % index)
        elif type(constant) is not UTF8:
            if not do_raise or default is not None:
                return default
            raise TypeError("Index %i is not a valid UTF-8 constant." % index)

        return constant.value

    def clear(self) -> None:
        """
        Clears this constant pool.
        """

        self._index = 1
        self._forward_entries.clear()
        self._backward_entries.clear()

    def add(self, constant: Union[ConstantInfo, str]) -> int:
        """
        Adds a constant to this constant pool.

        :param constant: The constant to add, could also be a string (in this case it'll be added as a UTF8 constant).
        :return: The index of the added constant.
        """

        if type(constant) is str:
            constant = UTF8(constant)
        elif type(constant) is Index:
            return constant.value

        index = self._backward_entries.get(constant)
        if index is not None:
            return index

        self._forward_entries[self._index] = constant
        self._backward_entries[constant] = self._index

        index = self._index
        self._index += 1
        if constant.wide:
            self._index += 1

        return index

    def add_utf8(self, value: str) -> int:
        """
        Adds a UTF8 constant to this constant pool.

        :param value: The value of the UTF8 constant.
        :return: The index of the added constant.
        """

        return self.add(value)

    def add_class(self, name: str) -> int:
        """
        Adds a class constant to this constant pool.

        :param name: The name of the class.
        :return: The index of the added constant.
        """

        return self.add(Class(name))

    def add_string(self, value: str) -> int:
        """
        Adds a string constant to this constant pool.

        :param value: The value of the string constant.
        :return: The index of the added constant.
        """

        return self.add(String(value))


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


from . import descriptor
from .. import types
from ..types.reference import ArrayType, ClassOrInterfaceType

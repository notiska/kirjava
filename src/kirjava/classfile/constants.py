#!/usr/bin/env python3

import logging
import struct
import typing
from abc import abstractmethod, ABC
from typing import Any, Callable, Dict, IO, List, Union

from ..abc import Constant
from ..version import Version

if typing.TYPE_CHECKING:
    from . import ClassFile
    from ..types import BaseType
    from ..types.primitive import IntegerType, LongType, FloatType, DoubleType

logger = logging.getLogger("kirjava.classfile.constants")


class Constant(Constant, ABC):
    """
    Represents a value in the constant pool.
    """

    __slots__ = ("value",)

    tag = -1
    wide = False
    since = Version(45, 0)

    @classmethod
    @abstractmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], "Constant"]], "Constant"]:
        """
        Reads this constant type from the provided buffer.

        :param buffer: The binary data buffer.
        :return: A funtion that, when invoked, creates the constant.
        """

        ...

    @abstractmethod
    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Writes this constant type to the provided buffer.

        :param class_file: The class file that the constant belongs to.
        :param buffer: The binary data buffer.
        """

        ...

    def get_type(self) -> "BaseType":
        """
        :return: The type that this constant represents.
        """

        raise TypeError("Cannot convert %r into a Java type." % self)  # By default


class Index(Constant):
    """
    A special type of constant that represents an invalid index in the constant pool.
    """

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "Integer"]:
        ...

    def __init__(self, value: int) -> None:
        super().__init__(value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        ...


class UTF8(Constant):
    """
    An MUTF-8 constant.
    """

    tag = 1
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "UTF8"]:
        value = buffer.read(struct.unpack(">H", buffer.read(2))[0])
        constant = cls(value.replace(b"\xc0\x80", b"\x00").decode("utf-8", errors="ignore"))
        return lambda _: constant

    def __init__(self, value: str) -> None:
        super().__init__(value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        value = self.value.encode("utf-8").replace(b"\x00", b"\xc0\x80")
        buffer.write(struct.pack(">H", len(value)))
        buffer.write(value)


class Integer(Constant):
    """
    A 32-bit signed integer constant.
    """

    tag = 3
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "Integer"]:
        value, = struct.unpack(">i", buffer.read(4))
        constant = cls(value)
        return lambda _: constant

    def __init__(self, value: int) -> None:
        super().__init__(value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">i", self.value))

    def get_type(self) -> "IntegerType":
        return types.int_t


class Float(Constant):
    """
    A 32-bit float constant.
    """

    tag = 4
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "Float"]:
        value, = struct.unpack(">f", buffer.read(4))
        constant = cls(value)
        return lambda _: constant

    def __init__(self, value: float) -> None:
        super().__init__(value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">f", self.value))

    def get_type(self) -> "FloatType":
        return types.float_t


class Long(Constant):
    """
    A 64-bit signed integer constant.
    """

    tag = 5
    wide = True
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "Long"]:
        value, = struct.unpack(">q", buffer.read(8))
        constant = cls(value)
        return lambda _: constant

    def __init__(self, value: int) -> None:
        super().__init__(value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">q", self.value))

    def get_type(self) -> "LongType":
        return types.long_t


class Double(Constant):
    """
    A 64-bit float constant.
    """

    tag = 6
    wide = True
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "Double"]:
        value, = struct.unpack(">d", buffer.read(8))
        constant = cls(value)
        return lambda _: constant

    def __init__(self, value: float) -> None:
        super().__init__(value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">d", self.value))

    def get_type(self) -> "DoubleType":
        return types.double_t


class Class(Constant):
    """
    A class constant.
    """

    __slots__ = ("name",)

    tag = 7
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "Class"]:
        name_index, = struct.unpack(">H", buffer.read(2))
        return lambda dynamic_deref: cls(dynamic_deref(name_index).value)

    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.name = name

    def __repr__(self) -> str:
        return "<Class(name=%r) at %x>" % (self.name, id(self))

    def __str__(self) -> str:
        return self.name

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", class_file.constant_pool.add_utf8(self.name)))

    def get_type(self) -> "ClassOrInterfaceType":
        # Interesting bug here lol, this method was previously get_actual_type. I'm sure you can imagine what problems
        # that caused.
        return types.class_t

    def get_actual_type(self) -> Union["ArrayType", "ClassOrInterfaceType"]:
        if self.name.startswith("["):  # Array type, duh
            return descriptor.parse_field_descriptor(self.name)
        return ClassOrInterfaceType(self.name)


class String(Constant):
    """
    The string constant.
    """

    tag = 8
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "String"]:
        value_index, = struct.unpack(">H", buffer.read(2))
        return lambda dynamic_deref: cls(dynamic_deref(value_index).value)

    def __init__(self, value: str) -> None:
        super().__init__(value)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", class_file.constant_pool.add_utf8(self.value)))

    def get_type(self) -> "ClassOrInterfaceType":
        return ClassOrInterfaceType("java/lang/String")


class FieldRef(Constant):
    """
    A reference to a field.
    """

    __slots__ = ("class_", "name_and_type")

    tag = 9
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "FieldRef"]:
        class_index, name_and_type_index = struct.unpack(">HH", buffer.read(4))
        return lambda dynamic_deref: cls(dynamic_deref(class_index), dynamic_deref(name_and_type_index))

    def __init__(self, class_: Class, name_and_type: "NameAndType") -> None:
        super().__init__((class_, name_and_type))

        self.class_ = class_
        self.name_and_type = name_and_type

    def __repr__(self) -> str:
        return "<%s(class=%s, name=%r, descriptor=%r) at %x>" % (
            self.__class__.__name__, self.class_.name, self.name_and_type.name,
            self.name_and_type.descriptor, id(self),
        )

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(
            ">HH", class_file.constant_pool.add(self.class_), class_file.constant_pool.add(self.name_and_type),
        ))

    def __str__(self) -> str:
        return "%s.%s" % (self.class_, self.name_and_type)


class MethodRef(FieldRef):
    """
    A reference to a method.
    """

    tag = 10
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "MethodRef"]:
        class_index, name_and_type_index = struct.unpack(">HH", buffer.read(4))
        return lambda dynamic_deref: cls(dynamic_deref(class_index), dynamic_deref(name_and_type_index))


class InterfaceMethodRef(MethodRef):
    """
    A reference to an interface method.
    """

    tag = 11
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "InterfaceMethodRef"]:
        class_index, name_and_type_index = struct.unpack(">HH", buffer.read(4))
        return lambda dynamic_deref: cls(dynamic_deref(class_index), dynamic_deref(name_and_type_index))


class NameAndType(Constant):
    """
    A name and type constant.
    """

    __slots__ = ("name", "descriptor")

    tag = 12
    since = Version(45, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "NameAndType"]:
        name_index, descriptor_index = struct.unpack(">HH", buffer.read(4))
        return lambda dynamic_deref: cls(dynamic_deref(name_index).value, dynamic_deref(descriptor_index).value)

    def __init__(self, name: str, descriptor: str) -> None:
        super().__init__((name, descriptor))

        self.name = name
        self.descriptor = descriptor

    def __repr__(self) -> str:
        return "<NameAndType(name=%r, descriptor=%s) at %x>" % (self.name, self.descriptor, id(self))

    def __str__(self) -> str:
        return "%s:%s" % (self.name, self.descriptor)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(
            ">HH", class_file.constant_pool.add_utf8(self.name), class_file.constant_pool.add_utf8(self.descriptor),
        ))


class MethodHandle(Constant):
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
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "MethodHandle"]:
        reference_kind, reference_index = struct.unpack(">BH", buffer.read(3))
        return lambda dynamic_deref: cls(reference_kind, dynamic_deref(reference_index))

    def __init__(self, reference_kind: int, reference: Union[FieldRef, MethodRef, InterfaceMethodRef]) -> None:
        super().__init__((reference_kind, reference))

        self.reference_kind = reference_kind
        self.reference = reference

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">BH", self.reference_kind, class_file.constant_pool.add(self.reference)))

    def get_type(self) -> "ClassOrInterfaceType":
        return ClassOrInterfaceType("java/lang/invoke/MethodHandle")


class MethodType(Constant):
    """
    A constant used to represent the descriptor of a method.
    """

    __slots__ = ("descriptor",)

    tag = 16
    since = Version(51, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "MethodType"]:
        index, = struct.unpack(">H", buffer.read(2))
        return lambda dynamic_deref: cls(dynamic_deref(index).value)

    def __init__(self, descriptor: str) -> None:
        super().__init__(descriptor)

        self.descriptor = descriptor

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", class_file.constant_pool.add_utf8(self.descriptor)))

    def get_type(self) -> "ClassOrInterfaceType":
        return ClassOrInterfaceType("java/lang/invoke/MethodType")


class Dynamic(Constant):
    """
    Represents a dynamically computed constant.
    """

    __slots__ = ("bootstrap_method_attr_index", "name_and_type")

    tag = 17
    since = Version(55, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "Dynamic"]:
        bootstrap_method_attr_index, name_and_type_index = struct.unpack(">HH", buffer.read(4))
        return lambda dynamic_deref: cls(bootstrap_method_attr_index, dynamic_deref(name_and_type_index))

    def __init__(self, bootstrap_method_attr_index: int, name_and_type: NameAndType) -> None:
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
        buffer.write(struct.pack(">HH", self.bootstrap_method_attr_index, class_file.constant_pool.add(self.name_and_type)))


class InvokeDynamic(Dynamic):
    """
    A constant used to reference an entity (field, method, interface method) dynamically.
    """

    tag = 18
    since = Version(51, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "InvokeDynamic"]:
        bootstrap_method_attr_index, name_and_type_index = struct.unpack(">HH", buffer.read(4))
        return lambda dynamic_deref: cls(bootstrap_method_attr_index, dynamic_deref(name_and_type_index))


class Module(Constant):
    """
    A constant that is used to represent a module.
    """

    __slots__ = ("name",)

    tag = 19
    since = Version(53, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "Module"]:
        index, = struct.unpack(">H", buffer.read(2))
        return lambda dynamic_deref: cls(dynamic_deref(index).value)

    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.name = name

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", class_file.constant_pool.add_utf8(self.name)))


class Package(Constant):
    """
    A constant that is used to represent a package exported or opened by a module.
    """

    __slots__ = ("name",)

    tag = 20
    since = Version(53, 0)

    @classmethod
    def read(cls, buffer: IO[bytes]) -> Callable[[Callable[[int], Constant]], "Package"]:
        index, = struct.unpack(">H", buffer.read(2))
        return lambda dynamic_deref: cls(dynamic_deref(index).value)

    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.name = name

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", class_file.constant_pool.add_utf8(self.name)))


class ConstantPool:
    """
    The constant pool structure.
    """

    __slots__ = ("_index", "_forward_entries", "_backward_entries")

    @classmethod
    def read(cls, class_file: "ClassFile", buffer: IO[bytes]) -> "ConstantPool":
        """
        Reads a constant pool from a buffer.

        :param class_file: The class file that this constant pool belongs to.
        :param buffer: The binary buffer to read from.
        :return: The constant pool that was read.
        """

        constant_pool = cls()

        constants_count, = struct.unpack(">H", buffer.read(2))
        # logger.debug("Reading %i constant pool entries..." % (constants_count - 1))

        lookups = {}  # We'll store the lookups first
        def dynamic_deref(index: int, visited: List[int]) -> Constant:
            """
            Dynamic dereferencing initially for constants with recursion detection.
            """

            if index in visited:
                raise ValueError("Recursive constant at index %i." % index)
            visited.append(index)
            deref = lookups[index](lambda index_: dynamic_deref(index_, visited))
            visited.pop()
            return deref

        offset = 1  # The constant pool starts at offset 1
        while offset < constants_count:
            tag = buffer.read(1)[0]
            if not tag in _constant_map:
                raise ValueError("Unknown constant tag: %i." % tag)
            constant = _constant_map[tag]
            if constant.since > class_file.version:
                raise ValueError("Constant %r is not supported in version %s." % (constant, class_file.version))
            lookups[offset] = constant.read(buffer)
            offset += 1
            if constant.wide:
                offset += 1

        # logger.debug("Dereferencing %i constant pool entries..." % len(lookups))
        for index, lookup in lookups.items():
            constant_pool[index] = lookup(lambda index_: dynamic_deref(index_, []))

        return constant_pool

    def __init__(self) -> None:
        self._index = 1
        self._forward_entries: Dict[int, Constant] = {}
        self._backward_entries: Dict[Constant, int] = {}

    def __repr__(self) -> str:
        return "<ConstantPool() at %x>" % id(self)

    def __len__(self) -> int:
        return len(self._forward_entries)

    def __contains__(self, item: Any) -> bool:
        if item.__class__ is int:
            return item in self._forward_entries
        elif isinstance(item, Constant):
            return item in self._backward_entries

        return False

    def __getitem__(self, item: Any) -> Union[Constant, int]:
        if item.__class__ is int:
            constant = self._forward_entries.get(item, None)
            if constant is not None:
                return constant
            return Index(item)

        elif isinstance(item, Constant):
            if item.__class__ is Index:
                return item.value
            return self._backward_entries[item]

        raise TypeError("Type %r is not a valid index for %r." % (item.__class__, self))

    def __setitem__(self, index: int, item: Any) -> None:
        if isinstance(item, Constant):
            if item.__class__ is Index:
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
        buffer.write(struct.pack(">H", offset))
        buffer.seek(current)

    # ------------------------------ Accessing ------------------------------ #

    def get(self, index: int, default: Union[Constant, None] = None, do_raise: bool = False) -> Constant:
        """
        Gets the constant at a given index.

        :param index: The index of the constant.
        :param default: The default value to get if the constant doesn't exist.
        :param do_raise: Raises an error if the index is invalid.
        :return: The constant at that index.
        """

        constant = self._forward_entries.get(index, None)
        if constant is not None:
            return constant
        if default is not None:
            return default

        if do_raise:
            raise IndexError("Constant pool index %i is not defined." % index)

        return Index(index)

    def get_utf8(self, index: int, default: Union[str, None] = None) -> str:
        """
        Gets a UTF-8 value at the given index.

        :param index: The index of the constant.
        :param default: The value to default to if not found.
        :return: The UTF-8 value of the constant.
        """

        constant = self._forward_entries.get(index, None)
        if constant is None:
            if default is not None:
                return default
            raise ValueError("Index %i not in constant pool." % index)
        elif constant.__class__ is not UTF8:
            if default is not None:
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

    def add(self, constant: Union[Constant, str]) -> int:
        """
        Adds a constant to this constant pool.

        :param constant: The constant to add, could also be a string (in this case it'll be added as a UTF8 constant).
        :return: The index of the added constant.
        """

        if constant.__class__ is str:
            constant = UTF8(constant)
        elif constant.__class__ is Index:
            return constant.value

        index = self._backward_entries.get(constant, None)
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

#!/usr/bin/env python3

__all__ = (
    "attributes", "constants", "descriptor", "instructions", "members", "signature",
    "ClassFile", "FieldInfo", "MethodInfo",
)

"""
Java classfile parsing and manipulation.
"""

import logging
import struct
import time
import typing
from io import BytesIO
from typing import Dict, IO, List, Tuple, Union

from .. import _argument, types
from ..abc import Class as Class_
from ..environment import Environment
from ..types import BaseType, ReferenceType
from ..version import Version

if typing.TYPE_CHECKING:
    from .attributes import AttributeInfo

logger = logging.getLogger("kirjava.classfile")


class ClassFile(Class_):
    """
    Represents a Java class file.
    """

    __slots__ = (
        "version", "constant_pool", "access_flags",
        "_this", "_super", "_interfaces",
        "_fields", "_methods", "attributes",
    )

    @classmethod
    def read(cls, buffer: IO[bytes]) -> "ClassFile":
        """
        Reads a class file from the given buffer.

        :param buffer: The binary data buffer.
        :return: The class file that was read.
        """

        if buffer.read(4) != b"\xca\xfe\xba\xbe":
            raise IOError("Not a class file, invalid magic.")

        start = time.perf_counter_ns()

        class_file = cls.__new__(cls)

        minor, major = struct.unpack(">HH", buffer.read(4))
        class_file.version = Version(major, minor)

        class_file.constant_pool = ConstantPool.read(class_file, buffer)

        class_file.access_flags, this_class_index, super_class_index = struct.unpack(">HHH", buffer.read(6))
        class_file._this = class_file.constant_pool[this_class_index]
        class_file._super = None if super_class_index < 1 else class_file.constant_pool[super_class_index]

        interfaces_count, = struct.unpack(">H", buffer.read(2))
        class_file._interfaces = [
            class_file.constant_pool[struct.unpack(">H", buffer.read(2))[0]] for index in range(interfaces_count)
        ]

        fields_count, = struct.unpack(">H", buffer.read(2))
        class_file._fields = [FieldInfo.read(class_file, buffer) for index in range(fields_count)]

        methods_count, = struct.unpack(">H", buffer.read(2))
        class_file._methods = [MethodInfo.read(class_file, buffer) for index in range(methods_count)]

        class_file.attributes = {}
        attributes_count, = struct.unpack(">H", buffer.read(2))
        for index in range(attributes_count):
            attribute_info = attributes.read_attribute(class_file, class_file, buffer)
            if not attribute_info.name in class_file.attributes:
                class_file.attributes[attribute_info.name] = ()
            class_file.attributes[attribute_info.name] = class_file.attributes[attribute_info.name] + (attribute_info,)

        logger.debug("Read classfile %r in %.1fms." % (class_file.name, (time.perf_counter_ns() - start) / 1_000_000))

        return class_file

    ACC_PUBLIC = 0x0001
    ACC_FINAL = 0x0010
    ACC_SUPER = 0x0020
    ACC_INTERFACE = 0x0200
    ACC_ABSTRACT = 0x0400
    ACC_SYNTHETIC = 0x1000
    ACC_ANNOTATION = 0x2000
    ACC_ENUM = 0x4000
    ACC_MODULE = 0x8000

    @property
    def is_public(self) -> bool:
        return bool(self.access_flags & ClassFile.ACC_PUBLIC)

    @is_public.setter
    def is_public(self, value: bool) -> None:
        if value:
            self.access_flags |= ClassFile.ACC_PUBLIC
        else:
            self.access_flags &= ~ClassFile.ACC_PUBLIC

    @property
    def is_final(self) -> bool:
        return bool(self.access_flags & ClassFile.ACC_FINAL)

    @is_final.setter
    def is_final(self, value: bool) -> None:
        if value:
            self.access_flags |= ClassFile.ACC_FINAL
        else:
            self.access_flags &= ~ClassFile.ACC_FINAL

    @property
    def is_super(self) -> bool:
        return bool(self.access_flags & ClassFile.ACC_SUPER)

    @is_super.setter
    def is_super(self, value: bool) -> None:
        if value:
            self.access_flags |= ClassFile.ACC_SUPER
        else:
            self.access_flags &= ~ClassFile.ACC_SUPER

    @property
    def is_interface(self) -> bool:
        return bool(self.access_flags & ClassFile.ACC_INTERFACE)

    @is_interface.setter
    def is_interface(self, value: bool) -> None:
        if value:
            self.access_flags |= ClassFile.ACC_INTERFACE
        else:
            self.access_flags &= ~ClassFile.ACC_INTERFACE

    @property
    def is_abstract(self) -> bool:
        return bool(self.access_flags & ClassFile.ACC_ABSTRACT)

    @is_abstract.setter
    def is_abstract(self, value: bool) -> None:
        if value:
            self.access_flags |= ClassFile.ACC_ABSTRACT
        else:
            self.access_flags &= ~ClassFile.ACC_ABSTRACT

    @property
    def is_synthetic(self) -> bool:
        return bool(self.access_flags & ClassFile.ACC_SYNTHETIC)

    @is_synthetic.setter
    def is_synthetic(self, value: bool) -> None:
        if value:
            self.access_flags |= ClassFile.ACC_SYNTHETIC
        else:
            self.access_flags &= ~ClassFile.ACC_SYNTHETIC

    @property
    def is_annotation(self) -> bool:
        return bool(self.access_flags & ClassFile.ACC_ANNOTATION)

    @is_annotation.setter
    def is_annotation(self, value: bool) -> None:
        if value:
            self.access_flags |= ClassFile.ACC_ANNOTATION
        else:
            self.access_flags &= ~ClassFile.ACC_ANNOTATION

    @property
    def is_enum(self) -> bool:
        return bool(self.access_flags & ClassFile.ACC_ENUM)

    @is_enum.setter
    def is_enum(self, value: bool) -> None:
        if value:
            self.access_flags |= ClassFile.ACC_ENUM
        else:
            self.access_flags &= ~ClassFile.ACC_ENUM

    @property
    def is_module(self) -> bool:
        return bool(self.access_flags & ClassFile.ACC_MODULE)

    @is_module.setter
    def is_module(self, value: bool) -> None:
        if value:
            self.access_flags |= ClassFile.ACC_MODULE
        else:
            self.access_flags &= ~ClassFile.ACC_MODULE

    @property
    def name(self) -> str:
        return self._this.name

    @name.setter
    def name(self, value: str) -> None:
        self._this = Class(value)

    @property
    def super(self) -> Union[Class_, None]:
        if self._super is None:
            return None
        return Environment.find_class(self._super.name)

    @super.setter
    def super(self, value: Union[Class_, None]) -> None:
        if value is None:
            self._super = None
        else:
            self._super = Class(value.name)

    @property
    def super_name(self) -> Union[str, None]:
        return None if self._super is None else self._super.name

    @super_name.setter
    def super_name(self, value: Union[str, None]) -> None:
        if value is None:
            self._super = None
        else:
            self._super = Class(value)

    @property
    def interfaces(self) -> Tuple[Class_, ...]:
        return tuple(Environment.find_class(interface.name) for interface in self._interfaces)

    @interfaces.setter
    def interfaces(self, value: Tuple[Class_, ...]) -> None:
        self._interfaces.clear()
        self._interfaces.extend(Class(interface.name) for interface in value)

    @property
    def interface_names(self) -> Tuple[str, ...]:
        return tuple(interface.name for interface in self._interfaces)

    @interface_names.setter
    def interface_names(self, value: Tuple[str, ...]) -> None:
        self._interfaces.clear()
        self._interfaces.extend(Class(interface_name) for interface_name in value)

    @property
    def this(self) -> "Class":
        return self._this

    @property
    def methods(self) -> Tuple["MethodInfo", ...]:
        return tuple(self._methods)

    @methods.setter
    def methods(self, value: Tuple["MethodInfo", ...]) -> None:
        self._methods.clear()
        for method in value:
            method._class = self
            self._methods.append(method)

    @property
    def fields(self) -> Tuple["FieldInfo", ...]:
        return tuple(self._fields)

    @fields.setter
    def fields(self, value: Tuple["FieldInfo", ...]) -> None:
        self._fields.clear()
        for field in value:
            field._class = self
            self._fields.append(field)

    def __init__(
            self,
            name: str,
            super_: Union["Class", ReferenceType, Class_, str, None] = types.object_t,
            interfaces: Union[List[Union["Class", ReferenceType, Class_, str]], None] = None,
            version: Version = Version(52, 0),
            is_public: bool = False,
            is_final: bool = False,
            is_super: bool = False,
            is_interface: bool = False,
            is_abstract: bool = False,
            is_synthetic: bool = False,
            is_annotation: bool = False,
            is_enum: bool = False,
            is_module: bool = False,
    ) -> None:
        """
        :param name: The name of this class.
        :param super_: The superclass of this class.
        :param interfaces: A list of interfaces this class implements.
        """

        self._this = Class(name)
        if super_ is None:
            self._super = None
        else:
            self._super = _argument.get_class_constant(super_.name)

        self._interfaces = []
        if interfaces is not None:
            self._interfaces.extend([_argument.get_class_constant(interface.name) for interface in interfaces])

        self.access_flags = 0
        self.version = version

        self.is_public = is_public
        self.is_final = is_final
        self.is_super = is_super
        self.is_interface = is_interface
        self.is_abstract = is_abstract
        self.is_synthetic = is_synthetic
        self.is_annotation = is_annotation
        self.is_enum = is_enum
        self.is_module = is_module

        self.constant_pool: Union[ConstantPool, None] = None

        self._methods: List[MethodInfo] = []
        self._fields: List[FieldInfo] = []
        self.attributes: Dict[str, Tuple[AttributeInfo, ...]] = {}

    def __repr__(self) -> str:
        return "<ClassFile(name=%r) at %x>" % (self._this.name, id(self))

    # ------------------------------ Methods ------------------------------ #

    def get_method(
            self,
            name: str,
            *descriptor: Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]],
    ) -> "MethodInfo":
        """
        Gets a method in this class.

        :param name: The name of the method.
        :param descriptor: The descriptor of the method, if not given, the first method with the name is returned.
        :return: The method.
        """

        if descriptor:
            descriptor = _argument.get_method_descriptor(*descriptor)

        for method in self._methods:
            if method._name == name:
                if not descriptor:
                    return method
                if (method._argument_types, method._return_type) == descriptor:
                    return method

        if descriptor:
            raise LookupError("Method %r was not found." % (
                "%s#%s %s(%s)" % (self.name, descriptor[1], name, ", ".join(map(str, descriptor[0]))),
            ))
        raise LookupError("Method %r was not found." % ("%s#%s" % (self.name, name)))

    def add_method(
            self,
            name: str,
            *descriptor: Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]],
            **access_flags: Dict[str, bool],
    ) -> "MethodInfo":
        """
        Adds a method to this class given the provided information about it.

        :param name: The name of the method.
        :param descriptor: The descriptor of the method.
        :param access_flags: Any access flags for the method
        :return: The method that was created.
        """

        # It's added to self._methods for us in the MethodInfo constructor, so we can return it directly
        return MethodInfo(self, name, *descriptor, **access_flags)

    def remove_method(
            self,
            name_or_method: Union[str, "MethodInfo"],
            *descriptor: Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]],
    ) -> bool:
        """
        Removes a method from this class.

        :param name_or_method: The name of the method, or the method.
        :param descriptor: The descriptor of the method.
        :return: Was the method removed?
        """

        if not isinstance(name_or_method, MethodInfo):
            method = self.get_method(name_or_method, *descriptor)
        if not method in self._methods:
            raise ValueError("Method %r was not found, and therefore cannot be removed." % str(method))

        while method in self._methods:
            self._methods.remove(method)

    # ------------------------------ Fields ------------------------------ #

    def get_field(self, name: str, descriptor: Union[BaseType, str, None] = None) -> "FieldInfo":
        """
        Gets a field in this class.

        :param name: The name of the field.
        :param descriptor: The descriptor of the field, if None, the first field with the name is returned.
        :return: The field.
        """

        if descriptor is not None:
            descriptor = _argument.get_field_descriptor(descriptor)

        for field in self._fields:
            if field._name == name:
                if descriptor is None:
                    return field
                if field._type == descriptor:
                    return field

        if descriptor is not None:
            raise LookupError("Field %r was not found." % (
                "%s#%s %s" % (self.name, descriptor, name),
            ))
        raise LookupError("Field %r was not found." % ("%s#%s" % (self.name, name)))

    def add_field(
            self, name: str, descriptor: Union[BaseType, str, None] = None, **access_flags: Dict[str, bool],
    ) -> "FieldInfo":
        """
        Adds a field to this class.

        :param name: The name of the field to add.
        :param descriptor: The descriptor of the field to add.
        :param access_flags: Any access flags for the field.
        :return: The field that was added.
        """

        return FieldInfo(self, name, descriptor, **access_flags)

    def remove_field(self, name_or_field: Union[str, "FieldInfo"], descriptor: Union[BaseType, str, None] = None) -> bool:
        """
        Removes a field from this class.

        :param name_or_field: The name of the field or the field.
        :param descriptor: The descriptor of the field.
        :return: Was the field removed?
        """

        if not isinstance(name_or_field, FieldInfo):
            field = self.get_field(name_or_field, descriptor)
        if not field in self._fields:
            raise ValueError("Field %r was not found, and therefore cannot be removed." % str(field))

        while field in self._fields:  # May be duplicates (cos we allow that), so remove all
            self._fields.remove(field)

    # ------------------------------ IO ------------------------------ #

    def write(self, buffer: IO[bytes]) -> None:
        """
        Writes this class file to a buffer.

        :param buffer: The binary buffer to write to.
        """

        start = time.perf_counter_ns()

        buffer.write(b"\xca\xfe\xba\xbe")
        buffer.write(struct.pack(">HH", self.version.minor, self.version.major))

        if self.constant_pool is None:
            self.constant_pool = ConstantPool()
        # self.constant_pool.clear()

        data = BytesIO()
        data.write(struct.pack(
            ">HHH", self.access_flags, self.constant_pool.add(self._this), 
            0 if self._super is None else self.constant_pool.add(self._super),
        ))
        data.write(struct.pack(">H", len(self._interfaces)))
        for interface in self._interfaces:
            data.write(struct.pack(">H", self.constant_pool.add(interface)))

        data.write(struct.pack(">H", len(self._fields)))
        for field in self._fields:
            field.write(self, data)

        data.write(struct.pack(">H", len(self._methods)))
        for method in self._methods:
            method.write(self, data)

        data.write(struct.pack(">H", len(self.attributes)))
        for attribute, *_ in self.attributes.values():  # Only write the first attribute cos yeah
            attributes.write_attribute(attribute, self, data)

        self.constant_pool.write(self, buffer)
        buffer.write(data.getvalue())

        logger.debug("Wrote classfile %r in %.1fms." % (self.name, (time.perf_counter_ns() - start) / 1_000_000))


from . import attributes, constants, descriptor, instructions, members, signature
from .constants import Constant, ConstantPool, Class
from .members import FieldInfo, MethodInfo

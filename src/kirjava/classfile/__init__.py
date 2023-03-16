#!/usr/bin/env python3

__all__ = (
    "attributes", "constants", "descriptor", "members", "signature",
    "ClassFile", "FieldInfo", "MethodInfo",
)

"""
Java classfile parsing and manipulation.
"""

import logging
import time
import typing
from io import BytesIO
from typing import Dict, IO, Iterable, List, Optional, Tuple, Union

from ._struct import *
from .. import _argument, environment, types
from ..abc import Class as Class_
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
    def read(cls, buffer: IO[bytes], fail_fast: bool = True) -> "ClassFile":
        """
        Reads a class file from the given buffer.

        :param buffer: The binary data buffer.
        :param fail_fast: If the class is invalid, should we fail immediately?
        :return: The class file that was read.
        """

        if buffer.read(4) != b"\xca\xfe\xba\xbe":
            raise IOError("Not a class file, invalid magic.")

        start = time.perf_counter_ns()

        minor, major = unpack_HH(buffer.read(4))
        version = Version(major, minor)

        constant_pool = ConstantPool.read(version, buffer)

        access_flags, this_class_index, super_class_index = unpack_HHH(buffer.read(6))
        this = constant_pool.get(this_class_index, do_raise=fail_fast)
        super_ = None if super_class_index < 1 else constant_pool.get(super_class_index, do_raise=fail_fast)

        try:
            interfaces_count, = unpack_H(buffer.read(2))
        except Exception as error:
            if fail_fast:
                raise error
            interfaces_count = 0

        interfaces = [ 
            constant_pool.get(unpack_H(buffer.read(2))[0], do_raise=fail_fast) for index in range(interfaces_count)
        ]

        class_file = cls(this.name, super_, interfaces, version)
        class_file.access_flags = access_flags
        class_file.constant_pool = constant_pool

        try:
            fields_count, = unpack_H(buffer.read(2))
            for index in range(fields_count):
                FieldInfo.read(class_file, buffer, fail_fast)
        except Exception as error:
            if fail_fast:
                raise error

        try:
            methods_count, = unpack_H(buffer.read(2))
            for index in range(methods_count):
                MethodInfo.read(class_file, buffer, fail_fast)
        except Exception as error:
            if fail_fast:
                raise error

        try:
            attributes_count, = unpack_H(buffer.read(2))
            for index in range(attributes_count):
                attribute_info = attributes.read_attribute(class_file, class_file, buffer, fail_fast)
                class_file.attributes[attribute_info.name] = (
                    class_file.attributes.setdefault(attribute_info.name, ()) + (attribute_info,)
                )
        except Exception as error:
            if fail_fast:
                raise error

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
    def super(self) -> Optional[Class_]:
        if self._super is None:
            return None
        return environment.find_class(self._super.name)

    @super.setter
    def super(self, value: Optional[Class_]) -> None:
        if value is None:
            self._super = None
        else:
            self._super = Class(value.name)

    @property
    def super_name(self) -> Optional[str]:
        return None if self._super is None else self._super.name

    @super_name.setter
    def super_name(self, value: Optional[str]) -> None:
        if value is None:
            self._super = None
        else:
            self._super = Class(value)

    @property
    def interfaces(self) -> Tuple[Class_, ...]:
        return tuple(environment.find_class(interface.name) for interface in self._interfaces)

    @interfaces.setter
    def interfaces(self, value: Iterable[Class_]) -> None:
        self._interfaces.clear()
        self._interfaces.extend(Class(interface.name) for interface in value)

    @property
    def interface_names(self) -> Tuple[str, ...]:
        return tuple(interface.name for interface in self._interfaces)

    @interface_names.setter
    def interface_names(self, value: Iterable[str]) -> None:
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
            if method.class_ != self:
                raise ValueError("Method %r does not belong to this class." % method)
            self._methods.append(method)

    @property
    def fields(self) -> Tuple["FieldInfo", ...]:
        return tuple(self._fields)

    @fields.setter
    def fields(self, value: Tuple["FieldInfo", ...]) -> None:
        self._fields.clear()
        for field in value:
            if field.class_ != self:
                raise ValueError("Field %r does not belong to this class." % field)
            self._fields.append(field)

    def __init__(
            self,
            name: str,
            super_: "_argument.ClassConstant" = types.object_t,
            interfaces: Optional[List["_argument.ClassConstant"]] = None,
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

        super().__init__()

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

        self.constant_pool: Optional[ConstantPool] = None

        self._methods: List[MethodInfo] = []
        self._fields: List[FieldInfo] = []
        self.attributes: Dict[str, Tuple[AttributeInfo, ...]] = {}

    def __repr__(self) -> str:
        return "<ClassFile(name=%r) at %x>" % (self._this.name, id(self))

    # ------------------------------ Methods ------------------------------ #

    def get_method(self, name: str, *descriptor_: "_argument.MethodDescriptor") -> "MethodInfo":
        """
        Gets a method in this class.

        :param name: The name of the method.
        :param descriptor_: The descriptor of the method, if not given, the first method with the name is returned.
        :return: The method.
        """

        if descriptor_:
            descriptor_ = _argument.get_method_descriptor(*descriptor_)

        for method in self._methods:
            if method._name == name:
                if not descriptor_:
                    return method
                if (method._argument_types, method._return_type) == descriptor_:
                    return method

        if descriptor_:
            raise LookupError("Method %r was not found." % (
                "%s#%s %s(%s)" % (self.name, descriptor_[1], name, ", ".join(map(str, descriptor_[0]))),
            ))
        raise LookupError("Method %r was not found." % ("%s#%s" % (self.name, name)))

    def add_method(
            self, name: str, *descriptor_: "_argument.MethodDescriptor", **access_flags: bool,
    ) -> "MethodInfo":
        """
        Adds a method to this class given the provided information about it.

        :param name: The name of the method.
        :param descriptor_: The descriptor of the method.
        :param access_flags: Any access flags for the method
        :return: The method that was created.
        """

        # It's added to self._methods for us in the MethodInfo constructor, so we can return it directly
        return MethodInfo(self, name, *descriptor_, **access_flags)

    def remove_method(
            self, name_or_method: Union[str, "MethodInfo"], *descriptor_: "_argument.MethodDescriptor",
    ) -> "MethodInfo":
        """
        Removes a method from this class.

        :param name_or_method: The name of the method, or the method.
        :param descriptor_: The descriptor of the method.
        :return: Was the method removed?
        """

        if not isinstance(name_or_method, MethodInfo):
            name_or_method = self.get_method(name_or_method, *descriptor_)

        if not name_or_method in self._methods:
            raise ValueError("Method %r was not found, and therefore cannot be removed." % str(name_or_method))

        while name_or_method in self._methods:
            self._methods.remove(name_or_method)
        return name_or_method

    # ------------------------------ Fields ------------------------------ #

    def get_field(self, name: str, descriptor_: Optional["_argument.FieldDescriptor"] = None) -> "FieldInfo":
        """
        Gets a field in this class.

        :param name: The name of the field.
        :param descriptor_: The descriptor of the field, if None, the first field with the name is returned.
        :return: The field.
        """

        if descriptor_ is not None:
            descriptor_ = _argument.get_field_descriptor(descriptor_)

        for field in self._fields:
            if field._name == name:
                if descriptor_ is None:
                    return field
                if field._type == descriptor_:
                    return field

        if descriptor_ is not None:
            raise LookupError("Field %r was not found." % (
                "%s#%s %s" % (self.name, descriptor_, name),
            ))
        raise LookupError("Field %r was not found." % ("%s#%s" % (self.name, name)))

    def add_field(
            self, name: str, descriptor_: Optional["_argument.FieldDescriptor"] = None, **access_flags: bool,
    ) -> "FieldInfo":
        """
        Adds a field to this class.

        :param name: The name of the field to add.
        :param descriptor_: The descriptor of the field to add.
        :param access_flags: Any access flags for the field.
        :return: The field that was added.
        """

        return FieldInfo(self, name, descriptor_, **access_flags)

    def remove_field(
            self, name_or_field: Union[str, "FieldInfo"], descriptor_: Optional["_argument.FieldDescriptor"] = None,
    ) -> "FieldInfo":
        """
        Removes a field from this class.

        :param name_or_field: The name of the field or the field.
        :param descriptor_: The descriptor of the field.
        :return: Was the field removed?
        """

        if not isinstance(name_or_field, FieldInfo):
            name_or_field = self.get_field(name_or_field, descriptor_)
        if not name_or_field in self._fields:
            raise ValueError("Field %r was not found, and therefore cannot be removed." % str(name_or_field))

        while name_or_field in self._fields:  # May be duplicates (cos we allow that), so remove all
            self._fields.remove(name_or_field)
        return name_or_field

    # ------------------------------ IO ------------------------------ #

    def write(self, buffer: IO[bytes]) -> None:
        """
        Writes this class file to a buffer.

        :param buffer: The binary buffer to write to.
        """

        start = time.perf_counter_ns()

        buffer.write(b"\xca\xfe\xba\xbe")
        buffer.write(pack_HH(self.version.minor, self.version.major))

        if self.constant_pool is None:
            self.constant_pool = ConstantPool()
        # self.constant_pool.clear()

        data = BytesIO()
        data.write(pack_HHH(
            self.access_flags, self.constant_pool.add(self._this), 
            0 if self._super is None else self.constant_pool.add(self._super),
        ))
        data.write(pack_H(len(self._interfaces)))
        for interface in self._interfaces:
            data.write(pack_H(self.constant_pool.add(interface)))

        data.write(pack_H(len(self._fields)))
        for field in self._fields:
            field.write(self, data)

        data.write(pack_H(len(self._methods)))
        for method in self._methods:
            method.write(self, data)

        attributes_ = []
        for attributes__ in self.attributes.values():
            attributes_.extend(attributes__)

        data.write(pack_H(len(attributes_)))
        for attribute in attributes_:
            attributes.write_attribute(attribute, self, data)

        self.constant_pool.write(self, buffer)
        buffer.write(data.getvalue())

        logger.debug("Wrote classfile %r in %.1fms." % (self.name, (time.perf_counter_ns() - start) / 1_000_000))


from . import attributes, constants, descriptor, members, signature
from .constants import ConstantPool, Class
from .members import FieldInfo, MethodInfo  # Important that these are imported first, I <3 Python

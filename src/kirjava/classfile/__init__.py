#!/usr/bin/env python3

__all__ = (
    "attributes", "members",
    "ClassFile", "FieldInfo", "MethodInfo",
    "ConstantPool", "Index",
    "DirectoryProvider", "ZipProvider",
)

"""
Java classfile parsing and manipulation.
"""

import logging
import time
from io import BytesIO
from typing import IO, Iterable, Union

from ._constant import *
from .attributes import *
from .. import _argument, constants, environment, types
from .._struct import *
from ..abc import Class
from ..environment import Environment
from ..error import ClassFormatError
from ..version import Version

# if typing.TYPE_CHECKING:

logger = logging.getLogger("kirjava.classfile")


class ClassFile(Class):
    """
    Represents a Java class file.
    """

    __slots__ = (
        "version", "constant_pool", "access_flags",
        "_this", "_super", "_interfaces",
        "_fields", "_methods", "attributes",
    )

    @classmethod
    def read(cls, buffer: IO[bytes], *, fail_fast: bool = True, min_deref: bool = False) -> "ClassFile":
        """
        Reads a class file from the given buffer.

        :param buffer: The binary data buffer.
        :param fail_fast: If the classfile is obviously invalid, an exception will be raised ASAP.
        :param min_deref: Only dereference required constant pool entries?
        :return: The class file that was read.
        """

        if buffer.read(4) != b"\xca\xfe\xba\xbe":
            raise ClassFormatError("Malformed class file: invalid magic.")

        start = time.perf_counter_ns()

        minor, major = unpack_HH(buffer.read(4))
        version = Version(major, minor)

        constant_pool = ConstantPool.read(version, buffer)

        access_flags, this_class_index, super_class_index = unpack_HHH(buffer.read(6))
        this = constant_pool.get(this_class_index, do_raise=fail_fast)
        super_ = None if super_class_index < 1 else constant_pool.get(super_class_index, do_raise=fail_fast)

        try:
            interfaces_count, = unpack_H(buffer.read(2))
            interfaces = [ 
                constant_pool.get(unpack_H(buffer.read(2))[0], do_raise=fail_fast)
                for index in range(interfaces_count)
            ]
        except Exception as error:
            if fail_fast:
                raise error
            interfaces = []

        constant_pool.min_deref = min_deref  # this, super and interfaces are required

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

    ACC_PUBLIC     = 0x0001
    ACC_FINAL      = 0x0010
    ACC_SUPER      = 0x0020
    ACC_INTERFACE  = 0x0200
    ACC_ABSTRACT   = 0x0400
    ACC_SYNTHETIC  = 0x1000
    ACC_ANNOTATION = 0x2000
    ACC_ENUM       = 0x4000
    ACC_MODULE     = 0x8000

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
        self._this = constants.Class(value)

    @property
    def super(self) -> Class | None:
        if self._super is None:
            return None
        return self.environment.find_class(self._super.name)

    @super.setter
    def super(self, value: Class | None) -> None:
        if value is None:
            self._super = None
        else:
            self._super = constants.Class(value.name)

    @property
    def super_name(self) -> str | None:
        return None if self._super is None else self._super.name

    @super_name.setter
    def super_name(self, value: str | None) -> None:
        if value is None:
            self._super = None
        else:
            self._super = constants.Class(value)

    @property
    def interfaces(self) -> tuple[Class, ...]:
        return tuple(self.environment.find_class(interface.name) for interface in self._interfaces)

    @interfaces.setter
    def interfaces(self, value: Iterable[Class]) -> None:
        self._interfaces.clear()
        self._interfaces.extend(constants.Class(interface.name) for interface in value)

    @property
    def interface_names(self) -> tuple[str, ...]:
        return tuple(interface.name for interface in self._interfaces)

    @interface_names.setter
    def interface_names(self, value: Iterable[str]) -> None:
        self._interfaces.clear()
        self._interfaces.extend(constants.Class(interface_name) for interface_name in value)

    @property
    def this(self) -> constants.Class:
        return self._this

    @property
    def methods(self) -> tuple["MethodInfo", ...]:
        return tuple(self._methods)

    @methods.setter
    def methods(self, value: tuple["MethodInfo", ...]) -> None:
        self._methods.clear()
        for method in value:
            if method.class_ != self:
                raise ValueError("Method %r does not belong to this class." % method)
            self._methods.append(method)

    @property
    def fields(self) -> tuple["FieldInfo", ...]:
        return tuple(self._fields)

    @fields.setter
    def fields(self, value: tuple["FieldInfo", ...]) -> None:
        self._fields.clear()
        for field in value:
            if field.class_ != self:
                raise ValueError("Field %r does not belong to this class." % field)
            self._fields.append(field)

    @property
    def bootstrap_methods(self) -> BootstrapMethods | None:
        for attribute in self.attributes.get(BootstrapMethods.name_, ()):
            if type(attribute) is BootstrapMethods:
                return attribute
        return None

    @bootstrap_methods.setter
    def bootstrap_methods(self, value: BootstrapMethods | None) -> None:
        if value is None:
            self.attributes.pop(BootstrapMethods.name_, None)
        else:
            self.attributes[value.name] = (value,)

    @property
    def inner_classes(self) ->  InnerClasses | None:
        for attribute in self.attributes.get(InnerClasses.name_, ()):
            if type(attribute) is InnerClasses:
                return attribute
        return None

    @inner_classes.setter
    def inner_classes(self, value: InnerClasses | None) -> None:
        if value is None:
            self.attributes.pop(InnerClasses.name_, None)
        else:
            self.attributes[value.name] = (value,)

    @property
    def enclosing_method(self) -> EnclosingMethod | None:
        for attribute in self.attributes.get(EnclosingMethod.name_, ()):
            if type(attribute) is EnclosingMethod:
                return attribute
        return None

    @enclosing_method.setter
    def enclosing_method(self, value: EnclosingMethod | None) -> None:
        if value is None:
            self.attributes.pop(EnclosingMethod.name_, None)
        else:
            self.attributes[value.name] = (value,)

    @property
    def source_file(self) -> SourceFile | None:
        for attribute in self.attributes.get(SourceFile.name_, ()):
            if type(attribute) is SourceFile:
                return attribute
        return None

    @source_file.setter
    def source_file(self, value: SourceFile | None) -> None:
        if value is None:
            self.attributes.pop(SourceFile.name_, None)
        else:
            self.attributes[value.name] = (value,)

    @property
    def signature(self) -> Signature | None:
        for attribute in self.attributes.get(Signature.name_, ()):
            if type(attribute) is Signature:
                return attribute
        return None

    @signature.setter
    def signature(self, value: Signature | None) -> None:
        if value is None:
            self.attributes.pop(Signature.name_, None)
        else:
            self.attributes[value.name] = (value,)

    @property
    def runtime_visible_annotations(self) -> RuntimeVisibleAnnotations | None:
        for attribute in self.attributes.get(RuntimeVisibleAnnotations.name_, ()):
            if type(attribute) is RuntimeVisibleAnnotations:
                return attribute
        return None

    @runtime_visible_annotations.setter
    def runtime_visible_annotations(self, value: RuntimeVisibleAnnotations | None) -> None:
        if value is None:
            self.attributes.pop(RuntimeVisibleAnnotations.name_, None)
        else:
            self.attributes[value.name] = (value,)

    @property
    def runtime_invisible_annotations(self) -> RuntimeInvisibleAnnotations | None:
        for attribute in self.attributes.get(RuntimeInvisibleAnnotations.name_, ()):
            if type(attribute) is RuntimeInvisibleAnnotations:
                return attribute
        return None

    @runtime_invisible_annotations.setter
    def runtime_invisible_annotations(self, value: RuntimeInvisibleAnnotations | None) -> None:
        if value is None:
            self.attributes.pop(RuntimeInvisibleAnnotations.name_, None)
        else:
            self.attributes[value.name] = (value,)

    def __init__(
            self,
            name: str,
            super_: _argument.ClassConstant = types.object_t,
            interfaces: list[_argument.ClassConstant] | None = None,
            version: Version = Version(52, 0),
            environment: Environment | None = environment.DEFAULT,
            *,
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

        self._this = constants.Class(name)
        if super_ is None:
            self._super = None
        else:
            self._super = _argument.get_class_constant(super_.name)

        self._interfaces = []
        if interfaces is not None:
            self._interfaces.extend([_argument.get_class_constant(interface.name) for interface in interfaces])

        super().__init__(environment)

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

        self.constant_pool: ConstantPool | None = None

        self._methods: list[MethodInfo] = []
        self._fields: list[FieldInfo] = []
        self.attributes: dict[str, tuple[AttributeInfo, ...]] = {}

    def __repr__(self) -> str:
        return "<ClassFile(name=%r) at %x>" % (self._this.name, id(self))

    def get_method(self, name: str, *descriptor: _argument.MethodDescriptor) -> "MethodInfo":
        if descriptor:
            descriptor = _argument.get_method_descriptor(*descriptor)

        for method in self._methods:
            if method.name == name:
                if not descriptor:
                    return method
                if (method.argument_types, method.return_type) == descriptor:
                    return method

        if descriptor:
            raise LookupError("Method %r was not found." % (
                "%s#%s %s(%s)" % (self.name, descriptor[1], name, ", ".join(map(str, descriptor[0]))),
            ))
        raise LookupError("Method %r was not found." % ("%s#%s" % (self.name, name)))

    def has_method(self, name: str, *descriptor: _argument.MethodDescriptor) -> bool:
        try:
            self.get_method(name, *descriptor)  # I'm lazy.
        except LookupError:
            return False
        return True

    def add_method(
            self, name: str, *descriptor: _argument.MethodDescriptor, **access_flags: bool,
    ) -> "MethodInfo":
        # It's added to self._methods for us in the MethodInfo constructor, so we can return it directly
        return MethodInfo(self, name, *descriptor, **access_flags)

    def remove_method(
            self, name_or_method: Union[str, "MethodInfo"], *descriptor: _argument.MethodDescriptor,
    ) -> "MethodInfo":
        if not isinstance(name_or_method, MethodInfo):
            name_or_method = self.get_method(name_or_method, *descriptor)

        if not name_or_method in self._methods:
            raise ValueError("Method %r was not found, and therefore cannot be removed." % str(name_or_method))

        while name_or_method in self._methods:
            self._methods.remove(name_or_method)
        return name_or_method

    def get_field(self, name: str, descriptor: _argument.FieldDescriptor | None = None) -> "FieldInfo":
        if descriptor is not None:
            descriptor = _argument.get_field_descriptor(descriptor)

        for field in self._fields:
            if field.name == name:
                if descriptor is None:
                    return field
                if field.type == descriptor:
                    return field

        if descriptor is not None:
            raise LookupError("Field %r was not found." % (
                "%s#%s %s" % (self.name, descriptor, name),
            ))
        raise LookupError("Field %r was not found." % ("%s#%s" % (self.name, name)))

    def has_field(self, name: str, descriptor: _argument.FieldDescriptor | None = None) -> bool:
        try:
            self.get_field(name, descriptor)
        except LookupError:
            return False
        return True

    def add_field(
            self, name: str, descriptor: _argument.FieldDescriptor | None = None, **access_flags: bool,
    ) -> "FieldInfo":
        return FieldInfo(self, name, descriptor, **access_flags)

    def remove_field(
            self, name_or_field: Union[str, "FieldInfo"], descriptor: _argument.FieldDescriptor | None = None,
    ) -> "FieldInfo":
        if not isinstance(name_or_field, FieldInfo):
            name_or_field = self.get_field(name_or_field, descriptor)
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


from . import attributes, members
from ._provider import *
from .members import FieldInfo, MethodInfo

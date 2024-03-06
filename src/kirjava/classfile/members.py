#!/usr/bin/env python3

__all__ = (
    "FieldInfo", "MethodInfo",
)

import logging
import typing
from typing import IO

from . import attributes
from .attributes import *
from .. import _argument
from .._struct import *
from ..abc import Field, Method
from ..constants import FieldRef, InterfaceMethodRef, MethodRef
from ..types import descriptor

if typing.TYPE_CHECKING:
    from . import ClassFile
    from .attributes import AttributeInfo

logger = logging.getLogger("kirjava.classfile.members")


class FieldInfo(Field):
    """
    Represents a field in class.
    """

    __slots__ = ("_class", "name", "type", "access_flags", "attributes")

    @classmethod
    def read(cls, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> "FieldInfo":
        """
        Reads a field info from the buffer, given the class file it belongs too as well.

        :param class_file: The class file that the field belongs to.
        :param buffer: The binary buffer to read from.
        :param fail_fast: If the field is obviously invalid, should we just throw an exception?
        :return: The field info that was read.
        """

        access_flags, name_index, descriptor_index = unpack_HHH(buffer.read(6))
        name = class_file.constant_pool.get_utf8(name_index, do_raise=fail_fast)
        descriptor_ = class_file.constant_pool.get_utf8(descriptor_index, do_raise=fail_fast)

        try:
            type_ = descriptor.parse_field_descriptor(descriptor_)
        except Exception as error:
            type_ = descriptor.parse_field_descriptor(descriptor_, do_raise=fail_fast)

            # logger.warning("Invalid descriptor %r in class %r: %r" % (descriptor_, class_file.name, error.args[0]))
            logger.debug("Invalid descriptor on field %r." % ("%s#%s" % (class_file.name, name)), exc_info=True)

        field_info = cls(class_file, name, type_)
        field_info.access_flags = access_flags

        try:
            attributes_count, = unpack_H(buffer.read(2))
            for index in range(attributes_count):
                attribute_info = attributes.read_attribute(field_info, class_file, buffer, fail_fast)
                field_info.attributes[attribute_info.name] = (
                        field_info.attributes.setdefault(attribute_info.name, ()) + (attribute_info,)
                )
        except Exception as error:
            if fail_fast:
                raise error

        return field_info

    ACC_PUBLIC = 0x0001
    ACC_PRIVATE = 0x0002
    ACC_PROTECTED = 0x0004
    ACC_STATIC = 0x0008
    ACC_FINAL = 0x0010
    ACC_VOLATILE = 0x0040
    ACC_TRANSIENT = 0x0080
    ACC_SYNTHETIC = 0x1000
    ACC_ENUM = 0x4000

    @property
    def is_public(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_PUBLIC)

    @is_public.setter
    def is_public(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_PUBLIC
        else:
            self.access_flags &= ~FieldInfo.ACC_PUBLIC

    @property
    def is_private(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_PRIVATE)

    @is_private.setter
    def is_private(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_PRIVATE
        else:
            self.access_flags &= ~FieldInfo.ACC_PRIVATE

    @property
    def is_protected(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_PROTECTED)

    @is_protected.setter
    def is_protected(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_PROTECTED
        else:
            self.access_flags &= ~FieldInfo.ACC_PROTECTED

    @property
    def is_static(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_STATIC)

    @is_static.setter
    def is_static(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_STATIC
        else:
            self.access_flags &= ~FieldInfo.ACC_STATIC

    @property
    def is_final(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_FINAL)

    @is_final.setter
    def is_final(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_FINAL
        else:
            self.access_flags &= ~FieldInfo.ACC_FINAL

    @property
    def is_volatile(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_VOLATILE)

    @is_volatile.setter
    def is_volatile(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_VOLATILE
        else:
            self.access_flags &= ~FieldInfo.ACC_VOLATILE

    @property
    def is_transient(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_TRANSIENT)

    @is_transient.setter
    def is_transient(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_TRANSIENT
        else:
            self.access_flags &= ~FieldInfo.ACC_TRANSIENT

    @property
    def is_synthetic(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_SYNTHETIC)

    @is_synthetic.setter
    def is_synthetic(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_SYNTHETIC
        else:
            self.access_flags &= ~FieldInfo.ACC_SYNTHETIC

    @property
    def is_enum(self) -> bool:
        return bool(self.access_flags & FieldInfo.ACC_ENUM)

    @is_enum.setter
    def is_enum(self, value: bool) -> None:
        if value:
            self.access_flags |= FieldInfo.ACC_ENUM
        else:
            self.access_flags &= ~FieldInfo.ACC_ENUM

    @property
    def value(self) -> ConstantValue | None:
        """
        :return: The value in the ConstantValue attribute of this field, if it has one.
        """

        for attribute in self.attributes.get(ConstantValue.name_, ()):
            if isinstance(attribute, ConstantValue):
                return attribute
        return None

    @value.setter
    def value(self, value: ConstantValue | None) -> None:
        if value is None:
            self.attributes.pop(ConstantValue.name_, None)
        else:
            self.attributes[ConstantValue.name_] = (value,)

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
            class_: "ClassFile",
            name: str,
            type_: _argument.FieldDescriptor,
            *,
            is_public: bool = False,
            is_private: bool = False,
            is_protected: bool = False,
            is_static: bool = False,
            is_final: bool = False,
            is_volatile: bool = False,
            is_transient: bool = False,
            is_synthetic: bool = False,
            is_enum: bool = False,
    ) -> None:
        """
        :param class_: The class that this field belongs to.
        :param name: The name of this field.
        :param type_: The type of this field.
        """

        super().__init__(class_)

        self.name = name
        self.type = _argument.get_field_descriptor(type_)

        if class_ is not None and not self in class_._fields:
            class_._fields.append(self)

        self.access_flags = 0

        self.is_public = is_public
        self.is_private = is_private
        self.is_protected = is_protected
        self.is_static = is_static
        self.is_final = is_final
        self.is_volatile = is_volatile
        self.is_transient = is_transient
        self.is_synthetic = is_synthetic
        self.is_enum = is_enum

        self.attributes: dict[str, tuple[AttributeInfo, ...]] = {}

    def __repr__(self) -> str:
        return "<FieldInfo(name=%r, type=%s) at %x>" % (self.name, self.type, id(self))

    def __str__(self) -> str:
        if self.class_ is None:
            return "%s %s" % (self.type, self.name)
        return "%s#%s %s" % (self.class_.name, self.type, self.name)

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Writes this field info to the buffer.

        :param class_file: The class file to write this field to.
        :param buffer: The binary buffer to write to.
        """

        if self.class_ is None:
            self.class_ = class_file

        buffer.write(pack_HHH(
            self.access_flags,
            class_file.constant_pool.add_utf8(self.name),
            class_file.constant_pool.add_utf8(descriptor.to_descriptor(self.type)),
        ))

        attributes_ = []
        for attributes__ in self.attributes.values():
            attributes_.extend(attributes__)

        buffer.write(pack_H(len(attributes_)))
        for attribute in attributes_:
            attributes.write_attribute(attribute, class_file, buffer)

    def get_reference(self) -> FieldRef:
        """
        :return: A reference to this field that can be used in instructions.
        """

        return FieldRef(self.class_, self.name, self.type)

    def get_ref(self) -> FieldRef:
        """
        :return: A reference to this field that can be used in instructions.
        """

        return FieldRef(self.class_, self.name, self.type)


class MethodInfo(Method):
    """
    Represents a method in a class.
    """

    __slots__ = ("name", "argument_types", "return_type", "access_flags", "attributes")

    @classmethod
    def read(cls, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> "MethodInfo":
        """
        Reads a method info from the buffer.

        :param class_file: The class file that the method belongs to.
        :param buffer: The binary buffer to read from.
        :param fail_fast: If the method is obviously invalid, should we just throw an exception?
        :return: The method info that was read.
        """

        access_flags, name_index, descriptor_index = unpack_HHH(buffer.read(6))
        name = class_file.constant_pool.get_utf8(name_index, do_raise=fail_fast)
        descriptor_ = class_file.constant_pool.get_utf8(descriptor_index, do_raise=fail_fast)

        try:
            type_ = descriptor.parse_method_descriptor(descriptor_)
            argument_types, return_type = type_

        except Exception as error:
            type_ = descriptor.parse_method_descriptor(descriptor_, do_raise=fail_fast)

            if type(type_) is not tuple or len(type_) != 2:
                argument_types = (type_,)
                return_type = type_
            else:
                argument_types, return_type = type_

            # TODO: Proper warnings
            # logger.warning("Invalid descriptor %r in class %r: %r" % (descriptor_, class_file.name, error))
            logger.debug("Invalid descriptor on method %r." % ("%s#%s" % (class_file.name, name)), exc_info=True)

        method_info = cls(class_file, name, argument_types, return_type)
        method_info.access_flags = access_flags

        try:
            attributes_count, = unpack_H(buffer.read(2))
            for index in range(attributes_count):
                attribute_info = attributes.read_attribute(method_info, class_file, buffer, fail_fast)
                method_info.attributes[attribute_info.name] = (
                    method_info.attributes.setdefault(attribute_info.name, ()) + (attribute_info,)
                )
        except Exception as error:
            if fail_fast:
                raise error

        return method_info

    ACC_PUBLIC = 0x0001
    ACC_PRIVATE = 0x0002
    ACC_PROTECTED = 0x0004
    ACC_STATIC = 0x0008
    ACC_FINAL = 0x0010
    ACC_SYNCHRONIZED = 0x0020
    ACC_BRIDGE = 0x0040
    ACC_VARARGS = 0x0080
    ACC_NATIVE = 0x0100
    ACC_ABSTRACT = 0x0400
    ACC_STRICT = 0x0800
    ACC_SYNTHETIC = 0x1000

    @property
    def is_public(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_PUBLIC)

    @is_public.setter
    def is_public(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_PUBLIC
        else:
            self.access_flags &= ~MethodInfo.ACC_PUBLIC

    @property
    def is_private(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_PRIVATE)

    @is_private.setter
    def is_private(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_PRIVATE
        else:
            self.access_flags &= ~MethodInfo.ACC_PRIVATE

    @property
    def is_protected(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_PROTECTED)

    @is_protected.setter
    def is_protected(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_PROTECTED
        else:
            self.access_flags &= ~MethodInfo.ACC_PROTECTED

    @property
    def is_static(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_STATIC)

    @is_static.setter
    def is_static(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_STATIC
        else:
            self.access_flags &= ~MethodInfo.ACC_STATIC

    @property
    def is_final(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_FINAL)

    @is_final.setter
    def is_final(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_FINAL
        else:
            self.access_flags &= ~MethodInfo.ACC_FINAL

    @property
    def is_synchronized(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_SYNCHRONIZED)

    @is_synchronized.setter
    def is_synchronized(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_SYNCHRONIZED
        else:
            self.access_flags &= ~MethodInfo.ACC_SYNCHRONIZED

    @property
    def is_bridge(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_BRIDGE)

    @is_bridge.setter
    def is_bridge(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_BRIDGE
        else:
            self.access_flags &= ~MethodInfo.ACC_BRIDGE

    @property
    def is_varargs(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_VARARGS)

    @is_varargs.setter
    def is_varargs(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_VARARGS
        else:
            self.access_flags &= ~MethodInfo.ACC_VARARGS

    @property
    def is_native(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_NATIVE)

    @is_native.setter
    def is_native(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_NATIVE
        else:
            self.access_flags &= ~MethodInfo.ACC_NATIVE

    @property
    def is_abstract(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_ABSTRACT)

    @is_abstract.setter
    def is_abstract(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_ABSTRACT
        else:
            self.access_flags &= ~MethodInfo.ACC_ABSTRACT

    @property
    def is_strict(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_STRICT)

    @is_strict.setter
    def is_strict(self, value: bool) -> None:
        if value:
            self.access_flags |= MethodInfo.ACC_STRICT
        else:
            self.access_flags &= ~MethodInfo.ACC_STRICT

    @property
    def is_synthetic(self) -> bool:
        return bool(self.access_flags & MethodInfo.ACC_SYNTHETIC)

    @is_synthetic.setter
    def is_synthetic(self, value: bool) -> None:
        if value: 
            self.access_flags |= MethodInfo.ACC_SYNTHETIC
        else:
            self.access_flags &= ~MethodInfo.ACC_SYNTHETIC

    @property
    def code(self) -> Code | None:
        for attribute in self.attributes.get(Code.name_, ()):
            if type(attribute) is Code:  # Find the first valid Code attribute.
                return attribute
        return None

    @code.setter
    def code(self, value: Code | None) -> None:
        if value is None:
            self.attributes.pop(Code.name_, None)
        else:
            self.attributes[value.name] = (value,)

    @property
    def exceptions(self) -> Exceptions | None:
        for attribute in self.attributes.get(Exceptions.name_, ()):
            if type(attribute) is Exceptions:
                return attribute
        return None

    @exceptions.setter
    def exceptions(self, value: Exceptions | None) -> None:
        if value is None:
            self.attributes.pop(Exceptions.name_, None)
        else:
            self.attributes[value.name] = value

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
            class_: "ClassFile",
            name: str,
            *descriptor_: _argument.MethodDescriptor,
            is_public: bool = False,
            is_private: bool = False,
            is_protected: bool = False,
            is_static: bool = False,
            is_final: bool = False,
            is_synchronized: bool = False,
            is_bridge: bool = False,
            is_varargs: bool = False,
            is_native: bool = False,
            is_abstract: bool = False,
            is_strict: bool = False,
            is_synthetic: bool = False,
    ) -> None:
        """
        :param class_: The classfile that this method belongs to.
        :param name: The name of the method.
        :param argument_types: The argument types of this method.
        :param return_type: The return type of this method.
        """

        super().__init__(class_)

        self.name = name
        self.argument_types, self.return_type = _argument.get_method_descriptor(*descriptor_)

        if class_ is not None and not self in class_._methods:
            class_._methods.append(self)

        self.access_flags = 0

        self.is_public = is_public
        self.is_private = is_private
        self.is_protected = is_protected
        self.is_static = is_static
        self.is_final = is_final
        self.is_synchronized = is_synchronized
        self.is_bridge = is_bridge
        self.is_varargs = is_varargs
        self.is_native = is_native
        self.is_abstract = is_abstract
        self.is_strict = is_strict
        self.is_synthetic = is_synthetic

        self.attributes: dict[str, tuple[AttributeInfo, ...]] = {}

    def __repr__(self) -> str:
        return "<MethodInfo(name=%r, argument_types=(%s), return_type=%s) at %x>" % (
            self.name,
            # More Pythonic looking to add a comma to the end
            ", ".join(map(str, self.argument_types)) + ("," if len(self.argument_types) == 1 else ""),
            self.return_type, id(self),
        )

    def __str__(self) -> str:
        if self.class_ is None:
            return "%s %s(%s)" % (self.return_type, self.name, ", ".join(map(str, self.argument_types)))
        return "%s#%s %s(%s)" % (
            self.class_.name, self.return_type, self.name, ", ".join(map(str, self.argument_types)),
        )

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        """
        Writes this method to the buffer.

        :param class_file: The class file that this method belongs to.
        :param buffer: The binary buffer to write to.
        """

        buffer.write(pack_HHH(
            self.access_flags,
            class_file.constant_pool.add_utf8(self.name),
            class_file.constant_pool.add_utf8(descriptor.to_descriptor(self.argument_types, self.return_type)),
        ))

        attributes_ = []
        for attributes__ in self.attributes.values():
            attributes_.extend(attributes__)

        buffer.write(pack_H(len(attributes_)))
        for attribute in attributes_:
            attributes.write_attribute(attribute, class_file, buffer)

    def get_reference(self) -> MethodRef | InterfaceMethodRef:
        """
        :return: A reference to this method that can be used in instructions.
        """

        if self.class_.is_interface:
            return InterfaceMethodRef(self.class_, self.name, self.argument_types, self.return_type)
        return MethodRef(self.class_, self.name, self.argument_types, self.return_type)

    def get_ref(self) -> MethodRef | InterfaceMethodRef:
        """
        :return: A reference to this method that can be used in instructions.
        """

        if self.class_.is_interface:
            return InterfaceMethodRef(self.class_, self.name, self.argument_types, self.return_type)
        return MethodRef(self.class_, self.name, self.argument_types, self.return_type)

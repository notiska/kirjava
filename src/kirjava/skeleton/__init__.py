#!/usr/bin/env python3

__all__ = (
    "load_skeletons",
)

"""
Java class skeletons in case we haven't loaded any Java libraries (rt.jar specifically).
"""

import json
import logging
import os
from typing import Dict, List, Tuple, Union

from .. import _argument
from ..abc import Class, Field, Method
from ..classfile import descriptor
from ..environment import Environment
from ..types import BaseType
from ..version import Version

logger = logging.getLogger("kirjava.skeleton")


def load_skeletons(version: Version = Version.get("11")) -> None:
    """
    Loads the skeleton classes for a given version, by default, Java 11.

    :param version: The Java version to load the skeleton classes for.
    """

    logger.debug("Loading skeletons for version %r..." % version.name)

    skeletons_dir = os.path.join(os.path.dirname(__file__), "skeletons")
    for file in os.listdir(skeletons_dir):
        if file.endswith(".json"):
            with open(os.path.join(skeletons_dir, file), "r") as stream:
                data = json.load(stream)
                if data["version"] == version:
                    break
    else:
        raise ValueError("Skeletons for version %r not found." % version)

    classes = {}

    for class_name, (class_access_flags, _, _, fields, methods) in data["classes"].items():
        classes[class_name] = _SkeletonClass(
            class_name, None, (),  # We'll need to fill in the super and interfaces later
            tuple(
                _SkeletonMethod(
                    method_name.split(":", 1)[0],
                    *descriptor.parse_method_descriptor(method_name.split(":", 1)[1]),
                    **{("is_%s" % flag): True for flag in method_access_flags}
                )
                for method_name, (method_access_flags,) in methods.items()
            ),
            tuple(
                _SkeletonField(
                    field_name.split(":", 1)[0],
                    descriptor.parse_field_descriptor(field_name.split(":", 1)[1]),
                    **{("is_%s" % flag): True for flag in field_access_flags},
                )
                for field_name, (field_access_flags,) in fields.items()
            ),
            **{("is_%s" % flag): True for flag in class_access_flags},
        )

    skipped = 0
    for class_name, (_, super_name, interface_names, _, _) in data["classes"].items():
        try:
            class_ = classes[class_name]
            if super_name is not None:
                class_._super = classes[super_name]
            class_._interfaces = tuple(classes[interface_name] for interface_name in interface_names)
        except KeyError:
            # logger.debug(" - Skipping class %r due to unresolved names." % class_name)
            skipped += 1
            del classes[class_name]
    if skipped:
        logger.debug(" - Skipped %i class(es) due to unresolved names." % skipped)

    Environment.register_classes(*classes.values())

    logger.debug("Found %i skeleton class(es)." % len(classes))


class _SkeletonClass(Class):
    """
    A fake Java class.
    """

    __slots__ = (
        "_is_public", "_is_final", "_is_super", "_is_abstract", 
        "_is_synthetic", "_is_annotation", "_is_enum", "_is_module"
        "_name", "_super", "_interfaces",
        "_methods", "_fields",
    )

    @property
    def is_public(self) -> bool:
        return self._is_public

    @property
    def is_final(self) -> bool:
        return self._is_final

    @property
    def is_super(self) -> bool:
        return self._is_super

    @property
    def is_interface(self) -> bool:
        return self._is_interface

    @property
    def is_abstract(self) -> bool:
        return self._is_abstract

    @property
    def is_synthetic(self) -> bool:
        return self._is_synthetic

    @property
    def is_annotation(self) -> bool:
        return self._is_annotation

    @property
    def is_enum(self) -> bool:
        return self._is_enum

    @property
    def is_module(self) -> bool:
        return self._is_module

    @property
    def name(self) -> str:
        return self._name

    @property
    def super(self) -> Union["_SkeletonClass", None]:
        return self._super

    @property
    def super_name(self) -> Union[str, None]:
        if self._super is None:
            return None
        return self._super.name

    @property
    def interfaces(self) -> Tuple["_SkeletonClass", ...]:
        return self._interfaces

    @property
    def interface_names(self) -> Tuple[str, ...]:
        return tuple(interface.name for interface in self._interfaces)

    @property
    def methods(self) -> Tuple["_SkeletonMethod", ...]:
        return tuple(self._methods)

    @property
    def fields(self) -> Tuple["_SkeletonField", ...]:
        return tuple(self._fields)

    def __init__(
            self,
            name: str,
            super_: Union["_SkeletonClass", None],
            interfaces: Tuple["_SkeletonClass", ...],
            methods: Tuple["_SkeletonMethod", ...],
            fields: Tuple["_SkeletonField", ...],
            add_members: bool = True,
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
        :param interfaces: The interfaces this class implements.
        :param methods: The methods in this class.
        :param fields: The fields in this class.
        :param add_members: Should the members be added as attributes to this class?
        """

        self._name = name
        self._super = super_
        self._interfaces = interfaces
        self._methods: List[_SkeletonMethod] = list(methods)
        self._fields: List[_SkeletonField] = list(fields)

        for method in self._methods:
            method._class = self
            # Unfortunately I can't really mitigate the issue of namespace conflicts due to method overloads or fields
            # and methods having the same names (both of which are valid in Java, but not Python). This can be overcome
            # with some difficulty, but I can't be bothered right now.
            # TODO: ^^^
            if add_members and not hasattr(self, method.name):
                setattr(self, method.name, method)

        for field in self._fields:
            field._class = self
            if add_members and not hasattr(self, field.name):
                setattr(self, field.name, field)

        self._is_public = is_public
        self._is_final = is_final
        self._is_super = is_super
        self._is_interface = is_interface
        self._is_abstract = is_abstract
        self._is_synthetic = is_synthetic
        self._is_annotation = is_annotation
        self._is_enum = is_enum
        self._is_module = is_module

    def __repr__(self) -> str:
        return "<_SkeletonClass(name=%r) at %x>" % (self._name, id(self))

    def get_method(
            self,
            name: str,
            *descriptor: Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]],
    ) -> "_SkeletonMethod":
        """
        Gets a method in this class.

        :param name: The name of the method.
        :param descriptor: The descriptor of the method, if not given, the first method with the name is returned.
        :return: The method.
        """

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

    def add_method(
            self,
            name: str,
            *descriptor: Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]],
            **access_flags: Dict[str, bool],
    ) -> None:
        raise AttributeError("Can't add method to skeleton class.")

    def remove_method(
            self,
            name_or_method: Union[str, "_SkeletonMethod"],
            *descriptor: Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]],
    ) -> None:
        raise AttributeError("Can't remove method from skeleton class.")

    def get_field(self, name: str, descriptor: Union[BaseType, str, None] = None) -> "_SkeletonField":
        """
        Gets a field in this class.

        :param name: The name of the field.
        :param descriptor: The descriptor of the field, if None, the first field with the name is returned.
        :return: The field.
        """

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

    def add_field(
            self, name: str, descriptor: Union[BaseType, str, None] = None, **access_flags: Dict[str, bool],
    ) -> None:
        raise AttributeError("Can't add field to skeleton class.")

    def remove_field(
            self, name_or_field: Union[str, "_SkeletonField"], descriptor: Union[BaseType, str, None] = None,
    ) -> None:
        raise AttributeError("Can't remove field from skeleton class.")


class _SkeletonField(Field):
    """
    A fake Java field.
    """

    __slots__ = (
        "_is_public", "_is_private", "_is_static", "_is_final", "_is_transient", "_is_synthetic", "_is_enum",
        "_name", "_type", "_class",
    )

    @property
    def is_public(self) -> bool:
        return self._is_public

    @property
    def is_private(self) -> bool:
        return self._is_private

    @property
    def is_protected(self) -> bool:
        return self._is_protected

    @property
    def is_static(self) -> bool:
        return self._is_static

    @property
    def is_final(self) -> bool:
        return self._is_final

    @property
    def is_volatile(self) -> bool:
        return self._is_volatile

    @property
    def is_transient(self) -> bool:
        return self._is_transient

    @property
    def is_synthetic(self) -> bool:
        return self._is_synthetic

    @property
    def is_enum(self) -> bool:
        return self._is_enum

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> BaseType:
        return self._type

    @property
    def class_(self) -> _SkeletonClass:
        return self._class

    def __init__(
            self,
            name: str,
            type_: BaseType,
            class_: Union[_SkeletonClass, None] = None,
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
        :param name: The name of this field.
        :param type_: The type of this field.
        """

        self._name = name
        self._type = type_
        self._class = class_

        if class_ is not None and not self in class_._fields:
            class_._fields.append(self)

        self._is_public = is_public
        self._is_private = is_private
        self._is_protected = is_protected
        self._is_static = is_static
        self._is_final = is_final
        self._is_volatile = is_volatile
        self._is_transient = is_transient
        self._is_synthetic = is_synthetic
        self._is_enum = is_enum

    def __repr__(self) -> str:
        return "_SkeletonField(name=%r, type=%s) at %x>" % (self._name, self._type, id(self))


class _SkeletonMethod(Method):
    """
    A fake Java method.
    """

    __slots__ = (
        "_is_public", "_is_private", "_is_protected", "_is_final", "_is_synchronized",
        "_is_bridge", "_is_varargs", "_is_abstract", "_is_native", "_is_synthetic",
        "_name", "_argument_types", "_return_type", "_class",
    )

    @property
    def is_public(self) -> bool:
        return self._is_public

    @property
    def is_private(self) -> bool:
        return self._is_private

    @property
    def is_protected(self) -> bool:
        return self._is_protected

    @property
    def is_static(self) -> bool:
        return self._is_static

    @property
    def is_final(self) -> bool:
        return self._is_final

    @property
    def is_synchronized(self) -> bool:
        return self._is_synchronized

    @property
    def is_bridge(self) -> bool:
        return self._is_bridge

    @property
    def is_varargs(self) -> bool:
        return self._is_varargs

    @property
    def is_abstract(self) -> bool:
        return self._is_abstract

    @property
    def is_native(self) -> bool:
        return self._is_native

    @property
    def is_synthetic(self) -> bool:
        return self._is_synthetic

    @property
    def name(self) -> str:
        return self._name

    @property
    def argument_types(self) -> Tuple[BaseType, ...]:
        return self._argument_types

    @property
    def return_type(self) -> BaseType:
        return self._return_type

    @property
    def class_(self) -> _SkeletonClass:
        return self._class

    def __init__(
            self,
            name: str,
            argument_types: Tuple[BaseType, ...],
            return_type: BaseType,
            class_: Union[_SkeletonClass, None] = None,
            is_public: bool = False,
            is_private: bool = False,
            is_protected: bool = False,
            is_static: bool = False,
            is_final: bool = False,
            is_synchronized: bool = False,
            is_bridge: bool = False,
            is_varargs: bool = False,
            is_abstract: bool = False,
            is_native: bool = False,
            is_synthetic: bool = False,
    ) -> None:
        """
        :param name: The name of this method.
        :param argument_types: The argument types of this method.
        :param return_type: The return type of this method.
        :param class_: The class that this method belongs to.
        """

        self._name = name
        self._argument_types = argument_types
        self._return_type = return_type
        self._class = class_

        if class_ is not None and not self in class_._methods:
            class_._methods.append(self)

        self._is_public = is_public
        self._is_private = is_private
        self._is_protected = is_protected
        self._is_static = is_static
        self._is_final = is_final
        self._is_synchronized = is_synchronized
        self._is_bridge = is_bridge
        self._is_varargs = is_varargs
        self._is_abstract = is_abstract
        self._is_native = is_native
        self._is_synthetic = is_synthetic

    def __repr__(self) -> str:
        return "<_SkeletonMethod(name=%r, argument_types=(%s), return_type=%s) at %x>" % (
            self._name,
            ", ".join(map(str, self._argument_types)) + ("," if len(self._argument_types) == 1 else ""),
            self._return_type, id(self),
        )

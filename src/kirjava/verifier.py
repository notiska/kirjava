#!/usr/bin/env python3

__all__ = (
    "verify_classfile", "verify_field_info", "verify_method_info",
    "verify_graph",
    "Error",
)

"""
Verifier implementation, verifies that graphs and/or methods are valid.
"""

import typing
from typing import Any, Iterable

from . import version
from .abc import Source
from .classfile import ClassFile, FieldInfo, Index, MethodInfo
from .error import VerifyError
from .types import top_t, Class, Type, Verification

if typing.TYPE_CHECKING:
    from .analysis import InsnGraph


def verify_classfile(classfile: ClassFile) -> None:
    """
    Verifies that a classfile is valid.

    :param classfile: The classfile to verify.
    :raises VerifyError: If the classfile is invalid.
    """

    errors = []

    if len(classfile.constant_pool) > 65535:
        errors.append(Error(
            "Constant pool has too many entries (%i), max is 65535" % len(classfile.constant_pool), classfile,
        ))
    if len(classfile.interface_names) > 65535:
        errors.append(Error("Class has too many interfaces (%i), max is 65535" % len(classfile.interface_names), classfile))
    if len(classfile.fields) > 65535:
        errors.append(Error("Class has too many fields (%i), max is 65535" % len(classfile.fields), classfile))
    if len(classfile.methods) > 65535:
        errors.append(Error("Class has too many methods (%i), max is 65535" % len(classfile.methods), classfile))
    if len(classfile.attributes) > 65535:
        errors.append(Error("Class has too many attributes (%i), max is 65535" % len(classfile.attributes), classfile))

    for constant_info in classfile.constant_pool:
        if constant_info.since < classfile.version:
            errors.append(Error("Constant is newer than classfile version %r", classfile.version, constant_info))
        elif type(constant_info) is Index and not constant_info.index in classfile.constant_pool:
            errors.append(Error("Constant references invalid index %i" % constant_info.index, constant_info))

    if classfile.is_module and classfile.version > version.JAVA_8:
        # Probably could do this more easily with the access flags directly, but I'll keep it this way for potential
        # future compatibility reasons.
        if (
            classfile.is_public or
            classfile.is_final or
            classfile.is_super or
            classfile.is_interface or
            classfile.is_abstract or
            classfile.is_synthetic or
            classfile.is_annotation or
            classfile.is_enum
        ):
            errors.append(Error("Module has other flags set", classfile))

        try:
            if classfile.name != "module-info":
                errors.append(Error("Module has invalid name, must be 'module-info'", classfile))
        except AttributeError:  # I'm starting to understand why people hate exceptions.
            errors.append(Error("Module is malformed and does not have a valid name", classfile))

        if classfile.super_name is not None:
            errors.append(Error("Module cannot have a super class", classfile))
        if classfile.interface_names:
            errors.append(Error("Module cannot have interfaces", classfile))
        if classfile.fields:
            errors.append(Error("Module cannot have fields", classfile))
        if classfile.methods:
            errors.append(Error("Module cannot have methods", classfile))

        # TODO: Check attributes?

    elif classfile.is_interface:
        # https://github.com/openjdk/jdk8u/blob/master/hotspot/src/share/vm/classfile/classFileParser.cpp#L3981
        if not classfile.is_abstract and classfile.version > version.JAVA_6:
            errors.append(Error("Interface does not have abstract flag set", classfile))

        if classfile.is_final:
            errors.append(Error("Interface has final flag set", classfile))
        if classfile.is_super:
            errors.append(Error("Interface has super flag set", classfile))
        if classfile.is_enum:
            errors.append(Error("Interface has enum flag set", classfile))
        if classfile.is_module:
            errors.append(Error("Interface has module flag set", classfile))

    else:
        if classfile.is_abstract and classfile.is_final:
            errors.append(Error("Class is both abstract and final", classfile))
        if classfile.is_annotation:
            errors.append(Error("Class has annotation flag set", classfile))

    for field in classfile.fields:
        try:
            verify_field_info(field)
        except VerifyError as error:
            errors.extend(error.errors)

    for method in classfile.methods:
        try:
            verify_method_info(method)
        except VerifyError as error:
            errors.extend(error.errors)

    # TODO: Attributes?

    if errors:
        raise VerifyError(errors)


def verify_field_info(field: FieldInfo) -> None:
    ...


def verify_method_info(method: MethodInfo) -> None:
    ...


def verify_graph(graph: "InsnGraph") -> None:
    """
    Verifies that the structure of a graph is valid.

    :param graph: The graph to verify.
    :raises VerifyError: If the graph is invalid.
    """

    ...


class Error:
    """
    An individual error.
    """

    __slots__ = ("message", "source", "_hash")

    def __init__(self, message: str, source: Source | None = None) -> None:
        self.message = message
        self.source = source

        self._hash = hash((self.message, self.source))

    def __repr__(self) -> str:
        return "<Error(message=%r, source=%r)>" % (self.message, self.source)

    def __str__(self) -> str:
        if self.source is not None:
            return "%s: %s" % (self.source, self.message)
        return self.message

    def __eq__(self, other: Any) -> bool:
        return type(other) is Error and other.message == self.message and other.source == self.source

    def __hash__(self) -> int:
        return self._hash

#!/usr/bin/env python3

"""
Nicer argument conversions for easier API usage.
"""

from typing import Tuple, Union

from . import types
from .abc import Class
from .classfile import descriptor
from .classfile.constants import Class as Class_
from .types import BaseType, ReferenceType
from .types.reference import ClassOrInterfaceType


def get_class_constant(argument: Union[Class_, ReferenceType, Class, str]) -> Class_:
    """
    Converts the argument into a class constant.

    :param argument: The argument to convert.
    :return: The class constant.
    """

    if isinstance(argument, Class_):
        return argument
    elif isinstance(argument, ClassOrInterfaceType):
        return Class_(argument.name)
    elif isinstance(argument, ReferenceType):
        return Class_(descriptor.to_descriptor(argument))
    elif isinstance(argument, Class):
        return Class_(argument.name)
    elif isinstance(argument, str):
        try:
            type_ = descriptor.parse_field_descriptor(argument)
            if not isinstance(type_, ReferenceType):
                raise Exception
            return get_class_constant(type_)
        except Exception:
            return Class_(argument)
    else:
        raise TypeError("Don't know how to convert %r into a class constant." % argument.__class__)


def get_reference_type(argument: Union[ReferenceType, Class, Class_, str]) -> ReferenceType:
    """
    Converts the argument into a reference type.

    :param argument: The argument to convert.
    :return: The reference type.
    """

    if isinstance(argument, ReferenceType):
        return argument
    elif isinstance(argument, Class):
        return argument.get_type()
    elif isinstance(argument, Class_):  # Lol, I know :p
        return argument.get_actual_type()
    elif isinstance(argument, str):
        try:
            type_ = descriptor.parse_field_descriptor(argument)
            if not isinstance(type_, ReferenceType):
                raise Exception
            return type_
        except Exception:
            return ClassOrInterfaceType(argument)
    else:
        raise TypeError("Don't know how to convert %r into a reference type." % argument.__class__)


def get_field_descriptor(argument: Union[BaseType, str]) -> BaseType:
    """
    Gets a field descriptor type from an argument.

    :param argument: The argument to convert.
    :return: The field type.
    """

    if isinstance(argument, BaseType) and argument != types.void_t:
        return argument
    elif isinstance(argument, str):
        return descriptor.parse_field_descriptor(argument)
    else:
        raise TypeError("Don't know how to convert %r into a field descriptor type." % argument.__class__)


def get_method_descriptor(
        *arguments: Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]],
) -> Tuple[Tuple[BaseType, ...], BaseType]:
    """
    Gets a method descriptor from some arguments.

    :param arguments: The arguments to convert.
    :return: The method argument and return types.
    """

    if not arguments:
        raise ValueError("Arguments required for method descriptor.")

    if len(arguments) == 1:
        argument, = arguments
        if isinstance(argument, str):
            return descriptor.parse_method_descriptor(argument)
        else:
            raise TypeError(
                "Don't know how to convert %r into a method descriptor argument and return types." % argument.__class__,
            )

    argument_types, return_type, *_ = arguments

    if isinstance(argument_types, tuple):
        argument_types_ = []
        for argument_type in argument_types:
            try:
                argument_types_.append(get_field_descriptor(argument_type))
            except TypeError as error:
                if error.args and error.args[0].startswith("Don't know how to convert"):  # :(
                    raise TypeError(
                        "Don't know how to convert %r into a method descriptor argument type." % argument_type.__class__,
                    )
                raise error
        argument_types = tuple(argument_types_)
    elif isinstance(argument_types, str):
        argument_types, _ = descriptor.parse_method_descriptor(argument_types + "V")
    else:
        raise TypeError("Don't know how to convert %r into method descriptor argument types." % argument_types.__class__)

    if isinstance(return_type, BaseType):
        return argument_types, return_type
    elif isinstance(return_type, str):
        _, return_type = descriptor.parse_method_descriptor("()" + return_type)
        return argument_types, return_type
    else:
        raise TypeError("Don't know how to convert %r into a method descriptor return type." % return_type.__class__)

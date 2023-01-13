#!/usr/bin/env python3

"""
Nicer argument conversions for easier API usage.
"""

from typing import Tuple, Union

from . import types
from .abc import Class
from .classfile import constants, descriptor
from .types import BaseType
from .types.reference import ClassOrInterfaceType


# ------------------------------ Types ------------------------------ #

ClassConstant = Union[types.ReferenceType, constants.Class, Class, str]
FieldDescriptor = Union[BaseType, str]
#                                       argument types              return type      full descriptor
MethodDescriptor = Union[Tuple[Union[Tuple[BaseType, ...], str], Union[BaseType, str]], Tuple[str]]
ReferenceType = Union[types.ReferenceType, constants.Class, Class, str]


# ------------------------------ Functions ------------------------------ #

def get_class_constant(argument: ClassConstant) -> constants.Class:
    """
    Converts the argument into a class constant.

    :param argument: The argument to convert.
    :return: The class constant.
    """

    argument_class = argument.__class__

    if argument_class is str:
        try:
            type_ = descriptor.parse_field_descriptor(argument)
            if not isinstance(type_, types.ReferenceType):
                raise Exception
            return get_class_constant(type_)
        except Exception:
            return constants.Class(argument)
    elif argument_class is constants.Class:
        return argument
    elif argument_class is ClassOrInterfaceType:
        return constants.Class(argument.name)
    elif isinstance(argument, types.ReferenceType):
        return constants.Class(descriptor.to_descriptor(argument))
    elif isinstance(argument, Class):
        return constants.Class(argument.name)
    else:
        raise TypeError("Don't know how to convert %r into a class constant." % argument_class)


def get_reference_type(argument: ReferenceType) -> types.ReferenceType:
    """
    Converts the argument into a reference type.

    :param argument: The argument to convert.
    :return: The reference type.
    """

    argument_class = argument.__class__

    if argument_class is str:
        try:
            type_ = descriptor.parse_field_descriptor(argument)
            if not isinstance(type_, types.ReferenceType):
                raise Exception
            return type_
        except Exception:
            return ClassOrInterfaceType(argument)
    elif argument_class is constants.Class:
        return argument.type
    elif isinstance(argument, types.ReferenceType):
        return argument
    elif isinstance(argument, Class):
        return argument.get_type()
    else:
        raise TypeError("Don't know how to convert %r into a reference type." % argument_class)


def get_field_descriptor(argument: FieldDescriptor) -> BaseType:
    """
    Gets a field descriptor type from an argument.

    :param argument: The argument to convert.
    :return: The field type.
    """

    if argument.__class__ is str:
        return descriptor.parse_field_descriptor(argument)
    if isinstance(argument, BaseType) and argument != types.void_t:
        return argument
    else:
        raise TypeError("Don't know how to convert %r into a field descriptor type." % argument.__class__)


def get_method_descriptor(*arguments: MethodDescriptor) -> Tuple[Tuple[BaseType, ...], BaseType]:
    """
    Gets a method descriptor from some arguments.

    :param arguments: The arguments to convert.
    :return: The method argument and return types.
    """

    if not arguments:
        raise ValueError("Arguments required for method descriptor.")

    if len(arguments) == 1:
        argument, = arguments
        if argument.__class__ is str:
            return descriptor.parse_method_descriptor(argument)
        else:
            raise TypeError(
                "Don't know how to convert %r into a method descriptor argument and return types." % argument.__class__,
            )

    argument_types, return_type, *_ = arguments

    if argument_types.__class__ is tuple:
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
    elif argument_types.__class__ is str:
        argument_types, _ = descriptor.parse_method_descriptor(argument_types + "V")
    else:
        raise TypeError("Don't know how to convert %r into method descriptor argument types." % argument_types.__class__)

    if return_type.__class__ is str:
        _, return_type = descriptor.parse_method_descriptor("()" + return_type)
        return argument_types, return_type
    elif isinstance(return_type, BaseType):
        return argument_types, return_type
    else:
        raise TypeError("Don't know how to convert %r into a method descriptor return type." % return_type.__class__)

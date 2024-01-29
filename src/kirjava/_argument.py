#!/usr/bin/env python3

__all__ = (
    "ClassConstant", "FieldDescriptor", "MethodDescriptor", "ReferenceType",
    "get_class_constant", "get_reference_type", "get_field_descriptor", "get_method_descriptor",
)

"""
Nicer argument conversions for easier API usage.
"""

from typing import Union

from . import types
from .abc import Class
from .types import descriptor, Reference, Type


# FIXME: Cleanup!!
ClassConstant = Union[Reference, "constants.Class", Class, str]
FieldDescriptor = Type | str
#                                 argument types              return type      full descriptor
MethodDescriptor = Union[tuple[Union[tuple[Type, ...], str], Union[Type, str]], tuple[str]]
ReferenceType = Union[Reference, "constants.Class", Class, str]


def get_class_constant(argument: ClassConstant) -> "constants.Class":
    """
    Converts the argument into a class constant.

    :param argument: The argument to convert.
    :return: The class constant.
    """

    argument_class = type(argument)

    if argument_class is str:
        return constants.Class(argument)
    elif argument_class is constants.Class:
        return argument
    elif argument_class is types.Class:
        return constants.Class(argument.name)
    elif isinstance(argument, Reference):
        return constants.Class(descriptor.to_descriptor(argument))
    elif isinstance(argument, Class):
        return constants.Class(argument.name)
    else:
        raise TypeError("Don't know how to convert %r into a class constant." % argument_class)


def get_reference_type(argument: ReferenceType) -> Reference:
    """
    Converts the argument into a reference type.

    :param argument: The argument to convert.
    :return: The reference type.
    """

    argument_class = type(argument)

    if argument_class is str:
        try:
            return descriptor.parse_field_descriptor(argument, reference_only=True)
        except (ValueError, TypeError):
            return types.Class(argument)
    elif argument_class is constants.Class:
        return argument.class_type
    elif isinstance(argument, Reference):
        return argument
    elif isinstance(argument, Class):
        return argument.get_type()
    else:
        raise TypeError("Don't know how to convert %r into a reference type." % argument_class)


def get_field_descriptor(argument: FieldDescriptor) -> Type:
    """
    Gets a field descriptor type from an argument.

    :param argument: The argument to convert.
    :return: The field type.
    """

    if type(argument) is str:
        return descriptor.parse_field_descriptor(argument)
    if isinstance(argument, Type) and argument != types.void_t:
        return argument
    else:
        raise TypeError("Don't know how to convert %r into a field descriptor type." % type(argument))


def get_method_descriptor(*arguments: MethodDescriptor) -> tuple[tuple[Type, ...], Type]:
    """
    Gets a method descriptor from some arguments.

    :param arguments: The arguments to convert.
    :return: The method argument and return types.
    """

    if not arguments:
        raise ValueError("Arguments required for method descriptor.")

    if len(arguments) == 1:
        argument, = arguments
        if type(argument) is str:
            return descriptor.parse_method_descriptor(argument)
        else:
            raise TypeError(
                "Don't know how to convert %r into a method descriptor argument and return types." % type(argument),
            )

    argument_types, return_type, *_ = arguments

    if type(argument_types) is tuple:
        argument_types_ = []
        for argument_type in argument_types:
            try:
                argument_types_.append(get_field_descriptor(argument_type))
            except TypeError as error:
                if error.args and error.args[0].startswith("Don't know how to convert"):  # :(
                    raise TypeError(
                        "Don't know how to convert %r into a method descriptor argument type." % type(argument_type),
                    )
                raise error
        argument_types = tuple(argument_types_)
    elif type(argument_types) is str:
        argument_types, _ = descriptor.parse_method_descriptor(argument_types + "V")
    else:
        raise TypeError("Don't know how to convert %r into method descriptor argument types." % type(argument_types))

    if type(return_type) is str:
        _, return_type = descriptor.parse_method_descriptor("()" + return_type)
        return argument_types, return_type
    elif isinstance(return_type, Type):
        return argument_types, return_type
    else:
        raise TypeError("Don't know how to convert %r into a method descriptor return type." % type(return_type))


from . import constants

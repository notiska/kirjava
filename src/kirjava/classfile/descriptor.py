#!/usr/bin/env python3

from typing import Tuple, Union

from .. import types
from ..types import BaseType, InvalidType
from ..types.reference import ArrayType, ClassOrInterfaceType

_FORWARD_BASE_TYPES = {
    "B": types.byte_t,
    "S": types.short_t,
    "I": types.int_t,
    "J": types.long_t,
    "C": types.char_t,
    "F": types.float_t,
    "D": types.double_t,
    "Z": types.bool_t,
    "V": types.void_t,
}
_BACKWARD_BASE_TYPES = {
    types.byte_t: "B",
    types.short_t: "S",
    types.int_t: "I",
    types.long_t: "J",
    types.char_t: "C",
    types.float_t: "F",
    types.double_t: "D",
    types.bool_t: "Z",
    types.void_t: "V",
}


def _find_enclosing(
        string: str,
        start_identifier: str,
        end_identifier: str,
) -> Union[Tuple[str, str, str], Tuple[None, None, None]]:
    """
    Finds the enclosing arguments within the provided start and ending identifiers, as well as the string before and
    after the start and end.
    """

    start_index = string.find(start_identifier)

    offset = start_index + 1
    end_index = string.find(end_identifier)
    if end_index < 0:
        return None, None, None

    while 0 < string.find(start_identifier, offset) < end_index:  # Find the next start in the initial bound
        offset = string.find(start_identifier, offset) + 1
        end_index = string.find(end_identifier, end_index + 1)
        if end_index < 0:  # No corresponding end identifier?
            return None, None, None

    return string[:start_index], string[start_index + 1: end_index], string[end_index + 1:]


def to_descriptor(*values: Union[Tuple[BaseType, ...], BaseType], dont_throw: bool = False) -> str:
    """
    Serializes the provided types to a descriptor.

    :param values: The values to serialize.
    :param dont_throw: Don't throw an exception when an invalid type is passed.
    :return: The serialized type string.
    """

    descriptor = ""
    for value in values:
        if value in _BACKWARD_BASE_TYPES:
            descriptor += _BACKWARD_BASE_TYPES[value]
        elif isinstance(value, ClassOrInterfaceType):
            descriptor += "L%s;" % value.name
        elif isinstance(value, ArrayType):
            descriptor += "%s%s" % ("[" * value.dimension, to_descriptor(value.element_type, dont_throw=dont_throw))
        elif isinstance(value, tuple):
            descriptor += "(%s)" % to_descriptor(*value, dont_throw=dont_throw)
        elif not dont_throw:
            raise TypeError("Invalid type for descriptor: %r." % value)

    return descriptor


def next_argument(descriptor: str) -> Tuple[BaseType, str]:
    """
    Gets the next argument from the descriptor.

    :param descriptor: The descriptor.
    :return: The next argument (can be None) and the remaining descriptor.
    """

    if not descriptor:
        return InvalidType(descriptor), ""

    char = descriptor[0]

    if char in _FORWARD_BASE_TYPES:
        return _FORWARD_BASE_TYPES[char], descriptor[1:]

    elif char == "L":
        end_index = descriptor.find(";")
        return ClassOrInterfaceType(descriptor[1: end_index]), descriptor[end_index + 1:]

    elif char == "[":
        element_type, descriptor = next_argument(descriptor[1:])  # FIXME: This could be done so much better
        if isinstance(element_type, ArrayType):
            element_type.dimension += 1
            array_type = element_type
        else:
            array_type = ArrayType(element_type)

        return array_type, descriptor

    else:
        return InvalidType(descriptor), ""


def parse_field_descriptor(
        descriptor: str,
        force_read: bool = False,
        dont_throw: bool = False,
) -> BaseType:
    """
    Parses a field descriptor.
    Note: This cannot parse signatures, use the signature parser instead.

    :param descriptor: The field descriptor.
    :param force_read: Force the already parsed field descriptor to be returned, even if there is an error.
    :param dont_throw: Don't throw an exception if the descriptor is invalid, instead return InvalidType.
    :return: The parsed field type.
    """

    if not force_read and not descriptor:
        if dont_throw:
            return InvalidType(descriptor)
        raise ValueError("Descriptor is empty.")

    type_, remaining = next_argument(descriptor)
    if not force_read:
        # Check for trailing data
        if remaining:
            if dont_throw:
                return InvalidType(descriptor)
            raise ValueError("Trailing data %r in descriptor." % remaining)

        # Check the type is valid
        if type_ == types.void_t or isinstance(type_, InvalidType):
            if dont_throw:
                return InvalidType(descriptor)
            raise TypeError("Invalid type argument %r found." % type_)

    return type_


def parse_method_descriptor(
        descriptor: str,
        force_read: bool = False,
        dont_throw: bool = False,
) -> Union[Tuple[Tuple[BaseType, ...], BaseType], InvalidType]:
    """
    Parses a method descriptor.
    Note: This cannot parse signatures, use the signature parser instead.

    :param descriptor: The method descriptor.
    :param force_read: Force the already parsed method descriptor to be returned, even if there is an error.
    :param dont_throw: Don't throw an exception if the descriptor is invalid, instead return InvalidType.
    :return: The parsed method types and the return type.
    """

    if not force_read and not descriptor:
        if dont_throw:
            return InvalidType(descriptor)
        raise ValueError("Descriptor is empty.")
    
    # This is extra, but who cares :p, if it causes MAJOR issues I'll remove it later
    preceding, arguments_descriptor, remaining = _find_enclosing(descriptor, "(", ")")

    argument_types = []
    while arguments_descriptor:  # If there are no (), arguments_descriptor should be None
        type_, arguments_descriptor = next_argument(arguments_descriptor)
        argument_types.append(type_)
        
    argument_types = tuple(argument_types)
    return_type, remaining = next_argument(remaining)
    
    if not force_read:
        # Checking for leading / trailing data
        if preceding:
            if dont_throw:
                return InvalidType(descriptor)
            raise ValueError("Leading data %r in descriptor." % preceding)

        if remaining:
            if dont_throw:
                return InvalidType(descriptor)
            raise ValueError("Trailing data %r in descriptor." % remaining)

        # Check we have arguments
        if arguments_descriptor is None:
            if dont_throw:
                return InvalidType(descriptor)
            raise ValueError("No argument types found.")

        # Check the types in the arguments are valid (i.e. no void types)
        for argument_type in argument_types:
            if argument_type == types.void_t or isinstance(argument_type, InvalidType):
                if dont_throw:
                    return InvalidType(descriptor)
                raise TypeError("Invalid argument type %r found." % argument_type)

        # Check the return type is valid
        if isinstance(return_type, InvalidType):
            raise TypeError("Invalid return type %r found." % return_type)

    return argument_types, return_type


# def parse_any_descriptor(descriptor: str, dont_throw: bool = False, force_tuple: bool = False,
#                          force_read: bool = True) -> Union[Tuple[BaseType, ...], BaseType]:
#     """
#     Parses any descriptor.
#     Note: This cannot parse signatures, use the signature parser instead.
# 
#     :param descriptor: The descriptor.
#     :param dont_throw: Don't throw an exception if the descriptor is invalid, instead return InvalidType.
#     :param force_tuple: Force the result to be a tuple.
#     :param force_read: Forcefully return results, even if an error occurs. An InvalidType is returned with any types
#                        that were successfully parsed.
#     :return: The parsed field or method types.
#     """
# 
#     original_descriptor = descriptor
#     types = []
# 
#     prev_descriptor = descriptor
#     while descriptor:
#         type_, descriptor = next_argument(descriptor)
#         if type_ is None or descriptor == prev_descriptor:
#             if force_read:
#                 types.append(InvalidType(descriptor))  # The descriptor is valid up to what we've just parsed
#                 break
#             if dont_throw:
#                 if force_tuple:
#                     return InvalidType(original_descriptor),
#                 return InvalidType(original_descriptor)
#             raise ValueError("Invalid descriptor %r." % descriptor)
# 
#         types.append(type_)
#         prev_descriptor = descriptor
# 
#     if len(types) == 1 and not force_tuple:
#         return types[0]
#     return tuple(types)

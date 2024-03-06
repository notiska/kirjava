#!/usr/bin/env python3

__all__ = (
    "to_descriptor", "parse_field_descriptor", "parse_method_descriptor",
)

from . import (
    boolean_t, byte_t, char_t, double_t, float_t, int_t, long_t, short_t, void_t, Array, Class, Invalid, Reference, Type,
)

_FORWARD_BASE_TYPES = {
    "B": byte_t,
    "S": short_t,
    "I": int_t,
    "J": long_t,
    "C": char_t,
    "F": float_t,
    "D": double_t,
    "Z": boolean_t,
    "V": void_t,
}
_BACKWARD_BASE_TYPES = {
    byte_t:    "B",
    short_t:   "S",
    int_t:     "I",
    long_t:    "J",
    char_t:    "C",
    float_t:   "F",
    double_t:  "D",
    boolean_t: "Z",
    void_t:    "V",
}


def _find_enclosing(
        string: str, start_identifier: str, end_identifier: str,
) -> tuple[str | None, str | None, str | None]:
    """
    Finds the enclosing arguments within the provided start and ending identifiers, as well as the string before and
    after the start and end.
    """

    end_index = string.find(end_identifier)
    if end_index < 0:
        return None, None, None
    start_index = string.find(start_identifier)
    offset = string.find(start_identifier, start_index + 1)

    while 0 < offset < end_index:  # Find the next start in the initial bound
        end_index = string.find(end_identifier, end_index + 1)
        if end_index < 0:  # No corresponding end identifier?
            return None, None, None
        offset = string.find(start_identifier, offset) + 1

    return string[:start_index], string[start_index + 1: end_index], string[end_index + 1:]


def to_descriptor(*values: tuple[Type, ...] | Type, do_raise: bool = True) -> str:
    """
    Serializes the provided types to a descriptor.

    :param values: The values to serialize.
    :param do_raise: Raises an exception when an invalid type is encountered.
    :return: The serialized type string.
    """

    descriptor = ""

    for value in values:
        base_type = _BACKWARD_BASE_TYPES.get(value)
        if base_type is not None:
            descriptor += base_type
        else:
            value_class = type(value)

            if value_class is Class:
                descriptor += "L%s;" % value.name
            elif value_class is Array:
                descriptor += "[" + to_descriptor(value.element, do_raise=do_raise)
            elif value_class is tuple:
                descriptor += "(%s)" % to_descriptor(*value, do_raise=do_raise)
            elif do_raise:
                raise TypeError("Invalid type for descriptor: %r." % value)

    return descriptor


def next_argument(descriptor: str) -> tuple[Type, str]:
    """
    Gets the next argument from the descriptor.

    :param descriptor: The descriptor.
    :return: The next argument (can be None) and the remaining descriptor.
    """

    if not descriptor:
        return Invalid(descriptor), ""

    if descriptor[0] == "L":
        end_index = descriptor.find(";")
        if end_index < 0:
            return Invalid(descriptor), ""
        return Class(descriptor[1: end_index]), descriptor[end_index + 1:]

    elif descriptor[0] == "[":
        element_type, descriptor = next_argument(descriptor[1:])  # FIXME: This could be done so much better
        return Array(element_type), descriptor

    else:
        base_type = _FORWARD_BASE_TYPES.get(descriptor[0])
        if base_type is not None:
            return base_type, descriptor[1:]
        return Invalid(descriptor), ""


def parse_field_descriptor(
        descriptor: str,
        *,
        force_read: bool = False,
        do_raise: bool = True,
        reference_only: bool = False,
) -> Type:
    """
    Parses a field descriptor.
    Note: This cannot parse signatures, use the signature parser instead.

    :param descriptor: The field descriptor.
    :param force_read: Force the already parsed field descriptor to be returned, even if there is an error.
    :param do_raise: Raises an exception if the descriptor is invalid. Otherwise, returns an InvalidType.
    :param reference_only: Expect only a reference type.
    :return: The parsed field type.
    """

    if not force_read and not descriptor:
        if do_raise:
            raise ValueError("Descriptor is empty.")
        return Invalid(descriptor)

    type_, remaining = next_argument(descriptor)

    if not force_read:
        # Check for trailing data
        if remaining:
            if do_raise:
                raise ValueError("Trailing data %r in descriptor." % remaining)
            return Invalid(descriptor)

        # Check the type is valid
        if type_ == void_t or type(type_) is Invalid:
            if do_raise:
                raise TypeError("Invalid type argument %r found." % type_)
            return Invalid(descriptor)

    # https://github.com/ItzSomebody/stopdecompilingmyjava/blob/master/decompiler-tool-bugs/entry-007/entry.md
    if reference_only and not isinstance(type_, Reference):
        return Class(descriptor)
    return type_


def parse_method_descriptor(
        descriptor: str,
        *,
        force_read: bool = False,
        do_raise: bool = True,
) -> tuple[tuple[Type, ...], Type] | Invalid:
    """
    Parses a method descriptor.
    Note: This cannot parse signatures, use the signature parser instead.

    :param descriptor: The method descriptor.
    :param force_read: Force the already parsed method descriptor to be returned, even if there is an error.
    :param do_raise: Raises an exception if the descriptor is invalid. Otherwise, returns an invalid type.
    :return: The parsed method types and the return type.
    """

    if not force_read and not descriptor:
        if do_raise:
            raise ValueError("Descriptor is empty.")
        return Invalid(descriptor)

    # This is extra, but who cares :p, if it causes MAJOR issues I'll remove it later
    preceding, arguments_descriptor, remaining = _find_enclosing(descriptor, "(", ")")

    argument_types = []
    while arguments_descriptor:  # If there are no (), arguments_descriptor should be None
        type_, arguments_descriptor = next_argument(arguments_descriptor)
        argument_types.append(type_)

    return_type, remaining = next_argument(remaining)
    
    if not force_read:
        # Checking for leading / trailing data
        if preceding:
            if do_raise:
                raise ValueError("Leading data %r in descriptor." % preceding)
            return Invalid(descriptor)

        if remaining:
            if do_raise:
                raise ValueError("Trailing data %r in descriptor." % remaining)
            return Invalid(descriptor)

        # Check we have arguments
        if arguments_descriptor is None:
            if do_raise:
                raise ValueError("No argument types found.")
            return Invalid(descriptor)

        # Check the types in the arguments are valid (i.e. no void types)
        for argument_type in argument_types:
            if argument_type == void_t or type(argument_type) is Invalid:
                if do_raise:
                    raise TypeError("Invalid argument type %r found." % argument_type)
                return Invalid(descriptor)

        # Check the return type is valid
        if type(return_type) is Invalid:
            raise TypeError("Invalid return type %r found." % return_type)

    return tuple(argument_types), return_type


# def parse_any_descriptor(descriptor: str, dont_throw: bool = False, force_tuple: bool = False,
#                          force_read: bool = True) -> tuple[BaseType, ...] | BaseType:
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

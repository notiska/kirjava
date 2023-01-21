# cython: language=c
# cython: language_level=3

from typing import Tuple, Union

from .. import types
from ..types import BaseType, InvalidType
from ..types.reference import ArrayType, ClassOrInterfaceType

cdef dict _FORWARD_BASE_TYPES = {
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
cdef dict _BACKWARD_BASE_TYPES = {
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


cpdef inline tuple _find_enclosing(str string, str start_identifier, str end_identifier):
    """
    Finds the enclosing arguments within the provided start and ending identifiers, as well as the string before and
    after the start and end.
    """

    cdef int end_index = string.find(end_identifier)
    if end_index < 0:
        return None, None, None
    cdef int start_index = string.find(start_identifier)
    cdef int offset = string.find(start_identifier, start_index + 1)

    while 0 < offset < end_index:  # Find the next start in the initial bound
        end_index = string.find(end_identifier, end_index + 1)
        if end_index < 0:  # No corresponding end identifier?
            return None, None, None
        offset = string.find(start_identifier, offset) + 1

    return string[:start_index], string[start_index + 1: end_index], string[end_index + 1:]


def to_descriptor(*values: Union[Tuple[BaseType, ...], BaseType], do_raise: bool = True) -> str:
    """
    Serializes the provided types to a descriptor.

    :param values: The values to serialize.
    :param do_raise: Raises an exception when an invalid type is encountered.
    :return: The serialized type string.
    """

    cdef str descriptor = ""
    for value in values:
        base_type = _BACKWARD_BASE_TYPES.get(value, None)
        if base_type is not None:
            descriptor += base_type
        else:
            value_class = value.__class__

            if value_class is ClassOrInterfaceType:
                descriptor += "L%s;" % value.name
            elif value_class is ArrayType:
                descriptor += "%s%s" % ("[" * value.dimension, to_descriptor(value.element_type, do_raise=do_raise))
            elif value_class is tuple:
                descriptor += "(%s)" % to_descriptor(*value, do_raise=do_raise)
            elif do_raise:
                raise TypeError("Invalid type for descriptor: %r." % value)

    return descriptor


cpdef inline tuple next_argument(str descriptor):  # -> Tuple[BaseType, str]:
    """
    Gets the next argument from the descriptor.

    :param descriptor: The descriptor.
    :return: The next argument (can be None) and the remaining descriptor.
    """

    if not descriptor:
        return InvalidType(descriptor), ""

    if descriptor[0] == "L":
        end_index = descriptor.find(";")
        if end_index < 0:
            return InvalidType(descriptor), ""
        return ClassOrInterfaceType(descriptor[1: end_index]), descriptor[end_index + 1:]

    elif descriptor[0] == "[":
        element_type, descriptor = next_argument(descriptor[1:])  # FIXME: This could be done so much better
        if element_type.__class__ is ArrayType:
            element_type.dimension += 1  # Evil
            array_type = element_type
        else:
            array_type = ArrayType(element_type)

        return array_type, descriptor

    else:
        base_type = _FORWARD_BASE_TYPES.get(descriptor[0], None)
        if base_type is not None:
            return base_type, descriptor[1:]
        return InvalidType(descriptor), ""


def parse_field_descriptor(
        descriptor: str,
        *,
        force_read: bool = False,
        do_raise: bool = True,
) -> BaseType:
    """
    Parses a field descriptor.
    Note: This cannot parse signatures, use the signature parser instead.

    :param descriptor: The field descriptor.
    :param force_read: Force the already parsed field descriptor to be returned, even if there is an error.
    :param do_raise: Raises an exception if the descriptor is invalid. Otherwise, returns an InvalidType.
    :return: The parsed field type.
    """

    if not force_read and not descriptor:
        if do_raise:
            raise ValueError("Descriptor is empty.")
        return InvalidType(descriptor)

    cdef str remaining

    type_, remaining = next_argument(descriptor)
    if not force_read:
        # Check for trailing data
        if remaining:
            if do_raise:
                raise ValueError("Trailing data %r in descriptor." % remaining)
            return InvalidType(descriptor)

        # Check the type is valid
        if type_ == types.void_t or type_.__class__ is InvalidType:
            if do_raise:
                raise TypeError("Invalid type argument %r found." % type_)
            return InvalidType(descriptor)

    return type_


def parse_method_descriptor(
        descriptor: str,
        *,
        force_read: bool = False,
        do_raise: bool = True,
) -> Union[Tuple[Tuple[BaseType, ...], BaseType], InvalidType]:
    """
    Parses a method descriptor.
    Note: This cannot parse signatures, use the signature parser instead.

    :param descriptor: The method descriptor.
    :param force_read: Force the already parsed method descriptor to be returned, even if there is an error.
    :param do_raise: Raises an exception if the descriptor is invalid. Otherwise, returns an InvalidType.
    :return: The parsed method types and the return type.
    """

    if not force_read and not descriptor:
        if do_raise:
            raise ValueError("Descriptor is empty.")
        return InvalidType(descriptor)

    cdef str preceding
    cdef str arguments_descriptor
    cdef str remaining

    # This is extra, but who cares :p, if it causes MAJOR issues I'll remove it later
    preceding, arguments_descriptor, remaining = _find_enclosing(descriptor, "(", ")")

    cdef list argument_types = []
    while arguments_descriptor:  # If there are no (), arguments_descriptor should be None
        type_, arguments_descriptor = next_argument(arguments_descriptor)
        argument_types.append(type_)

    return_type, remaining = next_argument(remaining)
    
    if not force_read:
        # Checking for leading / trailing data
        if preceding:
            if do_raise:
                raise ValueError("Leading data %r in descriptor." % preceding)
            return InvalidType(descriptor)

        if remaining:
            if do_raise:
                raise ValueError("Trailing data %r in descriptor." % remaining)
            return InvalidType(descriptor)

        # Check we have arguments
        if arguments_descriptor is None:
            if do_raise:
                raise ValueError("No argument types found.")
            return InvalidType(descriptor)

        # Check the types in the arguments are valid (i.e. no void types)
        for argument_type in argument_types:
            if argument_type == types.void_t or argument_type.__class__ is InvalidType:
                if do_raise:
                    raise TypeError("Invalid argument type %r found." % argument_type)
                return InvalidType(descriptor)

        # Check the return type is valid
        if return_type.__class__ is InvalidType:
            raise TypeError("Invalid return type %r found." % return_type)

    return tuple(argument_types), return_type


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

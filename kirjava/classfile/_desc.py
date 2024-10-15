#!/usr/bin/env python3

__all__ = (
    "parse_reference", "parse_field_descriptor", "parse_method_descriptor", "to_descriptor",
)

from ..model.types import (
    boolean_t, byte_t, char_t, double_t, float_t, int_t, long_t, short_t, void_t,
    Array, Class, Invalid, Reference, Type,
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
    Finds the enclosing arguments within provided start and end identifiers.
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


def _next_type(descriptor: str | None) -> tuple[Type, str]:
    """
    Gets the next type in a descriptor.
    """

    if not descriptor:  # or descriptor is None:
        return Invalid(""), ""
    elif descriptor[0] == "L":
        end = descriptor.find(";")
        if end >= 0:
            return Class(descriptor[1: end]), descriptor[end + 1:]
    elif descriptor[0] == "[":
        element_type, descriptor = _next_type(descriptor[1:])
        return Array(element_type), descriptor

    base_type = _FORWARD_BASE_TYPES.get(descriptor[0])
    if base_type is not None:
        return base_type, descriptor[1:]
    return Invalid(descriptor), ""


# ------------------------------ Public API ------------------------------ #

def parse_reference(descriptor: str) -> Reference:
    """
    Parses a reference type.

    Parameters
    ----------
    descriptor: str
        The descriptor to parse.

    Returns
    -------
    Reference
        The reference type.

    Raises
    ------
    ValueError
        If the descriptor is empty or contains trailing data.
    """

    if not descriptor:
        raise ValueError("reference descriptor is empty")

    if descriptor[0] == "L" and descriptor[-1] == ";":
        return Class(descriptor[1:-1])
    elif descriptor[0] == "[":
        element, trailing = _next_type(descriptor[1:])
        while trailing:
            if not isinstance(element, Array):
                raise ValueError(f"trailing data {trailing!r} in reference descriptor")
            element, trailing = _next_type(trailing)
        return Array(element)

    # TODO: May want to verify that the name is a qualified name.
    return Class(descriptor)


def parse_field_descriptor(descriptor: str) -> Type:
    """
    Parses a field descriptor.

    Parameters
    ----------
    descriptor: str
        The field descriptor.

    Returns
    -------
    Type
        The field type.

    Raises
    ------
    ValueError
        If either the descriptor is empty, contains trailing data or contains an
        invalid type.
    """

    if not descriptor:
        raise ValueError("field descriptor is empty")

    type_, remaining = _next_type(descriptor)
    if remaining:
        raise ValueError(f"trailing data {remaining!r} in descriptor")
    elif type_ is void_t or type(type_) is Invalid:
        raise ValueError(f"invalid type {type_!s} in descriptor")

    return type_


def parse_method_descriptor(descriptor: str) -> tuple[tuple[Type, ...], Type]:
    """
    Parses a method descriptor.

    Parameters
    ----------
    descriptor: str
        The method descriptor.

    Returns
    -------
    tuple[tuple[Type, ...], Type]
        The argument types and return type.

    Raises
    ------
    ValueError
        If either the descriptor is empty, contains leading and/or trailing data,
        has no argument types and/or contains an invalid type.
    """

    if not descriptor:
        raise ValueError("method descriptor is empty")

    # This is extra, but who cares :p, if it causes MAJOR issues I'll remove it later
    preceding, arguments_descriptor, remaining = _find_enclosing(descriptor, "(", ")")
    if preceding:
        raise ValueError(f"leading data {preceding!r} in method descriptor")

    argument_types = []
    while arguments_descriptor:  # If there are no (), arguments_descriptor should be None
        type_, arguments_descriptor = _next_type(arguments_descriptor)
        argument_types.append(type_)

    if arguments_descriptor is None:
        raise ValueError("no argument types in method descriptor")

    return_type, remaining = _next_type(remaining)
    if remaining:
        raise ValueError(f"trailing data {remaining!r} in method descriptor")

    for argument_type in argument_types:
        if argument_type is void_t or type(argument_type) is Invalid:
            raise ValueError(f"invalid argument type {argument_type!s} in method descriptor")
    if type(return_type) is Invalid:
        raise ValueError(f"invalid return type {return_type!s} in method descriptor")

    return tuple(argument_types), return_type


def to_descriptor(*types: tuple[Type, ...] | Type) -> str:
    """
    Creates a descriptor string from the provided types.

    Parameters
    ----------
    types: tuple[Type, ...] | Type
        The types.

    Returns
    -------
    str
        The descriptor string.
    """

    descriptor = ""

    for type_ in types:
        # This is done for performance, although mypy does complain. Might need a better solution in the future.
        base = _BACKWARD_BASE_TYPES.get(type_)  # type: ignore[call-overload]
        if base is not None:
            descriptor += base
        elif isinstance(type_, Class):
            descriptor += f"L{type_.name};"
        elif isinstance(type_, Array):
            descriptor += "[" + to_descriptor(type_.element)
        elif type(type_) is tuple:
            descriptor += f"({to_descriptor(*type_)})"
        elif isinstance(type_, Invalid):
            descriptor += type_.descriptor
        else:
            raise ValueError(f"invalid type {type_!s} in descriptor")

    return descriptor

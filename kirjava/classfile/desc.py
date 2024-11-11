#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "parse_reference", "parse_field_descriptor", "parse_method_descriptor", "to_descriptor",
)

from typing import Iterable

from ..backend import Err, Ok, Result
from ..model.types import (
    boolean_t, byte_t, char_t, double_t, float_t, int_t, long_t, short_t, void_t,
    Array, Class, Invalid, Primitive, Reference, Type,
)

_STR_TO_TYPE: dict[str, Primitive] = {
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
_TYPE_TO_STR: dict[Primitive, str] = {
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


def _find_enclosing(string: str, start_id: str, end_id: str) -> tuple[str | None, str | None, str]:
    """
    Finds the enclosing arguments within provided start and end identifiers.
    """

    end_index = string.find(end_id)
    if end_index < 0:
        return None, None, string
    start_index = string.find(start_id)
    offset = string.find(start_id, start_index + 1)

    while 0 < offset < end_index:  # Find the next start in the initial bound
        end_index = string.find(end_id, end_index + 1)
        if end_index < 0:  # No corresponding end identifier?
            return None, None, string
        offset = string.find(start_id, offset) + 1

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
        element, trailing = _next_type(descriptor[1:])
        if element is void_t:
            return Invalid(descriptor), ""
        return Array(element), trailing

    base_type = _STR_TO_TYPE.get(descriptor[0])
    if base_type is not None:
        return base_type, descriptor[1:]
    return Invalid(descriptor), ""


# ------------------------------ Public API ------------------------------ #

def parse_reference(descriptor: str, *, strict: bool = True) -> Result[Reference | Invalid]:
    """
    Parses a reference type descriptor.

    These may simply be class names, arrays or classes specified with `L;`.

    Parameters
    ----------
    descriptor: str
        The descriptor to parse.
    strict: bool
        Whether to return a value upon encountering an invalid type.

    Returns
    -------
    Result[Reference | Invalid]
        A result containing the reference type.
    """

    if not descriptor:
        return Err(ValueError("descriptor is empty"))

    if descriptor[0] == "L" and descriptor[-1] == ";":
        return Ok(Class(descriptor[1:-1]))
    elif descriptor[0] != "[":
        # TODO: May want to verify that the name is a qualified name.
        return Ok(Class(descriptor))

    with Result[Reference | Invalid]() as result:
        array, trailing = _next_type(descriptor)
        assert isinstance(array, (Array, Invalid)), "improperly parsed array type"

        if trailing:
            result.err(ValueError(f"trailing data {trailing!r} in descriptor"), reraise=strict)
        elif not isinstance(array, Array) or isinstance(array.lowest, Invalid):
            result.err(TypeError(f"invalid type {array!s} in descriptor"), reraise=strict)

        return result.ok(array)
    return result


def parse_field_descriptor(descriptor: str, *, strict: bool = True) -> Result[Type]:
    """
    Parses a field descriptor.

    Parameters
    ----------
    descriptor: str
        The descriptor to parse.
    strict: bool
        Whether to return a value upon encountering an invalid type.

    Returns
    -------
    Result[Type]
        The result containing the field type.
    """

    if not descriptor:
        return Err(ValueError("descriptor is empty"))

    with Result[Type]() as result:  # Guard against hard crashes from bugs, also recursion error is possible here.
        type, remaining = _next_type(descriptor)

        if remaining:
            result.err(ValueError(f"trailing data {remaining!r} in descriptor"), reraise=strict)
        if type is void_t or isinstance(type, Invalid):
            result.err(TypeError(f"invalid type {type!s} in descriptor"), reraise=strict)
        elif isinstance(type, Array) and isinstance(type.lowest, Invalid):
            result.err(TypeError(f"invalid type {type!s} in descriptor"), reraise=strict)

        return result.ok(type)
    return result


def parse_method_descriptor(descriptor: str, *, strict: bool = True) -> Result[tuple[tuple[Type, ...], Type]]:
    """
    Parses a method descriptor.

    Parameters
    ----------
    descriptor: str
        The descriptor to parse.
    strict: bool
        Whether to return a value upon encountering an invalid type.

    Returns
    -------
    Result[tuple[tuple[Type, ...], Type]]
        A result containing the argument types and return type.
        Note that void and invalid types could be present in the arguments. The
        return type may also be an invalid type.
    """

    if not descriptor:
        return Err(ValueError("descriptor is empty"))

    with Result[tuple[tuple[Type, ...], Type]]() as result:
        preceding, args_descriptor, remaining = _find_enclosing(descriptor, "(", ")")
        if preceding:
            result.err(ValueError(f"leading data {preceding!r} in descriptor"), reraise=strict)

        arg_types = []
        while args_descriptor:
            arg_type, args_descriptor = _next_type(args_descriptor)
            arg_types.append(arg_type)
            if arg_type is void_t or isinstance(arg_type, Invalid):
                result.err(TypeError(f"invalid argument type {arg_type!s} in descriptor"), reraise=strict)
            elif isinstance(arg_type, Array) and isinstance(arg_type.lowest, Invalid):
                result.err(TypeError(f"invalid argument type {arg_type!s} in descriptor"), reraise=strict)

        if args_descriptor is None:
            result.err(ValueError("no argument types in descriptor"), reraise=strict)

        ret_type, remaining = _next_type(remaining)
        if remaining:
            result.err(ValueError(f"trailing data {remaining!r} in descriptor"), reraise=strict)
        if isinstance(ret_type, Invalid):
            result.err(TypeError(f"invalid return type {ret_type!s} in descriptor"), reraise=strict)
        elif isinstance(ret_type, Array) and isinstance(ret_type.lowest, Invalid):
            result.err(TypeError(f"invalid return type {ret_type!s} in descriptor"), reraise=strict)

        return result.ok((tuple(arg_types), ret_type))
    return result


def to_descriptor(*types: Iterable[Type] | Type, strict: bool = True) -> Result[str]:
    """
    Creates a descriptor string from the provided types.

    Parameters
    ----------
    types: Iterable[Type] | Type
        The types to create a descriptor from.
    strict: bool
        Whether to return a value upon encountering an invalid type.
    """

    with Result[str]() as result:
        descriptor = ""

        for type in types:
            # This is done for performance, although mypy does complain. Might need a better solution in the future.
            base = _TYPE_TO_STR.get(type)  # type: ignore[call-overload]
            # FIXME: ^^^ will crash if type is unhashable. Could be encountered if lists are passed through, etc.
            if base is not None:
                descriptor += base
                continue
            elif isinstance(type, Class):
                descriptor += f"L{type.name};"
                continue
            elif isinstance(type, Array):
                descriptor += "[" + to_descriptor(type.element, strict=strict).unwrap_into(result)
                continue
            elif isinstance(type, Invalid):
                result.err(TypeError(f"invalid type {type!s} in descriptor"), reraise=strict)
                descriptor += type.descriptor
                continue

            try:
                descriptor += "(" + to_descriptor(*type, strict=strict).unwrap_into(result) + ")"  # type: ignore[misc]
            except TypeError:  # Hacky, yes, whatever.
                result.err(TypeError(f"invalid type {type!s} in descriptor"), reraise=strict)

        return result.ok(descriptor)
    return result

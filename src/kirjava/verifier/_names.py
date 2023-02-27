#!/usr/bin/env python3

"""
Verifies that class, method and field names are valid.
"""

from typing import List

from ..abc import Error


def check_binary_name(name: str, errors: List[Error]) -> None:
    """
    Checks that a binary name is valid.

    :param name: The binary name to verify.
    :param errors: The list of errors to add to.
    """

    for identifier in name.split("/"):
        if "." in identifier or ";" in identifier or "[" in identifier or "<" in identifier or ">" in identifier:
            break
    else:
        return  # No errors occurred

    errors.append(Error(-1, None, "invalid character(s) in binary name %r" % name))


def check_unqualified_name(name: str, errors: List[Error]) -> None:
    """
    Checks that an unqualified name is valid.

    :param name: The unqualified name to verify.
    :param errors: The list of errors to add to.
    """

    if "." in name or ";" in name or "[" in name or "/" in name:
        errors.append(Error(-1, None, "invalid character(s) in unqualified name %r" % name))
    elif "<" in name or ">" in name and not name in ("<init>", "<clinit>"):
        errors.append(Error(-1, None, "invalid character(s) in unqualified name %r" % name))


def check_module_or_package_name(name: str, errors: List[Error]) -> None:
    ...  # TODO

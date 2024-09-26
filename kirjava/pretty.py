#!/usr/bin/env python3

__all__ = (
    "pretty_repr",
)

"""
Pretty-ification of values.
"""

# Escaped special characters.
_SPECIAL = {
    "\a": "\\a",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\t": "\\t",
    "\v": "\\v",
}


# TODO: Something to limit lists of massive sizes.

def pretty_repr(name: str, max_len: int = 50) -> str:
    """
    Prettifies a string.

    When working with obfuscated classes with annoying names it's a lot easier if
    they're readable for debugging reasons.
    """

    for special in _SPECIAL:
        if special in name:
            name = name.replace(special, _SPECIAL[special])

    if len(name) >= max_len:
        name = name[:max_len - 3] + "..."

    name_ = ""
    for char in name:
        if 32 <= ord(char) < 127:
            name_ += char
        else:
            name_ += "-"

    return name_

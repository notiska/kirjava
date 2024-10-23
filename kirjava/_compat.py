#!/usr/bin/env python3

__all__ = (
    "replace",
    "Self",
)

import sys
from typing import TypeVar

T = TypeVar("T")

if sys.version_info >= (3, 13):
    from copy import replace
else:
    def replace(obj: T, /, **changes: object) -> T:
        try:
            return obj.__replace__(**changes)  # type: ignore[attr-defined,no-any-return]
        except AttributeError:
            raise TypeError(f"replace() does not support {type(obj)!r} objects")

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

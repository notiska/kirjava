#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Annotation",
)

import typing
from typing import Any, Mapping

if typing.TYPE_CHECKING:
    from .class_ import Class


class Annotation:
    """
    Information about a Java annotation.

    Attributes
    ----------
    class_: Class
        The annotation's class.
    visible: bool
        Whether this annotation is visible at runtime via reflection.
    values: dict[str, Any]
        The values declared for this annotation.
    """

    __slots__ = ("class_", "visible", "values")

    def __init__(self, class_: "Class", visible: bool = True, values: Mapping[str, Any] | None = None) -> None:
        self.class_ = class_
        self.visible = visible
        self.values: dict[str, Any] = {}  # FIXME: Narrow down the types.
        if values is not None:
            self.values.update(values)

    def __repr__(self) -> str:
        values_str = ", ".join(f"{name!r}={value!s}" for name, value in self.values.items())
        return f"<Annotation(class_={self.class_!s}, visible={self.visible}, values={{{values_str}}})>"

    def __str__(self) -> str:
        values_str = ", ".join(f"{name}={value!s}" for name, value in self.values.items())
        return f"@{self.class_.name}({values_str})"

    def __contains__(self, key: str) -> bool:
        return key in self.values

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.values[key] = value

    def __delitem__(self, key: str) -> None:
        del self.values[key]

    def __len__(self) -> int:
        return len(self.values)

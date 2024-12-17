#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Field",
)

import typing
from typing import Any, Generic, Optional

from ..._compat import TypeVar

if typing.TYPE_CHECKING:
    from ..annotation import Annotation
    from ..values import Constant
    from ..types import Type

T = TypeVar("T", default=Any)


class Field(Generic[T]):
    """
    A Java field model.

    Attributes
    ----------
    access: str
        A pretty access flag string.
    info: T | None
        The info that this field was generated from.
    name: str
        The name of the field.
    type: Type
        The type of the field.
    is_public: bool
        If the field is public.
    is_private: bool
        If the field is private.
    is_protected: bool
        If the field is protected.
    is_static: bool
        If the field is static.
    is_final: bool
        If the field is final.
    is_volatile: bool
        If the field is volatile.
    is_transient: bool
        If the field is transient.
    is_synthetic: bool
        If the field is synthetic.
    is_enum: bool
        If the field is an enum.
    documentation: bytes | None
        Any associated documentation for this field.
    synthetic: bool
        Whether this field is marked as synthetic (via an attribute).
        Not to be confused with `is_synthetic`, which is an access flag.
    deprecated: bool
        Whether this field is marked as deprecated.
    annotations: list[Annotation]
        Any annotations on this field.
    value: Constant | None
        If applicable, a constant value. Only stored with `static final` fields.
    """

    __slots__ = (
        "info",
        "name", "type",
        "is_public", "is_private", "is_protected", "is_static", "is_final",
        "is_volatile", "is_transient", "is_synthetic", "is_enum",
        "documentation", "synthetic", "deprecated", "annotations", "value",
    )

    @property
    def access(self) -> str:
        access = [
            "public" if self.is_public else None,
            "private" if self.is_private else None,
            "protected" if self.is_protected else None,
            "static" if self.is_static else None,
            "final" if self.is_final else None,
            "volatile" if self.is_volatile else None,
            "transient" if self.is_transient else None,
            "synthetic" if self.is_synthetic else None,
            "enum" if self.is_enum else None,
        ]
        return " ".join(filter(None, access))

    def __init__(
            self, name: str, type: "Type",
            *,
            is_public:    bool = False,
            is_private:   bool = False,
            is_protected: bool = False,
            is_static:    bool = False,
            is_final:     bool = False,
            is_volatile:  bool = False,
            is_transient: bool = False,
            is_synthetic: bool = False,
            is_enum:      bool = False,
    ) -> None:
        self.info: T | None = None

        self.name = name
        self.type = type

        self.is_public = is_public
        self.is_private = is_private
        self.is_protected = is_protected
        self.is_static = is_static
        self.is_final = is_final
        self.is_volatile = is_volatile
        self.is_transient = is_transient
        self.is_synthetic = is_synthetic
        self.is_enum = is_enum

        self.documentation: bytes | None = None
        self.synthetic = False
        self.deprecated = False
        self.annotations: list["Annotation"] = []
        self.value: Optional["Constant"] = None

    def __repr__(self) -> str:
        return f"<Field(name={self.name!r}, type={self.type!s})>"

    def __str__(self) -> str:
        return f"field({self.name!s}:{self.type!s})"

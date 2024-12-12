#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Method",
)

import typing
from typing import Any, Generic, Iterable

from ..._compat import TypeVar

if typing.TYPE_CHECKING:
    from . import Class
    from ..types import Type

T = TypeVar("T", default=Any)


class Method(Generic[T]):
    """
    A Java method model.

    Attributes
    ----------
    access: str
        A pretty access flag string.
    info: T | None
        The info that this method was generated from.
    name: str
        The name of the method.
    arg_types: tuple[Type, ...]
        The argument types of the method.
    ret_type: Type
        The return type of the method.
    is_public: bool
        If the method is public.
    is_private: bool
        If the method is private.
    is_protected: bool
        If the method is protected.
    is_static: bool
        If the method is static.
    is_final: bool
        If the method is final.
    is_synchronized: bool
        If the method is synchronized.
    is_bridge: bool
        If the method is a bridge.
    is_varargs: bool
        If the method is varargs.
    is_native: bool
        If the method is native.
    is_abstract: bool
        If the method is abstract.
    is_strictfp: bool
        If the method is strictfp.
    is_synthetic: bool
        If the method is synthetic.
    documentation: bytes | None
        Any associated documentation for this method.
    deprecated: bool
        Whether this method is marked as deprecated.
    parameters: list[Method.Parameter]
        A list of formal parameter information.
    throws: list[Class]
        A list of checked or unchecked exceptions that this method may throw.
    """

    __slots__ = (
        "info",
        "name", "arg_types", "ret_type",
        "is_public", "is_private", "is_protected", "is_static", "is_final", "is_synchronized",
        "is_bridge", "is_varargs", "is_native", "is_abstract", "is_strictfp", "is_synthetic",
        "documentation", "deprecated", "parameters", "throws",
    )

    @property
    def access(self) -> str:
        access = [
            "public" if self.is_public else None,
            "private" if self.is_private else None,
            "protected" if self.is_protected else None,
            "static" if self.is_static else None,
            "final" if self.is_final else None,
            "synchronized" if self.is_synchronized else None,
            "bridge" if self.is_bridge else None,
            "varargs" if self.is_varargs else None,
            "native" if self.is_native else None,
            "abstract" if self.is_abstract else None,
            "strictfp" if self.is_strictfp else None,
            "synthetic" if self.is_synthetic else None,
        ]
        return " ".join(filter(None, access))

    def __init__(
            self, name: str, arg_types: Iterable["Type"], ret_type: "Type",
            *,
            is_public:       bool = False,
            is_private:      bool = False,
            is_protected:    bool = False,
            is_static:       bool = False,
            is_final:        bool = False,
            is_synchronized: bool = False,
            is_bridge:       bool = False,
            is_varargs:      bool = False,
            is_native:       bool = False,
            is_abstract:     bool = False,
            is_strictfp:     bool = False,
            is_synthetic:    bool = False,
    ) -> None:
        self.info: T | None = None

        self.name = name
        self.arg_types = tuple(arg_types)
        self.ret_type = ret_type

        self.is_public = is_public
        self.is_private = is_private
        self.is_protected = is_protected
        self.is_static = is_static
        self.is_final = is_final
        self.is_synchronized = is_synchronized
        self.is_bridge = is_bridge
        self.is_varargs = is_varargs
        self.is_native = is_native
        self.is_abstract = is_abstract
        self.is_strictfp = is_strictfp
        self.is_synthetic = is_synthetic

        self.documentation: bytes | None = None
        self.deprecated = False
        self.parameters: list[Method.Parameter] = []
        self.throws: list["Class"] = []

    def __repr__(self) -> str:
        arg_types_str = ", ".join(map(str, self.arg_types))
        return f"<Method(name={self.name!r}, arg_types=[{arg_types_str}], ret_type={self.ret_type!s})>"

    def __str__(self) -> str:
        arg_types_str = ",".join(map(str, self.arg_types))
        return f"method({self.name!s}:({arg_types_str}){self.ret_type})"

    class Parameter:
        """
        Information about a formal method parameter.

        Attributes
        ----------
        index: int
            The index of the parameter.
        name: str | None
            The name of the parameter, as declared in the source code.
            If `None`, then no name exists in source code (AKA it is compiler-generated).
        is_final: bool
            If the parameter is final.
        is_synthetic: bool
            If the parameter is synthetic.
        is_mandated: bool
            If the parameter is mandated, meaing it was implicitly declared in the
            source code.
        """

        __slots__ = ("index", "name", "is_final", "is_synthetic", "is_mandated")

        def __init__(
                self, index: int, name: str | None,
                *,
                is_final:     bool = False,
                is_synthetic: bool = False,
                is_mandated:  bool = False,
        ) -> None:
            self.index = index
            self.name = name
            self.is_final = is_final
            self.is_synthetic = is_synthetic
            self.is_mandated = is_mandated

        def __repr__(self) -> str:
            return f"<Method.Paramter(index={self.index}, name={self.name!r})>"

        def __str__(self) -> str:
            if self.name is not None:
                return f"parameter({self.index}:{self.name!s})"
            return f"parameter({self.index})"

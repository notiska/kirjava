#!/usr/bin/env python3

__all__ = (
    "Method",
)

import typing

from ...pretty import pretty_repr

if typing.TYPE_CHECKING:
    from ..types import Type


class Method:
    """
    A Java method model.

    Attributes
    ----------
    access: str
        A pretty access flag string.
    name: str
        The name of the method.
    arguments: tuple[Type, ...]
        The argument types of the method.
    return_: Type
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
    """

    __slots__ = (
        "name", "arguments", "return_",
        "is_public", "is_private", "is_protected", "is_static", "is_final", "is_synchronized",
        "is_bridge", "is_varargs", "is_native", "is_abstract", "is_strictfp", "is_synthetic",
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
            self,
            name: str, arguments: tuple["Type", ...], return_: "Type",
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
        self.name = name
        self.arguments = arguments
        self.return_ = return_

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

    def __repr__(self) -> str:
        return "<Method(name=%r, arguments=%r, return_=%r)>" % (pretty_repr(self.name), self.arguments, self.return_)

    def __str__(self) -> str:
        return "%s %s %s(%s)" % (self.access, self.return_, pretty_repr(self.name), ", ".join(map(str, self.arguments)))
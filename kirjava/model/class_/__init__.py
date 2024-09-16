#!/usr/bin/env python3

__all__ = (
    "field", "method",
    "Class",
)

import typing

from ..types import Class as ClassType, Interface
from ...pretty import pretty_repr

if typing.TYPE_CHECKING:
    from .field import Field
    from .method import Method


class Class:
    """
    A Java class model.

    Attributes
    ----------
    access: str
        A pretty access flag string.
    name: str
        The internal name of the class (e.g. `java/lang/Object`).
    is_public: bool
        If the class is public.
    is_final: bool
        If the class is final.
    is_super: bool
        If the class is has a super class.
    is_interface: bool
        If the class is an interface.
    is_abstract: bool
        If the class is abstract.
    is_synthetic: bool
        If the class is synthetic.
    is_annotation: bool
        If the class is an annotation.
    is_enum: bool
        If the class is an enum.
    is_module: bool
        If the class is a module.

    Methods
    -------
    as_ctype(self) -> ClassType
        Gets the class type that this class represents.
    """

    __slots__ = (
        "name",
        "is_public", "is_final", "is_super", "is_interface", "is_abstract",
        "is_synthetic", "is_annotation", "is_enum", "is_module",
        "fields", "methods",
    )

    @property
    def access(self) -> str:
        access = [
            "public" if self.is_public else None,
            "final" if self.is_final else None,
            "super" if self.is_super else None,
            "interface" if self.is_interface else None,
            "abstract" if self.is_abstract else None,
            "synthetic" if self.is_synthetic else None,
            "annotation" if self.is_annotation else None,
            "enum" if self.is_enum else None,
            "module" if self.is_module else None,
        ]
        return " ".join(filter(None, access))

    def __init__(
            self,
            name: str,
            fields:   list["Field"] | None = None,
            methods: list["Method"] | None = None,
            *,
            is_public:     bool = True,
            is_final:      bool = False,
            is_super:      bool = False,
            is_interface:  bool = False,
            is_abstract:   bool = False,
            is_synthetic:  bool = False,
            is_annotation: bool = False,
            is_enum:       bool = False,
            is_module:     bool = False,
    ) -> None:
        self.name = name

        self.is_public = is_public
        self.is_final = is_final
        self.is_super = is_super
        self.is_interface = is_interface
        self.is_abstract = is_abstract
        self.is_synthetic = is_synthetic
        self.is_annotation = is_annotation
        self.is_enum = is_enum
        self.is_module = is_module

        self.fields = []
        self.methods = []

        if fields is not None:
            self.fields.extend(fields)
        if methods is not None:
            self.methods.extend(methods)

    def __repr__(self) -> str:
        return "<Class(name=%r)>" % self.name

    def __str__(self) -> str:
        return "%s class %s" % (self.access, pretty_repr(self.name))

    def as_ctype(self) -> ClassType:
        """
        Gets the class type that this class represents.

        Returns
        -------
        ClassType
            The representative class type.
        """

        if self.is_interface:
            return Interface(self.name)
        return ClassType(self.name)

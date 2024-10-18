#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "field", "method",
    "Class", "Field", "Method",
)

from typing import Iterable, Optional

from .field import Field
from .method import Method
from ..types import Class as ClassType, Interface, Type


class Class:
    """
    A Java class model.

    Attributes
    ----------
    access: str
        A pretty access flag string.
    name: str
        The internal name of the class (e.g. `java/lang/Object`).
    super: Class | None
        The direct superclass of this class.
    interfaces: list[Class]
        The interfaces that this class implements.
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
    fields: list[Field]
        The fields in this class.
    methods: list[Method]
        The methods in this class.

    Methods
    -------
    get_field(self, name: str, type_: Type) -> Field | None
        Gets a field in this class by its name and type.
    get_method(self, name: str, arg_types: tuple[Type, ...], ret_type: Type) -> Method | None
        Gets a method in this class by its name, argument types and return type
    as_type(self) -> ClassType
        Returns the type representation of this class.
    """

    __slots__ = (
        "name",
        "is_public", "is_final", "is_super", "is_interface", "is_abstract",
        "is_synthetic", "is_annotation", "is_enum", "is_module",
        "super", "interfaces",
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
            super_: Optional["Class"] = None,
            interfaces: Iterable["Class"] | None = None,
            fields:     Iterable["Field"] | None = None,
            methods:   Iterable["Method"] | None = None,
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

        self.super = super_
        self.interfaces: list[Class] = []
        self.fields:     list[Field] = []
        self.methods:   list[Method] = []

        if interfaces is not None:
            self.interfaces.extend(interfaces)
        if fields is not None:
            self.fields.extend(fields)
        if methods is not None:
            self.methods.extend(methods)

    def __repr__(self) -> str:
        interfaces_str = ", ".join(map(str, self.interfaces))
        return (
            f"<Class(name={self.name!r}, super={self.super!s}, interfaces=[{interfaces_str}], fields={self.fields!r}, "
            f"methods={self.methods!r})>"
        )

    def __str__(self) -> str:
        interfaces_str = ",".join(map(str, self.interfaces))
        fields_str = ",".join(map(str, self.fields))
        methods_str = ",".join(map(str, self.methods))
        return f"class({self.name!s},{self.super!s},[{interfaces_str}],[{fields_str}],[{methods_str}])"

    def get_field(self, name: str, type_: Type) -> Field | None:
        """
        Gets a field in this class by its name and type.

        Parameters
        ----------
        name: str
            The name of the field.
        type_: Type
            The type of the field.

        Returns
        -------
        Field | None
            The field, or `None` if not found.
        """

        for field in self.fields:
            if field.name == name and field.type == type_:
                return field
        return None

    def get_method(self, name: str, arg_types: tuple[Type, ...], ret_type: Type) -> Method | None:
        """
        Gets a method in this class by its name, argument types and return type.

        Parameters
        ----------
        name: str
            The name of the method.
        arg_types: tuple[Type, ...]
            The argument types of the method.
        ret_type: Type
            The return type of the method.

        Returns
        -------
        Method | None
            The method, or `None` if not found.
        """

        for method in self.methods:
            if method.name == name and method.arg_types == arg_types and method.ret_type == ret_type:
                return method
        return None

    def as_type(self) -> ClassType:
        """
        Returns the type representation of this class.
        """

        if self.is_interface:
            return Interface(self.name)
        return ClassType(self.name)

#!/usr/bin/env python3

__all__ = (
    "Class",
)

"""
Class abstraction.
"""

import typing
from typing import Iterable, Optional, Union

from .. import environment
from ..types import Class as ClassType, Interface

if typing.TYPE_CHECKING:
    from .field import Field
    from .method import Method
    from .._argument import FieldDescriptor, MethodDescriptor
    from ..environment import Environment


class Class:
    """
    An abstract representation of a Java class.
    """

    __slots__ = ("__weakref__", "environment")

    is_public: bool
    is_final: bool
    is_super: bool
    is_interface: bool
    is_abstract: bool
    is_synthetic: bool
    is_annotation: bool
    is_enum: bool
    is_module: bool

    name: str

    super: Optional["Class"]  # TODO: Any way to do "Class" | None?
    super_name: str | None

    interfaces: tuple["Class", ...]
    interface_names: tuple[str, ...]

    fields: tuple["Field", ...]
    methods: tuple["Method", ...]

    def __init__(self, environment: Optional["Environment"] = environment.DEFAULT) -> None:
        """
        :param environment: The environment that this class belongs to.
        """

        self.environment = environment
        if environment is not None:
            # We'll assume it's a weak reference by default. If this isn't the case, the user can re-register the class
            # as a strong reference.
            environment.register_class(self, weak=True)

    def get_method(self, name: str, *descriptor: "MethodDescriptor") -> "Method":
        """
        Gets a method in this class.

        :param name: The name of the method.
        :param descriptor: The descriptor of the method, if not given, the first method with the name is returned.
        :return: The method.
        """

        ...

    def has_method(self, name: str, *descriptor: "MethodDescriptor") -> bool:
        """
        Checks if this class has a method with the given name and descriptor.

        :param name: The name of the method.
        :param descriptor: The descriptor of the method.
        :return: Does any method with the given name and/or descriptor exist?
        """

        ...

    def add_method(self, name: str, *descriptor: "MethodDescriptor", **access_flags: bool) -> "Method":
        """
        Adds a method to this class given the provided information about it.

        :param name: The name of the method.
        :param descriptor: The descriptor of the method.
        :param access_flags: Any access flags to have on the method.
        :return: The method that was created.
        """

        ...

    def remove_method(self, name_or_method: Union[str, "Method"], *descriptor: "MethodDescriptor") -> "Method":
        """
        Removes a method from this class.

        :param name_or_method: The name of the method, or the method.
        :param descriptor: The descriptor of the method.
        :return: The method that was removed.
        """

        ...

    def get_field(self, name: str, descriptor: Optional["FieldDescriptor"] = None) -> "Field":
        """
        Gets a field in this class.

        :param name: The name of the field.
        :param descriptor: The descriptor of the field, if None, the first field with the name is returned.
        :return: The field.
        """

        ...

    def has_field(self, name: str, descriptor: Optional["FieldDescriptor"] = None) -> bool:
        """
        Checks if this class has a field with the given name and descriptor.

        :param name: The name of the field.
        :param descriptor: The descriptor of the field.
        :return: Does any field with the given name and/or descriptor exist?
        """

        ...

    def add_field(
            self, name: str, descriptor: Optional["FieldDescriptor"] = None, **access_flags: bool,
    ) -> "Field":
        """
        Adds a field to this class.

        :param name: The name of the field to add.
        :param descriptor: The descriptor of the field to add.
        :param access_flags: Any access flags to have on the field.
        :return: The field that was added.
        """

        ...

    def remove_field(self, name_or_field: Union[str, "Field"], descriptor: Optional["FieldDescriptor"] = None) -> "Field":
        """
        Removes a field from this class.

        :param name_or_field: The name of the field or the field.
        :param descriptor: The descriptor of the field.
        :return: The field that was removed.
        """

        ...

    def get_type(self) -> ClassType | Interface:
        """
        :return: The type representation of this class.
        """

        if self.is_interface:
            return Interface(self.name)
        return ClassType(self.name)

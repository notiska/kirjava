#!/usr/bin/env python3

__all__ = (
    "BootstrapMethods", "NestHost", "NestMembers", "PermittedSubclasses", "InnerClasses", "EnclosingMethod",
    "Record", "SourceFile",
)

"""
Attributes found exclusively in the ClassFile structure.
"""

import typing
from typing import Any, IO, Iterable

from . import AttributeInfo
from .. import attributes
from ..._struct import *
from ...constants import ConstantInfo, Class, MethodHandle, NameAndType, UTF8
from ...version import Version

if typing.TYPE_CHECKING:
    from .. import ClassFile


class BootstrapMethods(AttributeInfo):
    """
    Records bootstrap methods used to produce dynamically computed constants and callsites.
    """

    __slots__ = ("methods",)

    name_ = "BootstrapMethods"
    since = Version(51, 0)
    locations = ("ClassFile",)

    def __init__(self, parent: "ClassFile") -> None:
        super().__init__(parent, BootstrapMethods.name_)

        self.methods: list[BootstrapMethods.BootstrapMethod] = []

    def __repr__(self) -> str:
        return "<BootstrapMethods(methods=%r) at %x>" % (self.methods, id(self))

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.methods.clear()
        bootstrap_methods_count, = unpack_H(buffer.read(2))
        for index in range(bootstrap_methods_count):
            self.methods.append(BootstrapMethods.BootstrapMethod.read(class_file, buffer))

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(len(self.methods)))
        for bootstrap_method in self.methods:
            bootstrap_method.write(class_file, buffer)

    class BootstrapMethod:
        """
        Information about a bootstrap method, including the method handle and the bootstrap arguments.
        """

        __slots__ = ("method_handle", "arguments")

        @classmethod
        def read(cls, class_file: "ClassFile", buffer: IO[bytes]) -> "BootstrapMethods.BootstrapMethod":
            """
            Reads a bootstrap method info from the buffer.

            :param class_file: The class file the bootstrap method belongs to.
            :param buffer: The buffer to read from.
            :return: The read bootstrap method info.
            """

            bootstrap_method = cls.__new__(cls)

            bootstrap_method_index, = unpack_H(buffer.read(2))
            bootstrap_method.method_handle = class_file.constant_pool[bootstrap_method_index]

            bootstrap_method.arguments = []
            bootstrap_arguments_count, = unpack_H(buffer.read(2))
            for index in range(bootstrap_arguments_count):
                bootstrap_argument_index, = unpack_H(buffer.read(2))
                bootstrap_method.arguments.append(class_file.constant_pool[bootstrap_argument_index])

            return bootstrap_method

        def __init__(self, method_handle: MethodHandle, arguments: Iterable[ConstantInfo] | None = None) -> None:
            """
            :param method_handle: The method handle for this bootstrap method.
            :param arguments: The bootstrap arguments used to resolve the call site.
            """

            self.method_handle = method_handle
            self.arguments: list[ConstantInfo] = []

            if arguments is not None:
                self.arguments.extend(arguments)

        def __repr__(self) -> str:
            return "<BootstrapMethod(handle=%r, arguments=%r) at %x>" % (self.method_handle, self.arguments, id(self))

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            """
            Writes this bootstrap method info to a buffer.

            :param class_file: The class file that this bootstrap method info belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(pack_HH(class_file.constant_pool.add(self.method_handle), len(self.arguments)))
            for bootstrap_argument in self.arguments:
                buffer.write(pack_H(class_file.constant_pool.add(bootstrap_argument)))


class NestHost(AttributeInfo):
    """
    Records the host of the nest that this class/interface belongs to.
    """

    __slots__ = ("host_class",)

    name_ = "NestHost"
    since = Version(55, 0)
    locations = ("ClassFile",)
    
    def __init__(self, parent: "ClassFile", host_class: Class | None = None) -> None:
        """
        :param host_class: The host class of the nest that this class/interface belongs to.
        """

        super().__init__(parent, NestHost.name_)

        self.host_class = host_class

    def __repr__(self) -> str:
        return "<NestHost(host=%r) at %x>" % (self.host_class, id(self))
        
    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        host_class_index, = unpack_H(buffer.read(2))
        self.host_class = class_file.constant_pool[host_class_index]

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add(self.host_class)))


class NestMembers(AttributeInfo):
    """
    Records the classes/interfaces that belong to the nest that this class hosts.
    """

    __slots__ = ("classes",)

    name_ = "NestMembers"
    since = Version(55, 0)
    locations = ("ClassFile",)

    def __init__(self, parent: "ClassFile", classes: Iterable[Class] | None = None) -> None:
        """
        :param classes: The classes/interfaces that belong to the nest that this class hosts.
        """

        super().__init__(parent, NestMembers.name_)

        self.classes: list[Class] = []
        if classes is not None:
            self.classes.extend(classes)

    def __repr__(self) -> str:
        return "<NestMembers(classes=%r) at %x>" % (self.classes, id(self))

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.classes.clear()
        classes_count, = unpack_H(buffer.read(2))
        for index in range(classes_count):
            class_index, = unpack_H(buffer.read(2))
            self.classes.append(class_file.constant_pool[class_index])

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(len(self.classes)))
        for class_ in self.classes:
            buffer.write(pack_H(class_file.constant_pool.add(class_)))


class PermittedSubclasses(AttributeInfo):
    """
    Records classes/interfaces that are allowed to directly extend/implement this class/interface.
    """

    __slots__ = ("classes",)

    name_ = "PermittedSubclasses"
    since = Version(61, 0)
    locations = ("ClassFile",)

    def __init__(self, parent: "ClassFile", classes: Iterable[Class] | None = None) -> None:
        """
        :param classes: The list of permitted subclasses.
        """

        super().__init__(parent, PermittedSubclasses.name_)

        self.classes: list[Class] = []
        if classes is not None:
            self.classes.extend(classes)

    def __repr__(self) -> str:
        return "<PermittedSubclasses(classes=%r) at %x>" % (self.classes, id(self))

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.classes.clear()
        classes_count, = unpack_H(buffer.read(2))
        for index in range(classes_count):
            class_index, = unpack_H(buffer.read(2))
            self.classes.append(class_file.constant_pool[class_index])

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(len(self.classes)))
        for class_ in self.classes:
            buffer.write(pack_H(class_file.constant_pool.add(class_)))


class InnerClasses(AttributeInfo):
    """
    Contains information about inner classes (could be inner classes inside this class, or saying that this class is
    an inner class).
    """

    __slots__ = ("classes",)

    name_ = "InnerClasses"
    since = Version(45, 0)
    locations = ("ClassFile",)

    def __init__(self, parent: "ClassFile", classes: Iterable["InnerClasses.InnerClass"] | None = None) -> None:
        """
        :param classes: Information about inner classes.
        """

        super().__init__(parent, InnerClasses.name_)

        self.classes: list[InnerClasses.InnerClass] = []
        if classes is not None:
            self.classes.extend(classes)

    def __repr__(self) -> str:
        return "<InnerClasses(classes=%r) at %x>" % (self.classes, id(self))

    def __iter__(self) -> Iterable["InnerClasses.InnerClass"]:
        return iter(self.classes)

    def __getitem__(self, index: int) -> "InnerClasses.InnerClass":
        return self.classes[index]

    def __setitem__(self, index: int, value: "InnerClasses.InnerClass") -> None:
        self.classes[index] = value

    def __len__(self) -> int:
        return len(self.classes)

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.classes.clear()
        classes_count, = unpack_H(buffer.read(2))
        for index in range(classes_count):
            self.classes.append(InnerClasses.InnerClass.read(class_file, buffer, fail_fast))

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(len(self.classes)))
        for inner_class in self.classes:
            inner_class.write(class_file, buffer)

    class InnerClass:
        """
        Information about an inner class.
        """

        __slots__ = ("inner_class", "outer_class", "inner_name", "access_flags")

        @classmethod
        def read(cls, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool) -> "InnerClasses.InnerClass":
            """
            Reads an inner class info from the buffer.

            :param class_file: The class file that the inner class info belongs to.
            :param buffer: The binary buffer to read from.
            :param fail_fast: Throws an exception if it's obvious this inner class info is invalid.
            :return: The read inner class.
            """

            inner_class = cls.__new__(cls)

            (
                inner_class_index,
                outer_class_index,
                inner_class_name_index,
                inner_class.access_flags,
            ) = unpack_HHHH(buffer.read(8))

            inner_class.inner_class = class_file.constant_pool.get(inner_class_index, do_raise=fail_fast)
            inner_class.outer_class = (
                class_file.constant_pool.get(outer_class_index, do_raise=fail_fast) if outer_class_index else None
            )
            inner_class.inner_name = (
                class_file.constant_pool.get(inner_class_name_index, do_raise=fail_fast)
                if inner_class_name_index else None
            )

            return inner_class

        ACC_PUBLIC = 0x0001
        ACC_PRIVATE = 0x0002
        ACC_PROTECTED = 0x0004
        ACC_STATIC = 0x0008
        ACC_FINAL = 0x0010
        ACC_INTERFACE = 0x0200
        ACC_ABSTRACT = 0x0400
        ACC_SYNTHETIC = 0x1000
        ACC_ANNOTATION = 0x2000
        ACC_ENUM = 0x4000

        @property
        def is_public(self) -> bool:
            return bool(self.access_flags & InnerClasses.InnerClass.ACC_PUBLIC)

        @is_public.setter
        def is_public(self, value: bool) -> None:
            if value:
                self.access_flags |= InnerClasses.InnerClass.ACC_PUBLIC
            else:
                self.access_flags &= ~InnerClasses.InnerClass.ACC_PUBLIC

        @property
        def is_private(self) -> bool:
            return bool(self.access_flags & InnerClasses.InnerClass.ACC_PRIVATE)

        @is_private.setter
        def is_private(self, value: bool) -> None:
            if value:
                self.access_flags |= InnerClasses.InnerClass.ACC_PRIVATE
            else:
                self.access_flags &= ~InnerClasses.InnerClass.ACC_PRIVATE

        @property
        def is_protected(self) -> bool:
            return bool(self.access_flags & InnerClasses.InnerClass.ACC_PROTECTED)

        @is_protected.setter
        def is_protected(self, value: bool) -> None:
            if value:
                self.access_flags |= InnerClasses.InnerClass.ACC_PROTECTED
            else:
                self.access_flags &= ~InnerClasses.InnerClass.ACC_PROTECTED

        @property
        def is_static(self) -> bool:
            return bool(self.access_flags & InnerClasses.InnerClass.ACC_STATIC)

        @is_static.setter
        def is_static(self, value: bool) -> None:
            if value:
                self.access_flags |= InnerClasses.InnerClass.ACC_STATIC
            else:
                self.access_flags &= ~InnerClasses.InnerClass.ACC_STATIC

        @property
        def is_final(self) -> bool:
            return bool(self.access_flags & InnerClasses.InnerClass.ACC_FINAL)

        @is_final.setter
        def is_final(self, value: bool) -> None:
            if value:
                self.access_flags |= InnerClasses.InnerClass.ACC_FINAL
            else:
                self.access_flags &= ~InnerClasses.InnerClass.ACC_FINAL

        @property
        def is_interface(self) -> bool:
            return bool(self.access_flags & InnerClasses.InnerClass.ACC_INTERFACE)

        @is_interface.setter
        def is_interface(self, value: bool) -> None:
            if value:
                self.access_flags |= InnerClasses.InnerClass.ACC_INTERFACE
            else:
                self.access_flags &= ~InnerClasses.InnerClass.ACC_INTERFACE

        @property
        def is_abstract(self) -> bool:
            return bool(self.access_flags & InnerClasses.InnerClass.ACC_ABSTRACT)

        @is_abstract.setter
        def is_abstract(self, value: bool) -> None:
            if value:
                self.access_flags |= InnerClasses.InnerClass.ACC_ABSTRACT
            else:
                self.access_flags &= ~InnerClasses.InnerClass.ACC_ABSTRACT

        @property
        def is_synthetic(self) -> bool:
            return bool(self.access_flags & InnerClasses.InnerClass.ACC_SYNTHETIC)

        @is_synthetic.setter
        def is_synthetic(self, value: bool) -> None:
            if value:
                self.access_flags |= InnerClasses.InnerClass.ACC_SYNTHETIC
            else:
                self.access_flags &= ~InnerClasses.InnerClass.ACC_SYNTHETIC

        @property
        def is_annotation(self) -> bool:
            return bool(self.access_flags & InnerClasses.InnerClass.ACC_ANNOTATION)

        @is_annotation.setter
        def is_annotation(self, value: bool) -> None:
            if value:
                self.access_flags |= InnerClasses.InnerClass.ACC_ANNOTATION
            else:
                self.access_flags &= ~InnerClasses.InnerClass.ACC_ANNOTATION

        @property
        def is_enum(self) -> bool:
            return bool(self.access_flags & InnerClasses.InnerClass.ACC_ENUM)

        @is_enum.setter
        def is_enum(self, value: bool) -> None:
            if value:
                self.access_flags |= InnerClasses.InnerClass.ACC_ENUM
            else:
                self.access_flags &= ~InnerClasses.InnerClass.ACC_ENUM

        def __init__(
                self,
                inner_class: Class,
                outer_class: Class | None,
                inner_name: UTF8 | None,
                *,
                is_public: bool = False,
                is_private: bool = False,
                is_protected: bool = False,
                is_static: bool = False,
                is_final: bool = False,
                is_interface: bool = False,
                is_abstract: bool = False,
                is_synthetic: bool = False,
                is_annotation: bool = False,
                is_enum: bool = False,
        ) -> None:
            self.inner_class = inner_class
            self.outer_class = outer_class
            self.inner_name = inner_name

            self.access_flags = 0

            self.is_public = is_public
            self.is_private = is_private
            self.is_protected = is_protected
            self.is_static = is_static
            self.is_final = is_final
            self.is_interface = is_interface
            self.is_abstract = is_abstract
            self.is_synthetic = is_synthetic
            self.is_annotation = is_annotation
            self.is_enum = is_enum

        def __repr__(self) -> str:
            return "<InnerClass(inner=%r, outer=%r, inner_name=%r) at %x>" % (
                self.inner_class, self.outer_class, self.inner_name, id(self),
            )

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            """
            Writes this inner class info to an output buffer.

            :param class_file: The class file that this inner class belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(pack_HHHH(
                class_file.constant_pool.add(self.inner_class),
                0 if self.outer_class is None else class_file.constant_pool.add(self.outer_class),
                0 if self.inner_name is None else class_file.constant_pool.add(self.inner_name),
                self.access_flags,
            ))


class EnclosingMethod(AttributeInfo):
    """
    Used to denote that a class is a local or anonymous class.
    """

    __slots__ = ("class_", "method")

    name_ = "EnclosingMethod"
    since = Version(49, 0)
    locations = ("ClassFile",)

    def __init__(self, parent: "ClassFile", class_: Class | None = None, method: NameAndType | None = None) -> None:
        """
        :param class_: The class enclosing this class.
        :param method: The method enclosing this class, if any.
        """

        super().__init__(parent, EnclosingMethod.name_)

        self.class_ = class_
        self.method = method

    def __repr__(self) -> str:
        return "<EnclosingMethod(class=%r, method=%r) at %x>" % (self.class_, self.method, id(self))

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        class_index, method_index = unpack_HH(buffer.read(4))
        # No type information? Thanks Iska, really helpful!
        self.class_ = class_file.constant_pool[class_index]
        self.method = class_file.constant_pool[method_index] if method_index else None

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_HH(
            class_file.constant_pool.add(self.class_),
            0 if self.method is None else class_file.constant_pool.add(self.method),
        ))


class Record(AttributeInfo):
    """
    Indicates that the current class is a record, and stores information about the components of the record.
    """

    __slots__ = ("components",)

    name_ = "Record"
    since = Version(60, 0)
    locations = ("ClassFile",)

    def __init__(self, parent: "ClassFile", components: Iterable["Record.ComponentInfo"] | None = None) -> None:
        """
        :param components: The components of the record.
        """

        super().__init__(parent, Record.name_)

        self.components: list[Record.ComponentInfo] = []
        if components is not None:
            self.components.extend(components)

    def __repr__(self) -> str:
        return "<Record(components=%r) at %x>" % (self.components, id(self))

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        self.components.clear()
        components_count, = unpack_H(buffer.read(2))
        for index in range(components_count):
            self.components.append(Record.ComponentInfo.read(class_file, buffer, fail_fast))

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(len(self.components)))
        for component in self.components:
            component.write(class_file, buffer)

    class ComponentInfo:
        """
        Information about a component in a record.
        """

        __slots__ = ("__weakref__", "name", "descriptor", "attributes")

        @classmethod
        def read(cls, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool) -> "Record.ComponentInfo":
            """
            Reads a single component info from a buffer.

            :param class_file: The class file that the component info belongs to.
            :param buffer: The binary buffer to read from.
            :param fail_fast: Throws an exception if it's obvious that this record component info is invalid.
            :return: The read component info.
            """

            component_info = cls.__new__(cls)

            name_index, descriptor_index, attributes_count = unpack_HHH(buffer.read(6))

            component_info.name = class_file.constant_pool.get(name_index, do_raise=fail_fast)
            component_info.descriptor = class_file.constant_pool.get(descriptor_index, do_raise=fail_fast)

            component_info.attributes = {}
            for index in range(attributes_count):
                attribute_info = attributes.read_attribute(component_info, class_file, buffer, fail_fast)
                component_info.attributes[attribute_info.name] = (
                    component_info.attributes.setdefault(attribute_info.name, ()) + (attribute_info,)
                )

            return component_info

        def __init__(self, name: UTF8, descriptor: UTF8) -> None:
            self.name = name
            self.descriptor = descriptor

            self.attributes: dict[str, tuple[AttributeInfo, ...]] = {}

        def __repr__(self) -> str:
            return "<ComponentInfo(name=%r, descriptor=%r) at %x>" % (self.name, self.descriptor, id(self))

        def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
            """
            Writes this component info to an output buffer.

            :param class_file: The class file that this component info belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(pack_HH(
                class_file.constant_pool.add(self.name),
                class_file.constant_pool.add(self.descriptor),
            ))

            attributes_ = []
            for attributes__ in self.attributes.values():
                attributes_.extend(attributes__)

            buffer.write(pack_H(len(attributes_)))
            for attribute in attributes_:
                attributes.write_attribute(attribute, class_file, buffer)


class SourceFile(AttributeInfo):
    """
    The name of the source file that this class was compiled from.
    """

    __slots__ = ("source_file",)

    name_ = "SourceFile"
    since = Version(45, 0)
    locations = ("ClassFile",)

    def __init__(self, parent: "ClassFile", source_file: UTF8 | None = None) -> None:
        """
        :param source_file: The name of the source file that generated the class.
        """

        super().__init__(parent, SourceFile.name_)

        self.source_file = source_file

    def __repr__(self) -> str:
        return "<SourceFile(source_file=%r) at %x>" % (self.source_file, id(self))

    def __eq__(self, other: Any) -> bool:
        return type(other) is SourceFile and other.source_file == self.source_file

    def read(self, class_file: "ClassFile", buffer: IO[bytes], fail_fast: bool = True) -> None:
        source_file_index, = unpack_H(buffer.read(2))
        self.source_file = class_file.constant_pool[source_file_index]

    def write(self, class_file: "ClassFile", buffer: IO[bytes]) -> None:
        buffer.write(pack_H(class_file.constant_pool.add(self.source_file)))

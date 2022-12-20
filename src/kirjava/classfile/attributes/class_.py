#!/usr/bin/env python3

__all__ = (
    "BootstrapMethods", "NestHost", "NestMembers", "PermittedSubclasses", "InnerClasses", "EnclosingMethod",
    "Record", "SourceFile",
)

"""
Attributes found exclusively in the ClassFile structure.
"""

import struct
from typing import Dict, IO, List, Union

from . import AttributeInfo
from .. import attributes, ClassFile
from ..constants import Constant, Class
from ...version import Version


class BootstrapMethods(AttributeInfo):
    """
    Records bootstrap methods used to produce dynamically computed constants and callsites.
    """

    __slots__ = ("methods",)

    name_ = "BootstrapMethods"
    since = Version(51, 0)
    locations = (ClassFile,)

    def __init__(self, parent: ClassFile) -> None:
        super().__init__(parent, BootstrapMethods.name_)

        self.methods: List[BootstrapMethods.BootstrapMethod] = []

    def __repr__(self) -> str:
        return "<BootstrapMethods(methods=%r) at %x>" % (self.methods, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        self.methods.clear()
        bootstrap_methods_count, = struct.unpack(">H", buffer.read(2))
        for index in range(bootstrap_methods_count):
            self.methods.append(BootstrapMethods.BootstrapMethod.read(class_file, buffer))

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", len(self.methods)))
        for bootstrap_method in self.methods:
            bootstrap_method.write(class_file, buffer)

    class BootstrapMethod:
        """
        Information about a bootstrap method, including the method handle and the bootstrap arguments.
        """

        __slots__ = ("method_handle", "arguments")

        @classmethod
        def read(cls, class_file: ClassFile, buffer: IO[bytes]) -> "BootstrapMethods.BootstrapMethod":
            """
            Reads a bootstrap method info from the buffer.

            :param class_file: The class file the bootstrap method belongs to.
            :param buffer: The buffer to read from.
            :return: The read bootstrap method info.
            """

            bootstrap_method = cls()

            bootstrap_method_index, = struct.unpack(">H", buffer.read(2))
            bootstrap_method.method_handle = class_file.constant_pool[bootstrap_method_index]

            bootstrap_arguments_count, = struct.unpack(">H", buffer.read(2))
            for index in range(bootstrap_arguments_count):
                bootstrap_argument_index, = struct.unpack(">H", buffer.read(2))
                bootstrap_method.arguments.append(class_file.constant_pool[bootstrap_argument_index])

            return bootstrap_method

        def __init__(self) -> None:  # TODO: Constructor
            self.arguments: List[Constant] = []

        def __repr__(self) -> str:
            return "<BootstrapMethod(handle=%r, arguments=%r) at %x>" % (self.method_handle, self.arguments, id(self))

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            """
            Writes this bootstrap method info to a buffer.

            :param class_file: The class file that this bootstrap method info belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(struct.pack(">H", class_file.constant_pool.add(self.method_handle)))
            buffer.write(struct.pack(">H", len(self.arguments)))
            for bootstrap_argument in self.arguments:
                buffer.write(struct.pack(">H", class_file.constant_pool.add(bootstrap_argument)))


class NestHost(AttributeInfo):
    """
    Records the host of the nest that this class/interface belongs to.
    """

    __slots__ = ("host_class",)

    name_ = "NestHost"
    since = Version(55, 0)
    locations = (ClassFile,)
    
    def __init__(self, parent: ClassFile) -> None:  # TODO: Constructor
        super().__init__(parent, NestHost.name_)
        
    def __repr__(self) -> str:
        return "<NestHost(host=%r) at %x>" % (self.host_class, id(self))
        
    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        host_class_index, = struct.unpack(">H", buffer.read(2))
        self.host_class = class_file.constant_pool[host_class_index]

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", class_file.constant_pool.add(self.host_class)))


class NestMembers(AttributeInfo):
    """
    Records the classes/interfaces that belong to the nest that this class hosts.
    """

    __slots__ = ("classes",)

    name_ = "NestMembers"
    since = Version(55, 0)
    locations = (ClassFile,)

    def __init__(self, parent: ClassFile) -> None:
        super().__init__(parent, NestMembers.name_)

        self.classes: List[Class] = []

    def __repr__(self) -> str:
        return "<NestMembers(classes=%r) at %x>" % (self.classes, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        self.classes.clear()
        classes_count, = struct.unpack(">H", buffer.read(2))
        for index in range(classes_count):
            class_index, = struct.unpack(">H", buffer.read(2))
            self.classes.append(class_file.constant_pool[class_index])

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", len(self.classes)))
        for class_ in self.classes:
            buffer.write(struct.pack(">H", class_file.constant_pool.add(class_)))


class PermittedSubclasses(AttributeInfo):
    """
    Records classes/interfaces that are allowed to directly extend/implement this class/interface.
    """

    __slots__ = ("classes",)

    name_ = "PermittedSubclasses"
    since = Version(61, 0)
    locations = (ClassFile,)

    def __init__(self, parent: ClassFile) -> None:
        super().__init__(parent, PermittedSubclasses.name_)

        self.classes: List[Class] = []

    def __repr__(self) -> str:
        return "<PermittedSubclasses(classes=%r) at %x>" % (self.classes, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        self.classes.clear()
        classes_count, = struct.unpack(">H", buffer.read(2))
        for index in range(classes_count):
            class_index, = struct.unpack(">H", buffer.read(2))
            self.classes.append(class_file.constant_pool[class_index])

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", len(self.classes)))
        for class_ in self.classes:
            buffer.write(struct.pack(">H", class_file.constant_pool.add(class_)))


class InnerClasses(AttributeInfo):
    """
    Contains information about inner classes (could be inner classes inside this class, or saying that this class is
    an inner class).
    """

    __slots__ = ("classes",)

    name_ = "InnerClasses"
    since = Version(45, 0)
    locations = (ClassFile,)

    def __init__(self, parent: ClassFile) -> None:
        super().__init__(parent, InnerClasses.name_)

        self.classes: List[InnerClasses.InnerClass] = []

    def __repr__(self) -> str:
        return "<InnerClasses(classes=%r) at %x>" % (self.classes, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        self.classes.clear()
        classes_count, = struct.unpack(">H", buffer.read(2))
        for index in range(classes_count):
            self.classes.append(InnerClasses.InnerClass.read(class_file, buffer))

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", len(self.classes)))
        for inner_class in self.classes:
            inner_class.write(class_file, buffer)

    class InnerClass:
        """
        Information about an inner class.
        """

        __slots__ = ("inner_class", "outer_class", "inner_name", "access_flags")

        @classmethod
        def read(cls, class_file: ClassFile, buffer: IO[bytes]) -> "InnerClasses.InnerClass":
            """
            Reads an inner class info from the buffer.

            :param class_file: The class file that the inner class info belongs to.
            :param buffer: The binary buffer to read from.
            :return: The read inner class.
            """

            inner_class = cls()

            inner_class_index, outer_class_index = struct.unpack(">HH", buffer.read(4))
            inner_class.inner_class = class_file.constant_pool[inner_class_index]
            inner_class.outer_class = class_file.constant_pool[outer_class_index] if outer_class_index > 0 else None

            inner_class_name_index, inner_class.access_flags = struct.unpack(">HH", buffer.read(4))
            inner_class.inner_name = (
                class_file.constant_pool.get_utf8(inner_class_name_index, None) if inner_class_name_index > 0 else None
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

        def __init__(self) -> None:  # TODO: Constructor
            ...

        def __repr__(self) -> str:
            return "<InnerClass(inner=%r, outer=%r, inner_name=%r) at %x>" % (
                self.inner_class, self.outer_class, self.inner_name, id(self),
            )

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            """
            Writes this inner class info to an output buffer.

            :param class_file: The class file that this inner class belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(struct.pack(
                ">HH",
                class_file.constant_pool.add(self.inner_class),
                0 if self.outer_class is None else class_file.constant_pool.add(self.outer_class),
            ))
            buffer.write(struct.pack(
                ">HH", 
                0 if self.inner_name is None else class_file.constant_pool.add_utf8(self.inner_name),
                self.access_flags,
            ))


class EnclosingMethod(AttributeInfo):
    """
    Used to denote that a class is a local or anonymous class.
    """

    __slots__ = ("class_", "method")

    name_ = "EnclosingMethod"
    since = Version(49, 0)
    locations = (ClassFile,)

    def __init__(self, parent: ClassFile) -> None:  # TODO: Constructor
        super().__init__(parent, EnclosingMethod.name_)

    def __repr__(self) -> str:
        return "<EnclosingMethod(class=%r, method=%r) at %x>" % (self.class_, self.method, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        class_index, method_index = struct.unpack(">HH", buffer.read(4))
        # No type information? Thanks Iska, really helpful!
        self.class_ = class_file.constant_pool[class_index]
        self.method = class_file.constant_pool[method_index] if method_index > 0 else None

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(
            ">HH", class_file.constant_pool.add(self.class_),
            0 if self.method is None else class_file.constant_pool.add(self.method),
        ))


class Record(AttributeInfo):
    """
    Indicates that the current class is a record, and stores information about the components of the record.
    """

    __slots__ = ("components",)

    name_ = "Record"
    since = Version(60, 0)
    locations = (ClassFile,)

    def __init__(self, parent: ClassFile) -> None:
        super().__init__(parent, Record.name_)

        self.components: List[Record.ComponentInfo] = []

    def __repr__(self) -> str:
        return "<Record(components=%r) at %x>" % (self.components, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        self.components.clear()
        components_count, = struct.unpack(">H", buffer.read(2))
        for index in range(components_count):
            self.components.append(Record.ComponentInfo.read(class_file, buffer))

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", len(self.components)))
        for component in self.components:
            component.write(class_file, buffer)

    class ComponentInfo:
        """
        Information about a component in a record.
        """

        __slots__ = ("name", "descriptor", "attributes")

        @classmethod
        def read(cls, class_file: ClassFile, buffer: IO[bytes]) -> "Record.ComponentInfo":
            """
            Reads a single component info from a buffer.

            :param class_file: The class file that the component info belongs to.
            :param buffer: The binary buffer to read from.
            :return: The read component info.
            """

            component_info = cls()

            name_index, descriptor_index, = struct.unpack(">HH", buffer.read(4))

            component_info.name = class_file.constant_pool.get_utf8(name_index)
            component_info.descriptor = class_file.constant_pool.get_utf8(descriptor_index)

            attributes_count, = struct.unpack(">H", buffer.read(2))
            for index in range(attributes_count):
                attribute_info = attributes.read_attribute(component_info, class_file, buffer)
                component_info.attributes[attribute_info.name] = attribute_info

            return component_info

        def __init__(self, name: Union[str, None] = None, descriptor: Union[str, None] = None) -> None:
            self.name = name
            self.descriptor = descriptor

            self.attributes: Dict[str, AttributeInfo] = {}

        def __repr__(self) -> str:
            return "<ComponentInfo(name=%r, descriptor=%r) at %x>" % (self.name, self.descriptor, id(self))

        def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
            """
            Writes this component info to an output buffer.

            :param class_file: The class file that this component info belongs to.
            :param buffer: The binary buffer to write to.
            """

            buffer.write(struct.pack(
                ">HH", class_file.constant_pool.add_utf8(self.name), class_file.constant_pool.add_utf8(self.descriptor),
            ))

            buffer.write(struct.pack(">H", len(self.attributes)))
            for attribute in self.attributes.values():
                attributes.write_attribute(attribute, class_file, buffer)


class SourceFile(AttributeInfo):
    """
    The name of the source file that this class was compiled from.
    """

    __slots__ = ("source_file",)

    name_ = "SourceFile"
    since = Version(45, 0)
    locations = (ClassFile,)

    def __init__(self, parent: ClassFile, source_file: Union[str, None] = None) -> None:
        """
        :param source_file: The name of the source file that generated the class.
        """

        super().__init__(parent, SourceFile.name_)

        self.source_file = source_file

    def __repr__(self) -> str:
        return "<SourceFile(%r) at %x>" % (self.source_file, id(self))

    def read(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        source_file_index, = struct.unpack(">H", buffer.read(2))
        self.source_file = class_file.constant_pool.get_utf8(source_file_index)

    def write(self, class_file: ClassFile, buffer: IO[bytes]) -> None:
        buffer.write(struct.pack(">H", class_file.constant_pool.add_utf8(self.source_file)))

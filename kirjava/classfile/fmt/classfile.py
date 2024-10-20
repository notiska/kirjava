#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "ClassFile",
    "BootstrapMethods", "NestHost", "NestMembers", "PermittedSubclasses",
    "InnerClasses", "EnclosingMethod", "Record", "SourceFile",
    "SourceDebugExtension", "Module", "ModulePackages", "ModuleMainClass",
)

import sys
import typing
from os import SEEK_CUR
from typing import IO, Iterable, Union

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .attribute import AttributeInfo
from .constants import *
from .field import FieldInfo
from .method import MethodInfo
from .pool import ConstPool
from .._struct import *
from ..version import *
from ...backend import Result
from ...model import Class, Linker

if typing.TYPE_CHECKING:
    from ..visitor import ClassFileVisitor


class ClassFile:
    """
    A ClassFile struct.

    Contains all the information required to construct a class.

    Attributes
    ----------
    ACC_PUBLIC: int
        Access flag denoting that this class is declared `public` and may be
        accessed outside its package.
    ACC_FINAL: int
        Access flag denoting that this class is declared `final` and cannot be
        subclassed.
    ACC_SUPER: int
        Access flag denoting that superclass methods must be treated specially when
        invoked by the `invokespecial` instruction.
    ACC_INTERFACE: int
        Access flag denoting that this class is an interface.
    ACC_ABSTRACT: int
        Access flag denoting that this class is declared `abstract` and cannot be
        instantiated.
    ACC_SYNTHETIC: int
        Access flag denoting that this class is declared synthetic, meaning it does
        not appear in source.
    ACC_ANNOTATION: int
        Access flag denoting that this class is declared as an annotation interface.
    ACC_ENUM: int
        Access flag denoting that this class is declared as an enum.
    ACC_MODULE: int
        Access flag denoting that this class is a module.

    is_public: bool
        See `ACC_PUBLIC`.
    is_final: bool
        See `ACC_FINAL`.
    is_super: bool
        See `ACC_SUPER`.
    is_interface: bool
        See `ACC_INTERFACE`.
    is_abstract: bool
        See `ACC_ABSTRACT`.
    is_synthetic: bool
        See `ACC_SYNTHETIC`.
    is_annotation: bool
        See `ACC_ANNOTATION`.
    is_enum: bool
        See `ACC_ENUM`.
    is_module: bool
        See `ACC_MODULE`.
    version: Version
        The Java version that this class file was compiled for.
    pool: ConstPool
        A pool of constants used in this class file.
    access: int
        A bitmask indicating the access permissions and properties of this class.
    this: ConstInfo
        A class constant representing the class defined within this file.
    super: ConstInfo | None
        A class constant representing the direct superclass of this class.
        If `None`, this class has no superclass and is therefore `java/lang/Object`.
    interfaces: list[ConstInfo]
        A list of class constants representing all direct superinterfaces of this
        class.
    fields: list[FieldInfo]
        A list of information about all fields declared within this class.
    methods: list[MethodInfo]
        A list of information about all methods declared within this class.
    attributes: list[AttributeInfo]
        A list of attributes on this class.

    Methods
    -------
    read(stream: IO[bytes], reader: Reader) -> Result[Self]
        Reads a class file from a binary stream.

    write(self, stream: IO[bytes]) -> None
        Writes this class file to a binary stream.
    visit(self, visitor: ClassFileVisitor) -> None
        Calls a visitor on this class file.
    unwrap(self, linker: Linker) -> Result[Class]
        Unwraps this class file.
    """

    __slots__ = (
        "version", "pool",
        "access", "this", "super", "interfaces",
        "fields", "methods", "attributes",
    )

    ACC_PUBLIC     = 0x0001
    ACC_FINAL      = 0x0010
    ACC_SUPER      = 0x0020
    ACC_INTERFACE  = 0x0200
    ACC_ABSTRACT   = 0x0400
    ACC_SYNTHETIC  = 0x1000
    ACC_ANNOTATION = 0x2000
    ACC_ENUM       = 0x4000
    ACC_MODULE     = 0x8000

    @classmethod
    def read(cls, stream: IO[bytes]) -> Result[Self]:
        """
        Reads a class file from a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        """

        with Result[Self].meta(__name__) as result:
            magic = stream.read(4)
            if magic != b"\xca\xfe\xba\xbe":
                result.err(ValueError(f"invalid class file magic {magic!r}"))

            minor, major = unpack_HH(stream.read(4))
            version = Version(major, minor)
            pool = ConstPool.read(stream)

            access, this_index, super_index, interface_count = unpack_HHHH(stream.read(8))
            interfaces = [pool[index] for index, in iter_unpack_H(stream.read(interface_count * 2))]

            field_count, = unpack_H(stream.read(2))
            fields = [FieldInfo.read(stream, version, pool).unwrap_into(result) for _ in range(field_count)]
            method_count, = unpack_H(stream.read(2))
            methods = [MethodInfo.read(stream, version, pool).unwrap_into(result) for _ in range(method_count)]

            attr_count, = unpack_H(stream.read(2))
            attributes = [
                AttributeInfo.read(stream, version, pool, AttributeInfo.LOC_CLASS).unwrap_into(result)
                for _ in range(attr_count)
            ]

            return result.ok(cls(
                version, pool,
                access, pool[this_index], pool[super_index] if super_index else None, interfaces,
                fields, methods, attributes,
            ))
        return result

    @property
    def is_public(self) -> bool:
        return bool(self.access & ClassFile.ACC_PUBLIC)

    @is_public.setter
    def is_public(self, value: bool) -> None:
        if value:
            self.access |= ClassFile.ACC_PUBLIC
        else:
            self.access &= ~ClassFile.ACC_PUBLIC

    @property
    def is_final(self) -> bool:
        return bool(self.access & ClassFile.ACC_FINAL)

    @is_final.setter
    def is_final(self, value: bool) -> None:
        if value:
            self.access |= ClassFile.ACC_FINAL
        else:
            self.access &= ~ClassFile.ACC_FINAL

    @property
    def is_super(self) -> bool:
        return bool(self.access & ClassFile.ACC_SUPER)

    @is_super.setter
    def is_super(self, value: bool) -> None:
        if value:
            self.access |= ClassFile.ACC_SUPER
        else:
            self.access &= ~ClassFile.ACC_SUPER

    @property
    def is_interface(self) -> bool:
        return bool(self.access & ClassFile.ACC_INTERFACE)

    @is_interface.setter
    def is_interface(self, value: bool) -> None:
        if value:
            self.access |= ClassFile.ACC_INTERFACE
        else:
            self.access &= ~ClassFile.ACC_INTERFACE

    @property
    def is_abstract(self) -> bool:
        return bool(self.access & ClassFile.ACC_ABSTRACT)

    @is_abstract.setter
    def is_abstract(self, value: bool) -> None:
        if value:
            self.access |= ClassFile.ACC_ABSTRACT
        else:
            self.access &= ~ClassFile.ACC_ABSTRACT

    @property
    def is_synthetic(self) -> bool:
        return bool(self.access & ClassFile.ACC_SYNTHETIC)

    @is_synthetic.setter
    def is_synthetic(self, value: bool) -> None:
        if value:
            self.access |= ClassFile.ACC_SYNTHETIC
        else:
            self.access &= ~ClassFile.ACC_SYNTHETIC

    @property
    def is_annotation(self) -> bool:
        return bool(self.access & ClassFile.ACC_ANNOTATION)

    @is_annotation.setter
    def is_annotation(self, value: bool) -> None:
        if value:
            self.access |= ClassFile.ACC_ANNOTATION
        else:
            self.access &= ~ClassFile.ACC_ANNOTATION

    @property
    def is_enum(self) -> bool:
        return bool(self.access & ClassFile.ACC_ENUM)

    @is_enum.setter
    def is_enum(self, value: bool) -> None:
        if value:
            self.access |= ClassFile.ACC_ENUM
        else:
            self.access &= ~ClassFile.ACC_ENUM

    @property
    def is_module(self) -> bool:
        return bool(self.access & ClassFile.ACC_MODULE)

    @is_module.setter
    def is_module(self, value: bool) -> None:
        if value:
            self.access |= ClassFile.ACC_MODULE
        else:
            self.access &= ~ClassFile.ACC_MODULE

    def __init__(
            self,
            version: Version, pool: ConstPool,
            access: int, this: ConstInfo, super_: ConstInfo | None,
            interfaces:     Iterable[ConstInfo] | None = None,
            fields:         Iterable[FieldInfo] | None = None,
            methods:       Iterable[MethodInfo] | None = None,
            attributes: Iterable[AttributeInfo] | None = None,
    ) -> None:
        self.version = version
        self.pool = pool
        self.access = access
        self.this = this
        self.super = super_
        self.interfaces: list[ConstInfo] = []

        self.fields:   list[FieldInfo] = []
        self.methods: list[MethodInfo] = []

        self.attributes: list[AttributeInfo] = []

        if interfaces is not None:
            self.interfaces.extend(interfaces)
        if fields is not None:
            self.fields.extend(fields)
        if methods is not None:
            self.methods.extend(methods)
        if attributes is not None:
            self.attributes.extend(attributes)

    def __repr__(self) -> str:
        return (
            f"<ClassFile(version={self.version!r}, access=0x{self.access:04x}, "
            f"this={self.this!s}, super={self.super!s})>"
        )

    def __str__(self) -> str:
        super_str = str(self.super) if self.super is not None else "[none]"
        return f"ClassFile({self.version!s},0x{self.access:04x},{self.this!s},{super_str})"

    def write(self, stream: IO[bytes]) -> None:
        """
        Writes this class file to a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.

        Raises
        ------
        Exception
            If any writing errors occur.
        """

        stream.write(b"\xca\xfe\xba\xbe")
        stream.write(pack_HH(self.version.minor, self.version.major))

        this_index = self.pool.add(self.this)
        super_index = self.pool.add(self.super) if self.super is not None else 0
        interface_indices = [self.pool.add(interface) for interface in self.interfaces]

        # TODO: Pre-populate the constant pool, or rather check if all constants are in the pool.
        self.pool.write(stream)

        stream.write(pack_HHHH(self.access, this_index, super_index, len(self.interfaces)))
        for interface_index in interface_indices:
            stream.write(pack_H(interface_index))

        stream.write(pack_H(len(self.fields)))
        for field in self.fields:
            field.write(stream, self.version, self.pool)
        stream.write(pack_H(len(self.methods)))
        for method in self.methods:
            method.write(stream, self.version, self.pool)
        stream.write(pack_H(len(self.attributes)))
        for attribute in self.attributes:
            attribute.write(stream, self.version, self.pool)

    def visit(self, visitor: "ClassFileVisitor") -> None:
        """
        Calls a visitor on this class file.
        """

        visitor.visit_start(self)
        visitor.visit_pool(self.pool)
        for field in self.fields:
            visitor.visit_field(field)
        for method in self.methods:
            visitor.visit_method(method)
        for attribute in self.attributes:
            visitor.visit_attribute(attribute)
        visitor.visit_end(self)

    def unwrap(self, linker: Linker) -> Result[Class]:
        """
        Unwraps this class file.

        Parameters
        ----------
        linker: Linker
            The linker to use to resolve references.
        """

        with Result[Class].meta(__name__, self) as result:
            if not isinstance(self.this, ClassInfo):
                return result.err(TypeError(f"this class {self.this!s} is not a class constant"))

            # FIXME: This is actually quite lenient as we assume that this is a UTF8 constant, more thorough type checking
            #        should be required.
            name = str(self.this.name)
            super_ = None
            interfaces: list[Class] = []

            if self.super is not None:
                if not isinstance(self.super, ClassInfo):
                    return result.err(TypeError(f"super class {self.super!s} is not a class constant"))
                super_ = linker.find_class(str(self.super.name))

            for interface in self.interfaces:
                if not isinstance(interface, ClassInfo):
                    return result.err(TypeError(f"interface {interface!s} is not a class constant"))
                linker.find_class(str(interface.name))
                # interfaces.append()

            return result.ok(Class(
                str(self.this.name),
                super_, interfaces,
                [field.unwrap() for field in self.fields],
                [method.unwrap() for method in self.methods],
                is_public=self.is_public,
                is_final=self.is_final,
                is_super=self.is_super,
                is_interface=self.is_interface,
                is_abstract=self.is_abstract,
                is_synthetic=self.is_synthetic,
                is_annotation=self.is_annotation,
                is_enum=self.is_enum,
                is_module=self.is_module,
            ))
        return result


# ---------------------------------------- Attributes ---------------------------------------- #

class BootstrapMethods(AttributeInfo):
    """
    The BootstrapMethods attribute.

    A variable length attribute used to store bootstrap methods for dynamically
    computed constants and callsites.

    Attributes
    ----------
    methods: list[BootstrapMethods.BootstrapMethod]
        A list of bootstrap method invocation information.
    """

    __slots__ = ("methods",)

    tag = b"BootstrapMethods"
    since = JAVA_7
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            method_count, = unpack_H(stream.read(2))
            methods = []
            for _ in range(method_count):
                ref_index, arg_count = unpack_HH(stream.read(4))
                args = []
                for _ in range(arg_count):
                    arg_index, = unpack_H(stream.read(2))
                    args.append(pool[arg_index])
                methods.append(cls.BootstrapMethod(pool[ref_index], args))
            return result.ok(cls(methods))
        return result

    def __init__(self, methods: Iterable["BootstrapMethods.BootstrapMethod"] | None = None) -> None:
        super().__init__()
        self.methods: list[BootstrapMethods.BootstrapMethod] = []
        if methods is not None:
            self.methods.extend(methods)

    def __repr__(self) -> str:
        return f"<BoostrapMethods(methods={self.methods!r})>"

    def __str__(self) -> str:
        methods_str = ",".join(map(str, self.methods))
        return f"BootstrapMethods([{methods_str}])"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BootstrapMethods) and self.methods == other.methods

    def __getitem__(self, index: int) -> "BootstrapMethods.BootstrapMethod":
        return self.methods[index]

    def __setitem__(self, index: int, value: "BootstrapMethods.BootstrapMethod") -> None:
        self.methods[index] = value

    def __delitem__(self, key: Union[int, "BootstrapMethods.BootstrapMethod"]) -> None:
        if isinstance(key, int):
            del self.methods[key]
        else:
            self.methods.remove(key)

    def __len__(self) -> int:
        return len(self.methods)

    def _write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_H(len(self.methods)))
        for method in self.methods:
            stream.write(pack_HH(pool.add(method.ref), len(method.args)))
            for argument in method.args:
                stream.write(pack_H(pool.add(argument)))

    class BootstrapMethod:
        """
        A bootstrap_method struct.

        Attributes
        ----------
        ref: ConstInfo
            A method handle constant used to resolve a constant or callsite.
        args: list[ConstInfo]
            A list of constants to pass as static arguments to the bootstrap method.
        """

        __slots__ = ("ref", "args")

        def __init__(self, ref: ConstInfo, args: Iterable[ConstInfo] | None = None) -> None:
            self.ref = ref
            self.args: list[ConstInfo] = []
            if args is not None:
                self.args.extend(args)

        def __repr__(self) -> str:
            args_str = ", ".join(map(str, self.args))
            return f"<BootstrapMethods.BootstrapMethod(ref={self.ref!s}, args=[{args_str}])>"

        def __str__(self) -> str:
            args_str = ",".join(map(str, self.args))
            return f"boostrap_method({self.ref!s},[{args_str}])"

        def __eq__(self, other: object) -> bool:
            return (
                isinstance(other, BootstrapMethods.BootstrapMethod) and
                self.ref == other.ref and
                self.args == other.args
            )


class NestHost(AttributeInfo):
    """
    The NestHost attribute.

    A fixed length attribute used to store the host of the nest that this class
    belongs to.

    Attributes
    ----------
    host: ConstInfo
        A class constant, used to represent the nest host.
    """

    __slots__ = ("host",)

    tag = b"NestHost"
    since = JAVA_11
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            index, = unpack_H(stream.read(2))
            return result.ok(cls(pool[index]))
        return result

    def __init__(self, host: ConstInfo) -> None:
        super().__init__()
        self.host = host

    def __repr__(self) -> str:
        return f"<NestHost(host={self.host!s})>"

    def __str__(self) -> str:
        return f"NestHost({self.host!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NestHost) and self.host == other.host

    def write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None:
        stream.write(pack_HIH(pool.add(self.name or UTF8Info(self.tag)), 2 + len(self.extra), pool.add(self.host)))
        stream.write(self.extra)


class NestMembers(AttributeInfo):
    """
    The NestMembers attribute.

    A variable length attribute used to store the members of the nest that this
    class hosts.

    Attributes
    ----------
    classes: list[ConstInfo]
        A list of class constants, used to represent the nest members.
    """

    __slots__ = ("classes",)

    tag = b"NestMembers"
    since = JAVA_11
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            count, = unpack_H(stream.read(2))
            classes = [pool[index] for index, in iter_unpack_H(stream.read(count * 2))]
            # Some explicit checks do need to be added for some attributes, as the stream.read(count * 2) may not read
            # all required bytes which could result in a seemingly valid attribute read, which would not be correct.
            if len(classes) != count:
                return result.err(ValueError("nest members underread"))
            return result.ok(cls(classes))
        return result

    def __init__(self, classes: Iterable[ConstInfo] | None = None) -> None:
        super().__init__()
        self.classes: list[ConstInfo] = []
        if classes is not None:
            self.classes.extend(classes)

    def __repr__(self) -> str:
        classes_str = ", ".join(map(str, self.classes))
        return f"<NestMembers(classes=[{classes_str}])>"

    def __str__(self) -> str:
        classes_str = ",".join(map(str, self.classes))
        return f"NestMembers([{classes_str}])"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NestMembers) and self.classes == other.classes

    def __getitem__(self, index: int) -> ConstInfo:
        return self.classes[index]

    def __setitem__(self, index: int, value: ConstInfo) -> None:
        self.classes[index] = value

    def __delitem__(self, key: int | ConstInfo) -> None:
        if isinstance(key, int):
            del self.classes[key]
        else:
            self.classes.remove(key)

    def __len__(self) -> int:
        return len(self.classes)

    def write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None:
        stream.write(pack_HIH(
            pool.add(self.name or UTF8Info(self.tag)), 2 + len(self.extra) + len(self.classes) * 2, len(self.classes),
        ))
        for class_ in self.classes:
            stream.write(pack_H(pool.add(class_)))
        stream.write(self.extra)


class PermittedSubclasses(AttributeInfo):
    """
    The PermittedSubclasses attribute.

    A variable length attribute used to store the classes that are allowed to
    directly subclass this class.

    Attributes
    ----------
    classes: list[ConstInfo]
        A list of class constants, used to represent the permitted subclasses.
    """

    __slots__ = ("classes",)

    tag = b"PermittedSubclasses"
    since = JAVA_17
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            count, = unpack_H(stream.read(2))
            classes = [pool[index] for index, in iter_unpack_H(stream.read(count * 2))]
            if len(classes) != count:
                return result.err(ValueError("permitted subclasses underread"))
            return result.ok(cls(classes))
        return result

    def __init__(self, classes: Iterable[ConstInfo] | None = None) -> None:
        super().__init__()
        self.classes: list[ConstInfo] = []
        if classes is not None:
            self.classes.extend(classes)

    def __repr__(self) -> str:
        classes_str = ", ".join(map(str, self.classes))
        return f"<PermittedSubclasses(classes=[{classes_str}])>"

    def __str__(self) -> str:
        classes_str = ",".join(map(str, self.classes))
        return f"PermittedSubclasses([{classes_str}])"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PermittedSubclasses) and self.classes == other.classes

    def __getitem__(self, index: int) -> ConstInfo:
        return self.classes[index]

    def __setitem__(self, index: int, value: ConstInfo) -> None:
        self.classes[index] = value

    def __delitem__(self, key: int | ConstInfo) -> None:
        if isinstance(key, int):
            del self.classes[key]
        else:
            self.classes.remove(key)

    def __len__(self) -> int:
        return len(self.classes)

    def write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None:
        stream.write(pack_HIH(
            pool.add(self.name or UTF8Info(self.tag)), 2 + len(self.extra) + len(self.classes) * 2, len(self.classes),
        ))
        for class_ in self.classes:
            stream.write(pack_H(pool.add(class_)))
        stream.write(self.extra)


class InnerClasses(AttributeInfo):
    """
    The InnerClasses attribute.

    A variable length attribute used to store information about inner classes.

    Attributes
    ----------
    classes: list[InnerClasses.InnerClass]
        A list of information about inner classes.
    """

    __slots__ = ("classes",)

    tag = b"InnerClasses"
    since = JAVA_1_1
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            count, = unpack_H(stream.read(2))
            classes = []
            for _ in range(count):
                inner_index, outer_index, name_index, access = unpack_HHHH(stream.read(8))
                classes.append(cls.InnerClass(
                    pool[inner_index],
                    pool[outer_index] if outer_index else None,
                    pool[name_index] if name_index else None,
                    access,
                ))
            return result.ok(cls(classes))
        return result

    def __init__(self, classes: Iterable["InnerClasses.InnerClass"] | None = None) -> None:
        super().__init__()
        self.classes: list[InnerClasses.InnerClass] = []
        if classes is not None:
            self.classes.extend(classes)

    def __repr__(self) -> str:
        classes_str = ", ".join(map(str, self.classes))
        return f"<InnerClasses(classes=[{classes_str}])>"

    def __str__(self) -> str:
        classes_str = ",".join(map(str, self.classes))
        return f"InnerClasses([{classes_str}])"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, InnerClasses) and self.classes == other.classes

    def __getitem__(self, index: int) -> "InnerClasses.InnerClass":
        return self.classes[index]

    def __setitem__(self, index: int, value: "InnerClasses.InnerClass") -> None:
        self.classes[index] = value

    def __delitem__(self, key: Union[int, "InnerClasses.InnerClass"]) -> None:
        if isinstance(key, int):
            del self.classes[key]
        else:
            self.classes.remove(key)

    def __len__(self) -> int:
        return len(self.classes)

    def write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None:
        stream.write(pack_HIH(
            pool.add(self.name or UTF8Info(self.tag)), 2 + len(self.extra) + len(self.classes) * 8, len(self.classes),
        ))
        for inner in self.classes:
            stream.write(pack_HHHH(
                pool.add(inner.inner_class),
                pool.add(inner.outer_class) if inner.outer_class is not None else 0,
                pool.add(inner.name) if inner.name is not None else 0,
                inner.access,
            ))
        stream.write(self.extra)

    class InnerClass:
        """
        An inner class entry.

        Attributes
        ----------
        ACC_PUBLIC: int
            Access flag denoting that this inner class is either implicitly or
            explicitly marked `public` in source.
        ACC_PRIVATE: int
            Access flag denoting that this inner class is marked `private` in source.
        ACC_PROTECTED: int
            Access flag denoting that this inner class is marked `protected` in source.
        ACC_STATIC: int
            Access flag denoting that this inner class is either implicitly or
            explicitly marked `static` in source.
        ACC_FINAL: int
            Access flag denoting that this inner class is either implicitly or
            explicitly marked `final` in source.
        ACC_INTERFACE: int
            Access flag denoting that this inner class was an interface in source.
        ACC_ABSTRACT: int
            Access flag denoting that this inner class is either implicitly or
            explicitly marked `abstract` in source.
        ACC_SYNTHETIC: int
            Access flag denoting that this inner class is declared synthetic, meaning it
            does not appear in source.
        ACC_ANNOTATION: int
            Access flag denoting that this inner class is declared as an annotation
            interface.
        ACC_ENUM: int
            Access flag denoting that this inner class is declared as an enum.

        is_public: bool
            See `ACC_PUBLIC`.
        is_private: bool
            See `ACC_PRIVATE`.
        is_protected: bool
            See `ACC_PROTECTED`.
        is_static: bool
            See `ACC_STATIC`.
        is_final: bool
            See `ACC_FINAL`.
        is_interface: bool
            See `ACC_INTERFACE`.
        is_abstract: bool
            See `ACC_ABSTRACT`.
        is_synthetic: bool
            See `ACC_SYNTHETIC`.
        if_annotation: bool
            See `ACC_ANNOTATION`.
        is_enum: bool
            See `ACC_ENUM`.
        inner_class: ConstInfo
            A class constant, used to represent the inner class.
        outer_class: ConstInfo | None
            A class constant, used to represent the outer class.
            If `None`, the class is a top-level, local or anonymous class.
        name: ConstInfo | None
            A UTF8 constant, used as the simple name of the inner class.
            If `None`, the class is anonymous.
        access: int
            A bitmask indicating the access permissions and properties of the inner
            class.
        """

        __slots__ = ("inner_class", "outer_class", "name", "access")

        ACC_PUBLIC     = 0x0001
        ACC_PRIVATE    = 0x0002
        ACC_PROTECTED  = 0x0004
        ACC_STATIC     = 0x0008
        ACC_FINAL      = 0x0010
        ACC_INTERFACE  = 0x0200
        ACC_ABSTRACT   = 0x0400
        ACC_SYNTHETIC  = 0x1000
        ACC_ANNOTATION = 0x2000
        ACC_ENUM       = 0x4000

        @property
        def is_public(self) -> bool:
            return bool(self.access & InnerClasses.InnerClass.ACC_PUBLIC)

        @is_public.setter
        def is_public(self, value: bool) -> None:
            if value:
                self.access |= InnerClasses.InnerClass.ACC_PUBLIC
            else:
                self.access &= ~InnerClasses.InnerClass.ACC_PUBLIC

        @property
        def is_private(self) -> bool:
            return bool(self.access & InnerClasses.InnerClass.ACC_PRIVATE)

        @is_private.setter
        def is_private(self, value: bool) -> None:
            if value:
                self.access |= InnerClasses.InnerClass.ACC_PRIVATE
            else:
                self.access &= ~InnerClasses.InnerClass.ACC_PRIVATE

        @property
        def is_protected(self) -> bool:
            return bool(self.access & InnerClasses.InnerClass.ACC_PROTECTED)

        @is_protected.setter
        def is_protected(self, value: bool) -> None:
            if value:
                self.access |= InnerClasses.InnerClass.ACC_PROTECTED
            else:
                self.access &= ~InnerClasses.InnerClass.ACC_PROTECTED

        @property
        def is_static(self) -> bool:
            return bool(self.access & InnerClasses.InnerClass.ACC_STATIC)

        @is_static.setter
        def is_static(self, value: bool) -> None:
            if value:
                self.access |= InnerClasses.InnerClass.ACC_STATIC
            else:
                self.access &= ~InnerClasses.InnerClass.ACC_STATIC

        @property
        def is_final(self) -> bool:
            return bool(self.access & InnerClasses.InnerClass.ACC_FINAL)

        @is_final.setter
        def is_final(self, value: bool) -> None:
            if value:
                self.access |= InnerClasses.InnerClass.ACC_FINAL
            else:
                self.access &= ~InnerClasses.InnerClass.ACC_FINAL

        @property
        def is_interface(self) -> bool:
            return bool(self.access & InnerClasses.InnerClass.ACC_INTERFACE)

        @is_interface.setter
        def is_interface(self, value: bool) -> None:
            if value:
                self.access |= InnerClasses.InnerClass.ACC_INTERFACE
            else:
                self.access &= ~InnerClasses.InnerClass.ACC_INTERFACE

        @property
        def is_abstract(self) -> bool:
            return bool(self.access & InnerClasses.InnerClass.ACC_ABSTRACT)

        @is_abstract.setter
        def is_abstract(self, value: bool) -> None:
            if value:
                self.access |= InnerClasses.InnerClass.ACC_ABSTRACT
            else:
                self.access &= ~InnerClasses.InnerClass.ACC_ABSTRACT

        @property
        def is_synthetic(self) -> bool:
            return bool(self.access & InnerClasses.InnerClass.ACC_SYNTHETIC)

        @is_synthetic.setter
        def is_synthetic(self, value: bool) -> None:
            if value:
                self.access |= InnerClasses.InnerClass.ACC_SYNTHETIC
            else:
                self.access &= ~InnerClasses.InnerClass.ACC_SYNTHETIC

        @property
        def is_annotation(self) -> bool:
            return bool(self.access & InnerClasses.InnerClass.ACC_ANNOTATION)

        @is_annotation.setter
        def is_annotation(self, value: bool) -> None:
            if value:
                self.access |= InnerClasses.InnerClass.ACC_ANNOTATION
            else:
                self.access &= ~InnerClasses.InnerClass.ACC_ANNOTATION

        @property
        def is_enum(self) -> bool:
            return bool(self.access & InnerClasses.InnerClass.ACC_ENUM)

        @is_enum.setter
        def is_enum(self, value: bool) -> None:
            if value:
                self.access |= InnerClasses.InnerClass.ACC_ENUM
            else:
                self.access &= ~InnerClasses.InnerClass.ACC_ENUM

        def __init__(
                self, inner_class: ConstInfo, outer_class: ConstInfo | None, name: ConstInfo | None, access: int,
        ) -> None:
            self.inner_class = inner_class
            self.outer_class = outer_class
            self.name = name
            self.access = access

        def __repr__(self) -> str:
            return (
                f"<InnerClasses.InnerClass(inner_class={self.inner_class!s}, outer_class={self.outer_class!s}, "
                f"name={self.name!s}, access=0x{self.access:04x})>"
            )

        def __str__(self) -> str:
            outer_class_str = str(self.outer_class) if self.outer_class is not None else "[none]"
            name_str = str(self.name) if self.name is not None else "[none]"
            return f"inner_class({self.inner_class!s},{outer_class_str},{name_str},0x{self.access:04x})"

        def __eq__(self, other: object) -> bool:
            return (
                isinstance(other, InnerClasses.InnerClass) and
                self.inner_class == other.inner_class and
                self.outer_class == other.outer_class and
                self.name == other.name and
                self.access == other.access
            )


class EnclosingMethod(AttributeInfo):
    """
    The EnclosingMethod attribute.

    A fixed length attribute used to indicate whether a class is local or anonymous.

    Attributes
    ----------
    class_: ConstInfo
        A class constant, used to represent the outer class that encloses this class.
    method: ConstInfo | None
        A name and type constant, used to represent the method that encloses this
        class.
        If `None`, this class is not enclosed by a method.
    """

    __slots__ = ("class_", "method")

    tag = b"EnclosingMethod"
    since = JAVA_5
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            class_index, method_index = unpack_HH(stream.read(4))
            return result.ok(cls(pool[class_index], pool[method_index] if method_index else None))
        return result

    def __init__(self, class_: ConstInfo, method: ConstInfo | None) -> None:
        super().__init__()
        self.class_ = class_
        self.method = method

    def __repr__(self) -> str:
        return f"<EnclosingMethod(class_={self.class_!s}, method={self.method!s})>"

    def __str__(self) -> str:
        method_str = str(self.method) if self.method is not None else "[none]"
        return f"EnclosingMethod({self.class_!s},{method_str})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, EnclosingMethod) and self.class_ == other.class_ and self.method == other.method

    def write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None:
        stream.write(pack_HI(pool.add(self.name or UTF8Info(self.tag)), 4 + len(self.extra)))
        stream.write(pack_HH(pool.add(self.class_), pool.add(self.method) if self.method is not None else 0))
        stream.write(self.extra)


class Record(AttributeInfo):
    """
    The Record attribute.

    A variable length attribute used to indicate that this class is a record class,
    and to store information about the components of the record class.

    Attributes
    ----------
    components: list[Record.ComponentInfo]
        A list of info about record components.
    """

    __slots__ = ("components",)

    tag = b"Record"
    since = JAVA_16
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self].meta(__name__) as result:
            component_count, = unpack_H(stream.read(2))
            components = []
            for _ in range(component_count):
                name_index, desc_index, attr_count = unpack_HHH(stream.read(6))
                attributes = [
                    AttributeInfo.read(stream, version, pool, AttributeInfo.LOC_RECORD_COMPONENT).unwrap_into(result)
                    for _ in range(attr_count)
                ]
                components.append(cls.ComponentInfo(pool[name_index], pool[desc_index], attributes))
            return result.ok(cls(components))
        return result

    def __init__(self, components: Iterable["Record.ComponentInfo"] | None = None) -> None:
        super().__init__()
        self.components: list[Record.ComponentInfo] = []
        if components is not None:
            self.components.extend(components)

    def __repr__(self) -> str:
        return f"<Record(components={self.components!r})>"

    def __str__(self) -> str:
        components_str = ",".join(map(str, self.components))
        return f"Record([{components_str}])"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Record) and self.components == other.components

    def __getitem__(self, index: int) -> "Record.ComponentInfo":
        return self.components[index]

    def __setitem__(self, index: int, value: "Record.ComponentInfo") -> None:
        self.components[index] = value

    def __delitem__(self, key: Union[int, "Record.ComponentInfo"]) -> None:
        if isinstance(key, int):
            del self.components[key]
        else:
            self.components.remove(key)

    def __len__(self) -> int:
        return len(self.components)

    def _write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_H(len(self.components)))
        for component in self.components:
            stream.write(pack_HHH(pool.add(component.name), pool.add(component.descriptor), len(component.attributes)))
            for attribute in component.attributes:
                attribute.write(stream, version, pool)

    class ComponentInfo:
        """
        A record_component_info struct.

        Attributes
        ----------
        name: ConstInfo
            A UTF8 constant, used as the name of this component.
        descriptor: ConstInfo
            A UTF8 constant, used as the descriptor detailing the type of this component.
        attributes: list[AttributeInfo]
            A list of attributes in this record component.
        """

        __slots__ = ("name", "descriptor", "attributes")

        def __init__(
                self, name: ConstInfo, descriptor: ConstInfo, attributes: Iterable[AttributeInfo] | None = None,
        ) -> None:
            self.name = name
            self.descriptor = descriptor
            self.attributes: list[AttributeInfo] = []

            if attributes is not None:
                self.attributes.extend(attributes)

        def __repr__(self) -> str:
            return f"<Record.ComponentInfo(name={self.name!s}, descriptor={self.descriptor!s})>"

        def __str__(self) -> str:
            return f"record_component_info({self.name!s}:{self.descriptor!s})"

        def __eq__(self, other: object) -> bool:
            return (
                isinstance(other, Record.ComponentInfo) and
                self.name == other.name and
                self.descriptor == other.descriptor and
                self.attributes == other.attributes
            )


class SourceFile(AttributeInfo):
    """
    The SourceFile attribute.

    A fixed length attribute used to store the name of source file the class was
    compiled from.

    Attributes
    ----------
    file: ConstInfo
        A UTF8 constant, used to represent the name of the source file.
    """

    __slots__ = ("file",)

    tag = b"SourceFile"
    since = JAVA_1_0
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            index, = unpack_H(stream.read(2))
            return result.ok(cls(pool[index]))
        return result

    def __init__(self, file: ConstInfo) -> None:
        super().__init__()
        self.file = file

    def __repr__(self) -> str:
        return f"<SourceFile(file={self.file!s})>"

    def __str__(self) -> str:
        return f"SourceFile({self.file!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SourceFile) and self.file == other.file

    def write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None:
        stream.write(pack_HIH(pool.add(self.name or UTF8Info(self.tag)), 2 + len(self.extra), pool.add(self.file)))
        stream.write(self.extra)


class SourceDebugExtension(AttributeInfo):
    """
    The SourceDebugExtension attribute.

    A variable length attribute used to store extended debug information.

    Attributes
    ----------
    extension: bytes
        Debug extension data.
    """

    __slots__ = ("extension",)

    tag = b"SourceDebugExtension"
    since = JAVA_5
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            assert stream.seekable(), "stream is not seekable"
            stream.seek(-4, SEEK_CUR)
            length, = unpack_I(stream.read(4))
            return result.ok(cls(stream.read(length)))
        return result

    def __init__(self, extension: bytes) -> None:
        super().__init__()
        self.extension = extension

    def __repr__(self) -> str:
        return f"<DebugExtension(extension={self.extension!r})>"

    def __str__(self) -> str:
        return f"DebugExtension({self.extension!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SourceDebugExtension) and self.extension == other.extension

    def write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None:
        stream.write(pack_HI(pool.add(self.name or UTF8Info(self.tag)), len(self.extra) + len(self.extension)))
        stream.write(self.extension)
        stream.write(self.extra)


class Module(AttributeInfo):
    """
    The Module attribute.

    A variable length attribute used to store information about the module that this
    class represents.

    Attributes
    ----------
    ACC_OPEN: int
        Access flag denoting that this module is open.
    ACC_SYNTHETIC: int
        Access flag denoting that this module is declared synthetic, meaning it is
        not present in source.
    ACC_MANDATED: int
        Access flag denoting that this module was implicitly declared.

    is_open: bool
        See `ACC_OPEN`.
    is_synthetic: bool
        See `ACC_SYNTHETIC`.
    is_mandated: bool
        See `ACC_MANDATED`.
    module: ConstInfo
        A module constant, indicating the module that this class represents.
    flags: int
        A bitmask indicating the properties of the module.
    version: ConstInfo | None
        A UTF8 constant, used as the version of the module.
        If `None`, no version information is available.
    requires: list[Module.Require]
        A list of dependencies of this module, see `Module.Require`.
    exports: list[Module.Export]
        A list of packages exported from this module, see `Module.Export`.
    opens: list[Module.Open]
        A list of packages opened by this module, see `Module.Open`.
    uses: list[ConstInfo]
        A list of class constants representing service interfaces in this module.
    provides: list[Module.Provide]
        A list of service implementations in this module, see `Module.Provide`.
    """

    __slots__ = (
        "module", "flags", "version",
        "requires", "exports", "opens", "uses", "provides",
    )

    tag = b"Module"
    since = JAVA_9
    locations = frozenset({AttributeInfo.LOC_CLASS})

    ACC_OPEN      = 0x0020
    ACC_SYNTHETIC = 0x1000
    ACC_MANDATED  = 0x8000

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            module_index, flags, version_index = unpack_HHH(stream.read(6))

            require_count, = unpack_H(stream.read(2))
            requires = []
            for _ in range(require_count):
                require_index, require_flags, require_version_index = unpack_HHH(stream.read(6))
                requires.append(cls.Require(
                    pool[require_index], require_flags, pool[require_version_index] if require_version_index else None
                ))

            export_count, = unpack_H(stream.read(2))
            exports = []
            for _ in range(export_count):
                export_index, export_flags, exports_to_count = unpack_HHH(stream.read(6))
                exports_to = [pool[index] for index, in iter_unpack_H(stream.read(exports_to_count * 2))]
                if len(exports_to) != exports_to_count:
                    return result.err(ValueError("module exports underread"))
                exports.append(cls.Export(pool[export_index], export_flags, exports_to))

            open_count, = unpack_H(stream.read(2))
            opens = []
            for _ in range(open_count):
                open_index, open_flags, opens_to_count = unpack_HHH(stream.read(6))
                opens_to = [pool[index] for index, in iter_unpack_H(stream.read(opens_to_count * 2))]
                if len(opens_to) != opens_to_count:
                    return result.err(ValueError("module opens underread"))
                opens.append(cls.Open(pool[open_index], open_flags, opens_to))

            use_count, = unpack_H(stream.read(2))
            uses = [pool[index] for index, in iter_unpack_H(stream.read(use_count * 2))]

            provide_count, = unpack_H(stream.read(2))
            provides = []
            for _ in range(provide_count):
                provide_index, provides_with_count = unpack_HH(stream.read(4))
                provides_with = [pool[index] for index, in iter_unpack_H(stream.read(provides_with_count * 2))]
                if len(provides_with) != provides_with_count:
                    return result.err(ValueError("module provides underread"))
                provides.append(cls.Provide(pool[provide_index], provides_with))

            return result.ok(cls(
                pool[module_index], flags, pool[version_index] if version_index else None,
                requires, exports, opens, uses, provides,
            ))
        return result

    @property
    def is_open(self) -> bool:
        return bool(self.flags & Module.ACC_OPEN)

    @is_open.setter
    def is_open(self, value: bool) -> None:
        if value:
            self.flags |= Module.ACC_OPEN
        else:
            self.flags &= ~Module.ACC_OPEN

    @property
    def is_synthetic(self) -> bool:
        return bool(self.flags & Module.ACC_SYNTHETIC)

    @is_synthetic.setter
    def is_synthetic(self, value: bool) -> None:
        if value:
            self.flags |= Module.ACC_SYNTHETIC
        else:
            self.flags &= ~Module.ACC_SYNTHETIC

    @property
    def is_mandated(self) -> bool:
        return bool(self.flags & Module.ACC_MANDATED)

    @is_mandated.setter
    def is_mandated(self, value: bool) -> None:
        if value:
            self.flags |= Module.ACC_MANDATED
        else:
            self.flags &= ~Module.ACC_MANDATED

    def __init__(
            self, module: ConstInfo, flags: int, version: ConstInfo | None,
            requires: Iterable["Module.Require"] | None = None,
            exports:   Iterable["Module.Export"] | None = None,
            opens:       Iterable["Module.Open"] | None = None,
            uses:            Iterable[ConstInfo] | None = None,
            provides: Iterable["Module.Provide"] | None = None,
    ) -> None:
        super().__init__()
        self.module = module
        self.flags = flags
        self.version = version

        self.requires: list[Module.Require] = []
        self.exports:   list[Module.Export] = []
        self.opens:       list[Module.Open] = []
        self.uses:          list[ConstInfo] = []
        self.provides: list[Module.Provide] = []

        if requires is not None:
            self.requires.extend(requires)
        if exports is not None:
            self.exports.extend(exports)
        if opens is not None:
            self.opens.extend(opens)
        if uses is not None:
            self.uses.extend(uses)
        if provides is not None:
            self.provides.extend(provides)

    def __repr__(self) -> str:
        uses_str = ", ".join(map(str, self.uses))
        return (
            f"<Module(module={self.module!s}, flags=0x{self.flags:04x}, version={self.version!s}, "
            f"requires={self.requires!r}, exports={self.exports!r}, opens={self.opens!r}, uses=[{uses_str}], "
            f"provides={self.provides!r})>"
        )

    def __str__(self) -> str:
        version_str = str(self.version) if self.version is not None else "[none]"
        requires_str = ",".join(map(str, self.requires))
        exports_str = ",".join(map(str, self.exports))
        opens_str = ",".join(map(str, self.opens))
        uses_str = ",".join(map(str, self.uses))
        provides_str = ",".join(map(str, self.provides))
        return (  # Wow, this is kinda a mess...
            f"Module({self.module!s},0x{self.flags:04x},{version_str},[{requires_str}],[{exports_str}],[{opens_str}],"
            f"[{uses_str}],[{provides_str}])"
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Module) and
            self.module == other.module and
            self.flags == other.flags and
            self.version == other.version and
            self.requires == other.requires and
            self.exports == other.exports and
            self.opens == other.opens and
            self.uses == other.uses and
            self.provides == other.provides
        )

    def _write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None:
        stream.write(pack_HHH(
            pool.add(self.module), self.flags, pool.add(self.version) if self.version is not None else 0,
        ))

        stream.write(pack_H(len(self.requires)))
        for require in self.requires:
            stream.write(pack_HHH(
                pool.add(require.module),
                require.flags,
                pool.add(require.version) if require.version is not None else 0,
            ))

        stream.write(pack_H(len(self.exports)))
        for export in self.exports:
            stream.write(pack_HHH(pool.add(export.package), export.flags, len(export.exports_to)))
            for export_to in export.exports_to:
                stream.write(pack_H(pool.add(export_to)))

        stream.write(pack_H(len(self.opens)))
        for open_ in self.opens:
            stream.write(pack_HHH(pool.add(open_.package), open_.flags, len(open_.opens_to)))
            for open_to in open_.opens_to:
                stream.write(pack_H(pool.add(open_to)))

        stream.write(pack_H(len(self.uses)))
        for use in self.uses:
            stream.write(pack_H(pool.add(use)))

        stream.write(pack_H(len(self.provides)))
        for provide in self.provides:
            stream.write(pack_HH(pool.add(provide.interface), len(provide.impls)))
            for impl in provide.impls:
                stream.write(pack_H(pool.add(impl)))

    class Require:
        """
        A module requires entry.

        Specifies a module that this module depends on.

        Attributes
        ----------
        ACC_TRANSITIVE: int
            Access flag denoting that any modules depending on this module also depend
            on this dependency transitively.
        ACC_STATIC_PHASE: int
            Access flag denoting that this dependency is mandatory at compile time, but
            optional at runtime.
        ACC_SYNTHETIC: int
            Access flag denoting that this dependency was not declared in the source.
        ACC_MANDATED: int
            Access flag denoting that this dependency was implicitly declared.

        module: ConstInfo
            A module constant, used to represent the module that this module depends on.
        flags: int
            A bitmask indicating the properties of this dependency.
        version: ConstInfo | None
            A UTF8 constant, used as the version of the module that this module depends
            on.
            If `None`, no version information about the dependency is available.
        """

        __slots__ = ("module", "flags", "version")

        ACC_TRANSITIVE   = 0x0020
        ACC_STATIC_PHASE = 0x0040
        ACC_SYNTHETIC    = 0x1000
        ACC_MANDATED     = 0x8000

        def __init__(self, module: ConstInfo, flags: int, version: ConstInfo | None) -> None:
            self.module = module
            self.flags = flags
            self.version = version

        def __repr__(self) -> str:
            return f"<Module.Require(module={self.module!s}, flags=0x{self.flags:04x}, version={self.version!s})>"

        def __str__(self) -> str:
            version_str = str(self.version) if self.version is not None else "[none]"
            return f"module_require({self.module!s},0x{self.flags:04x},{version_str})"

        def __eq__(self, other: object) -> bool:
            return (
                isinstance(other, Module.Require) and
                self.module == other.module and
                self.flags == other.flags and
                self.version == other.version
            )

    class Export:
        """
        A module exports entry.

        Specifies a package exported by the current module.
        Only public and protected types and/or members may be accessed outside the
        module in this way.

        Attributes
        ----------
        ACC_SYNTHETIC: int
            Access flag denoting that this export was not declared in the source.
        ACC_MANDATED: int
            Access flag denoting that this export was implicitly declared.

        package: ConstInfo
            A package constant, used to represent a package exported by the module.
        flags: int
            A bitmask indicating the properties of this export.
        exports_to: list[ConstInfo]
            A list of module constants, used to represent the external modules that can
            use this export.
            If empty, all modules may use this export.
        """

        __slots__ = ("package", "flags", "exports_to")

        ACC_SYNTHETIC = 0x1000
        ACC_MANDATED  = 0x8000

        def __init__(self, package: ConstInfo, flags: int, exports_to: Iterable[ConstInfo] | None = None) -> None:
            self.package = package
            self.flags = flags
            self.exports_to: list[ConstInfo] = []

            if exports_to is not None:
                self.exports_to.extend(exports_to)

        def __repr__(self) -> str:
            exports_to_str = ", ".join(map(str, self.exports_to))
            return (
                f"<Module.Export(package={self.package!s}, flags=0x{self.flags:04x}, exports_to=[{exports_to_str}])>"
            )

        def __str__(self) -> str:
            exports_to_str = ",".join(map(str, self.exports_to))
            return f"module_export({self.package!s},0x{self.flags:04x},[{exports_to_str}])"

        def __eq__(self, other: object) -> bool:
            return (
                isinstance(other, Module.Export) and
                self.package == other.package and
                self.flags == other.flags and
                self.exports_to == other.exports_to
            )

    class Open:
        """
        A module opens entry.

        Specifies a package opened (available via reflection APIs) by the current module.

        Attributes
        ----------
        ACC_SYNTHETIC: int
            Access flag denoting that this opening was not declared in the source.
        ACC_MANDATED: int
            Access flag denoting that this opening was implicitly declared.

        package: ConstInfo
            A package constant, used to represent a package opened by the module.
        flags: int
            A bitmask indicating the properties of this opening.
        opens_to: list[ConstInfo]
            A list of module constants, used to represent the external modules that can
            use this opening.
            If empty, any other module may use this opening.
        """

        __slots__ = ("package", "flags", "opens_to")

        ACC_SYNTHETIC = 0x1000
        ACC_MANDATED  = 0x8000

        def __init__(self, package: ConstInfo, flags: int, opens_to: Iterable[ConstInfo] | None = None) -> None:
            self.package = package
            self.flags = flags
            self.opens_to: list[ConstInfo] = []

            if opens_to is not None:
                self.opens_to.extend(opens_to)

        def __repr__(self) -> str:
            opens_to_str = ", ".join(map(str, self.opens_to))
            return f"<Module.Open(package={self.package!s}, flags=0x{self.flags:04x}, opens_to=[{opens_to_str}])>"

        def __str__(self) -> str:
            opens_to_str = ",".join(map(str, self.opens_to))
            return f"module_open({self.package!s},0x{self.flags:04x},[{opens_to_str}])"

        def __eq__(self, other: object) -> bool:
            return (
                isinstance(other, Module.Open) and
                self.package == other.package and
                self.flags == other.flags and
                self.opens_to == other.opens_to
            )

    class Provide:
        """
        A module provides entry.

        Specifies a list of service implementations for a given service interface.

        Attributes
        ----------
        interface: ConstInfo
            A class constant, used to represent the service interface which the current
            module provides implementations for.
        impls: list[ConstInfo]
            A list of class constants, used to represent classes that implement the given
            service interface.
        """

        __slots__ = ("interface", "impls")

        def __init__(self, interface: ConstInfo, impls: Iterable[ConstInfo] | None = None) -> None:
            self.interface = interface
            self.impls: list[ConstInfo] = []

            if impls is not None:
                self.impls.extend(impls)

        def __repr__(self) -> str:
            impls_str = ", ".join(map(str, self.impls))
            return f"<Module.Provide(interface={self.interface!s}, impls=[{impls_str}])>"

        def __str__(self) -> str:
            impls_str = ",".join(map(str, self.impls))
            return f"module_provide({self.interface!s},[{impls_str}])"

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Module.Provide) and self.interface == other.interface and self.impls == other.impls


class ModulePackages(AttributeInfo):
    """
    The ModulePackages attribute.

    A variable length attribute used to store information about the packages of a
    module.
    These packages may be exported, opened, and/or may contain service
    implementations.
    They may also be none of the above.

    Attributes
    ----------
    packages: list[ConstInfo]
        A list of package constants which are relevant to the current module.
    """

    __slots__ = ("packages",)

    tag = b"ModulePackages"
    since = JAVA_9
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            count, = unpack_H(stream.read(2))
            packages = [pool[index] for index, in iter_unpack_H(stream.read(count * 2))]
            if len(packages) != count:
                return result.err(ValueError("module packages underread"))
            return result.ok(cls(packages))
        return result

    def __init__(self, packages: Iterable[ConstInfo] | None = None) -> None:
        super().__init__()
        self.packages: list[ConstInfo] = []
        if packages is not None:
            self.packages.extend(packages)

    def __repr__(self) -> str:
        packages_str = ", ".join(map(str, self.packages))
        return f"<ModulePackages(packages=[{packages_str}])>"

    def __str__(self) -> str:
        packages_str = ",".join(map(str, self.packages))
        return f"ModulePackages([{packages_str}])"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ModulePackages) and self.packages == other.packages

    def __getitem__(self, index: int) -> ConstInfo:
        return self.packages[index]

    def __setitem__(self, index: int, value: ConstInfo) -> None:
        self.packages[index] = value

    def __delitem__(self, key: int | ConstInfo) -> None:
        if isinstance(key, int):
            del self.packages[key]
        else:
            self.packages.remove(key)

    def __len__(self) -> int:
        return len(self.packages)

    def write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None:
        stream.write(pack_HIH(
            pool.add(self.name or UTF8Info(self.tag)), 2 + len(self.extra) + len(self.packages) * 2, len(self.packages),
        ))
        for package in self.packages:
            stream.write(pack_H(pool.add(package)))
        stream.write(self.extra)


class ModuleMainClass(AttributeInfo):
    """
    The ModuleMainClass attribute.

    A fixed length attribute used to store the main class of the current module.

    Attributes
    ----------
    class_: ConstInfo
        A class constant, used as the main class of this module.
    """

    __slots__ = ("class_",)

    tag = b"ModuleMainClass"
    since = JAVA_9
    locations = frozenset({AttributeInfo.LOC_CLASS})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]:
        with Result[Self]() as result:
            index, = unpack_H(stream.read(2))
            return result.ok(cls(pool[index]))
        return result

    def __init__(self, class_: ConstInfo) -> None:
        super().__init__()
        self.class_ = class_

    def __repr__(self) -> str:
        return f"<ModuleMainClass(class_={self.class_!s})>"

    def __str__(self) -> str:
        return f"ModuleMainClass({self.class_!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ModuleMainClass) and self.class_ == other.class_

    def write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None:
        stream.write(pack_HIH(pool.add(self.name or UTF8Info(self.tag)), 2 + len(self.extra), pool.add(self.class_)))
        stream.write(self.extra)

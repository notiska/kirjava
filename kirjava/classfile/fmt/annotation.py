#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "ElementValue", "Annotation", "ParameterAnnotations",
    "TargetInfo", "TypePath", "TypeAnnotation",
    "ConstValue", "EnumConstValue", "ClassValue", "AnnotationValue", "ArrayValue",
    "TypeParameterTarget", "SuperTypeTarget", "TypeParameterBoundTarget", "EmptyTarget",
    "FormalParameterTarget", "ThrowsTarget", "LocalVarTarget", "CatchTarget", "OffsetTarget",
    "TypeArgumentTarget",
)

"""
JVM class file annotation structs found in annotation attributes.
"""

import sys
import typing
from typing import IO, Iterable, Union

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .constants import ConstInfo
from .._struct import *

if typing.TYPE_CHECKING:
    from .pool import ConstPool


class ElementValue:
    """
    An element_value union.

    Attributes
    ----------
    tags: bytes
        The tags (kinds) that identify this type of element value.
    kind: int
        A single ASCII character indicating the kind of value.

    Methods
    -------
    lookup(kind: int) -> type[ElementValue] | None
        Looks up an element value type by kind.
    read(stream: IO[bytes], pool: ConstPool) -> Self
        Reads an annotation element value from a binary stream.
    write(self, stream: IO[bytes], pool: ConstPool) -> None
        Writes this annotation element value to a binary stream.
    """

    __slots__ = ("kind",)

    tags: bytes

    _cache: dict[int, type["ElementValue"] | None] = {}

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", kind: int) -> Self:
        """
        Internal annotation element value read.
        """

        raise NotImplementedError(f"_read() is not implemented for {cls!r}")

    @classmethod
    def lookup(cls, kind: int) -> type["ElementValue"] | None:
        """
        Looks up an element value type by kind.

        Parameters
        ----------
        kind: int
            The kind of element value.

        Returns
        -------
        type[ElementValue] | None
            The element value type, or `None` if not found.
        """

        for subclass in cls.__subclasses__():
            if kind in subclass.tags:
                return subclass
        return None

    @classmethod
    def read(cls, stream: IO[bytes], pool: "ConstPool") -> "ElementValue":
        """
        Reads an annotation element value from a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        pool: ConstPool
            The class file constant pool.
        """

        kind, = stream.read(1)
        subclass = cls._cache.get(kind)
        if subclass is None:
            subclass = cls.lookup(kind)
            cls._cache[kind] = subclass
        if subclass is None:  # Not much more we can do at this point.
            raise ValueError(f"invalid kind {kind} for element value")
        return subclass._read(stream, pool, kind)

    def __init__(self, kind: int) -> None:
        self.kind = kind

    def __repr__(self) -> str:
        raise NotImplementedError(f"repr() is not implemented for {type(self)!r}")

    def __str__(self) -> str:
        raise NotImplementedError(f"str() is not implemented for {type(self)!r}")

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError(f"== is not implemented for {type(self)!r}")

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        """
        Writes this annotation element value to a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        pool: ConstPool
            The class file constant pool.
        """

        raise NotImplementedError(f"write() is not implemented for {type(self)!r}")


class Annotation:
    """
    An annotation struct.

    Attributes
    ----------
    type: ConstInfo
        A UTF8 constant, used as a descriptor detailing the annotation's type.
    elements: list[Annotation.NamedElement]
        A list of name and element value pairs.

    Methods
    -------
    read(stream: IO[bytes], pool: ConstPool) -> Self
        Reads an annotation from a binary stream.
    write(self, stream: IO[bytes], pool: ConstPool) -> None
        Writes this annotation to a binary stream.
    """

    __slots__ = ("type", "elements")

    @classmethod
    def read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        """
        Reads an annotation from a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        pool: ConstPool
            The class file constant pool.
        """

        type_index, count = unpack_HH(stream.read(4))
        elements = []
        for _ in range(count):
            name_index, = unpack_H(stream.read(2))
            value = ElementValue.read(stream, pool)
            elements.append(Annotation.NamedElement(pool[name_index], value))
        return cls(pool[type_index], elements)

    def __init__(self, type_: ConstInfo, elements: Iterable["Annotation.NamedElement"] | None = None) -> None:
        self.type = type_
        self.elements: list[Annotation.NamedElement] = []

        # TODO: It may also be nice to accept a dictionary for a more Pythonic approach.
        if elements is not None:
            self.elements.extend(elements)

    def __repr__(self) -> str:
        return f"<Annotation(type={self.type!s}, elements={self.elements!r})>"

    def __str__(self) -> str:
        elements_str = ",".join(map(str, self.elements))
        return f"annotation({self.type!s},[{elements_str}])"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Annotation) and self.type == other.type and self.elements == other.elements

    def __getitem__(self, index: int) -> "Annotation.NamedElement":
        return self.elements[index]

    def __setitem__(self, index: int, value: "Annotation.NamedElement") -> None:
        self.elements[index] = value

    def __delitem__(self, key: Union[int, "Annotation.NamedElement"]) -> None:
        if isinstance(key, int):
            del self.elements[key]
        else:
            self.elements.remove(key)

    def __len__(self) -> int:
        return len(self.elements)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        """
        Writes this annotation to a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        pool: ConstPool
            The class file constant pool.
        """

        stream.write(pack_HH(pool.add(self.type), len(self.elements)))
        for element in self.elements:  # TODO: Maybe infinite look detection with nested elements?
            stream.write(pack_H(pool.add(element.name)))
            element.value.write(stream, pool)

    class NamedElement:
        """
        An element name and value pair.

        Attributes
        ----------
        name: ConstInfo
            A UTF8 constant, used as the name of the element.
        value: ElementValue
            The element value.
        """

        __slots__ = ("name", "value")

        def __init__(self, name: ConstInfo, value: ElementValue) -> None:
            self.name = name
            self.value = value

        def __repr__(self) -> str:
            return f"<Annotation.NamedElement(name={self.name!s}, value={self.value!r})>"

        def __str__(self) -> str:
            return f"{self.name!s}={self.value!s}"

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Annotation.NamedElement) and self.name == other.name and self.value == other.value

        def __iter__(self) -> Iterable[ConstInfo | ElementValue]:
            return iter((self.name, self.value))


class ParameterAnnotations:
    """
    A parameter_annotations struct.

    Describes annotations found on formal method parameters.

    Attributes
    ----------
    annotations: list[Annotation]
        A list of annotations declared on a single formal parameter.

    Methods
    -------
    read(stream: IO[bytes], pool: ConstPool) -> Self
        Reads parameter annotations from a binary stream.
    write(self, stream: IO[bytes], pool: ConstPool) -> None
        Writes these parameter annotations to a binary stream.
    """

    __slots__ = ("annotations",)

    @classmethod
    def read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        """
        Reads parameter annotations from a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        pool: ConstPool
            The class file constant pool.
        """

        count, = unpack_H(stream.read(2))
        return cls([Annotation.read(stream, pool) for _ in range(count)])

    def __init__(self, annotations: Iterable[Annotation] | None = None) -> None:
        self.annotations: list[Annotation] = []
        if annotations is not None:
            self.annotations.extend(annotations)

    def __repr__(self) -> str:
        return f"<ParameterAnnotations(annotations={self.annotations!r})>"

    def __str__(self) -> str:
        annotations_str = ",".join(map(str, self.annotations))
        return f"parameter_annotations([{annotations_str}])"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ParameterAnnotations) and self.annotations == other.annotations

    def __getitem__(self, index: int) -> Annotation:
        return self.annotations[index]

    def __setitem__(self, index: int, value: Annotation) -> None:
        self.annotations[index] = value

    def __delitem__(self, key: int | Annotation) -> None:
        if isinstance(key, int):
            del self.annotations[key]
        else:
            self.annotations.remove(key)

    def __len__(self) -> int:
        return len(self.annotations)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        """
        Writes these parameter annotations to a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        pool: ConstPool
            The class file constant pool.
        """

        stream.write(pack_H(len(self.annotations)))
        for annotation in self.annotations:
            annotation.write(stream, pool)


class TargetInfo:
    """
    A target_info union.

    Attributes
    ----------
    GENERIC_CLASS_TYPE_PARAMETER: int
        Indicates that the target is a type parameter declaration on a generic class.
    GENERIC_METHOD_TYPE_PARAMETER: int
        Indicates that the target is a type parameter on a generic method.
    SUPER_CLASS_OR_INTERFACE_TYPE: int
        Indicates that the target is a type in the `extends` or `implements` clause
        of a class.
    GENERIC_CLASS_TYPE_PARAMETER_BOUND: int
        Indicates that the target is a bound on a type parameter in a generic class
        declaration.
    GENERIC_METHOD_TYPE_PARAMETER_BOUND: int
        Indicates that the target is a bound on a type parameter in a generic method
        declaration.
    FIELD_OR_RECORD_COMPONENT_TYPE: int
        Indicates that the target is a type in either a field or record component
        declaration.
    METHOD_RETURN_TYPE_OR_NEW_OBJECT: int
        Indicates that the target is either the return type of a method or the type
        of a newly constructed object.
    METHOD_RECEIVER_TYPE: int
        Indicates that the target is the receiver type of a method.
    FORMAL_PARAMETER_TYPE: int
        Indicates that the target is the type of a formal parameter in a method
        declaration.
    THROWS_CLAUSE_TYPE: int
        Indicates that the target is a type in a `throws` clause of a method.
    LOCAL_VARIABLE_TYPE: int
        Indicates that the target is the type in a local variable declaration.
    RESOURCE_VARIABLE_TYPE: int
        Indicates that the target is the type in a resource declaration.
    CATCH_PARAMETER_TYPE: int
        Indicates that the target is a type in a catch clause.
    INSTANCEOF_TYPE: int
        Indicates that the target is the type in an `instanceof` expression.
    NEW_TYPE: int
        Indicates that the target is the type in a `new` expression.
    CONSTRUCTOR_REFERENCE_TYPE: int
        Indicates that the target is the type in a constructor reference expression.
    METHOD_REFERENCE_TYPE: int
        Indicates that the target is the type in a method reference expression.
    CAST_TYPE: int
        Indicates that the target is the type in a cast expression.
    GENERIC_CONSTRUCTOR_TYPE_ARGUMENT: int
        Indicates that the target is a type argument for a generic constructor in
        an explicit constructor invocation expression.
    GENERIC_METHOD_TYPE_ARGUMENT: int
        Indicates that the target is a type argument for a generic method in a
        method invocation expression.
    CONSTRUCTOR_REFERENCE_TYPE_ARGUMENT: int
        Indicates that the target is a type argument for a generic constructor in
        a method reference expression using `::new`.
    METHOD_REFERENCE_TYPE_ARGUMENT: int
        Indicates that the target is a type argument for a generic method in a method
        reference expression.

    tags: frozenset[int]
        The set of tags (kinds) that identify this type of target.
    kind: int
        The kind of target on which the annotation appears.

    Methods
    -------
    lookup(kind: int) -> type[TargetInfo] | None
        Looks up a target info type by kind.
    read(stream: IO[bytes]) -> TargetInfo
        Reads a target info from a binary stream.
    write(self, stream: IO[bytes]) -> None
        Writes this target info to a binary stream.
    """

    __slots__ = ("kind",)

    GENERIC_CLASS_TYPE_PARAMETER        = 0x00
    GENERIC_METHOD_TYPE_PARAMETER       = 0x01

    SUPER_CLASS_OR_INTERFACE_TYPE       = 0x10

    GENERIC_CLASS_TYPE_PARAMETER_BOUND  = 0x11
    GENERIC_METHOD_TYPE_PARAMETER_BOUND = 0x12

    FIELD_OR_RECORD_COMPONENT_TYPE      = 0x13
    METHOD_RETURN_TYPE_OR_NEW_OBJECT    = 0x14
    METHOD_RECEIVER_TYPE                = 0x15

    FORMAL_PARAMETER_TYPE               = 0x16

    THROWS_CLAUSE_TYPE                  = 0x17

    LOCAL_VARIABLE_TYPE                 = 0x40
    RESOURCE_VARIABLE_TYPE              = 0x41

    CATCH_PARAMETER_TYPE                = 0x42

    INSTANCEOF_TYPE                     = 0x43
    NEW_TYPE                            = 0x44
    CONSTRUCTOR_REFERENCE_TYPE          = 0x45
    METHOD_REFERENCE_TYPE               = 0x46

    CAST_TYPE                           = 0x47
    GENERIC_CONSTRUCTOR_TYPE_ARGUMENT   = 0x48
    GENERIC_METHOD_TYPE_ARGUMENT        = 0x49
    CONSTRUCTOR_REFERENCE_TYPE_ARGUMENT = 0x4a
    METHOD_REFERENCE_TYPE_ARGUMENT      = 0x4b

    _KINDS = {
        GENERIC_CLASS_TYPE_PARAMETER:        "GENERIC_CLASS_TYPE_PARAMETER",
        GENERIC_METHOD_TYPE_PARAMETER:       "GENERIC_METHOD_TYPE_PARAMETER",
        SUPER_CLASS_OR_INTERFACE_TYPE:       "SUPER_CLASS_OR_INTERFACE_TYPE",
        GENERIC_CLASS_TYPE_PARAMETER_BOUND:  "GENERIC_CLASS_TYPE_PARAMETER_BOUND",
        GENERIC_METHOD_TYPE_PARAMETER_BOUND: "GENERIC_METHOD_TYPE_PARAMETER_BOUND",
        FIELD_OR_RECORD_COMPONENT_TYPE:      "FIELD_OR_RECORD_COMPONENT_TYPE",
        METHOD_RETURN_TYPE_OR_NEW_OBJECT:    "METHOD_RETURN_TYPE_OR_NEW_OBJECT",
        METHOD_RECEIVER_TYPE:                "METHOD_RECEIVER_TYPE",
        FORMAL_PARAMETER_TYPE:               "FORMAL_PARAMETER_TYPE",
        THROWS_CLAUSE_TYPE:                  "THROWS_CLAUSE_TYPE",
        LOCAL_VARIABLE_TYPE:                 "LOCAL_VARIABLE_TYPE",
        RESOURCE_VARIABLE_TYPE:              "RESOURCE_VARIABLE_TYPE",
        CATCH_PARAMETER_TYPE:                "CATCH_PARAMETER_TYPE",
        INSTANCEOF_TYPE:                     "INSTANCEOF_TYPE",
        NEW_TYPE:                            "NEW_TYPE",
        CONSTRUCTOR_REFERENCE_TYPE:          "CONSTRUCTOR_REFERENCE_TYPE",
        METHOD_REFERENCE_TYPE:               "METHOD_REFERENCE_TYPE",
        CAST_TYPE:                           "CAST_TYPE",
        GENERIC_CONSTRUCTOR_TYPE_ARGUMENT:   "GENERIC_CONSTRUCTOR_TYPE_ARGUMENT",
        GENERIC_METHOD_TYPE_ARGUMENT:        "GENERIC_METHOD_TYPE_ARGUMENT",
        CONSTRUCTOR_REFERENCE_TYPE_ARGUMENT: "CONSTRUCTOR_REFERENCE_TYPE_ARGUMENT",
        METHOD_REFERENCE_TYPE_ARGUMENT:      "METHOD_REFERENCE_TYPE_ARGUMENT",
    }

    tags: frozenset[int]

    _cache: dict[int, type["TargetInfo"] | None] = {}

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        """
        Internal target info read.
        """

        raise NotImplementedError(f"_read() is not implemented for {cls!r}")

    @classmethod
    def lookup(cls, kind: int) -> type["TargetInfo"] | None:
        """
        Looks up a target info type by kind.

        Parameters
        ----------
        kind: int
            The kind of target info.

        Returns
        -------
        type[TargetInfo] | None
            The target info type, or `None` if not found.
        """

        for subclass in cls.__subclasses__():
            if kind in subclass.tags:
                return subclass
        return None

    @classmethod
    def read(cls, stream: IO[bytes]) -> "TargetInfo":
        """
        Reads a target info from a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.

        Returns
        -------
        TargetInfo
            The read target info.
        """

        kind, = stream.read(1)
        subclass = cls._cache.get(kind)
        if subclass is None:
            subclass = cls.lookup(kind)
            cls._cache[kind] = subclass
        if subclass is None:
            raise ValueError(f"invalid kind 0x{kind:02x} for target info")
        return subclass._read(stream, kind)

    def __init__(self, kind: int) -> None:
        self.kind = kind

    def __repr__(self) -> str:
        raise NotImplementedError(f"repr() is not implemented for {type(self)!r}")

    def __str__(self) -> str:
        raise NotImplementedError(f"str() is not implemented for {type(self)!r}")

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError(f"== is not implemented for {type(self)!r}")

    def write(self, stream: IO[bytes]) -> None:
        """
        Writes this target info to a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        """

        raise NotImplementedError(f"write() is not implemented for {type(self)!r}")


class TypePath:
    """
    A type_path struct.

    Used to identify which part of a type is annotated, as reference types may have
    additional locations where annotations can appear.

    Attributes
    ----------
    path: list[TypePath.Segment]
        A list of type path segments.

    Methods
    -------
    read(stream: IO[bytes]) -> Self
        Reads a type path from a binary stream.
    write(self, stream: IO[bytes]) -> None
        Writes this type path to a binary stream.
    """

    __slots__ = ("path",)

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads a type path from a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        """

        count, = stream.read(1)
        segments = []
        for _ in range(count):
            kind, index = stream.read(2)
            segments.append(TypePath.Segment(kind, index))
        return cls(segments)

    def __init__(self, path: Iterable["TypePath.Segment"] | None = None) -> None:
        self.path: list[TypePath.Segment] = []
        if path is not None:
            self.path.extend(path)

    def __repr__(self) -> str:
        return f"<TypePath(path={self.path!r})>"

    def __str__(self) -> str:
        path_str = ",".join(map(str, self.path))
        return f"type_path([{path_str}])"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TypePath) and self.path == other.path

    def __getitem__(self, index: int) -> "TypePath.Segment":
        return self.path[index]

    def __setitem__(self, index: int, value: "TypePath.Segment") -> None:
        self.path[index] = value

    def __delitem__(self, key: Union[int, "TypePath.Segment"]) -> None:
        if isinstance(key, int):
            del self.path[key]
        else:
            self.path.remove(key)

    def __len__(self) -> int:
        return len(self.path)

    def write(self, stream: IO[bytes]) -> None:
        """
        Writes this type path to a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        """

        stream.write(bytes((len(self.path),)))
        for segment in self.path:
            stream.write(bytes((segment.kind, segment.index)))

    class Segment:
        """
        A type_path segment.

        Attributes
        ----------
        ARRAY_NESTED: int
            Indicates that the annotation appears deeper in an array type.
        TYPE_NESTED: int
            Indicates that the annotation appears on a nested type.
        WILDCARD_BOUND: int
            Indicates that the annotation appears on the bound of a wildcard of a
            parameterised type.
        TYPE_ARGUMENT: int
            Indicates that the annotation appears on a type argument of a parameterised
            type.

        kind: int
            Describes how to interpret this path segment.
        index: int
            Either zero or the index of the type argument in a parameterised type.
        """

        __slots__ = ("kind", "index")

        ARRAY_NESTED   = 0
        TYPE_NESTED    = 1
        WILDCARD_BOUND = 2
        TYPE_ARGUMENT  = 3

        _KINDS = {
            ARRAY_NESTED:   "ARRAY_NESTED",
            TYPE_NESTED:    "TYPE_NESTED",
            WILDCARD_BOUND: "WILDCARD_BOUND",
            TYPE_ARGUMENT:  "TYPE_ARGUMENT",
        }

        def __init__(self, kind: int, index: int = 0) -> None:
            self.kind = kind
            self.index = index

        def __repr__(self) -> str:
            kind_str = TypePath.Segment._KINDS.get(self.kind) or str(self.kind)
            return f"<TypePath.Segment(kind={kind_str}, index={self.index})>"

        def __str__(self) -> str:
            kind_str = TypePath.Segment._KINDS.get(self.kind) or str(self.kind)
            return f"{kind_str}:{self.index}"

        def __eq__(self, other: object) -> bool:
            return isinstance(other, TypePath.Segment) and self.kind == other.kind and self.index == other.index

        def __iter__(self) -> Iterable[int]:
            return iter((self.kind, self.index))


class TypeAnnotation(Annotation):
    """
    A type_annotation struct.

    Describes annotations found on a type used in a declaration or expression.

    Attributes
    ----------
    info: TargetInfo
        Denotes precisely which type, in a declaration or expression, is annotated.
    path: TypePath
        Denotes precisely which part of the indicated type is annotated.
    """

    __slots__ = ("info", "path")

    @classmethod
    def read(cls, stream: IO[bytes], pool: "ConstPool") -> Self:
        info = TargetInfo.read(stream)
        path = TypePath.read(stream)

        # Unfortunately, this is just a copy+paste because we can't invoke the super type's read method.
        type_index, count = unpack_HH(stream.read(4))
        elements = []
        for _ in range(count):
            name_index, = unpack_H(stream.read(2))
            value = ElementValue.read(stream, pool)
            elements.append(Annotation.NamedElement(pool[name_index], value))

        return cls(pool[type_index], info, path, elements)

    def __init__(
            self, type_: ConstInfo, info: TargetInfo, path: TypePath,
            elements: Iterable["Annotation.NamedElement"] | None = None,
    ) -> None:
        super().__init__(type_, elements)
        self.info = info
        self.path = path

    def __repr__(self) -> str:
        return (
            f"<TypeAnnotation(type={self.type!s}, info={self.info!r}, "
            f"path={self.path!r}, elements={self.elements!r})>"
        )

    def __str__(self) -> str:
        elements_str = ",".join(map(str, self.elements))
        return f"type_annotation({self.type!s},{self.info!s},{self.path!s},[{elements_str}])"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TypeAnnotation) and
            self.type == other.type and
            self.info == other.info and
            self.path == other.path and
            self.elements == other.elements
        )

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        self.info.write(stream)
        self.path.write(stream)
        super().write(stream, pool)


# ---------------------------------------- Element Values ---------------------------------------- #

class ConstValue(ElementValue):
    """
    An element_value with a constant value.

    Attributes
    ----------
    BYTE: Int
        Kind denoting that the constant is a byte (internally int).
    CHAR: int
        Kind denoting that the constant is a char (internally int).
    DOUBLE: int
        Kind denoting that the constant is a double.
    FLOAT: int
        Kind denoting that the constant is a float.
    INT: int
        Kind denoting that the constant is an int.
    LONG: int
        Kind denoting that the constant value is a long.
    SHORT: int
        Kind denoting that the constant value is a short (internally int).
    BOOLEAN: int
        Kind denoting that the constant value is a boolean (internally int).
    STRING: int
        Kind denoting that the constant value is a string.

    value: ConstInfo
        The constant value.
    """

    __slots__ = ("value",)

    tags = b"BCDFIJSZs"

    BYTE    = tags[0]  # ord("B")
    CHAR    = tags[1]  # ord("C")
    DOUBLE  = tags[2]  # ord("D")
    FLOAT   = tags[3]  # ord("F")
    INT     = tags[4]  # ord("I")
    LONG    = tags[5]  # ord("J")
    SHORT   = tags[6]  # ord("S")
    BOOLEAN = tags[7]  # ord("Z")
    STRING  = tags[8]  # ord("s")

    _KINDS = {
        BYTE:    "BYTE",
        CHAR:    "CHAR",
        DOUBLE:  "DOUBLE",
        FLOAT:   "FLOAT",
        INT:     "INT",
        LONG:    "LONG",
        SHORT:   "SHORT",
        BOOLEAN: "BOOLEAN",
        STRING:  "STRING",
    }

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", kind: int) -> Self:
        index, = unpack_H(stream.read(2))
        return cls(kind, pool[index])

    def __init__(self, kind: int, value: ConstInfo) -> None:
        # if not kind in ConstValue.tags:
        #     raise ValueError(f"invalid kind {kind} for {type(self)!r}")
        super().__init__(kind)
        self.value = value

    def __repr__(self) -> str:
        kind_str = ConstValue._KINDS.get(self.kind) or str(self.kind)
        return f"<ConstValue(kind={kind_str}, value={self.value!s})>"

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ConstValue) and self.kind == other.kind and self.value == other.value

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(self.kind, pool.add(self.value)))


class EnumConstValue(ElementValue):
    """
    An element_value with an enum constant value.

    Attributes
    ----------
    type: ConstInfo
        A UTF8 constant, used as a descriptor detailing enum's type.
    name: ConstInfo
        A UTF8 constant, used as the name for enum constant's field.
    """

    __slots__ = ("type", "name")

    tags = b"e"

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", kind: int) -> Self:
        type_index, name_index = unpack_HH(stream.read(4))
        return cls(pool[type_index], pool[name_index])

    def __init__(self, type_: ConstInfo, name: ConstInfo) -> None:
        super().__init__(EnumConstValue.tags[0])
        self.type = type_
        self.name = name

    def __repr__(self) -> str:
        return f"<EnumConstValue(type={self.type!s}, name={self.name!s})>"

    def __str__(self) -> str:
        return f"{self.type!s}.{self.name!s}"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, EnumConstValue) and self.type == other.type and self.name == other.name

    # def __iter__(self) -> Iterable[ConstInfo]:
    #     return iter((self.type, self.name))

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BHH(EnumConstValue.tags[0], pool.add(self.type), pool.add(self.name)))


class ClassValue(ElementValue):
    """
    An element_value with a class value.

    Attributes
    ----------
    type: ConstInfo
        A UTF8 constant, used as a descriptor detailing the class type.
        Special cases occur for primitive and/or void types, in which the referenced
        descriptor will simply be said primitive.
    """

    __slots__ = ("type",)

    tags = b"c"

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", kind: int) -> Self:
        index, = unpack_H(stream.read(2))
        return cls(pool[index])

    def __init__(self, type_: ConstInfo) -> None:
        super().__init__(ClassValue.tags[0])
        self.type = type_

    def __repr__(self) -> str:
        return f"<ClassValue(type={self.type!s})>"

    def __str__(self) -> str:
        return str(self.type)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ClassValue) and self.type == other.type

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(ClassValue.tags[0], pool.add(self.type)))


class AnnotationValue(ElementValue):
    """
    An element_value with an annotation value.

    Attributes
    ----------
    annotation: Annotation
        The nested annotation value.
    """

    __slots__ = ("annotation",)

    tags = b"@"

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", kind: int) -> Self:
        return cls(Annotation.read(stream, pool))

    def __init__(self, annotation: Annotation) -> None:
        super().__init__(AnnotationValue.tags[0])
        self.annotation = annotation

    def __repr__(self) -> str:
        return f"<AnnotationValue(annotation={self.annotation!r})>"

    def __str__(self) -> str:
        return str(self.annotation)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AnnotationValue) and self.annotation == other.annotation

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(AnnotationValue.tags)
        self.annotation.write(stream, pool)


class ArrayValue(ElementValue):
    """
    An element_value with an array value.

    Attributes
    ----------
    values: list[ElementValue]
        A list of nested elements.
    """

    __slots__ = ("values",)

    tags = b"["

    @classmethod
    def _read(cls, stream: IO[bytes], pool: "ConstPool", kind: int) -> Self:
        count, = unpack_H(stream.read(2))
        return cls([ElementValue.read(stream, pool) for _ in range(count)])

    def __init__(self, values: Iterable[ElementValue] | None = None) -> None:
        super().__init__(ArrayValue.tags[0])
        self.values: list[ElementValue] = []
        if values is not None:
            self.values.extend(values)

    def __repr__(self) -> str:
        return f"<ArrayValue(values={self.values!r})>"

    def __str__(self) -> str:
        values_str = ",".join(map(str, self.values))
        return f"[{values_str}]"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ArrayValue) and self.values == other.values

    def __getitem__(self, index: int) -> ElementValue:
        return self.values[index]

    def __setitem__(self, index: int, value: ElementValue) -> None:
        self.values[index] = value

    def __delitem__(self, key: int | ElementValue) -> None:
        if isinstance(key, int):
            del self.values[key]
        else:
            self.values.remove(key)

    def __len__(self) -> int:
        return len(self.values)

    def write(self, stream: IO[bytes], pool: "ConstPool") -> None:
        stream.write(pack_BH(ArrayValue.tags[0], len(self.values)))
        for value in self.values:
            value.write(stream, pool)


# ---------------------------------------- Target Types ---------------------------------------- #

class TypeParameterTarget(TargetInfo):
    """
    A type_parameter_target struct.

    Indicates the position of the annotation in a generic class or method
    declaration.

    Attributes
    ----------
    index: int
        The index of the type parameter that the annotation appears on.
    """

    __slots__ = ("index",)

    tags = frozenset({TargetInfo.GENERIC_CLASS_TYPE_PARAMETER, TargetInfo.GENERIC_METHOD_TYPE_PARAMETER})

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        index, = stream.read(1)
        return cls(kind, index)

    def __init__(self, kind: int, index: int) -> None:
        # if not kind in TypeParameterTarget.tags:
        #     raise ValueError(f"invalid kind 0x{kind:02x} for {type(self)!r}")
        super().__init__(kind)
        self.index = index

    def __repr__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return f"<TypeParameterTarget(kind={kind_str}, index={self.index})>"

    def __str__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return f"type_parameter_target({kind_str},{self.index})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TypeParameterTarget) and self.kind == other.kind and self.index == other.index

    def write(self, stream: IO[bytes]) -> None:
        stream.write(bytes((self.kind, self.index)))


class SuperTypeTarget(TargetInfo):
    """
    A supertype_target struct.

    Indicates the position of the annotation in the `extends` or `implements` clause
    of a class.

    Attributes
    ----------
    index: int
        The index of the superinterface in the class file's interfaces array, or
        65535 to indicate the supertype of the class.
    """

    __slots__ = ("index",)

    tags = frozenset({TargetInfo.SUPER_CLASS_OR_INTERFACE_TYPE})

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        index, = unpack_H(stream.read(2))
        return cls(index)

    def __init__(self, index: int) -> None:
        super().__init__(TargetInfo.SUPER_CLASS_OR_INTERFACE_TYPE)
        self.index = index

    def __repr__(self) -> str:
        return f"<SuperTypeTarget(index={self.index})>"

    def __str__(self) -> str:
        return f"supertype_target({self.index})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SuperTypeTarget) and self.index == other.index

    def write(self, stream: IO[bytes]) -> None:
        stream.write(pack_BH(TargetInfo.SUPER_CLASS_OR_INTERFACE_TYPE, self.index))


class TypeParameterBoundTarget(TargetInfo):
    """
    A type_parameter_bound_target struct.

    Indicates the position of the annotation on a type parameter of a generic class
    or method.

    Attributes
    ----------
    param_index: int
        The index of the type parameter which has the annotated bound.
    bound_index: int
        The index of the bound that the annotation appears on.
    """

    __slots__ = ("param_index", "bound_index")

    tags = frozenset({TargetInfo.GENERIC_CLASS_TYPE_PARAMETER_BOUND, TargetInfo.GENERIC_METHOD_TYPE_PARAMETER_BOUND})

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        param_index, bound_index = stream.read(2)
        return cls(kind, param_index, bound_index)

    def __init__(self, kind: int, param_index: int, bound_index: int) -> None:
        # if not kind in TypeParameterBoundTarget.tags:
        #     raise ValueError(f"invalid kind 0x{kind:02x} for {type(self)!r}")
        super().__init__(kind)
        self.param_index = param_index
        self.bound_index = bound_index

    def __repr__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return (
            f"<TypeParameterBoundTarget(kind={kind_str}, param_index={self.param_index}, "
            f"bound_index={self.bound_index})>"
        )

    def __str__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return f"type_parameter_bound_target({kind_str},{self.param_index},{self.bound_index})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TypeParameterBoundTarget) and
            self.kind == other.kind and
            self.param_index == other.param_index and
            self.bound_index == other.bound_index
        )

    def write(self, stream: IO[bytes]) -> None:
        stream.write(bytes((self.kind, self.param_index, self.bound_index)))


class EmptyTarget(TargetInfo):
    """
    An empty_target struct.

    Indicates the position of the annotation on either the type in a field
    declaration, type in a record component, return type of a method, type of a
    newly constructed object or on the receiver type of a method.
    """

    tags = frozenset({
        TargetInfo.FIELD_OR_RECORD_COMPONENT_TYPE,
        TargetInfo.METHOD_RETURN_TYPE_OR_NEW_OBJECT,
        TargetInfo.METHOD_RECEIVER_TYPE,
    })

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        return cls(kind)

    def __init__(self, kind: int) -> None:
        # if not kind in EmptyTarget.tags:
        #     raise ValueError(f"invalid kind 0x{kind:02x} for {type(self)!r}")
        super().__init__(kind)

    def __repr__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return f"<EmptyTarget(kind={kind_str})>"

    def __str__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return f"empty_target({kind_str})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, EmptyTarget) and self.kind == other.kind

    def write(self, stream: IO[bytes]) -> None:
        stream.write(bytes((self.kind,)))


class FormalParameterTarget(TargetInfo):
    """
    A formal_parameter_target struct.

    Indicates the position of the annotation in a formal method declaration.

    Attributes
    ----------
    index: int
        The index of the formal parameter whose type the annotation appears on.
    """

    __slots__ = ("index",)

    tags = frozenset({TargetInfo.FORMAL_PARAMETER_TYPE})

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        index, = stream.read(1)
        return cls(index)

    def __init__(self, index: int) -> None:
        super().__init__(TargetInfo.FORMAL_PARAMETER_TYPE)
        self.index = index

    def __repr__(self) -> str:
        return f"<FormalParameterTarget(index={self.index})>"

    def __str__(self) -> str:
        return f"formal_parameter_target({self.index})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FormalParameterTarget) and self.index == other.index

    def write(self, stream: IO[bytes]) -> None:
        stream.write(bytes((self.kind, self.index)))


class ThrowsTarget(TargetInfo):
    """
    A throws_target struct.

    Indicates the position of the annotation in the `throws` clause of a method.

    Attributes
    ----------
    index: int
        The index of the exception type in the `Exceptions` attribute of the method.
    """

    __slots__ = ("index",)

    tags = frozenset({TargetInfo.THROWS_CLAUSE_TYPE})

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        index, = unpack_H(stream.read(2))
        return cls(index)

    def __init__(self, index: int) -> None:
        super().__init__(TargetInfo.THROWS_CLAUSE_TYPE)
        self.index = index

    def __repr__(self) -> str:
        return f"<ThrowsTarget(index={self.index})>"

    def __str__(self) -> str:
        return f"throws_target({self.index})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ThrowsTarget) and self.index == other.index

    def write(self, stream: IO[bytes]) -> None:
        stream.write(pack_BH(TargetInfo.THROWS_CLAUSE_TYPE, self.index))


class LocalVarTarget(TargetInfo):
    """
    A localvar_target struct.

    Indicates the position of the annotation in the implementation of a method,
    specifically on the type in a local variable declaration.

    Attributes
    ----------
    ranges: list[LocalVarTarget.LocalVar]
        A list of ranges at which the local variable occurs.
    """

    __slots__ = ("ranges",)

    tags = frozenset({TargetInfo.LOCAL_VARIABLE_TYPE, TargetInfo.RESOURCE_VARIABLE_TYPE})

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        count, = unpack_H(stream.read(2))
        ranges = []
        for _ in range(count):
            start_pc, length, index = unpack_HHH(stream.read(6))
            ranges.append(cls.LocalVar(start_pc, length, index))
        return cls(kind, ranges)

    def __init__(self, kind: int, ranges: Iterable["LocalVarTarget.LocalVar"] | None = None) -> None:
        # if not kind in LocalVarTarget.tags:
        #     raise ValueError(f"invalid kind 0x{kind:02x} for {type(self)!r}")
        super().__init__(kind)
        self.ranges: list[LocalVarTarget.LocalVar] = []
        if ranges is not None:
            self.ranges.extend(ranges)

    def __repr__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return f"<LocalVarTarget(kind={kind_str}, ranges={self.ranges!r})>"

    def __str__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        ranges_str = ",".join(map(str, self.ranges))
        return f"localvar_target({kind_str},[{ranges_str}])"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LocalVarTarget) and self.kind == other.kind and self.ranges == other.ranges

    def __getitem__(self, index: int) -> "LocalVarTarget.LocalVar":
        return self.ranges[index]

    def __setitem__(self, index: int, value: "LocalVarTarget.LocalVar") -> None:
        self.ranges[index] = value

    def __delitem__(self, key: Union[int, "LocalVarTarget.LocalVar"]) -> None:
        if isinstance(key, int):
            del self.ranges[key]
        else:
            self.ranges.remove(key)

    def __len__(self) -> int:
        return len(self.ranges)

    def write(self, stream: IO[bytes]) -> None:
        stream.write(pack_BH(self.kind, len(self.ranges)))
        for var in self.ranges:
            stream.write(pack_HHH(var.start_pc, var.length, var.index))

    class LocalVar:
        """
        A localvar_target entry.

        Attributes
        ----------
        start_pc: int
            The bytecode offset at which the current local range starts.
        length: int
            The length of the range.
        index: int
            The index into the local variable array indicating which local it is.
        """

        __slots__ = ("start_pc", "length", "index")

        def __init__(self, start_pc: int, length: int, index: int) -> None:
            self.start_pc = start_pc
            self.length = length
            self.index = index

        def __repr__(self) -> str:
            return f"<LocalVarTarget.LocalVar(start_pc={self.start_pc}, length={self.length}, index={self.index})>"

        def __str__(self) -> str:
            return f"localvar({self.start_pc}+{self.length},{self.index})"

        def __eq__(self, other: object) -> bool:
            return (
                isinstance(other, LocalVarTarget.LocalVar) and
                self.start_pc == other.start_pc and
                self.length == other.length and
                self.index == other.index
            )

        def __iter__(self) -> Iterable[int]:
            return iter((self.start_pc, self.length, self.index))


class CatchTarget(TargetInfo):
    """
    A catch_target struct.

    Indicates the position of the annotation in the implementation of a method,
    specifically on the type in a catch clause.

    Attributes
    ----------
    index: int
        The index in the exception table of the `Code` attribute, indicating the
        handler with the annotation.
    """

    __slots__ = ("index",)

    tags = frozenset({TargetInfo.CATCH_PARAMETER_TYPE})

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        index, = unpack_H(stream.read(2))
        return cls(index)

    def __init__(self, index: int) -> None:
        super().__init__(TargetInfo.CATCH_PARAMETER_TYPE)
        self.index = index

    def __repr__(self) -> str:
        return f"<CatchTarget(index={self.index})>"

    def __str__(self) -> str:
        return f"catch_target({self.index})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CatchTarget) and self.index == other.index

    def write(self, stream: IO[bytes]) -> None:
        stream.write(pack_BH(TargetInfo.CATCH_PARAMETER_TYPE, self.index))


class OffsetTarget(TargetInfo):
    """
    An offset_target struct.

    Indicates the position of the annotation in the implementation of a method,
    specifically on the type in an `instanceof`, `new` or :: method reference
    expression.

    Attributes
    ----------
    offset: int
        A bytecode index specifying the relevant bytecode instruction.
    """

    __slots__ = ("offset",)

    tags = frozenset({
        TargetInfo.INSTANCEOF_TYPE,
        TargetInfo.NEW_TYPE,
        TargetInfo.CONSTRUCTOR_REFERENCE_TYPE,
        TargetInfo.METHOD_REFERENCE_TYPE,
    })

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        offset, = unpack_H(stream.read(2))
        return cls(kind, offset)

    def __init__(self, kind: int, offset: int) -> None:
        # if not kind in OffsetTarget.tags:
        #     raise ValueError(f"invalid kind 0x{kind:02x} for {type(self)!r}")
        super().__init__(kind)
        self.offset = offset

    def __repr__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return f"<OffsetTarget(kind={kind_str}, offset={self.offset})>"

    def __str__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return f"offset_target({kind_str},{self.offset})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, OffsetTarget) and self.kind == other.kind and self.offset == other.offset

    def write(self, stream: IO[bytes]) -> None:
        stream.write(pack_BH(self.kind, self.offset))


class TypeArgumentTarget(TargetInfo):
    """
    A type_argument_target struct.

    Indicates the position of the annotation in the implementation of a method,
    specifically in either a type cast expression, explicit type argument list for
    a `new` expression, explicit constructor invocation statement, method invocation
    expression or a method reference expression.

    Attributes
    ----------
    offset: int
        A bytecode index specifying the relevant bytecode instruction.
    index: int
        The index in of the type in the cast, or the index of the type in the
        explicit argument list that has the annotation.
    """

    __slots__ = ("offset", "index")

    tags = frozenset({
        TargetInfo.CAST_TYPE,
        TargetInfo.GENERIC_CONSTRUCTOR_TYPE_ARGUMENT,
        TargetInfo.GENERIC_METHOD_TYPE_ARGUMENT,
        TargetInfo.CONSTRUCTOR_REFERENCE_TYPE_ARGUMENT,
        TargetInfo.METHOD_REFERENCE_TYPE_ARGUMENT,
    })

    @classmethod
    def _read(cls, stream: IO[bytes], kind: int) -> Self:
        offset, index = unpack_HB(stream.read(3))
        return cls(kind, offset, index)

    def __init__(self, kind: int, offset: int, index: int) -> None:
        # if not kind in TypeArgumentTarget.tags:
        #     raise ValueError(f"invalid kind 0x{kind:02x} for {type(self)!r}")
        super().__init__(kind)
        self.offset = offset
        self.index = index

    def __repr__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return f"<TypeArgumentTarget(kind={kind_str}, offset={self.offset}, index={self.index})>"

    def __str__(self) -> str:
        kind_str = TargetInfo._KINDS.get(self.kind) or f"0x{self.kind:02x}"
        return f"type_argument_target({kind_str},{self.offset},{self.index})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TypeArgumentTarget) and
            self.kind == other.kind and
            self.offset == other.offset and
            self.index == other.index
        )

    def write(self, stream: IO[bytes]) -> None:
        stream.write(pack_BHB(self.kind, self.offset, self.index))

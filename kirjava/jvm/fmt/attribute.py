#!/usr/bin/env python3

__all__ = (
    "AttributeInfo", "RawInfo",
    "Synthetic", "Signature", "Deprecated",
    "RuntimeVisibleAnnotations", "RuntimeInvisibleAnnotations",
    "RuntimeVisibleTypeAnnotations", "RuntimeInvisibleTypeAnnotations",
)

"""
JVM class file shared attributes.
"""

import typing
from functools import cache
from os import SEEK_CUR, SEEK_SET
from typing import IO, Iterable

from .annotation import Annotation, TypeAnnotation
from .constants import ConstInfo, UTF8Info
from .._struct import *
from ..version import *
from ...meta import Metadata

if typing.TYPE_CHECKING:
    from .classfile import ClassFile
    from .pool import ConstPool
    from ..verify import Verifier


class AttributeInfo:
    """
    An attribute_info struct.

    Attributes
    ----------
    LOC_CLASS: int
        The attribute can appear in a ClassFile structure.
    LOC_FIELD: int
        The attribute can appear in a field_info structure.
    LOC_METHOD: int
        The attribute can appear in a method_info structure.
    LOC_CODE: int
        The attribute can appear in a Code attribute.
    LOC_RECORD_COMPONENT: int
        The attribute can appear in a record component_info structure.
    tag: bytes
        The expected name of the attribute.
    since: Version
        The Java version that the attribute was introduced in.
    locations: frozenset[int]
        A set of locations the attribute can appear in.

    name: ConstInfo | None
        The preserved attribute name constant.
    extra: bytes
        Extra data that was read but not parsed.

    Methods
    -------
    lookup(tag: bytes) -> type[AttributeInfo] | None
        Looks up an attribute type by tag/name.
    read(stream: IO[bytes], version: Version, pool: ConstPool, location: int) -> tuple[AttributeInfo, Metadata]
        Reads an attribute from a binary stream.

    write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None
        Writes this attribute to a binary stream.
    verify(self, verifier: Verifier, location: int | None = None) -> None
        Verifies that this attribute is valid.
    """

    __slots__ = ("name", "extra")

    tag: bytes
    since: Version
    # TODO: Cutoff "until" version?
    locations: frozenset[int]

    LOC_CLASS            = 0
    LOC_FIELD            = 1
    LOC_METHOD           = 2
    LOC_CODE             = 3
    LOC_RECORD_COMPONENT = 4

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> tuple["AttributeInfo", Metadata | None]:
        """
        Internal attribute read.
        """

        raise NotImplementedError("_read() is not implemented for %r" % cls)

    @classmethod
    @cache
    def lookup(cls, tag: bytes) -> type["AttributeInfo"] | None:
        """
        Looks up an attribute type by tag/name.

        Parameters
        ----------
        tag: bytes
            The attribute tag/name to look up.

        Returns
        -------
        type[AttributeInfo] | None
            The attribute subclass, or `None` if not found.
        """

        for subclass in cls.__subclasses__():
            if subclass.tag == tag:
                return subclass
        return None

    @classmethod
    def read(
            cls, stream: IO[bytes], version: Version, pool: "ConstPool", location: int | None,
    ) -> tuple["AttributeInfo", Metadata]:
        """
        Reads an attribute from the binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        version: Version
            The class file version.
        pool: ConstPool
            The class file constant pool.
        location: int | None
            The location the attribute is being read from.
        """

        self: AttributeInfo

        meta = Metadata(__name__)

        index, length = unpack_HI(stream.read(6))
        name = pool[index]

        if not isinstance(name, UTF8Info):
            meta.error("read.name", "Invalid attribute name index %i (%s).", index, name)
            self = RawInfo(name, stream.read(length))
            meta.element = self
            return self, meta

        # TODO: Would be nice to have this feature, potentially.
        # if name.value in reader.skip_attrs:
        #     return RawInfo(name, stream.read(length))

        subclass: type[AttributeInfo] | None = cls.lookup(name.value)
        if subclass is None:
            meta.error("read.unknown", "Unknown attribute name %s.", name.decode())
            self = RawInfo(name, stream.read(length))
            meta.element = self
            return self, meta

        bad_version = version < subclass.since  # FIXME: This check can't be this simple, as preview features exist.
        bad_location = location is not None and location not in subclass.locations

        if bad_version:
            meta.warn("read.version", "Attribute %s appears in class with lower version than required.", name.decode())
        if bad_location:
            meta.warn("read.location", "Attribute %s is in wrong location.", name.decode())

        assert stream.seekable(), "stream is not seekable"

        start = stream.tell()
        # print(subclass, start, "-", start + length)
        try:
            self, child_meta = subclass._read(stream, version, pool)
            self.name = name
            if child_meta is not None:
                meta.add(child_meta)

            # TODO: Be able to handle extra data at the end, and re-write it back out if needed.

            # Reading sanity checks, over-reading can be an issue, etc.
            diff = stream.tell() - (start + length)
            if diff > 0:
                if bad_version or bad_location:
                    # Bad grammar, oh well.
                    meta.warn("read.overread", "Attribute %s read %i too many byte(s).", name.decode(), diff)
                else:
                    meta.error("read.overread", "Attribute %s read %i too many byte(s).", name.decode(), diff)
                raise ValueError("overread")
            elif diff < 0:
                # FIXME: Attributes at the end of the file that underread due to EOF will not preserve original length.
                meta.warn("read.underread", "Attribute %s read %i too few byte(s).", name.decode(), -diff)
                self.extra = stream.read(-diff)

        except Exception as error:
            if not isinstance(error, ValueError) or error.args[0] != "overread":  # Don't add this error twice.
                if bad_version or bad_location:
                    meta.warn("read.error", "Error reading attribute %s: %s", name.decode(), error)
                else:
                    meta.error("read.error", "Error reading attribute %s: %s", name.decode(), error)
            stream.seek(start, SEEK_SET)
            self = RawInfo(name, stream.read(length))

        meta.element = self
        return self, meta

    def __init__(self, name: ConstInfo | None = None, extra: bytes = b"") -> None:
        self.name = name
        self.extra = extra

    def __repr__(self) -> str:
        raise NotImplementedError("repr() is not implemented for %r" % type(self))

    def __str__(self) -> str:
        raise NotImplementedError("str() is not implemented for %s" % type(self))

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError("== is not implemented for %r" % type(self))

    def _write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        """
        Internal attribute write.
        """

        ...  # raise NotImplementedError("_write() is not implemented for %r" % type(self))

    def write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        """
        Writes this attribute to a binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        version: Version
            The class file version.
        pool: ConstPool
            The class file constant pool.
        """

        assert stream.seekable(), "stream is not seekable"  # Shouldn't occur.

        start = stream.tell() + 2
        stream.write(pack_HI(pool.add(self.name or UTF8Info(self.tag)), 0))

        self._write(stream, version, pool)
        stream.write(self.extra)

        end = stream.tell()
        stream.seek(start, SEEK_SET)
        stream.write(pack_I(end - start - 4))
        stream.seek(end, SEEK_SET)

    def verify(self, verifier: "Verifier", cf: "ClassFile", location: int) -> None:
        """
        Verifies that this attribute is valid.

        Parameters
        ----------
        verifier: Verifier
            The verifier to use and report to.
        cf: ClassFile
            The class file that this attribute belongs to.
        location: int
            The location of the attribute.
        """

        # If these conditions do occur, it's important to note that a lot of them may not actually be fatal errors,
        # simply because the JVM is very lenient regarding weird attributes.
        if verifier.check_attr_vers and cf.version < self.since:
            verifier.error(self, "attribute not valid in current class file version")
        if verifier.check_attr_locs and not location in self.locations:
            verifier.error(self, "attribute is in wrong location")


class RawInfo(AttributeInfo):
    """
    A raw attribute.

    Attributes
    ----------
    name: ConstInfo
        A UTF8 constant, used as the name of the attribute.
    data: bytes
        The attribute data.
    """

    __slots__ = ("data",)

    tag = b""
    since = JAVA_1_0
    locations = frozenset({
        AttributeInfo.LOC_CLASS, AttributeInfo.LOC_FIELD, AttributeInfo.LOC_METHOD, AttributeInfo.LOC_RECORD_COMPONENT,
    })

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> tuple["RawInfo", Metadata | None]:
        raise ValueError("attempted to parse raw attribute")

    def __init__(self, name: ConstInfo, data: bytes) -> None:
        super().__init__(name)
        self.name: ConstInfo
        self.data = data

    def __repr__(self) -> str:
        return "<RawAttributeInfo(name=%r, data=%r)>" % (self.name, self.data)

    def __str__(self) -> str:
        return "raw_info[%s,len=%i]" % (self.name, len(self.data))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RawInfo) and self.name == other.name and self.data == other.data

    def write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_HI(pool.add(self.name), len(self.data) + len(self.extra)))
        stream.write(self.data)
        stream.write(self.extra)

    def verify(self, verifier: "Verifier", cf: "ClassFile", location: int) -> None:
        if verifier.check_attr_data:
            verifier.error(self, "raw attribute")


class Documentation(AttributeInfo):
    """
    The Documentation attribute.

    A variable length attribute used to store documentation for classes, fields and
    methods.
    It was deprecated some time before Java 7 at the latest, perhaps even in Java 1.1.
    """
    # TODO: ^ find exactly when deprecated, likely long before 7.

    __slots__ = ("doc",)

    tag = b"Documentation"
    since = JAVA_1_0
    locations = frozenset({AttributeInfo.LOC_CLASS, AttributeInfo.LOC_FIELD, AttributeInfo.LOC_METHOD})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> tuple["Documentation", None]:
        assert stream.seekable(), "stream is not seekable"
        stream.seek(-4, SEEK_CUR)
        length, = unpack_I(stream.read(4))
        return cls(stream.read(length)), None

    def __init__(self, doc: bytes) -> None:
        super().__init__()
        self.doc = doc

    def __repr__(self) -> str:
        return "<Documentation(doc=%r)>" % self.doc

    def __str__(self) -> str:
        return "Documentation[len=%i]" % len(self.doc)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Documentation) and self.doc == other.doc

    def write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_HI(pool.add(self.name or UTF8Info(self.tag)), len(self.extra) + len(self.doc)))
        stream.write(self.doc)
        stream.write(self.extra)


class Synthetic(AttributeInfo):
    """
    The Synthetic attribute.

    A fixed length attribute, used to indicate that the element is generated by the
    compiler and is not present in the source code.
    """

    __slots__ = ()

    tag = b"Synthetic"
    since = JAVA_1_1
    locations = frozenset({AttributeInfo.LOC_CLASS, AttributeInfo.LOC_FIELD, AttributeInfo.LOC_METHOD})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> tuple["Synthetic", None]:
        return cls(), None

    def __str__(self) -> str:
        return "Synthetic"

    def __repr__(self) -> str:
        return "<Synthetic>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Synthetic)

    def write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_HI(pool.add(self.name or UTF8Info(self.tag)), len(self.extra)))
        stream.write(self.extra)


class Signature(AttributeInfo):
    """
    The Signature attribute.

    A fixed length attribute used to store generic signature information provided in
    the source code via type variables and/or parameterised types.

    Attributes
    ----------
    signature: ConstInfo
        A UTF8 constant, used as the generic signature.
    """

    __slots__ = ("signature",)

    tag = b"Signature"
    since = JAVA_5
    locations = frozenset({
        AttributeInfo.LOC_CLASS, AttributeInfo.LOC_FIELD, AttributeInfo.LOC_METHOD, AttributeInfo.LOC_RECORD_COMPONENT,
    })

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> tuple["Signature", None]:
        index, = unpack_H(stream.read(2))
        return cls(pool[index]), None

    def __init__(self, signature: ConstInfo) -> None:
        super().__init__()
        self.signature = signature

    def __repr__(self) -> str:
        return "<Signature(signature=%r)>" % self.signature

    def __str__(self) -> str:
        return "Signature[%s]" % self.signature

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Signature) and self.signature == other.signature

    def write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_HIH(
            pool.add(self.name or UTF8Info(self.tag)), 2 + len(self.extra), pool.add(self.signature),
        ))
        stream.write(self.extra)

    def verify(self, verifier: "Verifier", cf: "ClassFile", location: int) -> None:
        super().verify(verifier, cf, location)
        if verifier.check_const_types and not isinstance(self.signature, UTF8Info):
            verifier.error(self, "signature is not a UTF8 constant")


class Deprecated(AttributeInfo):
    """
    The Deprecated attribute.

    A fixed length attribute used to indicate element deprecation.
    """

    __slots__ = ()

    tag = b"Deprecated"
    since = JAVA_1_1
    locations = frozenset({
        AttributeInfo.LOC_CLASS, AttributeInfo.LOC_FIELD, AttributeInfo.LOC_METHOD, AttributeInfo.LOC_RECORD_COMPONENT,
    })

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> tuple["Deprecated", None]:
        return cls(), None

    def __repr__(self) -> str:
        return "<Deprecated>"

    def __str__(self) -> str:
        return "Deprecated"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Deprecated)

    def write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_HI(pool.add(self.name or UTF8Info(self.tag)), len(self.extra)))
        stream.write(self.extra)


class RuntimeVisibleAnnotations(AttributeInfo):
    """
    The RuntimeVisibleAnnotations attribute.

    A variable length attribute used to store runtime-visible annotations.

    Attributes
    ---------
    annotations: list[Annotation]
        A list of the runtime-visible annotations.
    """

    __slots__ = ("annotations",)

    tag = b"RuntimeVisibleAnnotations"
    since = JAVA_5
    locations = frozenset({
        AttributeInfo.LOC_CLASS, AttributeInfo.LOC_FIELD, AttributeInfo.LOC_METHOD, AttributeInfo.LOC_RECORD_COMPONENT,
    })

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> tuple["RuntimeVisibleAnnotations", None]:
        count, = unpack_H(stream.read(2))
        annotations = []
        for _ in range(count):
            annotations.append(Annotation.read(stream, pool))
        return cls(annotations), None

    def __init__(self, annotations: Iterable[Annotation] | None = None) -> None:
        super().__init__()
        self.annotations: list[Annotation] = []
        if annotations is not None:
            self.annotations.extend(annotations)

    def __repr__(self) -> str:
        return "<RuntimeVisibleAnnotations(annotations=%r)>" % self.annotations

    def __str__(self) -> str:
        return "RuntimeVisibleAnnotations[[%s]]" % ",".join(map(str, self.annotations))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RuntimeVisibleAnnotations) and self.annotations == other.annotations

    def __getitem__(self, index: int) -> Annotation:
        return self.annotations[index]

    def __setitem__(self, index: int, value: Annotation) -> None:
        self.annotations[index] = value

    def __delitem__(self, index: int) -> None:
        del self.annotations[index]

    def __len__(self) -> int:
        return len(self.annotations)

    def _write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_H(len(self.annotations)))
        for annotation in self.annotations:
            annotation.write(stream, pool)


class RuntimeInvisibleAnnotations(AttributeInfo):
    """
    The RuntimeInvisibleAnnotations attribute.

    A variable length attribute used to store runtime-invisible annotations.

    Attributes
    ----------
    annotations: list[Annotation]
        A list of the runtime-invisible annotations.
    """

    __slots__ = ("annotations",)

    tag = b"RuntimeInvisibleAnnotations"
    since = JAVA_5
    locations = frozenset({
        AttributeInfo.LOC_CLASS, AttributeInfo.LOC_FIELD, AttributeInfo.LOC_METHOD, AttributeInfo.LOC_RECORD_COMPONENT,
    })

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> tuple["RuntimeInvisibleAnnotations", None]:
        count, = unpack_H(stream.read(2))
        annotations = []
        for _ in range(count):
            annotations.append(Annotation.read(stream, pool))
        return cls(annotations), None

    def __init__(self, annotations: Iterable[Annotation] | None = None) -> None:
        super().__init__()
        self.annotations: list[Annotation] = []
        if annotations is not None:
            self.annotations.extend(annotations)

    def __repr__(self) -> str:
        return "<RuntimeInvisibleAnnotations(annotations=%r)>" % self.annotations

    def __str__(self) -> str:
        return "RuntimeInvisibleAnnotations[[%s]]" % ",".join(map(str, self.annotations))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RuntimeInvisibleAnnotations) and self.annotations == other.annotations

    def __getitem__(self, index: int) -> Annotation:
        return self.annotations[index]

    def __setitem__(self, index: int, value: Annotation) -> None:
        self.annotations[index] = value

    def __delitem__(self, index: int) -> None:
        del self.annotations[index]

    def __len__(self) -> int:
        return len(self.annotations)

    def _write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_H(len(self.annotations)))
        for annotation in self.annotations:
            annotation.write(stream, pool)


class RuntimeVisibleTypeAnnotations(AttributeInfo):
    """
    The RuntimeVisibleTypeAnnotations attribute.

    A variable length attribute used to store runtime-visible annotations present on
    types used in the declaration of the element containing this attribute.
    Additionally, it can be used to store the runtime-visible annotations present on
    type parameters in generics.

    Attributes
    ----------
    annotations: list[TypeAnnotation]
        A list of the runtime-visible type annotations.
    """

    __slots__ = ("annotations",)

    tag = b"RuntimeVisibleTypeAnnotations"
    since = JAVA_8
    locations = frozenset({
        AttributeInfo.LOC_CLASS, AttributeInfo.LOC_FIELD, AttributeInfo.LOC_METHOD,
        AttributeInfo.LOC_CODE, AttributeInfo.LOC_RECORD_COMPONENT,
    })

    @classmethod
    def _read(
            cls, stream: IO[bytes], version: Version, pool: "ConstPool",
    ) -> tuple["RuntimeVisibleTypeAnnotations", None]:
        count, = unpack_H(stream.read(2))
        annotations = []
        for _ in range(count):
            annotations.append(TypeAnnotation.read(stream, pool))
        return cls(annotations), None

    def __init__(self, annotations: Iterable[TypeAnnotation] | None = None) -> None:
        super().__init__()
        self.annotations: list[TypeAnnotation] = []
        if annotations is not None:
            self.annotations.extend(annotations)

    def __repr__(self) -> str:
        return "<RuntimeVisibleTypeAnnotations(annotations=%r)>" % self.annotations

    def __str__(self) -> str:
        return "RuntimeVisibleTypeAnnotations[[%s]]" % ",".join(map(str, self.annotations))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RuntimeVisibleTypeAnnotations) and self.annotations == other.annotations

    def __getitem__(self, index: int) -> TypeAnnotation:
        return self.annotations[index]

    def __setitem__(self, index: int, value: TypeAnnotation) -> None:
        self.annotations[index] = value

    def __delitem__(self, index: int) -> None:
        del self.annotations[index]

    def __len__(self) -> int:
        return len(self.annotations)

    def _write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_H(len(self.annotations)))
        for annotation in self.annotations:
            annotation.write(stream, pool)


class RuntimeInvisibleTypeAnnotations(AttributeInfo):
    """
    The RuntimeInvisibleTypeAnnotations attribute.

    A variable length attribute used to store runtime-invisible annotations present
    on types used in the declaration of the element containing this attribute.
    Additionally, it can be used to store the runtime-invisible annotations present
    on type parameters in generics.

    Attributes
    ----------
    annotations: list[TypeAnnotation]
        A list of the runtime-invisible type annotations.
    """

    __slots__ = ("annotations",)

    tag = b"RuntimeInvisibleTypeAnnotations"
    since = JAVA_8
    locations = frozenset({
        AttributeInfo.LOC_CLASS, AttributeInfo.LOC_FIELD, AttributeInfo.LOC_METHOD,
        AttributeInfo.LOC_CODE, AttributeInfo.LOC_RECORD_COMPONENT,
    })

    @classmethod
    def _read(
            cls, stream: IO[bytes], version: Version, pool: "ConstPool",
    ) -> tuple["RuntimeInvisibleTypeAnnotations", None]:
        count, = unpack_H(stream.read(2))
        annotations = []
        for _ in range(count):
            annotations.append(TypeAnnotation.read(stream, pool))
        return cls(annotations), None

    def __init__(self, annotations: Iterable[TypeAnnotation] | None = None) -> None:
        super().__init__()
        self.annotations: list[TypeAnnotation] = []
        if annotations is not None:
            self.annotations.extend(annotations)

    def __repr__(self) -> str:
        return "<RuntimeInvisibleTypeAnnotations(annotations=%r)>" % self.annotations

    def __str__(self) -> str:
        return "RuntimeInvisibleTypeAnnotations[[%s]]" % ",".join(map(str, self.annotations))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RuntimeInvisibleTypeAnnotations) and self.annotations == other.annotations

    def __getitem__(self, index: int) -> TypeAnnotation:
        return self.annotations[index]

    def __setitem__(self, index: int, value: TypeAnnotation) -> None:
        self.annotations[index] = value

    def __delitem__(self, index: int) -> None:
        del self.annotations[index]

    def __len__(self) -> int:
        return len(self.annotations)

    def _write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_H(len(self.annotations)))
        for annotation in self.annotations:
            annotation.write(stream, pool)

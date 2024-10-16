#!/usr/bin/env python3

__all__ = (
    "FieldInfo",
    "ConstantValue",
)

"""
JVM class file field info struct and attributes.
"""

import typing
from typing import IO, Iterable

from .attribute import AttributeInfo
from .constants import *
from .._desc import parse_field_descriptor
from .._struct import *
from ..version import JAVA_1_0, Version
from ...meta import Metadata
from ...model.class_.field import Field

if typing.TYPE_CHECKING:
    from .pool import ConstPool


class FieldInfo:
    """
    A field_info struct.

    Contains the name, descriptor, access flags, and attributes of a field.

    Attributes
    ----------
    ACC_PUBLIC: int
        Access flag denoting that this field is declared `public` and may be
        accessed outside its package.
    ACC_PRIVATE: int
        Access flag denoting that this field is declared `private` and is only
        accessible within this class and other classes belonging to the same nest.
    ACC_PROTECTED: int
        Access flag denoting that this field is declared `protected` and may be
        accessed within subclasses of this class.
    ACC_STATIC: int
        Access flag denoting that this field is declared `static`.
    ACC_FINAL: int
        Access flag denoting that this field is declared `final` and cannot be
        assigned to after object construction.
    ACC_VOLATILE: int
        Access flag denoting that this field is declared `volatile` and cannot be
        cached.
    ACC_TRANSIENT: int
        Access flag denoting that this field is declared `transient` and cannot be
        written by or read from a persistent object manager.
    ACC_SYNTHETIC: int
        Access flag denoting that this field is declared synthetic, meaning it is
        not present in the source.
    ACC_ENUM: int
        Access flag denoting that this field is declared as an element of an `enum`
        class.

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
    is_volatile: bool
        See `ACC_VOLATILE`.
    is_transient: bool
        See `ACC_TRANSIENT`.
    is_synthetic: bool
        See `ACC_SYNTHETIC`.
    is_enum: bool
        See `ACC_ENUM`.
    access: int
        A bitmask indicating the access permission and properties of this field.
    name: ConstInfo
        A UTF8 constant, used as the name of this field.
    descriptor: ConstInfo
        A UTF8 constant, used as a descriptor detailing this field's type.
    attributes: list[AttributeInfo]
        A list of attributes on this field.

    Methods
    -------
    read(stream: IO[bytes], version: Version, pool: ConstPool) -> tuple[FieldInfo, Metadata]
        Reads a field from the binary stream.

    write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None
        Writes this field to the binary stream.
    unwrap(self) -> Field
        Unwraps this field info.
    """

    __slots__ = ("access", "name", "descriptor", "attributes")

    ACC_PUBLIC    = 0x0001
    ACC_PRIVATE   = 0x0002
    ACC_PROTECTED = 0x0004
    ACC_STATIC    = 0x0008
    ACC_FINAL     = 0x0010
    ACC_VOLATILE  = 0x0040
    ACC_TRANSIENT = 0x0080
    ACC_SYNTHETIC = 0x1000
    ACC_ENUM      = 0x4000

    @classmethod
    def read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> tuple["FieldInfo", Metadata]:
        """
        Reads a field from the binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        version: Version
            The class file version.
        pool: ConstantPool
            The class file constant pool.
        """

        meta = Metadata(__name__)
        access, name_index, desc_index, attr_count = unpack_HHHH(stream.read(8))
        attributes = []
        for _ in range(attr_count):
            attr, child_meta = AttributeInfo.read(stream, version, pool, AttributeInfo.LOC_FIELD)
            attributes.append(attr)
            meta.add(child_meta)
        self = cls(access, pool[name_index], pool[desc_index], attributes)
        meta.element = self
        return self, meta

    @property
    def is_public(self) -> bool:
        return bool(self.access & FieldInfo.ACC_PUBLIC)

    @is_public.setter
    def is_public(self, value: bool) -> None:
        if value:
            self.access |= FieldInfo.ACC_PUBLIC
        else:
            self.access &= ~FieldInfo.ACC_PUBLIC

    @property
    def is_private(self) -> bool:
        return bool(self.access & FieldInfo.ACC_PRIVATE)

    @is_private.setter
    def is_private(self, value: bool) -> None:
        if value:
            self.access |= FieldInfo.ACC_PRIVATE
        else:
            self.access &= ~FieldInfo.ACC_PRIVATE

    @property
    def is_protected(self) -> bool:
        return bool(self.access & FieldInfo.ACC_PROTECTED)

    @is_protected.setter
    def is_protected(self, value: bool) -> None:
        if value:
            self.access |= FieldInfo.ACC_PROTECTED
        else:
            self.access &= ~FieldInfo.ACC_PROTECTED

    @property
    def is_static(self) -> bool:
        return bool(self.access & FieldInfo.ACC_STATIC)

    @is_static.setter
    def is_static(self, value: bool) -> None:
        if value:
            self.access |= FieldInfo.ACC_STATIC
        else:
            self.access &= ~FieldInfo.ACC_STATIC

    @property
    def is_final(self) -> bool:
        return bool(self.access & FieldInfo.ACC_FINAL)

    @is_final.setter
    def is_final(self, value: bool) -> None:
        if value:
            self.access |= FieldInfo.ACC_FINAL
        else:
            self.access &= ~FieldInfo.ACC_FINAL

    @property
    def is_volatile(self) -> bool:
        return bool(self.access & FieldInfo.ACC_VOLATILE)

    @is_volatile.setter
    def is_volatile(self, value: bool) -> None:
        if value:
            self.access |= FieldInfo.ACC_VOLATILE
        else:
            self.access &= ~FieldInfo.ACC_VOLATILE

    @property
    def is_transient(self) -> bool:
        return bool(self.access & FieldInfo.ACC_TRANSIENT)

    @is_transient.setter
    def is_transient(self, value: bool) -> None:
        if value:
            self.access |= FieldInfo.ACC_TRANSIENT
        else:
            self.access &= ~FieldInfo.ACC_TRANSIENT

    @property
    def is_synthetic(self) -> bool:
        return bool(self.access & FieldInfo.ACC_SYNTHETIC)

    @is_synthetic.setter
    def is_synthetic(self, value: bool) -> None:
        if value:
            self.access |= FieldInfo.ACC_SYNTHETIC
        else:
            self.access &= ~FieldInfo.ACC_SYNTHETIC

    @property
    def is_enum(self) -> bool:
        return bool(self.access & FieldInfo.ACC_ENUM)

    @is_enum.setter
    def is_enum(self, value: bool) -> None:
        if value:
            self.access |= FieldInfo.ACC_ENUM
        else:
            self.access &= ~FieldInfo.ACC_ENUM

    def __init__(
            self, access: int, name: ConstInfo, descriptor: ConstInfo,
            attributes: Iterable[AttributeInfo] | None = None,
    ) -> None:
        self.access = access
        self.name = name
        self.descriptor = descriptor
        self.attributes: list[AttributeInfo] = []

        if attributes is not None:
            self.attributes.extend(attributes)

    def __repr__(self) -> str:
        return f"<FieldInfo(access=0x{self.access:04x}, name={self.name!s}, descriptor={self.descriptor!s})>"

    def __str__(self) -> str:
        return f"field_info(0x{self.access:04x},{self.name!s}:{self.descriptor!s})"

    def write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        """
        Writes this field to the binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to write to.
        version: Version
            The class file version.
        pool: ConstPool
            The class file constant pool.
        """

        stream.write(pack_HHHH(self.access, pool.add(self.name), pool.add(self.descriptor), len(self.attributes)))
        for attribute in self.attributes:
            attribute.write(stream, version, pool)

    def unwrap(self) -> Field:
        """
        Unwraps this field info.

        Returns
        -------
        Field
            The unwrapped `Field`.
        """

        if not isinstance(self.name, UTF8Info):
            raise ValueError("name is not a UTF8 constant")
        if not isinstance(self.descriptor, UTF8Info):
            raise ValueError("descriptor is not a UTF8 constant")

        return Field(
            self.name.decode(), parse_field_descriptor(self.descriptor.decode()),
            is_public=self.is_public,
            is_private=self.is_private,
            is_protected=self.is_protected,
            is_static=self.is_static,
            is_final=self.is_final,
            is_volatile=self.is_volatile,
            is_transient=self.is_transient,
            is_synthetic=self.is_synthetic,
            is_enum=self.is_enum,
        )


# ---------------------------------------- Attributes ---------------------------------------- #

class ConstantValue(AttributeInfo):
    """
    The ConstantValue attribute.

    A fixed length attribute used to store constant values for `static` `final`
    fields.

    Attributes
    ----------
    value: ConstInfo
        The constant value.
    """

    __slots__ = ("value",)

    tag = b"ConstantValue"
    since = JAVA_1_0
    locations = frozenset({AttributeInfo.LOC_FIELD})

    @classmethod
    def _read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> tuple["ConstantValue", None]:
        index, = unpack_H(stream.read(2))
        return cls(pool[index]), None

    def __init__(self, value: ConstInfo) -> None:
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        return f"<ConstantValue(value={self.value!s})>"

    def __str__(self) -> str:
        return f"ConstantValue({self.value!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ConstantValue) and self.value == other.value

    def write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_HIH(
            pool.add(self.name or UTF8Info(self.tag)), 2 + len(self.extra), pool.add(self.value),
        ))
        stream.write(self.extra)

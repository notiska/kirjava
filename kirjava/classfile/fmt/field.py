#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "FieldInfo",
    "ConstantValue",
)

"""
JVM class file field info struct and attributes.
"""

import typing
from typing import IO, Iterable

from .attribute import AttributeInfo, Documentation
from .constants import *
from .._struct import *
from ..desc import parse_field_descriptor, to_descriptor
from ..version import JAVA_1_0, Version
from ..._compat import Self
from ...backend import Result
from ...model import Class, Field, Linker, Method

if typing.TYPE_CHECKING:
    from .pool import ConstPool
    from ..visitor import FieldInfoVisitor


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
    read(stream: IO[bytes], version: Version, pool: ConstPool) -> Result[Self]
        Reads a field from the binary stream.
    lower(field: Field) -> Result[Self]
        Lowers the provided field into a field info.

    visit(self, visitor: FieldInfoVisitor) -> None
        Calls a visitor on this field.
    lift(self, linker: Linker, *, strict: bool = True) -> Field
        Creates a lifted field from this field info.
    write(self, stream: IO[bytes], version: Version, pool: ConstPool) -> None
        Writes this field to the binary stream.
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
    def read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> Result[Self]:
        """
        Reads a field from the binary stream.

        Parameters
        ----------
        stream: IO[bytes]
            The binary stream to read from.
        version: Version
            The class file version.
        pool: ConstPool
            The class file constant pool.
        """

        with Result[Self].meta(__name__) as result:
            access, name_index, desc_index, attr_count = unpack_HHHH(stream.read(8))
            attributes = [
                AttributeInfo.read(stream, version, pool, AttributeInfo.LOC_FIELD).unwrap_into(result)
                for _ in range(attr_count)
            ]
            return result.ok(cls(access, pool[name_index], pool[desc_index], attributes))
        return result

    @classmethod
    def lower(cls, field: Field) -> Result[Self]:
        """
        Lowers the provided field into a field info.
        """

        with Result[Self]() as result:
            self = cls(0, UTF8Info.encode(field.name), UTF8Info.encode(to_descriptor(field.type).unwrap_into(result)))
            self.is_public = field.is_public
            self.is_private = field.is_private
            self.is_protected = field.is_protected
            self.is_static = field.is_static
            self.is_final = field.is_final
            self.is_volatile = field.is_volatile
            self.is_transient = self.is_transient
            self.is_synthetic = field.is_synthetic
            self.is_enum = field.is_enum
            return result.ok(self)
        return result

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

    def visit(self, visitor: "FieldInfoVisitor") -> None:
        """
        Calls a visitor on this field.
        """

        visitor.visit_start(self)
        for attribute in self.attributes:
            visitor.visit_attribute(attribute)
        visitor.visit_end(self)

    def lift(self, linker: Linker, *, strict: bool = True) -> Result[Field[Self]]:
        """
        Creates a lifted field from this field info.

        Parameters
        ----------
        linker: Linker
            The linker to use to resolve references.
        strict: bool
            Whether to return a value upon encountering non-critical errors.
        """

        with Result[Field]() as result:
            if not isinstance(self.name, UTF8Info):
                return result.err(TypeError(f"name {self.name!s} is not a UTF8 constant"))
            if not isinstance(self.descriptor, UTF8Info):
                return result.err(TypeError(f"descriptor {self.descriptor!s} is not a UTF8 constant"))

            lifted = Field(
                self.name.decode(), parse_field_descriptor(self.descriptor.decode(), strict=strict).unwrap_into(result),
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

            seen = set()
            for attribute in self.attributes:
                if type(attribute) in seen:
                    continue
                seen.add(type(attribute))
                attribute.lift(linker, self, lifted).unwrap_into(result, reraise=strict)

            return result.ok(lifted)
        return result

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


# ---------------------------------------- Attributes ---------------------------------------- #

class ConstantValue(AttributeInfo[FieldInfo, Field]):
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
    def _read(cls, stream: IO[bytes], version: Version, pool: "ConstPool") -> Result[Self]:
        with Result[Self]() as result:
            index, = unpack_H(stream.read(2))
            return result.ok(cls(pool[index]))
        return result

    def __init__(self, value: ConstInfo) -> None:
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        return f"<ConstantValue(value={self.value!s})>"

    def __str__(self) -> str:
        return f"ConstantValue({self.value!s})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ConstantValue) and self.value == other.value

    def lift(self, linker: Linker, parent: FieldInfo, lifted: Field) -> Result[Field]:
        required = False

        with Result[Field]() as result:
            if not isinstance(parent, FieldInfo):
                result.err(TypeError(f"constant value on wrong element {parent!s}"))
                return result.ok(lifted)

            # Basically saying that this attribute is required to be correct if the field is static and final.
            required = parent.is_static and parent.is_final

            assert isinstance(lifted, Field), "lifting field info to non-field"
            value = self.value.lift().unwrap_into(result)
            if lifted.type.verification() != value.type.verification():
                raise TypeError(f"value type {value.type!s} is not field type {lifted.type!s}")
            lifted.value = value
            return result.ok(lifted)

        if required:
            return result  # Allows an empty result to be returned if this is required, as it would be a critical error.
        return result.ok(lifted)

    def write(self, stream: IO[bytes], version: Version, pool: "ConstPool") -> None:
        stream.write(pack_HIH(
            pool.add(self.name or UTF8Info(self.tag)), 2 + len(self.extra), pool.add(self.value),
        ))
        stream.write(self.extra)

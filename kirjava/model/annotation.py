#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Annotation",
)

"""
Java annotation models and handling.
"""

import typing
from typing import Generic, Iterable, Iterator, Mapping

from .values.constants import (
    Boolean, Byte, Character, Class as ClassConst, Double, Float, Integer, Long, Short, String,
)
from .._compat import TypeVar

if typing.TYPE_CHECKING:
    from .class_ import Method
    from .types import Class as ClassType

T = TypeVar("T", bound="Annotation.Element")


class Annotation:
    """
    Information about a Java annotation.

    Attributes
    ----------
    type: ClassType
        The annotation's type.
    visible: bool
        Whether this annotation is visible at runtime via reflection.
    values: dict[str, Annotation.Element]
        The values declared for this annotation.
    """

    __slots__ = ("type", "visible", "values")

    def __init__(
        self, type: "ClassType", visible: bool = True, values: Mapping[str, "Annotation.Element"] | None = None,
    ) -> None:
        self.type = type
        self.visible = visible
        self.values: dict[str, Annotation.Element] = {}

        if values is not None:
            self.values.update(values)

    def __repr__(self) -> str:
        values_str = ", ".join(f"{name!r}={value!s}" for name, value in self.values.items())
        return f"<Annotation(type={self.type!s}, visible={self.visible}, values={{{values_str}}})>"

    def __str__(self) -> str:
        values_str = ", ".join(f"{name}={value!s}" for name, value in self.values.items())
        return f"@{self.type.name}({values_str})"

    def __contains__(self, key: str) -> bool:
        return key in self.values

    def __getitem__(self, key: str) -> "Annotation.Element":
        return self.values[key]

    def __setitem__(self, key: str, value: "Annotation.Element") -> None:
        self.values[key] = value

    def __delitem__(self, key: str) -> None:
        del self.values[key]

    def __len__(self) -> int:
        return len(self.values)

    # ------------------------------ Classes ------------------------------ #

    class Element:
        """
        An abstract annotation element.

        Used to wrap the actual value of an element in the annotation.
        """

        __slots__ = ()

        def __repr__(self) -> str:
            raise NotImplementedError(f"repr() is not implemented for {type(self)!r}")

        def __str__(self) -> str:
            raise NotImplementedError(f"str() is not implemented for {type(self)!r}")

        def __eq__(self, other: object) -> bool:
            raise NotImplementedError(f"== is not implemented for {type(self)!r}")

    class Constant(Element):
        """
        A Java constant element.

        Can be any primitive constant as well as a string or a class.

        Attributes
        ----------
        value: Boolean | Byte | Character | ClassConst | Double | Float | Integer | Long | Short | String
            The constant value of the element.
        """

        __slots__ = ("value",)

        def __init__(  # Well, this could definitely be typed better...
            self, value: Boolean | Byte | Character | ClassConst | Double | Float | Integer | Long | Short | String,
        ) -> None:
            self.value = value

        def __repr__(self) -> str:
            return f"<Annotation.Constant(value={self.value!r})>"

        def __str__(self) -> str:
            if isinstance(self.value, ClassConst):
                return f"{self.value.ref_type!s}.class"
            return str(self.value)

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Annotation.Constant) and self.value == other.value

    class EnumField(Element):
        """
        An enum constant element.

        Note that this is just a reference to the field, rather than the linked/resolved
        field itself.

        Attributes
        ----------
        type: ClassType
            The enum class containing the constant.
        name: str
            The name of the field on the enum.
        """

        __slots__ = ("type", "name")

        def __init__(self, type: "ClassType", name: str) -> None:
            self.type = type
            self.name = name

        def __repr__(self) -> str:
            return f"<Annotation.EnumField(type={self.type!s}, name={self.name!r})>"

        def __str__(self) -> str:
            return f"{self.type!s}.{self.name}"

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Annotation.EnumField) and self.type == other.type and self.name == other.name

    class Nested(Element):
        """
        A nested annotation element.

        Attributes
        ----------
        annotation: Annotation
            The nested annotation.
        """

        __slots__ = ("annotation",)

        def __init__(self, annotation: "Annotation") -> None:
            self.annotation = annotation

        def __repr__(self) -> str:
            return f"<Annotation.Nested(annotation={self.annotation!r})>"

        def __str__(self) -> str:
            return str(self.annotation)

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Annotation.Nested) and self.annotation == other.annotation

    class Array(Element, Generic[T]):
        """
        An array of nested element values.

        Attributes
        ----------
        values: list[T]
            The nested element values.
        """

        __slots__ = ("values",)

        def __init__(self, values: Iterable[T] | None = None) -> None:
            self.values: list[T] = []
            if values is not None:
                self.values.extend(values)

        def __repr__(self) -> str:
            return f"<Annotation.Array(values={self.values!r})>"

        def __str__(self) -> str:
            if not self.values:
                return "{}"
            values_str = ", ".join(map(str, self.values))
            return f"{{ {values_str} }}"

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Annotation.Array) and self.values == other.values

        def __iter__(self) -> Iterator[T]:
            return iter(self.values)

        def __getitem__(self, index: int) -> T:
            return self.values[index]

        def __setitem__(self, index: int, value: T) -> None:
            self.values[index] = value

        def __delitem__(self, key: int | T) -> None:
            if isinstance(key, int):
                del self.values[key]
            else:
                self.values.remove(key)

        def __len__(self) -> int:
            return len(self.values)

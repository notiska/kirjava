#!/usr/bin/env python3

"""
Type generification, used in the assembler.
"""

from ..abc import Class
from ..environment import Environment
from ..error import ClassNotFoundError
from ..types import object_t, Array, Primitive, Reference


class Generifier:
    """
    A reference type generifier.
    """

    __slots__ = ("environment", "_cache",)

    def __init__(self, environment: Environment) -> None:
        self.environment = environment
        self._cache: dict[tuple[Reference, Reference], Class] = {}

    def generify(self, type_a: Reference, type_b: Reference, *, do_raise: bool = True) -> Reference:
        common = self._cache.get((type_a, type_b))
        if common is not None:
            return common.get_type()

        if type(type_a) is Array:
            if type(type_b) is not Array:
                return object_t

        # These are used if there's an array type and we need to merge the element classes.
        old_a: Array | None = None
        old_b: Array | None = None

        error: Exception | None = None  # Might throw this later if needs be.
        supertypes: set[Class] = set()

        # Special handling for arrays. We need to try and merge their element types, this gets a little
        # more difficult with primitive and multi-dimensional arrays.
        if type(type_a) is Array:
            if type(type_b) is not Array:
                return object_t

            dim_a = type_a.dimensions
            dim_b = type_b.dimensions

            if dim_a != dim_b:
                return Array.from_dimension(object_t, min(dim_a, dim_b))

            old_a = type_a
            old_b = type_b
            type_a = type_a.lowest_element
            type_b = type_b.lowest_element

            # FIXME: Does the assembler get to this point? Array.mergeable() might handle this.
            # Handling primitive arrays here, we can try to merge them and if that's not possible then we'll set the
            # lowest to object_t (or an array with a lower dimension).
            # TODO: Profile, is this even faster?
            a_primitive = isinstance(type_a, Primitive)
            if a_primitive != isinstance(type_b, Primitive) or (a_primitive and type_a != type_b):
                dim_a -= 1
                if not dim_a:
                    return object_t
                return Array.from_dimension(object_t, dim_a - 1)  # Kinda a hack?

        # Try and get the type hierarchy for the higher type first. We'll check if we can find the lower type directly.
        # If not, we'll then go through the lower type's hierarchy.
        low = None
        try:
            class_ = self.environment.find_class(type_a.name)
            # .super_name is a safer way of checking if the class has a superclass for classfiles because .super can
            # throw (great design, Iska!!).
            while class_.super_name is not None:
                class_ = class_.super
                class_type = class_.get_type()
                if type_b == class_type:  # type_b is class_type:
                    low = class_type
                    self._cache[low, type_a] = class_
                    self._cache[type_a, low] = class_  # Have to be careful here, lol.
                    break
                supertypes.add(class_)
            else:
                low = None

        except ClassNotFoundError as error_:
            # FIXME: I don't think we can assign directly to error, afaik there's an implicit `del error`?
            error = error_
            low = None

        if low is not None:
            if old_a is not None and old_b is not None:
                low = Array.from_dimension(low, old_a.dimensions)
            return low

        # Going through the lower type's hierarchy now, as mentioned above.
        # TODO: Cache type hierarchies perhaps?
        low = None
        try:
            class_ = self.environment.find_class(type_b.name)
            while class_.super_name is not None:
                class_ = class_.super
                class_type = class_.get_type()
                if type_a == class_type or class_ in supertypes:
                    low = class_type
                    self._cache[low, type_a] = class_
                    self._cache[type_a, low] = class_
                    break
            else:
                low = None

        except ClassNotFoundError as error_:
            error = error or error_  # Mhm, not sure which to raise but I guess this is fine, for now.
            low = None

        if low is not None:
            if old_a is not None and old_b is not None:
                low = Array.from_dimension(low, old_a.dimensions)
            return low
        elif do_raise and error is not None:
            raise error

        # We know that they're arrays so we can do better by returning an java/lang/Object array.
        if old_a is not None or old_b is not None:
            return Array.from_dimension(object_t, old_a.dimensions)
        return object_t  # Otherwise, returning java/lang/Object is the best we can do.

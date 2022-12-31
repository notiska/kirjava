#!/usr/bin/env python3

"""
Generic types.
"""

from typing import Any, List, Union

from . import TypeArgument, TypeBound, ReferenceType
from .reference import ClassOrInterfaceType


class TypeParameter(TypeArgument):
    """
    An identifier used with generics. Explicitly defines a type variable.
    """

    __slots__ = ("identifier", "upper_bound", "additional_bounds")
    
    def __init__(
            self,
            identifier: str,
            upper_bound: TypeBound = ClassOrInterfaceType("java/lang/Object"),
            additional_bounds: Union[List[ClassOrInterfaceType], None] = None,
    ) -> None:
        """
        :param identifier: The name of the type variable.
        :param upper_bound: The upper bound of the type variable.
        :param additional_bounds: Any additional bounds that the type variable conforms to. These should be interfaces.
        """

        self.identifier = identifier
        self.upper_bound = upper_bound
        self.additional_bounds = []
        
        if additional_bounds is not None:
            self.additional_bounds.extend(additional_bounds)
        
    def __repr__(self) -> str:
        return "<TypeVariable(identifier=%s, bound=%r, additional_bounds=%r) at %x>" % \
               (self.identifier, self.upper_bound, self.additional_bounds, id(self))
        
    def __str__(self) -> str:
        return "%s extends %s%s" % (
            self.identifier, self.upper_bound,  " & ".join(map(str, [""] + self.additional_bounds)),
        )
        
    def __eq__(self, other: Any) -> bool:
        if other.__class__ is TypeParameter:
            return (
                other.identifier == self.identifier and 
                other.upper_bound == self.upper_bound and 
                other.additional_bounds == self.additional_bounds
            )
            
        return False

    def __hash__(self) -> int:
        return hash((self.identifier, self.upper_bound, self.additional_bounds))


class Wildcard(TypeArgument):
    """
    A wildcard type parameter, can be bounded.
    """

    __slots__ = ("upper_bound", "lower_bound")

    # TODO: Is it valid to have an explicit upper bound as well as a lower bound?
    def __init__(
            self,
            upper_bound: ReferenceType = ClassOrInterfaceType("java/lang/Object"),
            lower_bound: Union[ReferenceType, None] = None,
    ) -> None:
        """
        :param upper_bound: The upper bound (? extends <bound>).
        :param lower_bound: The lower bound (? super <bound>).
        """

        self.upper_bound = upper_bound
        self.lower_bound = lower_bound

    def __repr__(self) -> str:
        return "<Wildcard(upper=%r, lower=%r) at %x>" % (self.upper_bound, self.lower_bound, id(self))

    def __str__(self) -> str:
        if self.lower_bound is not None:
            return "? super %s" % self.lower_bound
        return "? extends %s" % self.upper_bound

    def __eq__(self, other: Any) -> bool:
        return other.__class__ is Wildcard and other.upper_bound == self.upper_bound and other.lower_bound == self.lower_bound

    def __hash__(self) -> int:
        return hash((self.upper_bound, self.lower_bound))

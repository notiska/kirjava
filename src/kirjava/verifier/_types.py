#!/usr/bin/env python3

__all__ = (
    "NoTypeChecker", "BasicTypeChecker", "FullTypeChecker",
)

"""
Type checker implementations.
"""

import logging
from typing import Dict, Optional, Set, Tuple

from .. import environment, types
from ..abc import TypeChecker
from ..types import ReferenceType, VerificationType
from ..types.reference import ArrayType, ClassOrInterfaceType
from ..types.verification import This, Uninitialized, UninitializedThis

logger = logging.getLogger("kirjava.analysis.verifier")


class NoTypeChecker(TypeChecker):
    """
    A type checker that does nothing (for no verification).
    """

    def check_merge(self, expected: Optional[VerificationType], actual: VerificationType) -> bool:
        return True  # Always assignable

    def check_reference(self, actual: VerificationType) -> bool:
        return True

    def check_class(self, actual: VerificationType) -> bool:
        return True

    def check_array(self, actual: VerificationType) -> bool:
        return True

    def check_category(self, actual: VerificationType, category: int = 2) -> bool:
        return True

    def merge(self, expected: Optional[VerificationType], actual: VerificationType) -> VerificationType:
        return actual  # Assume that the actual type is always correct


class BasicTypeChecker(TypeChecker):
    """
    Verifies that types are basically assignable, so doesn't check reference types thoroughly.
    """

    def check_merge(self, expected: Optional[VerificationType], actual: VerificationType) -> bool:
        if expected is None:
            return self.check_reference(actual)
        elif expected.can_merge(actual):
            return True
        elif (
            (
                type(actual) is This or
                type(actual) is Uninitialized or
                type(actual) is UninitializedThis
            ) and actual.class_ is not None
        ):
            return expected.can_merge(actual.class_)
        return False

    def check_reference(self, actual: VerificationType) -> bool:
        if (
            type(actual) is ClassOrInterfaceType or  # Faster checks for more common reference types
            type(actual) is ArrayType or
            type(actual) is Uninitialized or
            isinstance(actual, ReferenceType)  # Just to be sure we didn't miss anything
        ):
            return True
        return actual == types.null_t or actual == types.this_t or actual == types.uninit_this_t

    def check_class(self, actual: VerificationType) -> bool:
        return type(actual) is ClassOrInterfaceType or actual == types.null_t

    def check_array(self, actual: VerificationType) -> bool:
        return type(actual) is ArrayType or actual == types.null_t

    def check_category(self, actual: VerificationType, category: int = 2) -> bool:
        return actual.internal_size == category

    def merge(
            self,
            expected: Optional[VerificationType],
            actual: VerificationType,
            *,
            fallback: Optional[VerificationType] = None,
    ) -> VerificationType:
        if expected is None:
            return actual if fallback is None else fallback  # Might need to fall back sometimes, unfortunately
        elif expected == actual:
            return actual  # Could preserve any extra metadata, which is good :)
        return expected if fallback is None else fallback


class FullTypeChecker(BasicTypeChecker):
    """
    Verifies that types are assignable, including full checking of the Java type hierarchy.
    """

    def __init__(self) -> None:
        self._supertype_cache: Dict[Tuple[str, str], ClassOrInterfaceType] = {}

    def merge(
            self,
            expected: Optional[VerificationType],
            actual: VerificationType,
            *,
            fallback: Optional[VerificationType] = None,
    ) -> VerificationType:
        if expected is None:
            return actual if fallback is None else fallback
        elif expected == actual:
            return actual

        elif self.check_merge(expected, actual):
            # Merging class types

            if type(expected) is ClassOrInterfaceType and type(actual) is ClassOrInterfaceType:
                common: Optional[ClassOrInterfaceType] = self._supertype_cache.get((expected.name, actual.name), None)
                if common is not None:
                    return common
                else:
                    common = self._supertype_cache.get((actual.name, expected.name), None)
                    if common is not None:
                        self._supertype_cache[expected.name, actual.name] = common
                        return common

                if expected == types.object_t or actual == types.object_t:
                    self._supertype_cache[expected.name, actual.name] = types.object_t
                    return types.object_t

                super_classes_a: Set[str] = set()

                try:
                    class_a = environment.find_class(expected.name)
                    class_b = environment.find_class(actual.name)

                    # FIXME: Cleanup

                    # One of the classes is an interface, so we need to check if the other implements it.
                    if class_a.is_interface != class_b.is_interface:
                        if class_a.is_interface:
                            while class_b is not None:
                                # Cheaper to check the names as we don't have to do lookups that we've already done.
                                if class_a.name in class_b.interface_names:
                                    common = class_a.get_type()
                                    break
                                class_b = class_b.super
                        else:
                            while class_a is not None:
                                if class_b.name in class_a.interface_names:
                                    common = class_b.get_type()
                                    break
                                class_a = class_a.super

                    else:
                        while class_a is not None:
                            super_classes_a.add(class_a.name)
                            if class_a.name == class_b.name:
                                common = class_a.get_type()
                                break
                            try:
                                class_a = class_a.super
                            except LookupError:
                                break

                        while common is None and class_b is not None:
                            if class_b.name in super_classes_a:
                                common = class_b.get_type()
                                break
                            class_b = class_b.super

                except LookupError as error:
                    # FIXME: Warning?
                    logger.warning("Couldn't resolve common supertype for %r and %r." % (expected.name, actual.name))
                    logger.debug(error, exc_info=True)

                if common is not None:
                    logger.debug("Resolved common supertype for %r and %r -> %r." % (
                        expected.name, actual.name, str(common),
                    ))
                    self._supertype_cache[expected.name, actual.name] = common
                    return common

                # FIXME: We can do better than this, just needs more analysis of field and invocation instructions
                if fallback is None or type(fallback) is not ClassOrInterfaceType:
                    fallback = types.object_t  # java/lang/Object it is then :(
                self._supertype_cache[expected.name, actual.name] = fallback
                return fallback

            # Merging null types

            if expected == types.null_t:
                return actual
            elif actual == types.null_t:
                return expected

            # Merging this types

            expected_this = expected == types.this_t
            actual_this = actual == types.this_t

            if expected_this and actual_this:
                if expected.class_ is None:
                    return actual
                elif actual.class_ is None:
                    return expected
                return This(self.merge(expected.class_, actual.class_, fallback=fallback))
            elif expected_this:
                return This(self.merge(expected.class_, actual, fallback=fallback))
            elif actual_this:
                if actual.class_ is None:
                    return actual
                return This(self.merge(expected, actual.class_, fallback=fallback))

            # Merging uninitializedThis types

            expected_uninit_this = expected == types.uninit_this_t
            actual_uninit_this = actual == types.uninit_this_t

            if expected_uninit_this and actual_uninit_this:
                if expected.class_ is None:
                    return actual
                elif actual.class_ is None:
                    return expected
                return UninitializedThis(self.merge(expected.class_, actual.class_, fallback=fallback))
            elif expected_uninit_this:
                return UninitializedThis(self.merge(expected.class_, actual, fallback=fallback))
            elif actual_uninit_this:
                if actual.class_ is None:
                    return actual
                return UninitializedThis(self.merge(expected, actual.class_, fallback=fallback))

            # Merging uninitialised types

            expected_uninit = isinstance(expected, Uninitialized)
            actual_uninit = isinstance(actual, Uninitialized)

            if expected_uninit and actual_uninit:
                if expected.class_ is None:
                    return actual
                elif actual.class_ is None:
                    return expected
                return Uninitialized(actual.offset, self.merge(expected.class_, actual.class_, fallback=fallback))
            elif expected_uninit:
                return Uninitialized(expected.offset, self.merge(expected.class_, actual, fallback=fallback))
            elif actual_uninit:
                if actual.class_ is None:
                    return actual
                return Uninitialized(actual.offset, self.merge(expected, actual.class_, fallback=fallback))

            # TODO: Array types

        return expected

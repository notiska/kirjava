#!/usr/bin/env python3

"""
The bytecode verifier.
"""

import logging
from typing import Dict, Set, Tuple, Union

from ... import types
from ...abc import TypeChecker
from ...environment import Environment
from ...types import ReferenceType, VerificationType
from ...types.reference import ArrayType, ClassOrInterfaceType
from ...types.verification import This, Uninitialized, UninitializedThis

logger = logging.getLogger("kirjava.analysis.verifier")


class BasicTypeChecker(TypeChecker):
    """
    Verifies that types are basically assignable, so doesn't check reference types thoroughly.
    """

    def check_merge(self, expected: Union[VerificationType, None], actual: VerificationType) -> bool:
        if expected is None:
            return self.check_reference(actual)
        elif expected.can_merge(actual):
            return True
        elif isinstance(actual, This) and actual.class_ is not None:
            return expected.can_merge(actual.class_)
        elif isinstance(actual, Uninitialized) and actual.class_ is not None:
            return expected.can_merge(actual.class_)
        return False

    def check_reference(self, type_: VerificationType) -> bool:
        if isinstance(type_, ReferenceType) or isinstance(type_, Uninitialized):
            return True
        return type_ == types.null_t or type_ == types.this_t or type_ == types.uninit_this_t

    def check_array(self, type_: VerificationType) -> bool:
        return isinstance(type_, ArrayType) or type_ == types.null_t

    def check_category(self, type_: VerificationType, category: int = 2) -> bool:
        return type_.internal_size == category

    def merge(self, expected: Union[VerificationType, None], actual: VerificationType) -> VerificationType:
        if expected is None:
            return actual  # Might need to fall back sometimes, unfortunately
        elif expected == actual:
            return actual  # Could preserve any extra metadata, which is good :)
        return expected


class FullTypeChecker(BasicTypeChecker):
    """
    Verifies that types are assignable, including full checking of the Java type hierarchy.
    """

    def __init__(self) -> None:
        self._supertype_cache: Dict[Tuple[str, str], ClassOrInterfaceType] = {}

    def merge(self, expected: Union[VerificationType, None], actual: VerificationType) -> VerificationType:
        if expected is None:
            return actual
        elif expected == actual:
            return actual

        elif self.check_merge(expected, actual):
            # Merging null types

            if expected == types.null_t:
                return actual  # TODO: Specify that the type is nullable maybe?
            elif actual == types.null_t:
                return expected

            # Merging class types

            if isinstance(expected, ClassOrInterfaceType) and isinstance(actual, ClassOrInterfaceType):
                common: Union[ClassOrInterfaceType, None] = self._supertype_cache.get((expected.name, actual.name), None)
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
                    class_a = Environment.find_class(expected.name)
                    class_b = Environment.find_class(actual.name)

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
                self._supertype_cache[expected.name, actual.name] = types.object_t
                return types.object_t  # java/lang/Object it is then :(

            # Merging this types

            expected_this = expected == types.this_t
            actual_this = actual == types.this_t

            if expected_this and actual_this:
                if expected.class_ is None:
                    return actual
                elif actual.class_ is None:
                    return expected
                return This(self.merge(expected.class_, actual.class_))  # TODO: Figure out type bounds?
            elif expected_this:
                return This(self.merge(expected.class_, actual))
            elif actual_this:
                if actual.class_ is None:
                    return actual
                return This(self.merge(expected, actual.class_))

            # Merging uninitializedThis types

            expected_uninit_this = expected == types.uninit_this_t
            actual_uninit_this = actual == types.uninit_this_t

            if expected_uninit_this and actual_uninit_this:
                if expected.class_ is None:
                    return actual
                elif actual.class_ is None:
                    return expected
                return UninitializedThis(self.merge(expected.class_, actual.class_))
            elif expected_uninit_this:
                return UninitializedThis(self.merge(expected.class_, actual))
            elif actual_uninit_this:
                if actual.class_ is None:
                    return actual
                return UninitializedThis(self.merge(expected, actual.class_))

            # Merging uninitialised types

            expected_uninit = isinstance(expected, Uninitialized)
            actual_uninit = isinstance(actual, Uninitialized)

            if expected_uninit and actual_uninit:
                if expected.class_ is None:
                    return actual
                elif actual.class_ is None:
                    return expected
                return Uninitialized(actual.offset, self.merge(expected.class_, actual.class_))
            elif expected_uninit:
                return Uninitialized(expected.offset, self.merge(expected.class_, actual))
            elif actual_uninit:
                if actual.class_ is None:
                    return actual
                return Uninitialized(actual.offset, self.merge(expected, actual.class_))

            # TODO: Array types

        return expected

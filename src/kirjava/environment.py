#!/usr/bin/env python3

__all__ = (
    "Environment",
)

"""
Information about classes for Kirjava to use.
"""

import logging
import typing
from weakref import WeakValueDictionary
from typing import Iterable, Optional, Set, Union

if typing.TYPE_CHECKING:
    from .abc import Class

logger = logging.getLogger("kirjava.environment")


class Environment:
    """
    Allows for registration and lookup of classes.
    """

    __slots__ = ("do_raise", "_refs", "_classes")

    def __init__(self, inherit: Optional["Environment"] = None, *, do_raise: bool = False) -> None:
        """
        :param inherit: An old environment to inherit from.
        :param do_raise: Should an exception be raised if a class is not found?
        """

        self.do_raise = do_raise

        self._refs: Set["Class"] = set()  # Strong references to classes
        self._classes: WeakValueDictionary[str, "Class"] = WeakValueDictionary()
        if inherit is not None:
            self._classes.update(inherit._classes)

    def register_class(self, class_: "Class", *, weak: bool = False) -> None:
        """
        Registers a class with the environment.

        :param class_: The class to register.
        :param weak: Should the class be weakly referenced?
        """

        if class_.name in self._classes:
            logger.debug("Overriding already defined class %s.", class_.name)
        self._classes[class_.name] = class_
        if not weak:
            self._refs.add(class_)

    def register_classes(self, *classes: Union[Iterable["Class"], "Class"], weak: bool = False) -> None:
        """
        Registers multiple classes with the environment.

        :param classes: The classes to register.
        :param weak: Should the classes be weakly referenced?
        """

        for class_ in classes:
            try:
                self.register_classes(*class_, weak=weak)
            except TypeError:  # Ugh I hate not being able to import Class directly
                self.register_class(class_, weak=weak)

    def unregister_class(self, name: str) -> Optional["Class"]:
        """
        Unregisters the class with the given name.

        :param name: The name of the class to unregister.
        :return: The class that was unregistered.
        """

        class_ = self._classes.pop(name, None)
        self._refs.discard(class_)
        if class_ is None:
            if not self.do_raise:
                return None
            raise LookupError("Couldn't find class by name %r." % name)
        return class_

    def find_class(self, name: str) -> Optional["Class"]:
        """
        Retrieves a class from the environment.

        :param name: The name of the class to retrieve.
        :return: The class. A LookupError is thrown otherwise.
        """

        class_ = self._classes.get(name)
        if class_ is None:
            if not self.do_raise:
                return None
            raise LookupError("Couldn't find class by name %r." % name)
        return class_

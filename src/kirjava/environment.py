#!/usr/bin/env python3

__all__ = (
    "DEFAULT",
    "Provider",
    "Environment",
)

"""
Information about classes for Kirjava to use.
"""

import logging
import threading
import typing
from types import TracebackType
from typing import Iterable, Iterator, Optional, Union
from weakref import WeakValueDictionary

from .error import ClassNotFoundError

if typing.TYPE_CHECKING:
    from .abc import Class

logger = logging.getLogger("kirjava.environment")


class Provider:
    """
    Provides classes when looked up.
    """

    __slots__ = ()

    def provide_class(self, name: str) -> "Class":
        """
        Provides a class with the given name.
        """

        ...


class Environment:
    """
    Allows for registration and lookup of classes.
    """

    __slots__ = ("providers", "_refs", "_classes", "_lock")

    def __init__(self, inherit: Optional["Environment"] = None) -> None:
        self.providers: list[Provider] = []

        self._refs: set["Class"] = set()  # Strong references to classes
        self._classes: WeakValueDictionary[str, "Class"] = WeakValueDictionary()
        if inherit is not None:
            self._classes.update(inherit._classes)

        self._lock = threading.RLock()

    def __enter__(self) -> "Environment":
        self._lock.acquire()
        return self

    def __exit__(self, exc_type: type | None, exc_value: Exception | None, traceback: TracebackType | None) -> None:
        self._lock.release()

    def release_refs(self) -> None:
        """
        Releases all strong references to classes.
        """

        self._refs.clear()

    def register_class(self, class_: "Class", *, weak: bool = False) -> None:
        """
        Registers a class with the environment.

        :param class_: The class to register.
        :param weak: Should the class be weakly referenced?
        """

        with self._lock:
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

        with self._lock:
            for class_ in classes:
                try:
                    self.register_classes(*class_, weak=weak)
                except TypeError:  # Ugh I hate not being able to import Class directly
                    self.register_class(class_, weak=weak)

    def unregister_class(self, name: str, *, do_raise: bool = True) -> Optional["Class"]:
        """
        Unregisters the class with the given name.

        :param name: The name of the class to unregister.
        :param do_raise: Raises an exception if the class could not be found.
        :return: The class that was unregistered.
        """

        with self._lock:
            class_ = self._classes.pop(name, None)
            self._refs.discard(class_)
            if class_ is None:
                if not do_raise:
                    return None
                raise ClassNotFoundError(name)
            return class_

    def find_class(self, name: str, *, do_raise: bool = True) -> Optional["Class"]:
        """
        Retrieves a class from the environment.

        :param name: The name of the class to retrieve.
        :param do_raise: Raises an exception if the class could not be found.
        :return: The class.
        """

        with self._lock:
            class_ = self._classes.get(name)

            if class_ is None:
                for provider in self.providers:
                    class_ = provider.provide_class(name)
                    if class_ is not None:
                        self.register_class(class_, weak=True)  # We'll assume that we can discard afterwards.
                        return class_

                if not do_raise:
                    return None
                raise ClassNotFoundError(name)

            return class_

    def get_super_classes(self, class_: "Class") -> list["Class"]:
        ...

    def get_super_classes_iter(self, class_: "Class") -> Iterator["Class"]:
        ...


DEFAULT = Environment()

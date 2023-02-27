#!/usr/bin/env python3

__all__ = (
    "register_class", "register_classes", "find_class",
)

"""
Information about classes and such for Kirjava to use.
"""

import logging
from typing import Dict, Tuple

from .abc import Class

logger = logging.getLogger("kirjava.environment")
_classes: Dict[str, Class] = {}


def register_class(class_: Class) -> None:
    """
    Registers a class with the environment.

    :param class_: The class to register.
    """

    if class_.name in _classes:
        logger.debug("Overriding already defined class %s.", class_.name)
    _classes[class_.name] = class_


def register_classes(*classes: Tuple[Class, ...]) -> None:
    """
    Registers multiple classes with the environment.

    :param classes: The classes to register.
    """

    for class_ in classes:
        register_class(class_)


def unregister_class(name: str) -> Class:
    """
    Unregisters the class with the given name.

    :param name: The name of the class to unregister.
    :return: The class that was unregistered.
    """

    class_ = _classes.pop(name, None)
    if class_ is None:
        raise LookupError("Couldn't find class by name %r." % name)
    return class_


def find_class(name: str) -> Class:
    """
    Retrieves a class from the environment.

    :param name: The name of the class to retrieve.
    :return: The class.
    """

    class_ = _classes.get(name, None)
    if class_ is None:
        raise LookupError("Couldn't find class by name %r." % name)
    return class_

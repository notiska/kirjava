#!/usr/bin/env python3

__all__ = (
    "Environment",
)

"""
Information about classes and such for Kirjava to use.
"""

import logging
from typing import Dict, Tuple

from .abc import Class

logger = logging.getLogger("kirjava.environment")


class Environment:
    """
    The Kirjava environment.
    """

    _classes: Dict[str, Class] = {}

    # ------------------------------ Registering ------------------------------ #

    @classmethod
    def register_class(cls, class_: Class) -> None:
        """
        Registers a class with the environment.

        :param class_: The class to register.
        """

        if class_.name in cls._classes:
            logger.debug("Overriding already defined class %s.", class_.name)
        cls._classes[class_.name] = class_

    @classmethod
    def register_classes(cls, *classes: Tuple[Class, ...]) -> None:
        """
        Registers multiple classes with the environment.

        :param classes: The classes to register.
        """

        for class_ in classes:
            cls.register_class(class_)

    # ------------------------------ Retrieving ------------------------------ #

    @classmethod
    def find_class(cls, name: str) -> Class:
        """
        Retrieves a class from the environment.

        :param name: The name of the class to retrieve.
        :return: The class.
        """

        class_ = cls._classes.get(name, None)
        if class_ is None:
            raise LookupError("Couldn't find class by name %r." % name)
        return class_

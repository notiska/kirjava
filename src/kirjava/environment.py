#!/usr/bin/env python3

__all__ = (
    "Environment",
)

"""
Information about classes and such for Kirjava to use.
"""

import logging
from typing import Dict, Tuple, Union

from .abc import Class

logger = logging.getLogger("kirjava.environment")


class Environment:
    """
    The Kirjava environment.
    """

    INSTANCE: Union["Environment", None] = None

    def __init__(self) -> None:
        if self.__class__.INSTANCE is not None:
            raise Exception("An environment already exists!")
        self.__class__.INSTANCE = self

        logger.debug("Initialise Kirjava environment.")

        self._classes: Dict[str, Class] = {}

    # ------------------------------ Registering ------------------------------ #

    def register_class(self, class_: Class) -> None:
        """
        Registers a class with the environment.

        :param class_: The class to register.
        """

        if class_.name in self._classes:
            logger.debug("Overriding already defined class %s.", class_.name)
        self._classes[class_.name] = class_

    def register_classes(self, *classes: Tuple[Class, ...]) -> None:
        """
        Registers multiple classes with the environment.

        :param classes: The classes to register.
        """

        for class_ in classes:
            self.register_class(class_)

    # ------------------------------ Retrieving ------------------------------ #

    def find_class(self, name: str) -> Class:
        """
        Retrieves a class from the environment.

        :param name: The name of the class to retrieve.
        :return: The class.
        """

        class_ = self._classes.get(name, None)
        if class_ is None:
            raise LookupError("Couldn't find class by name %r." % name)
        return class_

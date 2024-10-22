#!/usr/bin/env python3

__all__ = (
    "backend", "classfile", "model",

    "__name__", "__version__", "__author__",
    "logger",  # In case anyone wants to modify the logger properties.
)

"""
kirjava - a Java bytecode library for Python.
"""

import logging
from logging import NullHandler

from . import backend, classfile, containers, model

__name__ = "kirjava"
__version__ = "0.2.3b1"
__author__ = "notiska / node3112 (Iska)"

logger = logging.getLogger("kirjava")
logger.addHandler(logging.NullHandler())  # As it's a library, we don't want to log any messages.
logger.setLevel(logging.DEBUG)
logger.parent = None

# TODO: Descriptors on constants and implicit casting (i.e. str -> UTF8Info).
# TODO: ABC regiments for iterables, lists, etc...
# TODO: Proper infrastructure regarding ensuring ABCs aren't instantiated (instructions) without using abc.ABC as that's
#       slow on `isinstance` checks.

# TODOs regarding / reasons for ditching older Python support:
#  1. Using `Self` type for `Instruction.make()` and others will eliminate mypy workarounds.
#  2. Generics could be used for classes like `ConstInfo` where we want to more easily imply an expected subclass type
#     but still support invalid classes, i.e. type: ConstInfo[UTF8Info].
#  3. Generics again for various pseudo-iterable types such as `Annotation.NamedElement`.

#!/usr/bin/env python3

"""
kirjava - a Java bytecode library for Python.
"""

__all__ = (
    "__name__", "__version__", "__author__",
    "backend", "classfile", "model",
)

import logging

from . import backend, classfile, model

__name__ = "kirjava"
__version__ = "0.2.3b1"
__author__ = "notiska / node3112 (Iska)"

logging.getLogger("kirjava").setLevel(logging.CRITICAL)  # As it's a library, we don't want to log any messages.

# TODO: Descriptors on constants and implicit casting (i.e. str -> UTF8Info).
# TODO: ABC regiments for iterables, lists, etc...
# TODO: Proper infrastructure regarding ensuring ABCs aren't instantiated (instructions) without using abc.ABC as that's
#       slow on `isinstance` checks.

# TODOs regarding / reasons for ditching older Python support:
#  1. Using `Self` type for `Instruction.make()` and others will eliminate mypy workarounds.
#  2. Generics could be used for classes like `ConstInfo` where we want to more easily imply an expected subclass type
#     but still support invalid classes, i.e. type: ConstInfo[UTF8Info].
#  3. Generics again for various pseudo-iterable types such as `Annotation.NamedElement`.

#!/usr/bin/env python3

"""
kirjava - a Java bytecode library for Python.
"""

__all__ = (
    "__name__", "__version__", "__author__",
    "jvm", "model",
)

import logging

from . import jvm, model

__name__ = "kirjava"
__version__ = "0.2.3-beta"
__author__ = "notiska / node3112 (Iska)"

logging.getLogger("kirjava").setLevel(logging.CRITICAL)  # As it's a library, we don't want to log any messages.

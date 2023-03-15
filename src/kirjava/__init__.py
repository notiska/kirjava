#!/usr/bin/env python3

# FIXME
# __all__ = (
#     "abc", "analysis", "classfile", "environment", "jarfile", "skeleton", "types",
#     "Class", "Field", "Method",
#     "ClassFile",
#     "Environment",
#     "Version",
# )

"""
Kirjava - A Java bytecode library for Python.
"""

__version__ = "0.1.4"

# Expose API
from . import abc, analysis, classfile, environment, instructions, jarfile, skeleton, types, verifier
from ._helper import *
from .analysis import *
from .classfile import *
from .environment import *
# from .jarfile import *
from .version import *

_initialised = False


def initialise(load_skeletons: bool = True, skeletons_version: Version = Version.get("11")) -> None:
    """
    Initialises Kirjava.

    :param load_skeletons: Loads the skeleton classes.
    :param skeletons_version: The Java version to load the skeleton classes for.
    """

    global _initialised

    if _initialised:
        return
    _initialised = True

    if load_skeletons:
        skeleton.load_skeletons(skeletons_version)

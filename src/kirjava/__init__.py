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

__version__ = "0.1.1"

# Expose API
from . import abc, classfile, environment, jarfile, skeleton
from .abc import *
from .classfile import *
from .environment import *
from .jarfile import *
from .version import *


def initialise(load_skeletons: bool = True, skeletons_version: Version = Version.get("11")) -> Environment:
    """
    Initialises Kirjava.

    :param load_skeletons: Loads the skeleton classes.
    :param skeletons_version: The Java version to load the skeleton classes for.
    :return: The initialised environment.
    """

    if Environment.INSTANCE is not None:
        return Environment.INSTANCE

    environ = Environment()

    if load_skeletons:
        skeleton.load_skeletons(skeletons_version)

    return environ

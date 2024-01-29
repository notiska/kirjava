#!/usr/bin/env python3

__all__ = (
    "SkeletonClass", "SkeletonField", "SkeletonMethod",
)

"""
Skeleton classes (classes that contain only basic information about the fields and methods).
"""

from .abc import Class, Field, Method


class SkeletonClass(Class):
    ...


class SkeletonField(Field):
    ...


class SkeletonMethod(Method):
    ...

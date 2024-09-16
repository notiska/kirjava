#!/usr/bin/env python3

"""
Visitor API for JVM class files.
"""

import typing

if typing.TYPE_CHECKING:
    from ..jvm.fmt.classfile import ClassFile
    from ..jvm.fmt.constants import ConstInfo
    from ..jvm.fmt.field import FieldInfo
    from ..jvm.fmt.method import MethodInfo


# class Visitor:
#     """
#     Visitor class for JVM class files.
#
#     Methods
#     -------
#     visit_const(self, info: ConstInfo) -> None
#         Called when visiting a constant pool entry.
#     visit_class(self, cf: ClassFile) -> None
#         Called when visiting a class file.
#     visit_field(self, field: FieldInfo) -> None
#         Called when visiting a field.
#     visit_method(self, method: MethodInfo) -> None
#         Called when visiting a method.
#     """
#
#     def visit_const(self, info: "ConstInfo") -> None:
#         """
#         Called when visiting a constant pool entry.
#         """
#
#         ...
#
#     def visit_class(self, cf: "ClassFile") -> None:
#         """
#         Called when visiting a class file.
#         """
#
#         ...
#
#     def visit_field(self, field: "FieldInfo") -> None:
#         """
#         Called when visiting a field.
#         """
#
#         ...
#
#     def visit_method(self, method: "MethodInfo") -> None:
#         """
#         Called when visiting a method.
#         """
#
#         ...

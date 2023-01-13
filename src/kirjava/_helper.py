#!/usr/bin/env python3

__all__ = (
    "load",
    "disassemble",
)

"""
Helper functions for Kirjava, to make the API more simplistic.
"""

from io import BytesIO
from typing import IO, Union

from .analysis.graph import InsnGraph
from .classfile import ClassFile
from .classfile.members import MethodInfo


def load(file_data_or_stream: Union[str, bytes, IO[bytes]]) -> ClassFile:
    """
    Reads a classfile given either the path to the file or a binary stream.

    :param file_data_or_stream: The path to a file, binary data or a binary stream.
    :return: The classfile that was read.
    """

    if file_data_or_stream.__class__ is str:
        with open(file_data_or_stream, "rb") as stream:
            return ClassFile.read(stream)
    elif file_data_or_stream.__class__ is bytes:
        return ClassFile.read(BytesIO(file_data_or_stream))
    return ClassFile.read(file_data_or_stream)


def disassemble(method: MethodInfo, ignore_flags: bool = False) -> InsnGraph:
    """
    Disassembles the provided method. If the method has multiple Code attributes, the first is chosen.

    :param method: The method to disassemble.
    :param ignore_flags: Skip checking if the method is abstract or native and try to disassemble anyway.
    :return: The disassembled instruction graph.
    """

    if not isinstance(method, MethodInfo):
        raise TypeError("Expected type %r, got %r." % (MethodInfo, method.__class__))

    if not ignore_flags:
        if method.is_abstract:
            raise ValueError("Method %r is abstract, cannot disassemble." % str(method))
        if method.is_native:
            raise ValueError("Method %r is native, cannot disassemble." % str(method))

    code = method.code
    if code is None:
        return InsnGraph(method)  # Just create an empty instruction graph
    return InsnGraph.disassemble(code)

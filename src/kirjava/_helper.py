#!/usr/bin/env python3

__all__ = (
    "load", "dump",
    "disassemble", "trace", "assemble",
)

"""
Helper functions for Kirjava, to make the API more simplistic.
"""

from io import BytesIO
from typing import IO

from .analysis import InsnGraph, Trace
from .classfile import ClassFile, MethodInfo


def load(file_data_or_stream: str | bytes | IO[bytes], **kwargs: bool) -> ClassFile:
    """
    Reads a classfile given either the path to the file or a binary stream.

    :param file_data_or_stream: The path to a file, binary data or a binary stream.
    :return: The classfile that was read.
    """

    if type(file_data_or_stream) is str:
        with open(file_data_or_stream, "rb") as stream:
            return ClassFile.read(stream, **kwargs)
    elif type(file_data_or_stream) is bytes:
        return ClassFile.read(BytesIO(file_data_or_stream), **kwargs)
    return ClassFile.read(file_data_or_stream, **kwargs)


def dump(classfile: ClassFile, file_or_stream: str | IO[bytes]) -> None:
    """
    Writes a classfile to the provided file or binary stream.

    :param classfile: The classfile to write.
    :param file_or_stream: The file or stream to write the classfile to.
    """

    if isinstance(file_or_stream, str):
        with open(file_or_stream, "wb") as stream:
            classfile.write(stream)
        return

    classfile.write(file_or_stream)


def disassemble(method: MethodInfo, ignore_flags: bool = False, **kwargs: bool) -> InsnGraph:
    """
    Disassembles the provided method. If the method has multiple Code attributes, the first is chosen.

    :param method: The method to disassemble.
    :param ignore_flags: Skip checking if the method is abstract or native and try to disassemble anyway.
    :param kwargs: Any extra arguments to pass to the disassemble method (see InsnGraph.disassemble()).
    :return: The disassembled instruction graph.
    """

    if not isinstance(method, MethodInfo):
        raise TypeError("Expected type %r, got %r." % (MethodInfo, type(method)))

    if not ignore_flags:
        if method.is_abstract:
            raise ValueError("Method %r is abstract, cannot disassemble." % str(method))
        if method.is_native:
            raise ValueError("Method %r is native, cannot disassemble." % str(method))

    if method.code is None:
        return InsnGraph(method)  # Just create an empty instruction graph
    return InsnGraph.disassemble(method, **kwargs)


def trace(method_or_graph: MethodInfo | InsnGraph, **kwargs: bool) -> Trace:
    """
    Traces the provided graph or method and prints the results to stdout.

    :param method_or_graph: The method or graph to trace.
    :param kwargs: Any extra arguments to pass to the trace method (see Trace.from_graph()).
    """

    if isinstance(method_or_graph, MethodInfo):
        method_or_graph = disassemble(method_or_graph)

    if not isinstance(method_or_graph, InsnGraph):
        raise TypeError("Expected type %r or %r, got %r." % (MethodInfo, InsnGraph, type(graph_or_method)))

    return Trace.from_graph(method_or_graph, **kwargs)


def assemble(graph: InsnGraph, **kwargs: bool) -> None:
    """
    Assembles the provided graph and sets the code attribute of the method it belongs to.

    :param graph: The graph to assemble.
    :param kwargs: Any extra arguments to pass to the assemble method (see InsnGraph.assemble()).
    """

    graph.method.code = graph.assemble(**kwargs)

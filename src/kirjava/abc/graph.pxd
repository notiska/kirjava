# cython: language=c
# cython: language_level=3

from .method cimport Method
from .source cimport Source


cdef class Block(Source):
    """
    An (extended) basic block.
    """

    cdef readonly int label


cdef class ReturnBlock(Block):
    """
    The return block for a graph.
    All blocks returning from the method should have an edge to this one.
    """

    pass


cdef class RethrowBlock(Block):
    """
    The rethrow block for a graph.
    All blocks with explicit throws or uncaught exceptions should have an edge to this one.
    """

    pass


cdef class Edge(Source):
    """
    An edge connects to vertices (blocks) in a control flow graph.
    """

    cdef readonly Block from_
    cdef readonly Block to


cdef class Graph:
    """
    A control flow graph representing a method.
    """

    cdef readonly Method method

    cdef public Block entry_block
    cdef readonly ReturnBlock return_block
    cdef readonly RethrowBlock rethrow_block

    cdef readonly dict _blocks
    cdef readonly dict _forward_edges
    cdef readonly dict _backward_edges
    cdef readonly set _opaque_edges

    cdef void _add(self, Block block, bint check = ?) except *
    cdef void _remove(self, Block block, bint check = ?) except *
    cdef void _connect(self, Edge edge, bint overwrite = ?, bint check = ?) except *
    cdef void _disconnect(self, Edge edge) except *

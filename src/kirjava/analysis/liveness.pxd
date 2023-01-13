# cython: language=c
# cython: language_level=3

from .graph cimport InsnGraph
from .trace cimport Trace


cdef class Liveness:
    """
    Liveness analysis information.
    """

    cdef readonly InsnGraph graph
    cdef readonly Trace trace

    cdef readonly object entries
    cdef readonly object exits

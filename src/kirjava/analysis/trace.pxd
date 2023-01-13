# cython: langauge=c
# cython: language_level=3

from .graph cimport InsnGraph


cdef class Entry:
    """
    An entry on either the stack or in the locals of a state.
    """

    cdef readonly int id
    cdef readonly object source
    cdef readonly object type
    cdef readonly object value
    cdef readonly tuple parents
    cdef readonly tuple merges


cdef class State:
    """
    A stack and locals state representation (also called stackmap frames, I think).
    """

    cdef readonly int _id
    cdef list _errors

    cdef readonly Entry _top

    cdef readonly list stack
    cdef readonly dict locals

    cdef public int max_stack
    cdef public int max_locals

    cdef readonly list local_accesses


cdef class FrozenState:
    """
    A frozen state object.
    """

    cdef readonly Entry _top

    cdef readonly tuple stack
    cdef readonly object locals

    cdef readonly int max_stack
    cdef readonly int max_locals

    cdef readonly tuple local_accesses


cdef class Trace:
    """
    Trace information that has been computed.
    """

    cdef readonly InsnGraph graph

    cdef readonly object states
    cdef readonly tuple errors

    cdef readonly frozenset leaf_edges
    cdef readonly frozenset back_edges
    cdef readonly object subroutines

    cdef readonly int max_stack
    cdef readonly int max_locals

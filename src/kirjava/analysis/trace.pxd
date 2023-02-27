# cython: language=c
# cython: language_level=3

from ..abc.constant cimport Constant
from ..abc.source cimport Source
from ..analysis.graph cimport InsnGraph
from ..verifier._verifier cimport Verifier


cdef class Entry:
    """
    A stack/locals entry.
    """

    cdef readonly Entry parent
    cdef readonly Source source
    cdef readonly object type
    cdef readonly Constant value


cdef class Frame:
    """
    A stack frame. Contains the stack and locals.
    """

    # Temp frame delta building variables
    cdef bint _delta
    cdef Source _source

    cdef list _pops
    cdef list _pushes
    cdef tuple _swaps
    cdef dict _dups
    cdef dict _overwrites

    cdef readonly Verifier verifier

    cdef readonly Entry top

    cdef readonly list stack
    cdef readonly dict locals
    cdef readonly list accesses  # Local accesses
    cdef readonly set consumed  # Entries that were completely consumed

    cdef readonly int max_stack
    cdef readonly int max_locals

    cdef bint _check_type(self, object expect, Entry entry, bint allow_return_address = ?)


cdef class FrameDelta:
    """
    The difference between two frames.
    """

    cdef int _hash  # Pre-computed hash for speed

    cdef readonly Source source

    cdef readonly tuple pops
    cdef readonly tuple pushes

    cdef readonly tuple swaps
    cdef readonly dict dups

    cdef readonly dict overwrites  # Locals overwrites


cdef class Trace:
    """
    A computed trace.
    """

    cdef readonly InsnGraph graph

    cdef readonly dict frames
    cdef readonly dict deltas

    cdef readonly set leaf_edges
    cdef readonly set back_edges
    cdef readonly dict subroutines

    cdef readonly int max_stack
    cdef readonly int max_locals

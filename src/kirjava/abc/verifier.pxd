# cython: language=c
# cython: language_level=3


cdef class TypeChecker:
    """
    The abstract base class for a type checker implementation. Type checkers are responsible for checking if
    verification types can be merged or if they match certain requirements. It is also responsible for merging them.
    """

# cython: language=c
# cython: language_level=3

from ..abc.source cimport Source
from ..abc.verifier cimport TypeChecker


cdef class Error:
    """
    An error that has occurred during verification.
    """

    cdef readonly object type
    cdef readonly Source source
    cdef readonly tuple messages


cdef class Verifier:
    """
    A verifier, performs certain checks to make sure the classfile is valid and reports any errors.
    """

    cdef readonly TypeChecker checker
    cdef list _errors

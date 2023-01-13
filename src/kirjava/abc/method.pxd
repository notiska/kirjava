# cython: language=c
# cython: language_level=3

from .class_ cimport Class


cdef class Method:
    """
    An abstract representation of a Java method.
    """

    cdef readonly Class class_

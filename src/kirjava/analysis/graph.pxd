# cython: language=c
# cython: language_level=3

from ..abc.graph cimport Block, Edge, Graph


cdef class InsnBlock(Block):
    """
    A block containing Java instructions.
    """

    cdef readonly list _instructions
    cdef public object inline_


cdef class InsnEdge(Edge):
    """
    An edge that can contain an instruction. This instruction is added to the block that we're coming from.
    """

    cdef readonly object instruction


cdef class FallthroughEdge(InsnEdge):
    """
    A fallthrough edge (also called an immediate edge) between two blocks.
    This occurs when there are no jumps between blocks, so the flow just falls through to the next block.
    """

    pass


cdef class JumpEdge(InsnEdge):
    """
    An edge that occurs when an explicit jump instruction is used.
    This may be a conditional jump, if so, it must be matched with a fallthrough edge, this is enforced when the graph
    is assembled.
    """

    pass


cdef class JsrJumpEdge(JumpEdge):
    """
    Specific edge for jsr instruction. This edge jumps to the subroutine.
    The corresponding JsrFallthroughEdge is used to return from the subroutine, if it returns at all.
    """

    pass


cdef class JsrFallthroughEdge(JumpEdge):
    """
    Specific edge for jsr instruction. This edge is used to return from the subroutine.
    Should be matched with a JsrJumpEdge.
    """

    pass


cdef class RetEdge(JumpEdge):
    """
    A specific edge for a ret instruction. Might be opaque, if the target is unknown.
    """

    pass


cdef class SwitchEdge(JumpEdge):
    """
    An edge created by a switch instruction (tableswitch or lookupswitch).
    Contains the value and offset, as well as the switch instruction.
    """

    cdef readonly object value


cdef class ExceptionEdge(InsnEdge):
    """
    An edge for an exception handler.
    Contains the exception being caught and a priority (determined by the order of the handlers in the code).
    """

    cdef readonly int priority
    cdef readonly object throwable
    cdef readonly object inline_coverage


cdef class InsnGraph(Graph):
    """
    A control flow graph that contains Java instructions.
    """

    pass

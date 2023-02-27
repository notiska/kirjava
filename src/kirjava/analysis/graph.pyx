# cython: language=c
# cython: language_level=3

__all__ = (
    "InsnBlock", "InsnReturnBlock", "InsnRethrowBlock",
    "FallthroughEdge",
    "JumpEdge",
    "JsrJumpEdge", "JsrFallthroughEdge",
    "RetEdge",
    "ExceptionEdge",
    "InsnGraph",
)

"""
A control flow graph containing the Java instructions (with offsets removed, so somewhat abstracted).
"""

import typing

from .. import _argument
from ..abc.graph cimport Edge, Graph
from ..verifier import FullTypeChecker, VerifyError

if typing.TYPE_CHECKING:
    from ..classfile.members import MethodInfo

include "_assembler.pxi"
include "_block.pxi"
include "_disassembler.pxi"
include "_edge.pxi"

logger = logging.getLogger("kirjava.analysis.graph")


cdef class InsnGraph(Graph):
    """
    A control flow graph that contains Java instructions.
    """

    @classmethod
    def disassemble(cls, code: Code) -> InsnGraph:
        """
        Disassembles a method's code and returns the disassembled graph.

        :param code: The method code to disassemble.
        :return: The created graph.
        """

        logger.debug("Disassembling method %r:" % str(code.parent))

        cdef InsnGraph graph = cls(code.parent)

        jump_targets, handler_targets, exception_bounds = _find_targets_and_bounds(code)
        logger.debug(" - Found %i jump target(s), %i exception handler target(s) and %i exception bound(s)." % (
            len(jump_targets), len(handler_targets), len(exception_bounds),
        ))

        _create_blocks_and_edges(
            graph, code, jump_targets, handler_targets, exception_bounds,
        )
        logger.debug(" - Found %i basic block(s)." % (len(graph._blocks) - 2))  # - 2 for the return and rethrow blocks

        return graph

    def __init__(self, method: "MethodInfo") -> None:
        super().__init__(method, InsnBlock(0), InsnReturnBlock(), InsnRethrowBlock())

    def assemble(
            self,
            do_raise: bool = True,
            simplify_exception_ranges: bool = True,
            compute_frames: bool = True,
            compress_frames: bool = True,
            remove_dead_blocks: bool = True,
    ) -> Code:
        """
        Assembles this graph into a Code attribute.

        :param do_raise: Raise an exception if there are verify errors.
        :param simplify_exception_ranges: Merges overlapping exception ranges, if possible.
        :param compute_frames: Computes stackmap frames and creates a StackMapTable attribute for the code.
        :param compress_frames: Uses compressed stackmap frames instead of just writing out FullFrames.
        :param remove_dead_blocks: Doesn't write dead blocks.
        """

        logger.debug("Assembling method %r:" % str(self.method))

        if compute_frames:
            if self.method.class_.version < StackMapTable.since:
                compute_frames = False
                logger.debug(" - Not computing frames as the class version is %s (min is %s)." % (
                    self.method.class_.version.name, StackMapTable.since.name,
                ))

        cdef Verifier verifier = Verifier(FullTypeChecker())  # TODO: Allow specified type checker through verifier parameter
        cdef Trace trace = Trace.from_graph(self, verifier)
        code = Code(self.method, trace.max_stack, trace.max_locals)

        logger.debug(" - Method trace information:")
        logger.debug("    - %i error(s)." % len(verifier._errors))
        logger.debug("    - %i leaf edge(s), %i back edge(s), %i subroutine(s)." % (
            len(trace.leaf_edges), len(trace.back_edges), sum(map(len, trace.subroutines.values())),
        ))
        logger.debug("    - Max stack: %i, max locals: %i." % (trace.max_stack, trace.max_locals))

        # Write blocks and record the offsets they were written at, as well as keeping track of jump, switch and
        # exception offsets for later adjustment, as we don't know all the offsets while we're writing.

        cdef int offset = 0
        # Record the blocks that have been written and their start/end offsets as well as new instruction mappings
        # (this for keeping track of uninitialised types, hacky, I know). Note that blocks can actually be written
        # multiple times if they have inline=True, so take that into account.
        cdef dict offsets = {}
        cdef set dead = set()

        cdef dict jumps = {}
        cdef dict switches = {}
        cdef list exceptions = []
        cdef dict inlined = {}

        # We'll record blocks that we've created for the purpose of assembling so that we can remove them later, as we
        # don't want to alter the state of the graph.
        cdef set temporary = set()

        logger.debug(" - Writing %i block(s):" % len(self._blocks))

        # Write the entry block first, no matter what
        offset = _write_block(
            self, verifier, offset, self.entry_block, code, offsets, jumps, switches, exceptions, temporary, inlined,
        )
        for label in sorted(self._blocks):
            block = self._blocks[label]
            if block in offsets:
                continue
            if remove_dead_blocks and not block in trace.frames:
                dead.add(block)
                continue
            offset = _write_block(
                self, verifier, offset, block, code, offsets, jumps, switches, exceptions, temporary, inlined,
            )

        # We may need to forcefully write any inline blocks if we have direct jumps to them.
        for block in self._blocks.values():
            # Is the block inline-able or has already been written, so we don't need to worry about it.
            if not block.inline_ or block in offsets:
                continue
            for edge in itertools.chain(jumps.values(), *switches.values(), exceptions):
                if edge is not None and edge.to == block:
                    offset = _write_block(
                        self, verifier, offset, block, code, offsets, jumps, switches, exceptions, temporary, inlined,
                    )
                    logger.debug(" - Force write %s due to non-inlined edge reference." % block)
                    break

        if temporary:
            logger.debug("    - %i temporary block(s) generated while writing." % len(temporary))
            for block in temporary:
                self.remove(block)
        if inlined:
            logger.debug("    - %i block(s) inlined." % len(inlined))

        _adjust_jumps_and_add_exception_handlers(verifier, code, jumps, switches, exceptions, offsets, inlined)
        if simplify_exception_ranges:
            _simplify_exception_ranges(code, exceptions, offsets)

        if compute_frames:
            _nop_out_dead_blocks_and_compute_frames(
                self, verifier, trace, code,
                jumps, switches, exceptions,
                dead, offsets, inlined,
                compress_frames,
            )

        if do_raise and verifier._errors:
            verifier.raise_()

            logger.debug(" - %i error(s) during assembling:" % len(verifier._errors))
            for error in verifier._errors:
                logger.debug("    - %s" % error)

        return code

    # ------------------------------ Edges ------------------------------ #

    def fallthrough(self, from_: InsnBlock, to: InsnBlock, overwrite: bool = False) -> FallthroughEdge:
        """
        Creates and connects a fallthrough edge between two blocks.

        :param from_: The block we're coming from.
        :param to: The block we're going to.
        :param overwrite: Removes already existing fallthrough edges.
        :return: The created fallthrough edge.
        """

        edge = FallthroughEdge(from_, to)
        self.connect(edge, overwrite)
        return edge

    def jump(
            self,
            from_: InsnBlock,
            to: InsnBlock,
            jump: Union[Type[Instruction], Instruction] = instructions.goto,
            overwrite: bool = True,
    ) -> JumpEdge:
        """
        Creates a jump edge between two blocks.

        :param from_: The block we're jumping from.
        :param to: The block we're jumping to.
        :param jump: The jump instruction.
        :param overwrite: Overwrites already existing jump edges.
        :return: The jump edge that was created.
        """

        if type(jump) is type:
            jump = jump()

        if isinstance(jump, JsrInstruction) or jump == instructions.ret:
            raise TypeError("Cannot add jsr/ret instructions with jump() method.")
        elif jump in (instructions.tableswitch, instructions.lookupswitch):
            raise TypeError("Cannot add switch instructions with jump() method.")

        edge = JumpEdge(from_, to, jump)
        self.connect(edge, overwrite)
        return edge

    def catch(
            self,
            from_: InsnBlock,
            to: InsnBlock,
            priority: Union[int, None] = None,
            exception: _argument.ReferenceType = types.throwable_t,
    ) -> ExceptionEdge:
        """
        Creates an exception edge between two blocks.

        :param from_: The block we're coming from.
        :param to: The block that will act as the exception handler.
        :param priority: The priority of this exception handler, lower values mean higher priority.
        :param exception: The exception type being caught.
        :return: The exception edge that was created.
        """

        exception = _argument.get_reference_type(exception)
        if priority is None:  # Determine this automatically
            priority = 0
            for edge in self._forward_edges.get(from_, ()):
                if isinstance(edge, ExceptionEdge) and edge.priority >= priority:
                    priority = edge.priority + 1

        edge = ExceptionEdge(from_, to, priority, exception)
        self.connect(edge)
        return edge

    def return_(self, from_: InsnBlock, overwrite: bool = False) -> FallthroughEdge:
        """
        Creates a fallthrough edge from the given block to the return block.

        :param from_: The block we're coming from.
        :param overwrite: Overwrites any existing fallthrough edges.
        :return: The fallthrough edge that was created.
        """

        return_type = self.method.return_type

        if return_type != types.void_t:
            return_type = return_type.to_verification_type()

            if return_type == types.int_t:
                instruction = instructions.ireturn()
            elif return_type == types.long_t:
                instruction = instructions.lreturn()
            elif return_type == types.float_t:
                instruction = instructions.freturn()
            elif return_type == types.double_t:
                instruction = instructions.dreturn()
            else:
                instruction = instructions.areturn()
        else:
            instruction = instructions.return_()

        edge = FallthroughEdge(from_, self.return_block, instruction)
        self.connect(edge, overwrite)
        return edge

    def throw(self, from_: InsnBlock, overwrite: bool = False) -> FallthroughEdge:
        """
        Creates a fallthrough edge from the given block to the rethrow block.

        :param from_: The block we're coming from.
        :param overwrite: Overwrites any existing fallthrough edges.
        :return: The fallthrough edge that was created.
        """

        edge = FallthroughEdge(from_, self.rethrow_block, instructions.athrow())
        self.connect(edge, overwrite)
        return edge

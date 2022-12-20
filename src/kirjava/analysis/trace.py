#!/usr/bin/env python3

"""
Bytecode information tracing.
"""

import typing
from typing import Any, Tuple, Union

from . import Error
from .. import types
from ..classfile.instructions import Instruction
from ..classfile.members import MethodInfo
from ..types import ReferenceType, VerificationType
from ..types.verification import This, Uninitialized, UninitializedThis

if typing.TYPE_CHECKING:
    from .graph import Block


def trace(state: "State", block: "Block", walk: bool = False) -> Tuple["Trace", ...]:
    """
    Computes trace information for a block.

    :param state: The entry state to start with.
    :param block: The block to trace.
    :param walk: Should we also walk the block's out edges?
    :return: The computed trace information.
    """

    traces: List[Trace] = []

    return tuple(traces)


def _check_reference_type(offset: int, instruction: Instruction, type_: VerificationType) -> Union[Error, None]:
    """
    Checks that the given type is a valid reference type, otherwise a TypeError is thrown.
    """

    # Basic verification type checks first
    if type_ == types.null_t or type_ == types.this_t or type_ == types.uninit_this_t:
        return None
    # Instance checks
    if isinstance(type_, Uninitialized) or isinstance(type_, ReferenceType):
        return None

    return Error(offset, instruction, "expected reference type, got %s" % type_)


# ------------------------------ Classes ------------------------------ #


class Trace:
    """
    Trace information that has been computed.
    """

    __slots__ = ("block", "entry_state", "exit_state", "static_constraints")

    def __init__(self, block: "Block", entry_state: "State", exit_state: "State") -> None:
        """
        :param block: The block that this trace information applies to.
        :param entry_state: The block entry state constraints.
        :param exit_state: The block exit state.
        """

        self.block = block
        self.entry_state = entry_state
        self.exit_state = exit_state

        self.static_constraints: Dict[ReferenceType, List[ReferenceType]] = {}

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Trace) and other.block == self.block

    def __hash__(self) -> int:
        return hash(self.block)


class Entry:
    """
    An entry on either the stack or in the locals of a state.
    """

    __slots__ = ("offset", "type")

    def __init__(self, offset: int, type_: VerificationType) -> None:
        """
        :param offset: The origin offset of the entry.
        :param type_: The type of the entry.
        """

        self.offset = offset
        self.type = type_

    def __repr__(self) -> str:
        return "<Entry(offset=%i, type=%r) at %x>" % (self.offset, self.type, id(self))

    def __str__(self) -> str:
        return str(self.type)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Entry) and other.offset == self.offset and other.type == self.type

    def __hash__(self) -> int:
        return hash((self.offset, self.type))


class State:
    """
    A stack and locals state representation (also called stackmap frames, I think).
    """

    __slots__ = ("offset", "parent", "stack", "locals", "local_accesses", "max_stack", "max_locals")

    @classmethod
    def make_initial(cls, method_info: MethodInfo) -> "State":
        """
        Creates the initial stack state for a given method.

        :param method_info: The method to create the initial state for.
        :return: The new state.
        """

        state = cls(-1)

        offset = 0
        if not method_info.is_static:
            this_class = method_info.class_.get_type()
            if method_info.name == "<init>" and method_info.return_type == types.void_t:  # Constructor method?
                state.set(0, Entry(-1, UninitializedThis(-1, this_class)))
            else:
                state.set(0, Entry(-1, This(this_class)))
            offset += this_class.internal_size

        for index, argument_type in enumerate(method_info.argument_types):
            argument_type = argument_type.to_verification_type()
            state.set(offset, Entry(-(index + 2), argument_type))
            offset += argument_type.internal_size

        state.max_locals = offset  # Also adjust the max locals
        # These don't actually count as local accesses, lmao, you would not believe how LONG it took me to find this
        # fucking bug, good job Iska!!!!
        state.local_accesses.clear()

        return state

    def __init__(self, offset: int, parent: Union["State", None] = None) -> None:
        """
        :param offset: The bytecode offset that this state applies at.
        :param parent: The parent frame to copy the data from.
        """

        self.offset = offset
        self.parent = parent

        self.stack: List[Entry] = []
        self.locals: Dict[int, Entry] = {}

        self.max_stack = 0
        self.max_locals = 0

        # Record locals that were accessed and the type access for liveness tracing later. True means the local was read
        # from and False means it was written to. The intention is that the order of these accesses is maintained so that
        # we can store liveness on a per-block level rather than a per-instruction level, hopefully saving memory and
        # processing time.
        self.local_accesses: List[Tuple[int, bool]] = []

        if parent is not None:
            self.stack.extend(parent.stack)
            self.locals.update(parent.locals)

    def copy(self, offset: Union[int, None] = None) -> "State":
        """
        Creates a copy of this state.

        :param offset: The new bytecode offset to use for the copied state.
        :return: The copied state.
        """

        if offset is None:
            offset = self.offset

        return self.__class__(offset, self)

    def replace(self, old: Entry, new: Entry) -> None:
        """
        Replaces all occurrences of an old entry with a new one.

        :param old: The old entry to replace.
        :param new: The new entry to replace it with.
        """

        for index, entry in enumerate(self.stack):
            if entry == old:
                self.stack[index] = new

        for index, entry in self.locals.items():
            if entry == old:
                self.locals[index] = new

    def pop(self, amount: int = 1, tuple_: bool = False) -> Union[Tuple[Entry, ...], Entry]:
        """
        Pops one or multiple entries off the stack.

        :param amount: The number of entries to pop off the stack.
        :param tuple_: Should the output be returned as a tuple?
        :return: The entry (or multiple entries) that was/were popped off the stack.
        """

        if amount == 1 and not tuple_:
            return self.stack.pop()
        return tuple([self.stack.pop() for index in range(amount)])

    def push(self, entry: Entry) -> None:
        """
        Pushes the provided entry onto the stack.

        :param entry: The entry to push to the stack.
        """

        if entry.type.internal_size > 1:
            self.stack.append(Entry(entry.offset, types.top_t))
        self.stack.append(entry)

        stack_size = len(self.stack) + 1  # FIXME: Doesn't this actually overshoot by 1?
        if stack_size > self.max_stack:
            self.max_stack = stack_size

    def get(self, index: int) -> Entry:
        """
        Gets the value of the local at a given index.

        :param index: The index of the local variable to get.
        :return: The local variable entry.
        """

        self.local_accesses.append((index, True))
        return self.locals[index]

    def set(self, index: int, entry: Entry) -> None:
        """
        Sets the value of the local at a given index to the provided entry.

        :param index: The index of the local to set.
        :param entry: The entry to set the local to.
        """

        self.local_accesses.append((index, False))
        self.locals[index] = entry
        if entry.type.internal_size > 1:
            index += 1
            self.locals[index] = Entry(entry.offset, types.top_t)

        index += 1
        if index > self.max_locals:
            self.max_locals = index

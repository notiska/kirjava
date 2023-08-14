#!/usr/bin/env python3

__all__ = (
    "frame", "graph",
    "Entry", "Frame",
    "InsnBlock", "InsnReturnBlock", "InsnRethrowBlock",
    "FallthroughEdge", "JumpEdge",
    "JsrJumpEdge", "JsrFallthroughEdge", "RetEdge",
    "ExceptionEdge",
    "InsnGraph",
    "Context", "Trace",
)

"""
Bytecode analysis stuff.
"""

import typing
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from . import frame
from .frame import *
from ..abc import Method, Source
from ..types import reserved_t, Type, Verification

if typing.TYPE_CHECKING:
    from .graph import InsnBlock, InsnGraph, JsrJumpEdge, RetEdge


class Context:
    """
    Used while computing the trace so that instructions have context.
    """

    __slots__ = (
        "method", "graph",
        "do_raise",
        "_frame", "source",
        "conflicts",
        "__push_direct", "__pop_direct",
        "__set_direct", "__get_direct",
        "local_uses", "local_defs",
    )

    @property
    def frame(self) -> Optional[Frame]:
        return self._frame

    @frame.setter
    def frame(self, value: Optional[Frame]) -> None:
        """
        Resets everything in preparation for the new block to be traced.
        """

        self._frame = value

        if value is not None:
            self.__push_direct = value.push
            self.__pop_direct = value.pop
            self.__set_direct = value.set
            self.__get_direct = value.get
        else:
            self.__push_direct = lambda *args: None
            self.__pop_direct = lambda *args: None
            self.__set_direct = lambda *args: None
            self.__get_direct = lambda *args: None

        # self.local_uses = set()
        # self.local_defs = set()

    def __init__(self, method: Method, graph: "InsnGraph", do_raise: bool = True) -> None:
        self.method = method
        self.graph = graph

        self.do_raise = do_raise

        self._frame: Optional[Frame] = None
        self.source: Optional[Source] = None  # The source of the current tracing instruction

        self.conflicts: Set[Trace.Conflict] = set()

        self.__push_direct = lambda *args: None
        self.__pop_direct = lambda *args: None
        self.__set_direct = lambda *args: None
        self.__get_direct = lambda *args: None

        # These are used on a per-block basis, namely for live variable analysis. The intention is that they are reset
        # every time a new block is entered.
        self.local_uses: Set[int] = set()
        self.local_defs: Set[int] = set()

    def __repr__(self) -> str:
        return "<Context(method=%r, frame=%r) at %x>" % (self.method, self.frame, id(self))

    def replace(self, entry: Entry, type_: Type) -> None:
        """
        Replaces all occurrences of an entry with a new type.

        :param entry: The old entry to replace.
        :param type_: The new type.
        """

        new = entry.cast(type_, self.source)
        if new is entry:
            return
        old = entry

        for index, entry in enumerate(self._frame.stack):
            if entry is old:
                self._frame.stack[index] = new
        for index, entry in self._frame.locals.items():
            if entry is old:
                self._frame.locals[index] = new
        self._frame.tracked.add(new)

    # ------------------------------ Stack operations ------------------------------ #

    def push(self, entry_or_type: Union[Entry, Type], constraint: Optional[Type] = None) -> Entry:
        """
        Pushes an entry or type onto the top of the stack.
        This also handles wide types automatically.

        :param entry_or_type: An entry to push or a type used to create an entry.
        :param constraint: A type to constrain the entry to. Different from using Entry.constrain as it will create a
                           child entry if the types cannot be merged.
        :return: The entry that was pushed to the stack.
        """

        if type(entry_or_type) is not Entry:
            entry = Entry(entry_or_type, self.source)
        else:
            entry = entry_or_type

        if constraint is not None:
            added = entry.constrain(constraint, self.source)
            if added and not constraint.as_vtype().mergeable(entry._type):
                self.conflicts.add(Trace.Conflict(entry, constraint, self.source))
                entry = Entry(constraint, self.source, entry)

        self.__push_direct(entry)  # self._frame.push(entry)
        if entry._type.wide:
            self.__push_direct(Entry(reserved_t, self.source))  # self._frame.push(Frame.RESERVED)

        return entry

    def pop(self, count: int = 1, *, as_tuple: bool = False) -> Union[Tuple[Entry, ...], Entry]:
        """
        Pops one or more entries from the stack.
        Does not handle wide types.

        :param count: The number of entries to pop.
        :param as_tuple: Whether to return a tuple of entries or a single entry.
        """

        entries = self.__pop_direct(count)  # self._frame.pop(count)

        if self.source is not None:
            for entry in entries:
                if entry is Frame.TOP:
                    break
                entry._consumers.append(self.source)

        if count == 1 and not as_tuple:
            return entries[0]
        return tuple(entries)

    # ------------------------------ Locals operations ------------------------------ #

    def set(self, index: int, entry_or_type: Union[Entry, Type], constraint: Optional[Type] = None) -> None:
        """
        Sets the local at the given index to the given entry or type.
        This also handles wide types automatically.

        :param index: The index of the local to set.
        :param entry_or_type: An entry to set or a type used to create an entry.
        :param constraint: A type to constrain the entry to. Different from using Entry.constrain as it will create a
                           child entry if the types cannot be merged.
        """

        if type(entry_or_type) is not Entry:
            entry = Entry(entry_or_type, self.source)
        else:
            entry = entry_or_type

        if constraint is not None:
            added = entry.constrain(constraint, self.source)
            if added and not constraint.mergeable(entry._type):
                self.conflicts.add(Trace.Conflict(entry, constraint, self.source))
                entry = Entry(constraint, self.source, entry)

        self.__set_direct(index, entry)  # self._frame.set(index, entry)
        self.local_defs.add(index)
        if entry._type.wide:
            self.__set_direct(index + 1, Entry(reserved_t, self.source))  # self._frame.set(index + 1, Frame.RESERVED)
            self.local_defs.add(index + 1)

    def get(self, index: int) -> Entry:
        """
        Gets a local entry from the frame.

        :param index: The index of the local to get.
        """

        entry = self.__get_direct(index)  # self._frame.get(index)
        if self.source is not None and entry is not Frame.TOP:
            entry._consumers.append(self.source)

        # If the local has already been overwritten then don't add it to the reads. The better solution would be storing
        # an actual use-def chain, but using sets is much faster. My thinking behind this is that since we're working
        # backwards, we don't care if the local is used in the same block it's overwritten as if it's not used in any
        # subsequent blocks then it's not live again.
        if not index in self.local_defs:
            self.local_uses.add(index)
            if entry._type.wide:
                # I wouldn't necessarily consider making the reserved half of the wide type live hacky per-se, it might
                # seem somewhat unconventional but it does save us a lot of time (and code) when generating stackmap
                # frames. And tbh, I'm not sure how other libraries handle this lol.
                self.local_uses.add(index + 1)

        return entry

    def constrain(self, entry: Entry, constraint: Type, *, original: bool = False) -> None:
        """
        Constrains an entry to a given type. This is only a "passive" constraint, and will only be checked after the
        has been completed fully.
        """

        # We don't want to add constraints to these as they are class fields.
        if entry is Frame.TOP:
            # TODO: Maybe do something else with this?
            return

        added = entry.constrain(constraint, self.source, original=original)
        if added and not constraint.as_vtype().mergeable(entry._type):
            self.conflicts.add(Trace.Conflict(entry, constraint, self.source))


class Trace:
    """
    Trace information for a given method.
    """

    __slots__ = (
        "graph",
        "entries", "exits",
        "conflicts",
        "subroutines",
        "pre_liveness", "post_liveness",
        "max_stack", "max_locals",
    )

    @classmethod
    def from_graph(cls, graph: "InsnGraph", *, do_raise: bool = True) -> "Trace":
        """
        Creates a trace from an instruction graph.

        :param graph: The instruction graph.
        :param do_raise: Raise an exception if part of the graph is invalid.
        :return: The trace.
        """

        self = cls(graph)
        trace(self, graph, do_raise)
        return self

    def __init__(self, graph: "InsnGraph") -> None:
        """
        :param graph: The graph that was traced.
        """

        self.graph = graph

        self.entries: Dict["InsnBlock", List[Frame]] = defaultdict(list)
        self.exits: Dict["InsnBlock", List[Frame]] = defaultdict(list)

        self.conflicts: Set[Trace.Conflict] = set()
        self.subroutines: List[Trace.Subroutine] = []

        self.pre_liveness: Dict["InsnBlock", Set[int]] = {}
        self.post_liveness: Dict["InsnBlock", Set[int]] = {}

        self.max_stack = 0
        self.max_locals = 0

    def __repr__(self) -> str:
        return "<Trace(entries=%i, exits=%i, conflicts=%i, subroutines=%i, max_stack=%i, max_locals=%i) at %x>" % (
            len(self.entries), len(self.exits), len(self.conflicts), len(self.subroutines), self.max_stack, self.max_locals, id(self),
        )

    class Conflict:
        """
        A type conflict.
        """

        __slots__ = ("entry", "expected", "source", "_hash")

        def __init__(self, entry: Entry, expected: Type, source: Optional[Source]) -> None:
            self.entry = entry
            self.expected = expected
            self.source = source

            self._hash = hash((entry, expected, source))

        def __repr__(self) -> str:
            return "<Trace.Conflict(entry=%s, expected=%s, source=%s)>" % (self.entry, self.expected, self.source)

        def __str__(self) -> str:
            if self.source is not None:
                return "%s expected type %s, got %s." % (self.source, self.expected, self.entry)
            return "expected type %s, got %s." % (self.expected, self.entry)

        def __eq__(self, other: Any) -> bool:
            return (
                type(other) is Trace.Conflict and
                self.entry == other.entry and
                self.expected == other.expected and
                self.source == other.source
            )

        def __hash__(self) -> int:
            return self._hash

    class Subroutine:
        """
        Information about a subroutine.
        """

        __slots__ = ("jsr_edge", "ret_edge", "exit_block", "frame")

        def __init__(self, jsr_edge: "JsrJumpEdge", ret_edge: "RetEdge", exit_block: "InsnBlock", frame: Frame) -> None:
            self.jsr_edge = jsr_edge
            self.ret_edge = ret_edge
            self.exit_block = exit_block
            self.frame = frame

        def __repr__(self) -> str:
            return "<Trace.Subroutine(jsr_edge=%r, ret_edge=%r, exit_block=%r, frame=%r) at %x>" % (
                self.jsr_edge, self.ret_edge, self.exit_block, self.frame, id(self),
            )

        def __str__(self) -> str:
            return "%s (-> %s)" % (self.jsr_edge, self.ret_edge.copy(to=self.exit_block))


from . import graph
from ._trace import *
from .graph import *

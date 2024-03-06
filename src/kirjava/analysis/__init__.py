#!/usr/bin/env python3

__all__ = (
    "frame", "graph",
    "Entry", "Frame",
    "InsnBlock", "InsnReturnBlock", "InsnRethrowBlock",
    "FallthroughEdge", "JumpEdge",
    "JsrJumpEdge", "JsrFallthroughEdge", "RetEdge",
    "ExceptionEdge",
    "InsnGraph",
    "Generifier",
    "Trace", "Context",
)

"""
Bytecode analysis stuff.
"""

import typing
from collections import defaultdict
from typing import Any

from . import frame
from ._generify import *
from .frame import *
from ..abc import Method, Source
from ..types import reserved_t, Type

if typing.TYPE_CHECKING:
    from .graph import InsnBlock, InsnGraph, JsrJumpEdge, RetEdge


class Trace:
    """
    Trace information for a given method.
    """

    __slots__ = (
        "graph",
        "entries", "exits",
        "conflicts",
        "returned",
        "subroutines",
        "pre_liveness", "post_liveness",
        "max_stack", "max_locals",
    )

    @classmethod
    def from_graph(
            cls, graph: "InsnGraph",
            *,
            do_raise: bool = True,
            merge_non_live: bool = True,
            make_params_live: bool = False,
    ) -> "Trace":
        """
        Creates a trace from an instruction graph.

        :param graph: The instruction graph.
        :param do_raise: Raise an exception if part of the graph is invalid.
        :param merge_non_live: Attempts to merge non-live locals, can be slower but may result in more insightful
                               analysis, though it does assume that locals aren't reused (which may not be default
                               behaviour in some samples).
        :param make_params_live: Makes the parameters appear live in the initial frame. This is useful for generating
                                 stackmap frames, though may not be entirely accurate.
        :return: The trace information.
        """

        self = cls(graph)
        trace(self, graph, do_raise, merge_non_live, make_params_live)
        return self

    def __init__(self, graph: "InsnGraph") -> None:
        """
        :param graph: The graph that was traced.
        """

        self.graph = graph

        self.entries: dict["InsnBlock", list[Frame]] = defaultdict(list)
        self.exits: dict["InsnBlock", list[Frame]] = defaultdict(list)

        self.conflicts: set[Trace.Conflict] = set()
        self.returned: set[Entry] = set()
        self.subroutines: list[Trace.Subroutine] = []

        self.pre_liveness: dict["InsnBlock", set[int]] = {}
        self.post_liveness: dict["InsnBlock", set[int]] = {}

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

        def __init__(self, entry: Entry, expected: Type, source: Source | None) -> None:
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


class Context:
    """
    Used while computing the trace so that instructions have context.
    """

    __slots__ = (
        "method", "graph",
        "do_raise",
        "frame", "source",
        "returned",
        "conflicts",
        "local_uses", "local_defs",
    )

    def __init__(self, method: Method, graph: "InsnGraph", do_raise: bool = True) -> None:
        self.method = method
        self.graph = graph

        self.do_raise = do_raise

        self.frame: Frame | None = None
        self.source: Source | None = None  # The source of the current tracing instruction

        self.returned: set[Entry] = set()
        self.conflicts: set[Trace.Conflict] = set()

        # These are used on a per-block basis, namely for live variable analysis. The intention is that they are reset
        # every time a new block is entered.
        self.local_uses: set[int] = set()
        self.local_defs: set[int] = set()

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

        for index, entry in enumerate(self.frame.stack):
            if entry is old:
                self.frame.stack[index] = new
        for index, entry in self.frame.locals.items():
            if entry is old:
                self.frame.locals[index] = new
        self.frame.tracked.add(new)

    # ------------------------------ Stack operations ------------------------------ #

    def push(self, entry_or_type: Entry | Type, constraint: Type | None = None) -> Entry:
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
        type_ = entry.generic

        if constraint is not None:
            added = entry.constrain(constraint, self.source)
            conflict = constraint.abstract and not constraint.mergeable(type_)
            if added and conflict and not type_.mergeable(constraint):
                self.conflicts.add(Trace.Conflict(entry, constraint, self.source))
                entry = Entry(constraint.as_vtype(), self.source, entry)

        # The same behaviour as `self.frame.push`, but it's much faster to just implement it here.
        self.frame.stack.append(entry)
        self.frame.tracked.add(entry)
        if type_.wide:
            reserved = Entry(reserved_t, self.source)
            self.frame.stack.append(reserved)
            self.frame.tracked.add(reserved)

        if len(self.frame.stack) > self.frame.max_stack:
            self.frame.max_stack = len(self.frame.stack)

        return entry

    def pop(self, count: int = 1, *, as_tuple: bool = False) -> tuple[Entry, ...] | Entry:
        """
        Pops one or more entries from the stack.
        Does not handle wide types.

        :param count: The number of entries to pop.
        :param as_tuple: Whether to return a tuple of entries or a single entry.
        """

        # We'll use a faster path here because we know that this method will only really be called by instructions.
        if count == 1 and self.frame.stack:
            entries = [self.frame.stack.pop()]
        # TODO: Faster equivalent for a count of 2?
        else:
            entries = self.frame.pop(count)

        if self.source is not None:  # FIXME: When will this really ever be the case? Remove probably.
            for entry in entries:
                if entry is Frame.TOP:
                    break
                entry._consumers.append(self.source)

        if count == 1 and not as_tuple:
            return entries[0]
        return tuple(entries)

    # ------------------------------ Locals operations ------------------------------ #

    def set(self, index: int, entry_or_type: Entry | Type, constraint: Type | None = None) -> None:
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
        type_ = entry.generic

        if constraint is not None:
            added = entry.constrain(constraint, self.source)
            conflict = constraint.abstract and not constraint.mergeable(type_)
            if added and conflict and not type_.mergeable(constraint):
                self.conflicts.add(Trace.Conflict(entry, constraint, self.source))
                entry = Entry(constraint.as_vtype(), self.source, entry)

        self.frame.locals[index] = entry
        self.frame.tracked.add(entry)
        self.local_defs.add(index)

        if type_.wide:
            index += 1
            reserved = Entry(reserved_t, self.source)
            self.frame.locals[index] = reserved
            self.frame.tracked.add(reserved)
            self.local_defs.add(index)

        if index >= self.frame.max_locals:
            self.frame.max_locals = index + 1

    def get(self, index: int) -> Entry:
        """
        Gets a local entry from the frame.

        :param index: The index of the local to get.
        """

        entry = self.frame.get(index)
        if entry is Frame.TOP:
            return Frame.TOP
        if self.source is not None:
            entry._consumers.append(self.source)

        # If the local has already been overwritten then don't add it to the reads. The better solution would be storing
        # an actual use-def chain, but using sets is much faster. My thinking behind this is that since we're working
        # backwards, we don't care if the local is used in the same block it's overwritten as if it's not used in any
        # subsequent blocks then it's not live again.
        new = not index in self.local_defs
        if new:
            self.local_uses.add(index)

        if entry.generic.wide:
            reserved = self.frame.get(index + 1)
            if reserved.generic is not reserved_t:
                self.conflicts.add(Trace.Conflict(reserved, reserved_t, self.source))
            if new:
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
        if added and not constraint.as_vtype().mergeable(entry.generic):
            self.conflicts.add(Trace.Conflict(entry, constraint, self.source))


from . import graph
from ._trace import *
from .graph import *

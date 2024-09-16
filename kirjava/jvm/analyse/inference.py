#!/usr/bin/env python3

__all__ = (
    "Generaliser",
)

import logging
import typing

if typing.TYPE_CHECKING:
    from .entry import Entry

logger = logging.getLogger("ijd.analysis.inference")


class Generaliser:
    """
    An entry generaliser.

    Methods
    -------
    generalise(self, entry: Entry) -> Entry
        Fully generalises an entry (including type and value).
    """

    __slots__ = ("_entry_cache")

    def __init__(self) -> None:
        self._entry_cache: dict["Entry", "Entry"] = {}

    def generalise(self, entry: "Entry") -> "Entry":
        """
        Fully generalises an entry (including type and value).

        Parameters
        ----------
        entry: Entry
            The entry to generalise.

        Returns
        -------
        Entry
            The generalised entry.
        """

        generalised = self._entry_cache.get(entry)
        if generalised is not None:
            return generalised

        adjacent = set()
        if not entry.generified:
            adjacent.add(entry)
        constraints = entry.constraints.copy()

        visited = {entry}
        stack = entry.adjacent.copy()

        while stack:
            merged = stack.pop()
            if merged in visited:
                continue
            elif not merged.generified:
                adjacent.add(merged)
            constraints.update(merged.constraints)
            stack.update(merged.adjacent.symmetric_difference(visited))

        if len(adjacent) == 1:  # Easy case for us as there is only one possible entry.
            generalised = adjacent.pop()
            self._entry_cache[entry] = generalised
            self._entry_cache[generalised] = generalised  # May save us some time later, or may not.
            if entry is not generalised and entry.generified:
                logger.debug("Generalised %s -> %s from (%s).", entry, generalised, generalised.source)
            return generalised

        for entry in adjacent:
            print(repr(entry))
        for constraint in constraints:
            print(constraint)
        raise NotImplementedError("multiple possible entries")

# #!/usr/bin/env python3

# __all__ = (
#     "Entry",
# )

# import logging

# from ...model.types import *
# from ...model.values import Value
# from ...model.values.constants import Constant

# logger = logging.getLogger("ijd.jvm.analyse.entry")


# class Entry:
#     """
#     A type entry on either the operand stack or in the local variables.

#     Attributes
#     ----------
#     type : Type
#         The type of this entry.
#     source: Source | None
#         The original producer of this entry.
#     generified: bool
#         Whether the type has been generified, this could be due to stack merging, etc.
#     hidword: bool
#         Whether this is the high dword of a wide type.
#     split: bool
#         Whether this entry has been split from a wide type.
#     value: Value | None
#         The value of this entry, if known.
#     parent: Entry | None
#         The parent of this entry.
#     adjacent: set[Entry]
#         Adjacent entries that are essentially the same as this one, created from
#         merges, etc.
#     escapes: set[Source]
#         A set of sources where this entry escapes the method.

#     Methods
#     -------
#     copy(self) -> Entry
#         Creates a copy of this entry.
#     generify(self) -> Entry
#         Creates a generified copy of this entry.
#     cast(self, type_: Type, source: Source | None = None) -> Entry
#         Casts this entry to a different type.
#     constrain(self, type_: Type, source: Source | None = None) -> Entry
#         Adds a type constraint to this entry.
#     hint(self, type_: Type, source: Source | None = None) -> None
#         Adds a type hint to this entry.
#     """

#     __slots__ = (
#         "type", "source", "hidword", "split", "generified",
#         "value", "parent", "adjacent",
#         "escapes", "conflicts", "hints", "constraints",
#     )

#     def __init__(self, type_: Type, source: Source | None = None, *, hidword: bool = True) -> None:
#         self.type = type_.as_vtype()
#         self.source = source
#         self.hidword = hidword
#         self.split = False
#         self.generified = False

#         self.value: Value | None = None
#         self.parent: Entry | None = None
#         self.adjacent: set[Entry] = set()

#         self.escapes:               set[Source] = set()
#         self.conflicts:     set[Entry.Conflict] = set()
#         self.hints:       set[Entry.Constraint] = set()
#         self.constraints: set[Entry.Constraint] = set()

#         if self.type != type_:
#             self.hints.add(Entry.Constraint(type_, source))

#     def __repr__(self) -> str:
#         return "<Entry(type=%s, source=%r, hidword=%s, generified=%s, value=%r)>" % (
#             self.type, self.source, self.hidword, self.generified, self.value,
#         )

#     def __str__(self) -> str:
#         if isinstance(self.value, Constant):
#             string = str(self.value)
#         else:
#             string = str(self.type)
#         if self.generified:  # Generified types will not be primitives.
#             return "GENERIFIED(%s)" % string
#         elif not self.type.wide:
#             return "%s" % string
#         elif self.hidword:
#             return "HIDWORD(%s)" % string
#         else:
#             return "LODWORD(%s)" % string

#     def copy(self) -> "Entry":
#         """
#         Creates a copy of this entry.

#         Returns
#         -------
#         Entry
#             The copy of this entry.
#         """

#         entry = Entry(self.type, self.source, hidword=self.hidword)

#         # Copying only the "essential" information across.
#         entry.generified = self.generified
#         entry.split = self.split
#         entry.parent = self.parent
#         entry.value = self.value
#         entry.adjacent.add(self)
#         # entry.escapes.update(self.escapes)

#         return entry

#     def generify(self) -> "Entry":
#         """
#         Creates a generified copy of this entry, if applicable.

#         Only initialised reference types will be generified. In any other case, a
#         copy of this entry will be returned.

#         Returns
#         -------
#         Entry
#             Either a copy of this entry or the generified copy of this entry.
#         """

#         if (
#             self.generified or
#             self.type == object_t or
#             not isinstance(self.type, Reference) or
#             isinstance(self.type, Uninitialized)
#         ):
#             entry = self.copy()
#             entry.value = None
#             return entry

#         entry = Entry(object_t)

#         entry.generified = True
#         entry.adjacent.add(self)
#         # entry.escapes.update(self.escapes)
#         # entry.constraints.add(Entry.Constraint(self.type, self.source))

#         return entry

#     def cast(self, type_: Type, source: Source | None = None) -> "Entry":
#         """
#         Casts this entry to a different type.

#         Parameters
#         ----------
#         type_: Type
#             The type to cast the entry to.
#         source: Source | None
#             The source responsible for the type cast.

#         Returns
#         -------
#         Entry
#             The type casted entry.
#         """

#         if type_ == self.type:
#             return self

#         entry = Entry(type_, source)
#         entry.parent = self
#         if self.type.assignable(type_):
#             self.constraints.add(Entry.Constraint(type_, source))
#         return entry

#     def constrain(self, type_: Type, source: Source | None = None) -> "Entry":
#         """
#         Adds a type constraint to this entry.

#         Parameters
#         ----------
#         type_: Type
#             The type constraint to add.
#         source: Source | None
#             The source responsible for the type constraint.

#         Returns
#         -------
#         Entry
#             Either this entry or a new one with the correct type, if the type
#             constraint was not met.
#         """

#         if type_ == self.type:
#             return self
#         elif not type_.assignable(self.type):
#             entry = Entry(type_, source)
#             entry.parent = self
#             self.conflicts.add(Entry.Conflict(entry, type_, source))
#             # print(self, type_)
#             # raise Exception()
#             return entry

#         # We won't add abstract types as constraints if we know that the current type of this entry already satisfies
#         # said constraint because they don't add any more typing information.
#         if not type_.abstract:
#             self.constraints.add(Entry.Constraint(type_, source))
#         return self

#     def hint(self, type_: Type, source: Source | None = None) -> None:
#         """
#         Adds a type hint to this entry.

#         Parameters
#         ----------
#         type_: Type
#             The type hint to add.
#         source: Source | None
#             The source responsible for the type hint.
#         """

#         if type_ == self.type:
#             return
#         self.hints.add(Entry.Constraint(type_, source))

#     # ------------------------------ Classes ------------------------------ #

#     class Constraint:
#         """
#         An entry type constraint.

#         Attributes
#         ----------
#         type : Type
#             The type constraint.
#         source: Source | None
#             The source responsible for the type constraint.
#         """

#         __slots__ = ("type", "source", "_hash")

#         def __init__(self, type_: Type, source: Source | None) -> None:
#             self.type = type_
#             self.source = source
#             self._hash = hash((self.type, self.source))

#         def __repr__(self) -> str:
#             return "<Entry.Constraint(type=%s, source=%s)>" % (self.type, self.source)

#         def __eq__(self, other: object) -> bool:
#             return isinstance(other, Entry.Constraint) and self.type == other.type and self.source == other.source

#         def __hash__(self) -> int:
#             return self._hash

#     class Conflict:
#         """
#         Information about a type conflict.

#         Attributes
#         ----------
#         entry: Entry
#             The resulting entry with the correct type, created due to this type conflict.
#         expect: Type
#             The expected type of the entry.
#         source: Source | None
#             The source expecting the entry to be the given type.
#         """

#         __slots__ = ("entry", "expect", "source", "_hash")

#         def __init__(self, entry: "Entry", expect: Type, source: Source | None) -> None:
#             self.entry = entry
#             self.expect = expect
#             self.source = source

#             self._hash = hash((entry, expect, source))

#         def __repr__(self) -> str:
#             return "<Entry.Conflict(entry=%r, expect=%s, source=%s)>" % (self.entry, self.expect, self.source)

#         def __eq__(self, other: object) -> bool:
#             return (
#                 isinstance(other, Entry.Conflict) and
#                 self.entry == other.entry and
#                 self.expect == other.expect and
#                 self.source == other.source
#             )

#         def __hash__(self) -> int:
#             return self._hash

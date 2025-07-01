#!/usr/bin/env python3

from __future__ import annotations

__all__ = (
    "Loader", "CachingLoader", "Linker",
)

import typing
from typing import Iterable, Iterator
from weakref import WeakValueDictionary

from .class_ import Class, Field, Method
from .types import Class as ClassType, Reference, Type
from ..backend import Err, Ok, Result


class Loader:
    """
    A class loader base.

    Responsible for looking up classes given their names.

    Methods
    -------
    find_class(self, linker: Linker, name: str) -> Result[Class]
        Finds a class given its name.
    find_resource(self, name: str) -> Result[bytes]
        Finds a resource given its name.
    """

    __slots__ = ()

    # owns_class(self, class_: Class) -> bool
    #     Checks if the loader owns a class, AKA it was resolved by this loader.

    # def owns_class(self, class_: Class) -> bool:
    #     """
    #     Checks if the loader owns a class, AKA it was resolved by this loader.

    #     Parameters
    #     ----------
    #     class_: Class
    #         The class to check.

    #     Returns
    #     -------
    #     bool
    #         Whether this loader owns the class.
    #     """

    #     raise NotImplementedError(f"owns_class() not implemented for {type(self)!r}")

    def find_class(self, linker: "Linker", name: str) -> Result[Class]:
        """
        Finds a class given its name.

        Parameters
        ----------
        linker: Linker
            The linker to use to resolve further references.
        name: str
            The unqualified name of the class.
        """

        raise NotImplementedError(f"find_class() not implemented for {type(self)!r}")

    def find_resource(self, name: str) -> Result[bytes]:
        """
        Finds a resource given its name.

        Parameters
        ----------
        name: str
            The name of the resource.
        """

        raise NotImplementedError(f"find_resource() not implemented for {type(self)!r}")


class CachingLoader(Loader):
    """
    A loader that holds strong references to classes.

    Attributes
    ----------
    cached: int
        The number of cached classes.
    delegate: Loader
        The delegate loader to load and cache from.

    Methods
    -------
    clear(self) -> None
        Clears the class cache.
    """

    __slots__ = ("delegate", "_cache")

    @property
    def cached(self) -> int:
        return len(self._cache)

    def __init__(self, delegate: Loader) -> None:
        self.delegate = delegate
        self._cache: dict[tuple[Linker, str], Class] = {}

    def find_class(self, linker: "Linker", name: str) -> Result[Class]:
        # Honestly this shouldn't happen if we're holding strong references because the linker should also look it up in
        # its cache, but this acts as a fallback nonetheless.
        class_ = self._cache.get((linker, name))
        if class_ is not None:
            return Ok(class_)
        return self.delegate.find_class(linker, name)

    def find_resource(self, name: str) -> Result[bytes]:
        return self.delegate.find_resource(name)

    def clear(self) -> None:
        """
        Clears the class cache.
        """

        self._cache.clear()


class Linker:
    """
    A static linker implementation.

    Provides lookups for classes, fields and methods given various loaders. This may
    not be 100% accurate of a real runtime, as classloaders may be relatively
    complex.

    It is advised that the user creates their own implementations to match their
    desired functionality.

    Attributes
    ----------
    loaders: tuple[Loader, ...]
        An immutable tuple of the loaders to use when looking up classes.
        The loaders are checked from first to last.
    cached: int
        The number of currently cached classes.

    Methods
    -------
    add(self, loader: Loader) -> None
        Appends a class loader to the linker.
    insert(self, index: int, loader: Loader) -> None
        Inserts a class loader at a specific index.
    remove(self, loader: Loader) -> bool
        Removes a class loader from the linker.
    clear(self) -> None
        Clears all class loaders from the linker.
    find_class(self, name: str) -> Result[Class]
    find_field(self, name: str, type: Type) -> Field | None
    find_method(self, name: str, arg_types: tuple[Type, ...], ret_type: Type) -> Method | None
    """

    __slots__ = ("_loaders", "_cached")

    @property
    def loaders(self) -> tuple[Loader, ...]:
        return tuple(self._loaders)

    @property
    def cached(self) -> int:
        return len(self._cached)

    def __init__(self, loaders: Iterable[Loader] | None = None) -> None:
        self._loaders: list[Loader] = []
        self._cached: WeakValueDictionary[Reference, Class] = WeakValueDictionary()

        if loaders is not None:
            self._loaders.extend(loaders)

    def __repr__(self) -> str:
        return f"<Linker(loaders={self.loaders!r}, cached={self.cached})>"

    def __iter__(self) -> Iterator[Loader]:
        return iter(self._loaders)

    # FIXME: typing.overload for specifics. Needed in quite a few places actually.
    def __getitem__(self, key: int | str) -> Loader | Class:
        if isinstance(key, int):
            return self._loaders[key]
        return self.find_class(key).unwrap()

    def __setitem__(self, index: int, value: Loader) -> None:
        self._loaders[index] = value
        self._cached.clear()

    def __delitem__(self, key: int | Loader) -> None:
        if isinstance(key, int):
            del self._loaders[key]
            self._cached.clear()
        else:
            self.remove(key)

    # ------------------------------ Loader API ------------------------------ #

    def add(self, loader: Loader) -> None:
        """
        Adds a class loader to the linker.

        Duplicates are not allowed.

        Parameters
        ----------
        loader: Loader
            The loader to append.
        """

        if loader in self._loaders:
            return
        self._loaders.append(loader)
        # We don't actually need to clear the cache in this place, as this loader is the lowest priority and therefore
        # any classes already loaded will have been loaded by a higher priority loader.

    def insert(self, index: int, loader: Loader) -> None:
        """
        Inserts a class loader at a specific index.

        Duplicates are not allowed, and if the index is out of bounds, the loader is
        inserted at the closest valid index.

        Parameters
        ----------
        index: int
            The index to insert at.
        loader: Loader
            The loader to insert.
        """

        if loader in self._loaders:
            return
        self._loaders.insert(index, loader)
        # FIXME: A smarter cache clearing algorithm, we only need to clear classes loaded by lower priority loaders.
        self._cached.clear()

    def remove(self, loader: Loader) -> bool:
        """
        Removes a class loader from the linker.

        Parameters
        ----------
        loader: Loader
            The loader to remove.

        Returns
        -------
        bool
            Whether the loader was in the list, and therefore if it was removed.
        """

        try:
            self._loaders.remove(loader)
            self._cached.clear()  # FIXME: See above.
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """
        Clears all class loaders from the linker.
        """

        self._loaders.clear()
        self._cached.clear()

    # ------------------------------ Resolution API ------------------------------ #

    def find_class(self, name_or_type: str | Reference) -> Result[Class]:
        """
        Finds a class given its name or type.
        """

        if not isinstance(name_or_type, Reference):
            name_or_type = ClassType(name_or_type)

        cached = self._cached.get(name_or_type)
        if cached is not None:
            if cached.as_type() == name_or_type:  # Need to do this check as `Class` objects are mutable.
                return Ok(cached)
            del self._cached[name_or_type]
            self._cached[cached.as_type()] = cached

        with Result[Class]() as result:
            for loader in self.loaders:
                class_ = loader.find_class(self, name_or_type.name).into(result).value
                if class_ is not None:
                    self._cached[name_or_type] = class_
                    return result.ok(class_)
            return result.err(KeyError(name_or_type))
        return result

    # FIXME: Static lookups needed too.

    def find_field(self, name: str, type: Type) -> Result[Field]:
        raise NotImplementedError()

    def find_method(self, name: str, arg_types: tuple[Type, ...], ret_type: Type) -> Result[Method]:
        raise NotImplementedError()

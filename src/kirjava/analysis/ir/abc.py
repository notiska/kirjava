#!/usr/bin/env python3

"""
Abstract base classes.
"""

from abc import abstractmethod, ABC

from ...types import BaseType


class Expression(ABC):
    """
    A base expression.
    """

    @property
    @abstractmethod
    def type(self) -> BaseType:
        """
        :return: The output type of this expression.
        """

        ...


class Statement(ABC):
    """
    A base statement.
    """

    ...

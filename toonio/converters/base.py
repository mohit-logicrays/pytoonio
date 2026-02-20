"""
ToonIO Base Converter Module.

Defines the abstract base classes for all encoders and decoders
following the Interface Segregation Principle.

Author: Mohit
License: MIT
"""

from abc import ABC, abstractmethod
from typing import Any

from toonio.constants import DEFAULT_DELIMITER, DEFAULT_INDENT, Delimiter
from toonio.utils import resolve_delimiter, validate_indent


class BaseEncoder(ABC):
    """Abstract base class for encoding data to TOON format.

    All encoder implementations must inherit from this class
    and provide a concrete ``encode`` method.

    Attributes:
        indent_size: Number of spaces per indentation level.
        delimiter: The Delimiter enum value for tabular output.
    """

    def __init__(
        self,
        indent: int = DEFAULT_INDENT,
        delimiter: str | Delimiter = DEFAULT_DELIMITER,
    ) -> None:
        """Initialize the encoder with formatting options.

        Args:
            indent: Number of spaces per indent level (2 or 4).
            delimiter: Delimiter for tabular data ('comma', 'tab', 'pipe').

        Raises:
            ToonInvalidIndentError: If indent is not 2 or 4.
            ToonInvalidDelimiterError: If delimiter is not recognized.
        """
        self.indent_size: int = validate_indent(indent)
        self.delimiter: Delimiter = resolve_delimiter(delimiter)

    @abstractmethod
    def encode(self, data: Any) -> str:
        """Encode data to TOON format string.

        Args:
            data: The input data to encode.

        Returns:
            A TOON-formatted string.

        Raises:
            ToonEncodeError: If encoding fails.
        """
        ...


class BaseDecoder(ABC):
    """Abstract base class for decoding TOON format strings.

    All decoder implementations must inherit from this class
    and provide a concrete ``decode`` method.

    Attributes:
        delimiter: The Delimiter enum value for parsing tabular data.
    """

    def __init__(
        self,
        delimiter: str | Delimiter = DEFAULT_DELIMITER,
    ) -> None:
        """Initialize the decoder with parsing options.

        Args:
            delimiter: Delimiter used in tabular data ('comma', 'tab', 'pipe').

        Raises:
            ToonInvalidDelimiterError: If delimiter is not recognized.
        """
        self.delimiter: Delimiter = resolve_delimiter(delimiter)

    @abstractmethod
    def decode(self, toon_str: str) -> Any:
        """Decode a TOON format string to structured data.

        Args:
            toon_str: The TOON-formatted string to decode.

        Returns:
            The parsed Python data structure.

        Raises:
            ToonDecodeError: If decoding fails.
        """
        ...

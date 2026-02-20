"""
ToonIO - A Python library to convert JSON and XML to TOON format and vice versa.

TOON is a human-readable data format designed to be simpler and easier to write
than JSON and XML. It combines the structural clarity of both formats while
reducing visual clutter.

Features:
    - JSON ↔ TOON conversion
    - XML ↔ TOON conversion
    - Configurable indentation (2 or 4 spaces)
    - Configurable delimiters (comma, tab, pipe)
    - Class-based architecture with SOLID principles
    - Full type hinting support

Example:
    >>> from toonio import convert
    >>> toon = convert.json_to_toon({"name": "Mohit", "age": 25})
    >>> print(toon)
    name: Mohit
    age: 25

Author: Mohit
License: MIT
"""

from toonio import convert
from toonio.constants import DEFAULT_DELIMITER, DEFAULT_INDENT, Delimiter, IndentSize
from toonio.converters import (
    BaseDecoder,
    BaseEncoder,
    JsonToToonEncoder,
    ToonToJsonDecoder,
    ToonToXmlDecoder,
    XmlToToonEncoder,
)
from toonio.exceptions import (
    ToonDecodeError,
    ToonEncodeError,
    ToonInvalidDelimiterError,
    ToonInvalidIndentError,
    ToonIOError,
)

__version__: str = "0.0.1"
__author__: str = "Mohit"
__email__: str = "mohitdevelopment2001@gmail.com"
__license__: str = "MIT"

__all__: list[str] = [
    # Public API
    "convert",
    # Constants
    "Delimiter",
    "IndentSize",
    "DEFAULT_INDENT",
    "DEFAULT_DELIMITER",
    # Base classes
    "BaseEncoder",
    "BaseDecoder",
    # JSON converters
    "JsonToToonEncoder",
    "ToonToJsonDecoder",
    # XML converters
    "XmlToToonEncoder",
    "ToonToXmlDecoder",
    # Exceptions
    "ToonIOError",
    "ToonEncodeError",
    "ToonDecodeError",
    "ToonInvalidDelimiterError",
    "ToonInvalidIndentError",
]
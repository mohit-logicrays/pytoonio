"""
ToonIO Utilities Module.

Shared utility functions for type detection, string escaping,
indentation management, and delimiter resolution.

Author: Mohit
License: MIT
"""

from typing import Any

from toonio.constants import (
    BARE_DELIMITER_CHARS,
    DELIMITER_ALIASES,
    DELIMITER_CHARS,
    TOON_FALSE,
    TOON_NULL,
    TOON_TRUE,
    VALID_INDENT_SIZES,
    Delimiter,
)
from toonio.exceptions import ToonInvalidDelimiterError, ToonInvalidIndentError


def resolve_delimiter(delimiter: str | Delimiter) -> Delimiter:
    """Resolve a delimiter string or enum to a Delimiter enum value.

    Args:
        delimiter: A string alias ('comma', 'tab', 'pipe', ',', '|', '\\t')
                   or a Delimiter enum value.

    Returns:
        The resolved Delimiter enum value.

    Raises:
        ToonInvalidDelimiterError: If the delimiter is not recognized.
    """
    if isinstance(delimiter, Delimiter):
        return delimiter

    raw: str = str(delimiter)

    # Check raw value first (handles '\t' before stripping removes it)
    resolved: Delimiter | None = DELIMITER_ALIASES.get(raw)
    if resolved is not None:
        return resolved

    # Fallback: strip and lowercase (handles "  COMMA  " etc.)
    normalized: str = raw.strip().lower()
    resolved = DELIMITER_ALIASES.get(normalized)

    if resolved is None:
        raise ToonInvalidDelimiterError(str(delimiter))

    return resolved



def validate_indent(indent: int) -> int:
    """Validate and return the indent size.

    Args:
        indent: The indent size to validate (must be 2 or 4).

    Returns:
        The validated indent size.

    Raises:
        ToonInvalidIndentError: If the indent size is not supported.
    """
    if indent not in VALID_INDENT_SIZES:
        raise ToonInvalidIndentError(indent)
    return indent


def get_delimiter_char(delimiter: Delimiter) -> str:
    """Get the actual character(s) for a given Delimiter enum value.

    Args:
        delimiter: A Delimiter enum value.

    Returns:
        The corresponding delimiter character string (may include spaces).
    """
    return DELIMITER_CHARS[delimiter]


def get_bare_delimiter_char(delimiter: Delimiter) -> str:
    """Get the bare (no surrounding spaces) delimiter character.

    Used in the ``key[N]{headers}:`` list annotation format and data rows.

    Args:
        delimiter: A Delimiter enum value.

    Returns:
        The bare delimiter character string (no padding spaces).
    """
    return BARE_DELIMITER_CHARS[delimiter]


def make_indent(level: int, size: int) -> str:
    """Generate an indentation string for the given nesting level.

    Args:
        level: The current nesting depth (0-based).
        size: The number of spaces per indent level.

    Returns:
        A string of spaces representing the indentation.
    """
    return " " * (level * size)


def is_uniform_object_list(data: list[Any]) -> bool:
    """Check if a list consists entirely of dicts with identical keys.

    This determines whether the list can be rendered in TOON's
    tabular (CSV-like) format.

    Args:
        data: The list to inspect.

    Returns:
        True if all elements are dicts with the same keys, False otherwise.
    """
    if not data or not isinstance(data[0], dict):
        return False

    reference_keys: set[str] = set(data[0].keys())
    return all(
        isinstance(item, dict) and set(item.keys()) == reference_keys
        for item in data
    )


def escape_string(value: str, delimiter_char: str) -> str:
    """Quote a string value if it contains special characters.

    Values are quoted with double quotes if they contain:
    - The delimiter character
    - Double quotes (which are escaped)
    - Newlines or colons

    Args:
        value: The string value to potentially escape.
        delimiter_char: The delimiter character to check against.

    Returns:
        The original or quoted string.
    """
    needs_quoting: bool = any(
        char in value for char in (delimiter_char.strip(), '"', "\n", ":", ",")
    )

    if needs_quoting or not value:
        escaped: str = value.replace('"', '\\"')
        return f'"{escaped}"'

    return value


def unescape_string(value: str) -> str:
    """Remove surrounding quotes and unescape internal quotes.

    Args:
        value: The potentially quoted string to unescape.

    Returns:
        The unescaped string value.
    """
    stripped: str = value.strip()

    if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
        inner: str = stripped[1:-1]
        return inner.replace('\\"', '"')

    return stripped


def detect_type(value_str: str) -> Any:
    """Infer the Python type from a TOON string literal.

    Detects null, booleans, integers, floats, and strings.

    Args:
        value_str: The raw string value from TOON format.

    Returns:
        The parsed Python value (None, bool, int, float, or str).
    """
    stripped: str = value_str.strip()

    if stripped == TOON_NULL:
        return None

    if stripped == TOON_TRUE:
        return True

    if stripped == TOON_FALSE:
        return False

    # Quoted string
    if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
        return unescape_string(stripped)

    # Integer
    try:
        return int(stripped)
    except ValueError:
        pass

    # Float
    try:
        return float(stripped)
    except ValueError:
        pass

    # Unquoted string
    return stripped


def python_to_toon_literal(value: Any, delimiter_char: str) -> str:
    """Convert a Python primitive value to its TOON string representation.

    Args:
        value: The Python value to convert (None, bool, int, float, or str).
        delimiter_char: The delimiter character (for string escaping).

    Returns:
        The TOON string representation of the value.
    """
    if value is None:
        return TOON_NULL

    if isinstance(value, bool):
        return TOON_TRUE if value else TOON_FALSE

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, str):
        return escape_string(value, delimiter_char)

    return escape_string(str(value), delimiter_char)

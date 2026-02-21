"""
ToonIO Public API Facade.

Provides simple module-level functions for converting between
JSON, XML, and TOON formats. This is the recommended entry point
for most users.

Example:
    >>> from toonio import convert
    >>> toon = convert.json_to_toon('{"name": "Mohit"}')
    >>> json_str = convert.toon_to_json(toon)
"""

from typing import Any

from toonio.constants import DEFAULT_DELIMITER, DEFAULT_INDENT, Delimiter
from toonio.converters.json_converter import JsonToToonEncoder, ToonToJsonDecoder
from toonio.converters.xml_converter import ToonToXmlDecoder, XmlToToonEncoder


def json_to_toon(
    json_data: str | dict[str, Any] | list[Any],
    indent: int = DEFAULT_INDENT,
    delimiter: str | Delimiter = DEFAULT_DELIMITER,
) -> str:
    """Convert JSON data to a TOON format string.

    Args:
        json_data: A JSON string, Python dict, or list.
        indent: Number of spaces per indent level (2 or 4). Default: 2.
        delimiter: Delimiter for tabular data ('comma', 'tab', 'pipe').
                   Default: 'comma'.

    Returns:
        A TOON-formatted string.

    Raises:
        ToonEncodeError: If encoding fails.
        ToonInvalidIndentError: If indent is not 2 or 4.
        ToonInvalidDelimiterError: If delimiter is not recognized.

    Example:
        >>> toon = json_to_toon({"name": "Mohit", "age": 25})
        >>> print(toon)
        name: Mohit
        age: 25
    """
    encoder: JsonToToonEncoder = JsonToToonEncoder(indent=indent, delimiter=delimiter)
    return encoder.encode(json_data)


def toon_to_json(
    toon_data: str,
    delimiter: str | Delimiter = DEFAULT_DELIMITER,
    as_string: bool = True,
) -> str | dict[str, Any]:
    """Convert a TOON format string to JSON.

    Args:
        toon_data: The TOON-formatted string to parse.
        delimiter: Delimiter used in tabular data ('comma', 'tab', 'pipe').
                   Default: 'comma'.
        as_string: If True, returns a JSON string. If False, returns a
                   Python dict/list. Default: True.

    Returns:
        A JSON string (if as_string=True) or a Python data structure.

    Raises:
        ToonDecodeError: If decoding fails.
        ToonInvalidDelimiterError: If delimiter is not recognized.

    Example:
        >>> data = toon_to_json("name: Mohit\\nage: 25\\n")
        >>> print(data)
        {"name": "Mohit", "age": 25}
    """
    decoder: ToonToJsonDecoder = ToonToJsonDecoder(delimiter=delimiter)

    if as_string:
        return decoder.decode_to_json(toon_data)

    return decoder.decode(toon_data)


def xml_to_toon(
    xml_data: str,
    indent: int = DEFAULT_INDENT,
    delimiter: str | Delimiter = DEFAULT_DELIMITER,
) -> str:
    """Convert XML data to a TOON format string.

    Args:
        xml_data: An XML string.
        indent: Number of spaces per indent level (2 or 4). Default: 2.
        delimiter: Delimiter for tabular data ('comma', 'tab', 'pipe').
                   Default: 'comma'.

    Returns:
        A TOON-formatted string.

    Raises:
        ToonEncodeError: If the XML is invalid or encoding fails.
        ToonInvalidIndentError: If indent is not 2 or 4.
        ToonInvalidDelimiterError: If delimiter is not recognized.

    Example:
        >>> toon = xml_to_toon("<user><name>Mohit</name></user>")
        >>> print(toon)
        user:
          name: Mohit
    """
    encoder: XmlToToonEncoder = XmlToToonEncoder(indent=indent, delimiter=delimiter)
    return encoder.encode(xml_data)


def toon_to_xml(
    toon_data: str,
    delimiter: str | Delimiter = DEFAULT_DELIMITER,
) -> str:
    """Convert a TOON format string to XML.

    Args:
        toon_data: The TOON-formatted string to parse.
        delimiter: Delimiter used in tabular data ('comma', 'tab', 'pipe').
                   Default: 'comma'.

    Returns:
        An XML string.

    Raises:
        ToonDecodeError: If decoding fails or structure is invalid for XML.
        ToonInvalidDelimiterError: If delimiter is not recognized.

    Example:
        >>> xml = toon_to_xml("user:\\n  name: Mohit\\n")
        >>> print(xml)
        <user><name>Mohit</name></user>
    """
    decoder: ToonToXmlDecoder = ToonToXmlDecoder(delimiter=delimiter)
    return decoder.decode(toon_data)

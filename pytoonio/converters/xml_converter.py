"""
PyToonIO XML Converter Module.

Provides concrete implementations for converting between XML and TOON formats.

- ``XmlToToonEncoder``: Converts an XML string → TOON string.
- ``ToonToXmlDecoder``: Parses a TOON string → XML string.

Uses ``xml.etree.ElementTree`` from the standard library for XML parsing
and generation. Conversion is done via an intermediate Python dict.
"""

import xml.etree.ElementTree as ET
from typing import Any

from pytoonio.constants import DEFAULT_DELIMITER, DEFAULT_INDENT, Delimiter
from pytoonio.converters.base import BaseDecoder, BaseEncoder
from pytoonio.converters.json_converter import JsonToToonEncoder, ToonToJsonDecoder
from pytoonio.exceptions import ToonDecodeError, ToonEncodeError


class XmlToToonEncoder(BaseEncoder):
    """Encoder that converts XML data to TOON format.

    Parses the XML string into an intermediate Python dictionary,
    then delegates to ``JsonToToonEncoder`` for TOON serialization.

    Example:
        >>> encoder = XmlToToonEncoder(indent=2, delimiter="comma")
        >>> xml = "<user><name>Mohit</name><age>25</age></user>"
        >>> print(encoder.encode(xml))
        user:
          name: Mohit
          age: 25
    """

    def __init__(
        self,
        indent: int = DEFAULT_INDENT,
        delimiter: str | Delimiter = DEFAULT_DELIMITER,
    ) -> None:
        """Initialize the XML to TOON encoder.

        Args:
            indent: Number of spaces per indent level (2 or 4).
            delimiter: Delimiter for tabular data ('comma', 'tab', 'pipe').
        """
        super().__init__(indent=indent, delimiter=delimiter)
        self._json_encoder: JsonToToonEncoder = JsonToToonEncoder(
            indent=indent, delimiter=delimiter
        )

    def encode(self, data: Any) -> str:
        """Encode XML data to a TOON format string.

        Args:
            data: An XML string or an ``ElementTree.Element`` object.

        Returns:
            A TOON-formatted string.

        Raises:
            ToonEncodeError: If the XML cannot be parsed or encoded.
        """
        try:
            if isinstance(data, str):
                root: ET.Element = ET.fromstring(data)
            elif isinstance(data, ET.Element):
                root = data
            else:
                raise ToonEncodeError(
                    f"Expected XML string or Element, got {type(data).__name__}"
                )

            intermediate: dict[str, Any] = self._element_to_dict(root)
            return self._json_encoder.encode(intermediate)
        except ET.ParseError as exc:
            raise ToonEncodeError(f"Invalid XML: {exc}") from exc

    def _element_to_dict(self, element: ET.Element) -> dict[str, Any]:
        """Convert an XML element tree to a Python dictionary.

        Handles nested elements, text content, attributes, mixed children,
        and repeated tags (converted to lists).

        Args:
            element: The root XML element to convert.

        Returns:
            A nested dictionary representation of the XML.
        """
        result: dict[str, Any] = {}
        tag: str = element.tag

        children: list[ET.Element] = list(element)

        if not children:
            # Leaf node — text content
            text: str = (element.text or "").strip()
            value: Any = self._infer_value(text)

            if element.attrib:
                inner: dict[str, Any] = {"_text": value}
                inner.update(self._convert_attribs(element.attrib))
                return {tag: inner}

            return {tag: value}

        # Has children
        child_dict: dict[str, Any] = {}

        # Add attributes as prefixed keys
        if element.attrib:
            child_dict.update(self._convert_attribs(element.attrib))

        # Track repeated tags for list conversion
        tag_counts: dict[str, int] = {}
        for child in children:
            tag_counts[child.tag] = tag_counts.get(child.tag, 0) + 1

        for child in children:
            child_data: dict[str, Any] = self._element_to_dict(child)
            child_tag: str = child.tag
            child_value: Any = child_data[child_tag]

            if tag_counts[child_tag] > 1:
                # Repeated tag — build a list
                if child_tag not in child_dict:
                    child_dict[child_tag] = []
                child_dict[child_tag].append(child_value)
            else:
                child_dict[child_tag] = child_value

        return {tag: child_dict}

    def _convert_attribs(self, attribs: dict[str, str]) -> dict[str, Any]:
        """Convert XML attributes to dictionary entries.

        Attributes are prefixed with ``@`` to distinguish them from
        child elements.

        Args:
            attribs: The attribute dictionary from an XML element.

        Returns:
            A dictionary with ``@``-prefixed keys.
        """
        return {f"@{key}": self._infer_value(val) for key, val in attribs.items()}

    def _infer_value(self, text: str) -> Any:
        """Infer the Python type from an XML text value.

        Args:
            text: The raw text content.

        Returns:
            A typed Python value (None, bool, int, float, or str).
        """
        if not text:
            return None

        lower: str = text.lower()
        if lower == "true":
            return True
        if lower == "false":
            return False
        if lower == "null" or lower == "none":
            return None

        try:
            return int(text)
        except ValueError:
            pass

        try:
            return float(text)
        except ValueError:
            pass

        return text


class ToonToXmlDecoder(BaseDecoder):
    """Decoder that parses TOON format strings into XML.

    First decodes TOON to an intermediate Python dictionary using
    ``ToonToJsonDecoder``, then constructs an XML tree from the result.

    Example:
        >>> decoder = ToonToXmlDecoder(delimiter="comma")
        >>> toon = "user:\\n  name: Mohit\\n  age: 25\\n"
        >>> print(decoder.decode(toon))
        <user><name>Mohit</name><age>25</age></user>
    """

    def __init__(
        self,
        delimiter: str | Delimiter = DEFAULT_DELIMITER,
    ) -> None:
        """Initialize the TOON to XML decoder.

        Args:
            delimiter: Delimiter used in tabular data ('comma', 'tab', 'pipe').
        """
        super().__init__(delimiter=delimiter)
        self._toon_decoder: ToonToJsonDecoder = ToonToJsonDecoder(delimiter=delimiter)

    def decode(self, toon_str: str) -> str:
        """Decode a TOON format string to an XML string.

        Args:
            toon_str: The TOON-formatted string to parse.

        Returns:
            An XML string representation.

        Raises:
            ToonDecodeError: If the TOON string cannot be parsed.
        """
        try:
            intermediate: Any = self._toon_decoder.decode(toon_str)

            if not isinstance(intermediate, dict):
                raise ToonDecodeError(
                    "TOON data must represent an object (dict) for XML conversion"
                )

            # Build XML tree
            root: ET.Element = self._dict_to_element(intermediate)
            return ET.tostring(root, encoding="unicode")
        except ToonDecodeError:
            raise
        except Exception as exc:
            raise ToonDecodeError(f"Failed to convert TOON to XML: {exc}") from exc

    def _dict_to_element(self, data: dict[str, Any]) -> ET.Element:
        """Convert a Python dictionary to an XML element tree.

        The dictionary should have exactly one top-level key representing
        the root element tag.

        Args:
            data: The dictionary to convert.

        Returns:
            An ``ElementTree.Element`` representing the XML structure.

        Raises:
            ToonDecodeError: If the dict structure is invalid for XML.
        """
        if len(data) != 1:
            # Wrap in a root element if multiple top-level keys
            root: ET.Element = ET.Element("root")
            self._build_children(root, data)
            return root

        tag: str = next(iter(data))
        value: Any = data[tag]

        root = ET.Element(tag)
        self._set_element_value(root, value)
        return root

    def _set_element_value(self, element: ET.Element, value: Any) -> None:
        """Set the value/children of an XML element from a Python value.

        Args:
            element: The XML element to populate.
            value: The Python value (primitive, dict, or list).
        """
        if value is None:
            element.text = ""
        elif isinstance(value, bool):
            element.text = "true" if value else "false"
        elif isinstance(value, (int, float)):
            element.text = str(value)
        elif isinstance(value, str):
            element.text = value
        elif isinstance(value, dict):
            self._build_children(element, value)
        elif isinstance(value, list):
            self._build_list_children(element, value)

    def _build_children(self, parent: ET.Element, data: dict[str, Any]) -> None:
        """Build child XML elements from a dictionary.

        Keys prefixed with ``@`` are treated as XML attributes.
        The key ``_text`` sets the element's text content.

        Args:
            parent: The parent XML element.
            data: The dictionary of children to add.
        """
        for key, value in data.items():
            if key.startswith("@"):
                # XML attribute
                attr_name: str = key[1:]
                parent.set(attr_name, str(value) if value is not None else "")
            elif key == "_text":
                parent.text = str(value) if value is not None else ""
            elif isinstance(value, list):
                # Repeated elements
                for item in value:
                    child: ET.Element = ET.SubElement(parent, key)
                    self._set_element_value(child, item)
            else:
                child = ET.SubElement(parent, key)
                self._set_element_value(child, value)

    def _build_list_children(
        self, parent: ET.Element, items: list[Any]
    ) -> None:
        """Build child XML elements from a list.

        Each list item becomes an ``<item>`` child element.

        Args:
            parent: The parent XML element.
            items: The list of values to add as children.
        """
        for item in items:
            child: ET.Element = ET.SubElement(parent, "item")
            self._set_element_value(child, item)

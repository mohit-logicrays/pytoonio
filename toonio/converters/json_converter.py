"""
ToonIO JSON Converter Module.

Provides concrete implementations for converting between JSON and TOON formats.

- ``JsonToToonEncoder``: Converts a JSON string (or Python dict) → TOON string.
- ``ToonToJsonDecoder``: Parses a TOON string → JSON string (or Python dict).

Author: Mohit
License: MIT
"""

import json
from typing import Any

from toonio.constants import DEFAULT_DELIMITER, DEFAULT_INDENT, Delimiter
from toonio.converters.base import BaseDecoder, BaseEncoder
from toonio.exceptions import ToonDecodeError, ToonEncodeError
from toonio.utils import (
    detect_type,
    get_delimiter_char,
    is_uniform_object_list,
    make_indent,
    python_to_toon_literal,
)


class JsonToToonEncoder(BaseEncoder):
    """Encoder that converts JSON data to TOON format.

    Supports nested objects, primitive lists (inline), and uniform
    object lists (tabular CSV-like format).

    Example:
        >>> encoder = JsonToToonEncoder(indent=2, delimiter="comma")
        >>> print(encoder.encode({"name": "Mohit", "age": 25}))
        name: Mohit
        age: 25
    """

    def __init__(
        self,
        indent: int = DEFAULT_INDENT,
        delimiter: str | Delimiter = DEFAULT_DELIMITER,
    ) -> None:
        """Initialize the JSON to TOON encoder.

        Args:
            indent: Number of spaces per indent level (2 or 4).
            delimiter: Delimiter for tabular data ('comma', 'tab', 'pipe').
        """
        super().__init__(indent=indent, delimiter=delimiter)
        self._delimiter_char: str = get_delimiter_char(self.delimiter)

    def encode(self, data: Any) -> str:
        """Encode JSON data to a TOON format string.

        Args:
            data: A JSON string, Python dict, list, or primitive value.

        Returns:
            A TOON-formatted string.

        Raises:
            ToonEncodeError: If the data cannot be encoded.
        """
        try:
            # Parse JSON string if needed
            if isinstance(data, str):
                data = json.loads(data)

            lines: list[str] = []
            self._encode_value(data, level=0, lines=lines)
            return "\n".join(lines) + "\n"
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ToonEncodeError(f"Failed to encode to TOON: {exc}") from exc

    def _encode_value(self, value: Any, level: int, lines: list[str]) -> None:
        """Recursively encode a Python value into TOON lines.

        Args:
            value: The Python value to encode.
            level: Current nesting level for indentation.
            lines: Accumulator list for output lines.
        """
        if isinstance(value, dict):
            self._encode_dict(value, level, lines)
        elif isinstance(value, list):
            self._encode_list(value, level, lines)
        else:
            # Primitive at top-level — just convert to literal
            lines.append(python_to_toon_literal(value, self._delimiter_char))

    def _encode_dict(self, data: dict[str, Any], level: int, lines: list[str]) -> None:
        """Encode a dictionary to TOON key-value pairs.

        Args:
            data: The dictionary to encode.
            level: Current nesting level.
            lines: Accumulator list for output lines.
        """
        indent: str = make_indent(level, self.indent_size)

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent}{key}:")
                self._encode_dict(value, level + 1, lines)
            elif isinstance(value, list):
                lines.append(f"{indent}{key}:")
                self._encode_list(value, level + 1, lines)
            else:
                literal: str = python_to_toon_literal(value, self._delimiter_char)
                lines.append(f"{indent}{key}: {literal}")

    def _encode_list(self, data: list[Any], level: int, lines: list[str]) -> None:
        """Encode a list to TOON format.

        Uniform object lists are rendered as tables; primitive lists
        are rendered inline.

        Args:
            data: The list to encode.
            level: Current nesting level.
            lines: Accumulator list for output lines.
        """
        indent: str = make_indent(level, self.indent_size)

        if not data:
            lines.append(f"{indent}[]")
            return

        # Uniform object list → tabular format
        if is_uniform_object_list(data):
            self._encode_table(data, level, lines)
            return

        # Check if all items are primitives
        if all(not isinstance(item, (dict, list)) for item in data):
            # Inline primitive list
            items: list[str] = [
                python_to_toon_literal(item, self._delimiter_char) for item in data
            ]
            joined: str = self._delimiter_char.join(items)
            lines.append(f"{indent}[{joined}]")
            return

        # Mixed or nested list → dash notation
        for item in data:
            if isinstance(item, dict):
                lines.append(f"{indent}-")
                self._encode_dict(item, level + 1, lines)
            elif isinstance(item, list):
                lines.append(f"{indent}-")
                self._encode_list(item, level + 1, lines)
            else:
                literal = python_to_toon_literal(item, self._delimiter_char)
                lines.append(f"{indent}- {literal}")

    def _encode_table(
        self, data: list[dict[str, Any]], level: int, lines: list[str]
    ) -> None:
        """Encode a uniform object list as a TOON table.

        Args:
            data: The list of dicts with identical keys.
            level: Current nesting level.
            lines: Accumulator list for output lines.
        """
        indent: str = make_indent(level, self.indent_size)
        headers: list[str] = list(data[0].keys())

        # Header row
        lines.append(f"{indent}{self._delimiter_char.join(headers)}")

        # Data rows
        for row in data:
            values: list[str] = [
                python_to_toon_literal(row[key], self._delimiter_char)
                for key in headers
            ]
            lines.append(f"{indent}{self._delimiter_char.join(values)}")


class ToonToJsonDecoder(BaseDecoder):
    """Decoder that parses TOON format strings into Python data structures.

    Handles indentation-based nesting, inline lists, and tabular data.

    Example:
        >>> decoder = ToonToJsonDecoder(delimiter="comma")
        >>> result = decoder.decode("name: Mohit\\nage: 25\\n")
        >>> print(result)  # {'name': 'Mohit', 'age': 25}
    """

    def __init__(
        self,
        delimiter: str | Delimiter = DEFAULT_DELIMITER,
    ) -> None:
        """Initialize the TOON to JSON decoder.

        Args:
            delimiter: Delimiter used in tabular data ('comma', 'tab', 'pipe').
        """
        super().__init__(delimiter=delimiter)
        self._delimiter_char: str = get_delimiter_char(self.delimiter)

    def decode(self, toon_str: str) -> Any:
        """Decode a TOON format string to a Python data structure.

        Args:
            toon_str: The TOON-formatted string to parse.

        Returns:
            A Python dict, list, or primitive value.

        Raises:
            ToonDecodeError: If the TOON string cannot be parsed.
        """
        try:
            lines: list[str] = toon_str.splitlines()
            result, _ = self._parse_block(lines, start=0, base_indent=0)
            return result
        except Exception as exc:
            if isinstance(exc, ToonDecodeError):
                raise
            raise ToonDecodeError(f"Failed to decode TOON: {exc}") from exc

    def decode_to_json(self, toon_str: str) -> str:
        """Decode a TOON string and return a JSON-formatted string.

        Args:
            toon_str: The TOON-formatted string to parse.

        Returns:
            A pretty-printed JSON string.

        Raises:
            ToonDecodeError: If the TOON string cannot be parsed.
        """
        data: Any = self.decode(toon_str)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _get_indent_level(self, line: str) -> int:
        """Calculate the indentation level of a line.

        Args:
            line: The input line.

        Returns:
            The number of leading spaces.
        """
        return len(line) - len(line.lstrip())

    def _parse_block(
        self, lines: list[str], start: int, base_indent: int
    ) -> tuple[Any, int]:
        """Parse a block of TOON lines starting at a given position.

        This is the core recursive parser. It detects whether the block
        represents an object (key-value pairs), a table, or a list.

        Args:
            lines: All lines of the TOON input.
            start: The line index to start parsing from.
            base_indent: The expected indentation for this block.

        Returns:
            A tuple of (parsed_value, next_line_index).
        """
        if start >= len(lines):
            return {}, start

        result: dict[str, Any] = {}
        idx: int = start

        while idx < len(lines):
            line: str = lines[idx]

            # Skip empty lines
            if not line.strip():
                idx += 1
                continue

            current_indent: int = self._get_indent_level(line)

            # End of block — back to parent level
            if current_indent < base_indent:
                break

            stripped: str = line.strip()

            # Dash list items
            if stripped.startswith("- ") or stripped == "-":
                list_result, idx = self._parse_list(lines, idx, current_indent)
                return list_result, idx

            # Inline list at top level
            if stripped.startswith("[") and stripped.endswith("]"):
                return self._parse_inline_list(stripped), idx + 1

            # Key-value line
            if ":" in stripped:
                colon_pos: int = stripped.index(":")
                key: str = stripped[:colon_pos].strip()
                value_part: str = stripped[colon_pos + 1 :].strip()

                if value_part:
                    # Inline value
                    if value_part.startswith("[") and value_part.endswith("]"):
                        result[key] = self._parse_inline_list(value_part)
                    else:
                        result[key] = detect_type(value_part)
                    idx += 1
                else:
                    # Block value — look ahead
                    child_indent: int = base_indent + self._detect_indent_size(
                        lines, idx + 1
                    )
                    if idx + 1 < len(lines):
                        next_stripped: str = lines[idx + 1].strip()
                        # Check if the next block is a table
                        if self._is_table_header(lines, idx + 1, child_indent):
                            table, idx = self._parse_table(
                                lines, idx + 1, child_indent
                            )
                            result[key] = table
                        elif next_stripped.startswith("- ") or next_stripped == "-":
                            list_val, idx = self._parse_list(
                                lines, idx + 1, child_indent
                            )
                            result[key] = list_val
                        else:
                            child, idx = self._parse_block(
                                lines, idx + 1, child_indent
                            )
                            result[key] = child
                    else:
                        result[key] = None
                        idx += 1
            else:
                # Could be a table header row at this level
                if self._is_table_header(lines, idx, current_indent):
                    table, idx = self._parse_table(lines, idx, current_indent)
                    return table, idx
                else:
                    idx += 1

        return result, idx

    def _parse_list(
        self, lines: list[str], start: int, base_indent: int
    ) -> tuple[list[Any], int]:
        """Parse a dash-notation list from TOON lines.

        Args:
            lines: All lines of the TOON input.
            start: The line index to start parsing from.
            base_indent: The expected indentation for list items.

        Returns:
            A tuple of (parsed_list, next_line_index).
        """
        result: list[Any] = []
        idx: int = start

        while idx < len(lines):
            line: str = lines[idx]

            if not line.strip():
                idx += 1
                continue

            current_indent: int = self._get_indent_level(line)

            if current_indent < base_indent:
                break

            stripped: str = line.strip()

            if stripped.startswith("- "):
                value_str: str = stripped[2:].strip()
                if value_str:
                    result.append(detect_type(value_str))
                else:
                    # Nested block under dash
                    child_indent: int = current_indent + self._detect_indent_size(
                        lines, idx + 1
                    )
                    child, idx = self._parse_block(lines, idx + 1, child_indent)
                    result.append(child)
                    continue
                idx += 1
            elif stripped == "-":
                child_indent = current_indent + self._detect_indent_size(
                    lines, idx + 1
                )
                child, idx = self._parse_block(lines, idx + 1, child_indent)
                result.append(child)
            elif current_indent > base_indent:
                idx += 1
            else:
                break

        return result, idx

    def _parse_inline_list(self, value: str) -> list[Any]:
        """Parse an inline list like ``[1, 2, "hello"]``.

        Args:
            value: The inline list string including brackets.

        Returns:
            A list of parsed Python values.
        """
        inner: str = value[1:-1].strip()
        if not inner:
            return []

        items: list[str] = self._split_respecting_quotes(inner)
        return [detect_type(item.strip()) for item in items]

    def _split_respecting_quotes(self, text: str) -> list[str]:
        """Split text by the delimiter while respecting quoted strings.

        Args:
            text: The text to split.

        Returns:
            A list of split segments.
        """
        parts: list[str] = []
        current: list[str] = []
        in_quotes: bool = False
        i: int = 0

        # Determine actual split character
        delim: str = self._delimiter_char.strip()
        if not delim:
            delim = ","  # Fallback for tab delimiter in inline lists

        while i < len(text):
            char: str = text[i]

            if char == '"' and (i == 0 or text[i - 1] != "\\"):
                in_quotes = not in_quotes
                current.append(char)
            elif char == delim and not in_quotes:
                parts.append("".join(current))
                current = []
            else:
                current.append(char)

            i += 1

        if current:
            parts.append("".join(current))

        return parts

    def _parse_table(
        self, lines: list[str], start: int, base_indent: int
    ) -> tuple[list[dict[str, Any]], int]:
        """Parse a tabular block (header row + data rows) into a list of dicts.

        Args:
            lines: All lines of the TOON input.
            start: The line index of the header row.
            base_indent: The expected indentation for table rows.

        Returns:
            A tuple of (list_of_dicts, next_line_index).
        """
        result: list[dict[str, Any]] = []

        # Parse header
        header_line: str = lines[start].strip()
        headers: list[str] = [
            h.strip() for h in self._split_respecting_quotes(header_line)
        ]

        idx: int = start + 1

        while idx < len(lines):
            line: str = lines[idx]

            if not line.strip():
                idx += 1
                continue

            current_indent: int = self._get_indent_level(line)

            if current_indent < base_indent:
                break

            stripped: str = line.strip()
            values: list[str] = [
                v.strip() for v in self._split_respecting_quotes(stripped)
            ]

            if len(values) == len(headers):
                row: dict[str, Any] = {}
                for header, val in zip(headers, values):
                    row[header] = detect_type(val)
                result.append(row)
                idx += 1
            else:
                break

        return result, idx

    def _is_table_header(
        self, lines: list[str], idx: int, expected_indent: int
    ) -> bool:
        """Determine if a line is likely a table header row.

        A table header is detected when:
        - The line has no colon before a potential delimiter split
        - The next line exists at the same indent with the same number of delimited fields
        - Neither line starts with a dash

        Args:
            lines: All lines of the TOON input.
            idx: The index of the candidate header line.
            expected_indent: The expected indentation level.

        Returns:
            True if the line looks like a table header.
        """
        if idx >= len(lines) or idx + 1 >= len(lines):
            return False

        line: str = lines[idx].strip()
        next_line: str = lines[idx + 1].strip()

        # Must not be dash items or key-value lines
        if line.startswith("-") or next_line.startswith("-"):
            return False

        # Check both lines have delimiters
        delim: str = self._delimiter_char.strip()
        if not delim:
            delim = ","

        if delim not in line or delim not in next_line:
            return False

        # Should have the same number of fields
        header_count: int = len(self._split_respecting_quotes(line))
        data_count: int = len(self._split_respecting_quotes(next_line))

        if header_count != data_count or header_count < 2:
            return False

        # Header fields should look like identifiers (no complex values)
        headers: list[str] = [h.strip() for h in self._split_respecting_quotes(line)]
        return all(
            h.isidentifier() or (h.startswith('"') and h.endswith('"'))
            for h in headers
        )

    def _detect_indent_size(self, lines: list[str], from_idx: int) -> int:
        """Detect the indent size by looking at the next non-empty line.

        Args:
            lines: All lines.
            from_idx: Index to start looking from.

        Returns:
            The detected indent difference, defaulting to 2.
        """
        if from_idx >= len(lines):
            return 2

        for i in range(from_idx, min(from_idx + 5, len(lines))):
            if lines[i].strip():
                indent: int = self._get_indent_level(lines[i])
                if indent > 0:
                    return indent - (
                        self._get_indent_level(lines[from_idx - 1])
                        if from_idx > 0
                        else 0
                    )

        return 2

"""
ToonIO JSON Converter Module.

Provides concrete implementations for converting between JSON and TOON formats.

TOON List Format Rules
----------------------
- **Uniform object list** (all dicts share identical keys):
  ``key[N]{col1,col2,...}:`` followed by bare-delimiter data rows.

  Example::

      users[3]{id,name,role}:
        1,Alice,admin
        2,Bob,user
        3,Charlie,user

- **Non-uniform / mixed list** (dicts with different keys, or mixed types):
  ``key[N]:`` followed by ``-`` separated blocks.

  Example::

      users[2]:
        -
          id: 1
          name: Alice
        -
          name: Charlie
          role: user

- **Primitive list** (all items are non-dict scalars):
  Inline bracket notation: ``[val1, val2, val3]``

Author: Mohit
License: MIT
"""

import json
import re
from typing import Any

from toonio.constants import DEFAULT_DELIMITER, DEFAULT_INDENT, Delimiter
from toonio.converters.base import BaseDecoder, BaseEncoder
from toonio.exceptions import ToonDecodeError, ToonEncodeError
from toonio.utils import (
    detect_type,
    get_bare_delimiter_char,
    get_delimiter_char,
    is_uniform_object_list,
    make_indent,
    python_to_toon_literal,
)

# ── Decoder regexes ───────────────────────────────────────────────────────────
# Matches:  users[3]{id,name,email}:
_UNIFORM_TABLE_RE = re.compile(r"^([^\[\]]+)\[(\d+)\]\{([^}]*)\}:\s*$")
# Matches:  users[2]:
_NONUNIFORM_LIST_RE = re.compile(r"^([^\[\]]+)\[(\d+)\]:\s*$")


# ─────────────────────────────────────────────────────────────────────────────
# Encoder
# ─────────────────────────────────────────────────────────────────────────────


class JsonToToonEncoder(BaseEncoder):
    """Encoder that converts JSON data to TOON format.

    Supports nested objects, primitive lists (inline), and list-of-dicts
    using the annotated ``key[N]{headers}:`` or ``key[N]:`` formats.

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
            delimiter: Delimiter for list annotations ('comma', 'tab', 'pipe').
        """
        super().__init__(indent=indent, delimiter=delimiter)
        self._delimiter_char: str = get_delimiter_char(self.delimiter)
        self._bare_delimiter_char: str = get_bare_delimiter_char(self.delimiter)

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
            if isinstance(data, str):
                data = json.loads(data)
            lines: list[str] = []
            self._encode_value(data, level=0, lines=lines)
            return "\n".join(lines) + "\n"
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ToonEncodeError(f"Failed to encode to TOON: {exc}") from exc

    # ── Private helpers ───────────────────────────────────────────────────────

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
            self._encode_list_standalone(value, level, lines)
        else:
            lines.append(python_to_toon_literal(value, self._delimiter_char))

    def _encode_dict(self, data: dict[str, Any], level: int, lines: list[str]) -> None:
        """Encode a dictionary to TOON key-value pairs.

        List values under a key use the new annotated format:
        - Uniform   → ``key[N]{h1,h2,...}:``
        - Otherwise → ``key[N]:`` with ``-`` blocks

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
                if not value:
                    lines.append(f"{indent}{key}: []")
                elif all(not isinstance(item, (dict, list)) for item in value):
                    # Primitive list — inline
                    items = [
                        python_to_toon_literal(item, self._delimiter_char)
                        for item in value
                    ]
                    joined = self._delimiter_char.join(items)
                    lines.append(f"{indent}{key}: [{joined}]")
                elif is_uniform_object_list(value):
                    self._encode_uniform_table_key(key, value, level, lines)
                else:
                    self._encode_nonuniform_list_key(key, value, level, lines)

            else:
                literal = python_to_toon_literal(value, self._delimiter_char)
                lines.append(f"{indent}{key}: {literal}")

    def _encode_uniform_table_key(
        self,
        key: str,
        data: list[dict[str, Any]],
        level: int,
        lines: list[str],
    ) -> None:
        """Encode a uniform object list using the annotated table format.

        Produces::

            key[N]{col1,col2,...}:
              val1,val2,...
              val1,val2,...

        Args:
            key: The parent dict key name.
            data: The list of dicts with identical keys.
            level: Current nesting level.
            lines: Accumulator list for output lines.
        """
        indent: str = make_indent(level, self.indent_size)
        child_indent: str = make_indent(level + 1, self.indent_size)
        bare: str = self._bare_delimiter_char
        headers: list[str] = list(data[0].keys())
        header_str: str = bare.join(headers)

        lines.append(f"{indent}{key}[{len(data)}]{{{header_str}}}:")

        for row in data:
            values: list[str] = [
                python_to_toon_literal(row[h], bare) for h in headers
            ]
            lines.append(f"{child_indent}{bare.join(values)}")

    def _encode_nonuniform_list_key(
        self,
        key: str,
        data: list[Any],
        level: int,
        lines: list[str],
    ) -> None:
        """Encode a non-uniform list using the annotated dash-block format.

        Produces::

            key[N]:
              -
                k1: v1
                k2: v2
              -
                ...

        Args:
            key: The parent dict key name.
            data: The list (non-uniform dicts or mixed types).
            level: Current nesting level.
            lines: Accumulator list for output lines.
        """
        indent: str = make_indent(level, self.indent_size)
        child_indent: str = make_indent(level + 1, self.indent_size)

        lines.append(f"{indent}{key}[{len(data)}]:")

        for item in data:
            lines.append(f"{child_indent}-")
            if isinstance(item, dict):
                self._encode_dict(item, level + 2, lines)
            elif isinstance(item, list):
                self._encode_list_standalone(item, level + 2, lines)
            else:
                literal = python_to_toon_literal(item, self._delimiter_char)
                lines.append(f"{make_indent(level + 2, self.indent_size)}{literal}")

    def _encode_list_standalone(
        self, data: list[Any], level: int, lines: list[str]
    ) -> None:
        """Encode a standalone list (not under a named dict key).

        Used for top-level lists or lists nested inside other lists.
        Primitives are rendered inline; object lists use dash blocks.

        Args:
            data: The list to encode.
            level: Current nesting level.
            lines: Accumulator list for output lines.
        """
        indent: str = make_indent(level, self.indent_size)

        if not data:
            lines.append(f"{indent}[]")
            return

        # All primitives → inline
        if all(not isinstance(item, (dict, list)) for item in data):
            items = [python_to_toon_literal(item, self._delimiter_char) for item in data]
            joined = self._delimiter_char.join(items)
            lines.append(f"{indent}[{joined}]")
            return

        # Object / mixed list → dash blocks
        for item in data:
            if isinstance(item, dict):
                lines.append(f"{indent}-")
                self._encode_dict(item, level + 1, lines)
            elif isinstance(item, list):
                lines.append(f"{indent}-")
                self._encode_list_standalone(item, level + 1, lines)
            else:
                literal = python_to_toon_literal(item, self._delimiter_char)
                lines.append(f"{indent}- {literal}")


# ─────────────────────────────────────────────────────────────────────────────
# Decoder
# ─────────────────────────────────────────────────────────────────────────────


class ToonToJsonDecoder(BaseDecoder):
    """Decoder that parses TOON format strings into Python data structures.

    Handles:
    - ``key[N]{h1,h2}:`` → uniform object list
    - ``key[N]:``         → non-uniform list (dash blocks)
    - ``key: value``      → primitive key-value
    - ``key:``            → nested dict block
    - ``[v1, v2]``        → inline primitive list

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
            delimiter: Delimiter used in list annotations ('comma', 'tab', 'pipe').
        """
        super().__init__(delimiter=delimiter)
        self._delimiter_char: str = get_delimiter_char(self.delimiter)
        self._bare_delimiter_char: str = get_bare_delimiter_char(self.delimiter)

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

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_indent_level(self, line: str) -> int:
        """Return the number of leading spaces in a line."""
        return len(line) - len(line.lstrip())

    def _find_child_indent(self, lines: list[str], from_idx: int) -> int:
        """Return the indent level of the next non-empty line from from_idx."""
        for i in range(from_idx, min(from_idx + 10, len(lines))):
            if lines[i].strip():
                return self._get_indent_level(lines[i])
        return 0

    def _parse_block(
        self, lines: list[str], start: int, base_indent: int
    ) -> tuple[Any, int]:
        """Parse a block of TOON lines starting at ``start``.

        Recognises:
        - ``key[N]{headers}:`` → uniform annotated table
        - ``key[N]:``          → non-uniform annotated list
        - ``key: value``       → inline primitive
        - ``key:``             → nested object block
        - ``-`` / ``- value``  → list items (bare, no key)
        - ``[...]``            → inline primitive list

        Args:
            lines: All lines of the TOON input.
            start: Line index to start parsing from.
            base_indent: Expected indentation for this block.

        Returns:
            A tuple of (parsed_value, next_line_index).
        """
        if start >= len(lines):
            return {}, start

        result: dict[str, Any] = {}
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

            # ── Dash list items (bare, no key context) ────────────────────
            if stripped.startswith("- ") or stripped == "-":
                list_result, idx = self._parse_dash_list(lines, idx, current_indent)
                return list_result, idx

            # ── Inline list at top level ──────────────────────────────────
            if stripped.startswith("[") and stripped.endswith("]"):
                return self._parse_inline_list(stripped), idx + 1

            # ── Annotated uniform table: key[N]{h1,h2,...}: ───────────────
            m = _UNIFORM_TABLE_RE.match(stripped)
            if m:
                key: str = m.group(1).strip()
                headers: list[str] = [
                    h.strip()
                    for h in self._split_bare(m.group(3))
                ]
                child_indent: int = self._find_child_indent(lines, idx + 1)
                table, idx = self._parse_annotated_table(
                    lines, idx + 1, child_indent, headers
                )
                result[key] = table
                continue

            # ── Annotated non-uniform list: key[N]: ───────────────────────
            m2 = _NONUNIFORM_LIST_RE.match(stripped)
            if m2:
                key = m2.group(1).strip()
                child_indent = self._find_child_indent(lines, idx + 1)
                lst, idx = self._parse_annotated_nonuniform_list(
                    lines, idx + 1, child_indent
                )
                result[key] = lst
                continue

            # ── Key-value or key: block ───────────────────────────────────
            if ":" in stripped:
                colon_pos: int = stripped.index(":")
                key = stripped[:colon_pos].strip()
                value_part: str = stripped[colon_pos + 1 :].strip()

                if value_part:
                    if value_part.startswith("[") and value_part.endswith("]"):
                        result[key] = self._parse_inline_list(value_part)
                    else:
                        result[key] = detect_type(value_part)
                    idx += 1
                else:
                    # Nested block
                    child_indent = self._find_child_indent(lines, idx + 1)
                    if child_indent > current_indent:
                        next_stripped = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
                        if next_stripped == "-" or next_stripped.startswith("- "):
                            child_val, idx = self._parse_dash_list(
                                lines, idx + 1, child_indent
                            )
                            result[key] = child_val
                        else:
                            child, idx = self._parse_block(
                                lines, idx + 1, child_indent
                            )
                            result[key] = child
                    else:
                        result[key] = None
                        idx += 1
            else:
                idx += 1

        return result, idx

    def _parse_annotated_table(
        self,
        lines: list[str],
        start: int,
        base_indent: int,
        headers: list[str],
    ) -> tuple[list[dict[str, Any]], int]:
        """Parse data rows of an annotated uniform table.

        Args:
            lines: All TOON lines.
            start: Line index of the first data row.
            base_indent: Expected indentation of data rows.
            headers: Column names from the header annotation.

        Returns:
            Tuple of (list of row dicts, next_line_index).
        """
        result: list[dict[str, Any]] = []
        idx: int = start

        while idx < len(lines):
            line: str = lines[idx]
            if not line.strip():
                idx += 1
                continue

            current_indent: int = self._get_indent_level(line)
            if current_indent < base_indent:
                break

            parts: list[str] = self._split_bare(line.strip())
            if len(parts) == len(headers):
                row: dict[str, Any] = {
                    h: detect_type(v.strip()) for h, v in zip(headers, parts)
                }
                result.append(row)
            idx += 1

        return result, idx

    def _parse_annotated_nonuniform_list(
        self,
        lines: list[str],
        start: int,
        base_indent: int,
    ) -> tuple[list[Any], int]:
        """Parse dash-block items of an annotated non-uniform list.

        Args:
            lines: All TOON lines.
            start: Line index of the first ``-`` marker.
            base_indent: Expected indentation of ``-`` markers.

        Returns:
            Tuple of (list of items, next_line_index).
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

            if stripped == "-":
                item_indent: int = self._find_child_indent(lines, idx + 1)
                if item_indent > current_indent:
                    item, idx = self._parse_block(lines, idx + 1, item_indent)
                    result.append(item)
                else:
                    result.append(None)
                    idx += 1
            elif stripped.startswith("- "):
                result.append(detect_type(stripped[2:].strip()))
                idx += 1
            else:
                idx += 1

        return result, idx

    def _parse_dash_list(
        self, lines: list[str], start: int, base_indent: int
    ) -> tuple[list[Any], int]:
        """Parse a series of ``-`` prefixed items from TOON lines.

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
                result.append(detect_type(stripped[2:].strip()))
                idx += 1
            elif stripped == "-":
                child_indent: int = self._find_child_indent(lines, idx + 1)
                if child_indent > current_indent:
                    child, idx = self._parse_block(lines, idx + 1, child_indent)
                    result.append(child)
                else:
                    result.append(None)
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
        """Split text by the full delimiter char while respecting quoted strings.

        Args:
            text: The text to split.

        Returns:
            A list of split segments.
        """
        parts: list[str] = []
        current: list[str] = []
        in_quotes: bool = False
        delim: str = self._delimiter_char.strip() or ","

        for i, char in enumerate(text):
            if char == '"' and (i == 0 or text[i - 1] != "\\"):
                in_quotes = not in_quotes
                current.append(char)
            elif char == delim and not in_quotes:
                parts.append("".join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append("".join(current))

        return parts

    def _split_bare(self, text: str) -> list[str]:
        """Split text by the bare delimiter while respecting quoted strings.

        Used for parsing table rows and header annotations.

        Args:
            text: The text to split.

        Returns:
            A list of split segments.
        """
        bare: str = self._bare_delimiter_char
        parts: list[str] = []
        current: list[str] = []
        in_quotes: bool = False
        i: int = 0

        while i < len(text):
            char: str = text[i]
            if char == '"' and (i == 0 or text[i - 1] != "\\"):
                in_quotes = not in_quotes
                current.append(char)
            elif not in_quotes and text[i : i + len(bare)] == bare:
                parts.append("".join(current))
                current = []
                i += len(bare)
                continue
            else:
                current.append(char)
            i += 1

        if current:
            parts.append("".join(current))

        return parts

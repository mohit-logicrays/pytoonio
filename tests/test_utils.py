"""
Tests for utility functions and custom exceptions.

Covers:
- resolve_delimiter()
- validate_indent()
- get_delimiter_char()
- make_indent()
- is_uniform_object_list()
- escape_string() / unescape_string()
- detect_type()
- python_to_toon_literal()
- All custom exception classes

Author: Mohit
License: MIT
"""

from __future__ import annotations

import pytest

from toonio.constants import Delimiter
from toonio.exceptions import (
    ToonDecodeError,
    ToonEncodeError,
    ToonInvalidDelimiterError,
    ToonInvalidIndentError,
    ToonIOError,
)
from toonio.utils import (
    detect_type,
    escape_string,
    get_delimiter_char,
    is_uniform_object_list,
    make_indent,
    python_to_toon_literal,
    resolve_delimiter,
    unescape_string,
    validate_indent,
)


class TestResolveDelimiter:
    """Tests for resolve_delimiter()."""

    @pytest.mark.parametrize(
        "alias, expected",
        [
            ("comma", Delimiter.COMMA),
            (",", Delimiter.COMMA),
            ("tab", Delimiter.TAB),
            ("\t", Delimiter.TAB),
            ("pipe", Delimiter.PIPE),
            ("|", Delimiter.PIPE),
        ],
    )
    def test_valid_aliases(self, alias: str, expected: Delimiter) -> None:
        """All valid string aliases resolve to the correct Delimiter."""
        assert resolve_delimiter(alias) == expected

    def test_enum_passthrough(self) -> None:
        """Delimiter enum values pass through unchanged."""
        assert resolve_delimiter(Delimiter.COMMA) == Delimiter.COMMA
        assert resolve_delimiter(Delimiter.TAB) == Delimiter.TAB
        assert resolve_delimiter(Delimiter.PIPE) == Delimiter.PIPE

    def test_invalid_alias_raises(self) -> None:
        """Invalid delimiter string raises ToonInvalidDelimiterError."""
        with pytest.raises(ToonInvalidDelimiterError) as exc_info:
            resolve_delimiter("semicolon")
        assert "semicolon" in exc_info.value.message

    def test_case_insensitive(self) -> None:
        """Delimiter aliases are case-insensitive."""
        assert resolve_delimiter("COMMA") == Delimiter.COMMA
        assert resolve_delimiter("Pipe") == Delimiter.PIPE


class TestValidateIndent:
    """Tests for validate_indent()."""

    @pytest.mark.parametrize("size", [2, 4])
    def test_valid_sizes(self, size: int) -> None:
        """Valid indent sizes (2, 4) pass through unchanged."""
        assert validate_indent(size) == size

    @pytest.mark.parametrize("size", [0, 1, 3, 5, 8])
    def test_invalid_sizes_raise(self, size: int) -> None:
        """Invalid indent sizes raise ToonInvalidIndentError."""
        with pytest.raises(ToonInvalidIndentError) as exc_info:
            validate_indent(size)
        assert str(size) in exc_info.value.message


class TestGetDelimiterChar:
    """Tests for get_delimiter_char()."""

    def test_comma_char(self) -> None:
        """COMMA delimiter returns ', '."""
        assert get_delimiter_char(Delimiter.COMMA) == ", "

    def test_tab_char(self) -> None:
        """TAB delimiter returns tab character."""
        assert get_delimiter_char(Delimiter.TAB) == "\t"

    def test_pipe_char(self) -> None:
        """PIPE delimiter returns ' | '."""
        assert get_delimiter_char(Delimiter.PIPE) == " | "


class TestMakeIndent:
    """Tests for make_indent()."""

    def test_level_0_returns_empty(self) -> None:
        """Level 0 returns an empty string."""
        assert make_indent(0, 2) == ""
        assert make_indent(0, 4) == ""

    def test_level_1_size_2(self) -> None:
        """Level 1, size 2 returns 2 spaces."""
        assert make_indent(1, 2) == "  "

    def test_level_1_size_4(self) -> None:
        """Level 1, size 4 returns 4 spaces."""
        assert make_indent(1, 4) == "    "

    def test_level_3_size_2(self) -> None:
        """Level 3, size 2 returns 6 spaces."""
        assert make_indent(3, 2) == "      "

    def test_level_2_size_4(self) -> None:
        """Level 2, size 4 returns 8 spaces."""
        assert make_indent(2, 4) == "        "


class TestIsUniformObjectList:
    """Tests for is_uniform_object_list()."""

    def test_uniform_list_returns_true(self) -> None:
        """A list of dicts with identical keys returns True."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        assert is_uniform_object_list(data) is True

    def test_empty_list_returns_false(self) -> None:
        """An empty list returns False."""
        assert is_uniform_object_list([]) is False

    def test_primitive_list_returns_false(self) -> None:
        """A list of primitives returns False."""
        assert is_uniform_object_list([1, 2, 3]) is False

    def test_dicts_different_keys_returns_false(self) -> None:
        """Dicts with different keys return False."""
        data = [{"a": 1}, {"b": 2}]
        assert is_uniform_object_list(data) is False

    def test_mixed_list_returns_false(self) -> None:
        """A mixed list (dict + primitive) returns False."""
        data = [{"name": "Alice"}, "Bob"]
        assert is_uniform_object_list(data) is False

    def test_single_dict_list_returns_true(self) -> None:
        """A list with one dict returns True."""
        assert is_uniform_object_list([{"key": "val"}]) is True


class TestEscapeUnescape:
    """Tests for escape_string() and unescape_string()."""

    def test_simple_string_not_quoted(self) -> None:
        """Simple strings without special chars are not quoted."""
        result = escape_string("hello", ", ")
        assert result == "hello"

    def test_string_with_comma_is_quoted(self) -> None:
        """Strings containing the delimiter are quoted."""
        result = escape_string("a, b", ", ")
        assert result.startswith('"')
        assert result.endswith('"')

    def test_string_with_colon_is_quoted(self) -> None:
        """Strings containing ':' are quoted."""
        result = escape_string("key: val", ", ")
        assert result.startswith('"')

    def test_empty_string_is_quoted(self) -> None:
        """Empty strings are quoted."""
        result = escape_string("", ", ")
        assert result == '""'

    def test_unescape_quoted_string(self) -> None:
        """Quoted strings are correctly unescaped."""
        assert unescape_string('"hello"') == "hello"

    def test_unescape_escaped_quotes(self) -> None:
        """Internal escaped quotes are unescaped."""
        assert unescape_string('"say \\"hi\\""') == 'say "hi"'

    def test_unescape_plain_string_unchanged(self) -> None:
        """Plain strings pass through unescape unchanged."""
        assert unescape_string("hello") == "hello"


class TestDetectType:
    """Tests for detect_type()."""

    def test_null(self) -> None:
        """'null' → None."""
        assert detect_type("null") is None

    def test_true(self) -> None:
        """'true' → True."""
        assert detect_type("true") is True

    def test_false(self) -> None:
        """'false' → False."""
        assert detect_type("false") is False

    def test_integer(self) -> None:
        """Integer string → int."""
        assert detect_type("42") == 42
        assert isinstance(detect_type("42"), int)

    def test_negative_integer(self) -> None:
        """-1 parses as int."""
        assert detect_type("-1") == -1

    def test_float(self) -> None:
        """Float string → float."""
        assert detect_type("3.14") == pytest.approx(3.14)
        assert isinstance(detect_type("3.14"), float)

    def test_quoted_string(self) -> None:
        """Quoted string → unquoted str."""
        assert detect_type('"hello world"') == "hello world"

    def test_plain_string(self) -> None:
        """Unquoted, non-numeric string → str."""
        assert detect_type("Mohit") == "Mohit"


class TestPythonToToonLiteral:
    """Tests for python_to_toon_literal()."""

    def test_none_to_null(self) -> None:
        """None → 'null'."""
        assert python_to_toon_literal(None, ", ") == "null"

    def test_true_to_true(self) -> None:
        """True → 'true'."""
        assert python_to_toon_literal(True, ", ") == "true"

    def test_false_to_false(self) -> None:
        """False → 'false'."""
        assert python_to_toon_literal(False, ", ") == "false"

    def test_int_to_string(self) -> None:
        """int → its string representation."""
        assert python_to_toon_literal(42, ", ") == "42"

    def test_float_to_string(self) -> None:
        """float → its string representation."""
        assert python_to_toon_literal(3.14, ", ") == "3.14"

    def test_simple_string(self) -> None:
        """Simple string passes through."""
        assert python_to_toon_literal("hello", ", ") == "hello"


class TestExceptions:
    """Tests for all custom exception classes."""

    def test_toonio_error_base(self) -> None:
        """ToonIOError is a subclass of Exception."""
        err = ToonIOError("oops")
        assert isinstance(err, Exception)
        assert err.message == "oops"

    def test_default_message(self) -> None:
        """Default message is set when no message is provided."""
        err = ToonIOError()
        assert isinstance(err.message, str)
        assert len(err.message) > 0

    def test_encode_error(self) -> None:
        """ToonEncodeError inherits from ToonIOError."""
        err = ToonEncodeError("encode fail")
        assert isinstance(err, ToonIOError)
        assert "encode fail" in str(err)

    def test_decode_error(self) -> None:
        """ToonDecodeError inherits from ToonIOError."""
        err = ToonDecodeError("decode fail")
        assert isinstance(err, ToonIOError)

    def test_invalid_delimiter_error(self) -> None:
        """ToonInvalidDelimiterError stores the invalid delimiter."""
        err = ToonInvalidDelimiterError("semicolon")
        assert isinstance(err, ToonIOError)
        assert err.delimiter == "semicolon"
        assert "semicolon" in err.message

    def test_invalid_indent_error(self) -> None:
        """ToonInvalidIndentError stores the invalid indent value."""
        err = ToonInvalidIndentError(3)
        assert isinstance(err, ToonIOError)
        assert err.indent == 3
        assert "3" in err.message

    def test_exceptions_can_be_raised(self) -> None:
        """Exceptions can be raised and caught correctly."""
        with pytest.raises(ToonIOError):
            raise ToonEncodeError("test error")

    def test_invalid_delimiter_raised_by_resolve(self) -> None:
        """resolve_delimiter() raises ToonInvalidDelimiterError."""
        with pytest.raises(ToonInvalidDelimiterError):
            resolve_delimiter("bad_delim")

    def test_invalid_indent_raised_by_validate(self) -> None:
        """validate_indent() raises ToonInvalidIndentError."""
        with pytest.raises(ToonInvalidIndentError):
            validate_indent(3)

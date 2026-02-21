"""
Tests for JSON ↔ TOON conversion.

Covers:
- Simple flat dicts
- Nested objects
- Tabular data (uniform object lists)
- Primitive lists
- Round-trip conversion (JSON → TOON → JSON)
- All real-world fixture datasets (users, analytics, catalog, company)
- Delimiter options (comma, tab, pipe)
- Indent options (2 and 4)

Author: Mohit
License: MIT
"""

from __future__ import annotations

import json

import pytest

from pytoonio.converters.json_converter import JsonToToonEncoder, ToonToJsonDecoder


class TestJsonToToonEncoder:
    """Tests for JsonToToonEncoder."""

    # ── Simple cases ──────────────────────────────────────────────────────

    def test_flat_dict_produces_key_value_lines(self, simple_dict: dict) -> None:
        """Flat dict keys appear as top-level TOON lines."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(simple_dict)
        assert "name: Mohit" in result
        assert "age: 25" in result

    def test_boolean_true_encodes_as_toon_literal(self, simple_dict: dict) -> None:
        """Python True encodes to TOON 'true'."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(simple_dict)
        assert "active: true" in result

    def test_none_encodes_as_null(self, simple_dict: dict) -> None:
        """Python None encodes to TOON 'null'."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(simple_dict)
        assert "score: null" in result

    def test_accepts_json_string(self) -> None:
        """Encoder accepts a raw JSON string."""
        encoder = JsonToToonEncoder()
        result = encoder.encode('{"key": "value", "num": 42}')
        assert "key: value" in result
        assert "num: 42" in result

    # ── Nested objects ────────────────────────────────────────────────────

    def test_nested_dict_indented(self, nested_dict: dict) -> None:
        """Nested dicts are indented correctly under their parent key."""
        encoder = JsonToToonEncoder(indent=2)
        result = encoder.encode(nested_dict)
        assert "user:" in result
        assert "  name: Mohit" in result
        assert "  address:" in result
        assert "    city: Jaipur" in result

    def test_indent_4_applied(self, nested_dict: dict) -> None:
        """Indent size of 4 is applied to nested keys."""
        encoder = JsonToToonEncoder(indent=4)
        result = encoder.encode(nested_dict)
        assert "    name: Mohit" in result
        assert "        city: Jaipur" in result

    # ── Lists ─────────────────────────────────────────────────────────────

    def test_primitive_list_inline(self, primitive_list_data: dict) -> None:
        """A list of primitives is rendered inline in brackets."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(primitive_list_data)
        assert "[Python, Django, REST]" in result

    def test_uniform_object_list_is_tabular(self, tabular_data: dict) -> None:
        """A list of dicts with identical keys renders as key[N]{headers}: annotation."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(tabular_data)
        # New format: contributors[3]{name,role,id}:
        assert "contributors[3]{name,role,id}:" in result
        assert "Alice,Maintainer,1" in result
        assert "Bob,Contributor,2" in result

    def test_tabular_pipe_delimiter(self, tabular_data: dict) -> None:
        """Pipe delimiter separates tabular columns in annotation header and rows."""
        encoder = JsonToToonEncoder(delimiter="pipe")
        result = encoder.encode(tabular_data)
        assert "contributors[3]{name|role|id}:" in result
        assert "Alice|Maintainer|1" in result

    def test_tabular_tab_delimiter(self, tabular_data: dict) -> None:
        """Tab delimiter appears in tabular annotation header and data rows."""
        encoder = JsonToToonEncoder(delimiter="tab")
        result = encoder.encode(tabular_data)
        # Tab delimiter in header annotation and data rows
        assert "contributors[3]{name\trole\tid}:" in result

    # ── Real-world fixtures ───────────────────────────────────────────────

    def test_users_json_encodes(self, users_json_str: str) -> None:
        """Users dataset encodes to TOON without errors."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(users_json_str)
        assert isinstance(result, str)
        assert len(result) > 0
        # Top-level keys from users fixture
        assert "totalCount" in result
        assert "activeCount" in result
        assert "lastUpdated" in result

    def test_users_json_contains_user_data(self, users_json_str: str) -> None:
        """TOON output from users dataset contains user names and emails."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(users_json_str)
        assert "Emma Wilson" in result
        assert "James Brown" in result
        assert "emma.wilson@example.com" in result

    def test_analytics_json_encodes(self, analytics_json_str: str) -> None:
        """Analytics dataset encodes to TOON without errors."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(analytics_json_str)
        assert "pageViews" in result
        assert "uniqueVisitors" in result
        assert "bounceRate" in result
        assert "trafficSources" in result

    def test_analytics_top_pages_tabular(self, analytics_data: dict) -> None:
        """Top pages uniform list renders with annotated key[N]{headers}: format."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(analytics_data)
        assert "topPages[3]{url,views,avgTime}:" in result

    def test_catalog_json_encodes(self, catalog_json_str: str) -> None:
        """Catalog dataset encodes to TOON without errors."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(catalog_json_str)
        assert "Electronics" in result
        assert "Wireless Headphones" in result
        assert "AudioTech" in result

    def test_catalog_nested_specs(self, catalog_data: dict) -> None:
        """Catalog products (uniform list) render with annotated key[N]{headers}: format."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(catalog_data)
        # Products have uniform top-level keys → annotation header must appear
        assert "products[3]{id,name,brand,price,stock,specs,ratings}:" in result
        assert "Wireless Headphones" in result
        assert "Smart Watch" in result
        assert "Laptop Pro" in result

    def test_company_json_encodes(self, company_json_str: str) -> None:
        """Company dataset encodes to TOON without errors."""
        encoder = JsonToToonEncoder()
        result = encoder.encode(company_json_str)
        assert "TechCorp International" in result
        assert "San Francisco" in result

    def test_company_deep_nesting(self, company_data: dict) -> None:
        """Deeply nested address block (3 levels) is encoded."""
        encoder = JsonToToonEncoder(indent=2)
        result = encoder.encode(company_data)
        assert "456 Tech Ave" in result
        assert "94102" in result


class TestToonToJsonDecoder:
    """Tests for ToonToJsonDecoder."""

    # ── Simple cases ──────────────────────────────────────────────────────

    def test_simple_key_value_decodes(self) -> None:
        """Simple TOON key-value pairs decode to a flat dict."""
        decoder = ToonToJsonDecoder()
        result = decoder.decode("name: Mohit\nage: 25\n")
        assert result == {"name": "Mohit", "age": 25}

    def test_null_decodes_to_none(self) -> None:
        """TOON 'null' decodes to Python None."""
        decoder = ToonToJsonDecoder()
        result = decoder.decode("value: null\n")
        assert result == {"value": None}

    def test_boolean_true_decodes(self) -> None:
        """TOON 'true' decodes to Python True."""
        decoder = ToonToJsonDecoder()
        result = decoder.decode("active: true\n")
        assert result["active"] is True

    def test_boolean_false_decodes(self) -> None:
        """TOON 'false' decodes to Python False."""
        decoder = ToonToJsonDecoder()
        result = decoder.decode("disabled: false\n")
        assert result["disabled"] is False

    def test_integer_decodes(self) -> None:
        """Integer strings decode to Python int."""
        decoder = ToonToJsonDecoder()
        result = decoder.decode("count: 42\n")
        assert result == {"count": 42}

    def test_float_decodes(self) -> None:
        """Float strings decode to Python float."""
        decoder = ToonToJsonDecoder()
        result = decoder.decode("rate: 42.5\n")
        assert result == {"rate": 42.5}

    def test_decode_to_json_returns_string(self) -> None:
        """decode_to_json() returns a valid JSON string."""
        decoder = ToonToJsonDecoder()
        result = decoder.decode_to_json("name: Mohit\nage: 25\n")
        parsed = json.loads(result)
        assert parsed == {"name": "Mohit", "age": 25}

    # ── Round-trips ───────────────────────────────────────────────────────

    def test_round_trip_simple_dict(self, simple_dict: dict) -> None:
        """Simple dict survives JSON → TOON → JSON round-trip."""
        encoder = JsonToToonEncoder()
        decoder = ToonToJsonDecoder()
        toon = encoder.encode(simple_dict)
        result = decoder.decode(toon)
        assert result["name"] == simple_dict["name"]
        assert result["age"] == simple_dict["age"]
        assert result["active"] == simple_dict["active"]
        assert result["score"] is None

    def test_round_trip_nested_dict(self, nested_dict: dict) -> None:
        """Nested dict survives JSON → TOON → JSON round-trip."""
        encoder = JsonToToonEncoder()
        decoder = ToonToJsonDecoder()
        toon = encoder.encode(nested_dict)
        result = decoder.decode(toon)
        assert result["user"]["name"] == "Mohit"
        assert result["user"]["address"]["city"] == "Jaipur"

    def test_round_trip_tabular_data(self, tabular_data: dict) -> None:
        """Tabular data survives JSON → TOON → JSON round-trip with new format."""
        encoder = JsonToToonEncoder()
        decoder = ToonToJsonDecoder()
        toon = encoder.encode(tabular_data)
        # Verify new format in encoded output
        assert "contributors[3]{name,role,id}:" in toon
        result = decoder.decode(toon)
        contributors = result["contributors"]
        assert len(contributors) == 3
        assert contributors[0]["name"] == "Alice"
        assert contributors[1]["name"] == "Bob"

    def test_round_trip_users_fixture(self, users_data: dict) -> None:
        """Users fixture survives JSON → TOON → JSON round-trip."""
        encoder = JsonToToonEncoder()
        decoder = ToonToJsonDecoder()
        toon = encoder.encode(users_data)
        result = decoder.decode(toon)
        assert result["totalCount"] == 8
        assert result["activeCount"] == 7

    def test_round_trip_analytics_fixture(self, analytics_data: dict) -> None:
        """Analytics fixture survives JSON → TOON → JSON round-trip."""
        encoder = JsonToToonEncoder()
        decoder = ToonToJsonDecoder()
        toon = encoder.encode(analytics_data)
        result = decoder.decode(toon)
        assert result["analytics"]["period"] == "2024-11"
        assert result["analytics"]["metrics"]["pageViews"] == 125000
        assert result["analytics"]["metrics"]["bounceRate"] == 42.5

    def test_round_trip_pipe_delimiter(self, tabular_data: dict) -> None:
        """Tabular round-trip works with pipe delimiter using new annotation format."""
        encoder = JsonToToonEncoder(delimiter="pipe")
        decoder = ToonToJsonDecoder(delimiter="pipe")
        toon = encoder.encode(tabular_data)
        assert "contributors[3]{name|role|id}:" in toon
        result = decoder.decode(toon)
        assert result["contributors"][0]["name"] == "Alice"

    def test_round_trip_indent_4(self, nested_dict: dict) -> None:
        """Nested round-trip works with indent=4."""
        encoder = JsonToToonEncoder(indent=4)
        decoder = ToonToJsonDecoder()
        toon = encoder.encode(nested_dict)
        result = decoder.decode(toon)
        assert result["user"]["address"]["country"] == "India"

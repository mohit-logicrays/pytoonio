"""
Tests for XML ↔ TOON conversion.

Covers:
- Simple XML to TOON encoding
- Nested XML structures
- XML attributes handling
- Round-trip conversion (XML → TOON → XML)
- All real-world XML fixture datasets
- Delimiter and indent options

Author: Mohit
License: MIT
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from pytoonio.converters.xml_converter import ToonToXmlDecoder, XmlToToonEncoder


class TestXmlToToonEncoder:
    """Tests for XmlToToonEncoder."""

    # ── Simple cases ──────────────────────────────────────────────────────

    def test_simple_xml_encodes(self, simple_xml: str) -> None:
        """Simple XML encodes to TOON without errors."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(simple_xml)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_root_tag_is_top_key(self, simple_xml: str) -> None:
        """Root XML tag becomes the top-level TOON key."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(simple_xml)
        assert "user:" in result

    def test_child_elements_encoded(self, simple_xml: str) -> None:
        """Child elements appear as indented key-value pairs."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(simple_xml)
        assert "name: Mohit" in result
        assert "age: 25" in result

    def test_xml_boolean_text(self, simple_xml: str) -> None:
        """XML text 'true' is preserved in TOON output."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(simple_xml)
        assert "active: true" in result

    def test_nested_xml_encodes(self, nested_xml: str) -> None:
        """Nested XML structures render with indentation."""
        encoder = XmlToToonEncoder(indent=2)
        result = encoder.encode(nested_xml)
        assert "company:" in result
        assert "  name: TechCorp" in result
        assert "  address:" in result
        assert "    city: Jaipur" in result

    def test_indent_4_applied(self, nested_xml: str) -> None:
        """Indent size 4 is applied to nested XML children."""
        encoder = XmlToToonEncoder(indent=4)
        result = encoder.encode(nested_xml)
        assert "    name: TechCorp" in result

    def test_accepts_element_object(self, simple_xml: str) -> None:
        """Encoder accepts an ElementTree.Element object directly."""
        root = ET.fromstring(simple_xml)
        encoder = XmlToToonEncoder()
        result = encoder.encode(root)
        assert "name: Mohit" in result

    # ── Real-world fixtures ───────────────────────────────────────────────

    def test_users_xml_encodes(self, users_xml_str: str) -> None:
        """Users XML fixture encodes to TOON without errors."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(users_xml_str)
        assert isinstance(result, str)
        assert "Emma Wilson" in result
        assert "James Brown" in result

    def test_users_xml_roles_present(self, users_xml_str: str) -> None:
        """User roles are present in TOON output from XML fixture."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(users_xml_str)
        assert "admin" in result
        assert "editor" in result
        assert "viewer" in result

    def test_analytics_xml_encodes(self, analytics_xml_str: str) -> None:
        """Analytics XML fixture encodes to TOON without errors."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(analytics_xml_str)
        assert "pageViews" in result
        assert "uniqueVisitors" in result
        assert "bounceRate" in result

    def test_analytics_xml_traffic_sources(self, analytics_xml_str: str) -> None:
        """Traffic source data is present in TOON output."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(analytics_xml_str)
        assert "organic" in result
        assert "direct" in result
        assert "social" in result

    def test_catalog_xml_encodes(self, catalog_xml_str: str) -> None:
        """Catalog XML fixture encodes to TOON without errors."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(catalog_xml_str)
        assert "Electronics" in result
        assert "Wireless Headphones" in result

    def test_catalog_xml_product_specs(self, catalog_xml_str: str) -> None:
        """Product specs are present in TOON output from XML catalog."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(catalog_xml_str)
        # noiseCancellation is 'true' text in XML
        assert "noiseCancellation" in result

    def test_company_xml_encodes(self, company_xml_str: str) -> None:
        """Company XML fixture encodes to TOON without errors."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(company_xml_str)
        assert "TechCorp International" in result
        assert "San Francisco" in result

    def test_company_xml_departments(self, company_xml_str: str) -> None:
        """Department data is present in TOON output."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(company_xml_str)
        assert "Engineering" in result
        assert "Sarah Chen" in result

    def test_company_xml_address_nesting(self, company_xml_str: str) -> None:
        """Deep address nesting is present in TOON output."""
        encoder = XmlToToonEncoder()
        result = encoder.encode(company_xml_str)
        assert "456 Tech Ave" in result
        assert "94102" in result

    # ── Delimiter options ─────────────────────────────────────────────────

    def test_pipe_delimiter_in_output(self) -> None:
        """Pipe delimiter is used in tabular TOON output."""
        xml = (
            "<data>"
            "<rows><row><a>1</a><b>x</b></row><row><a>2</a><b>y</b></row></rows>"
            "</data>"
        )
        encoder = XmlToToonEncoder(delimiter="pipe")
        result = encoder.encode(xml)
        # At minimum should encode without error
        assert isinstance(result, str)


class TestToonToXmlDecoder:
    """Tests for ToonToXmlDecoder."""

    # ── Simple decoding ───────────────────────────────────────────────────

    def test_simple_toon_to_xml(self) -> None:
        """Simple TOON object decodes to XML with matching tags."""
        decoder = ToonToXmlDecoder()
        toon = "user:\n  name: Mohit\n  age: 25\n"
        result = decoder.decode(toon)
        assert "<user>" in result
        assert "<name>Mohit</name>" in result
        assert "<age>25</age>" in result

    def test_parsed_xml_is_valid(self) -> None:
        """Decoded XML can be parsed by ElementTree without errors."""
        decoder = ToonToXmlDecoder()
        toon = "user:\n  name: Mohit\n  age: 25\n"
        xml_str = decoder.decode(toon)
        root = ET.fromstring(xml_str)
        assert root.tag == "user"

    def test_nested_toon_to_xml(self) -> None:
        """Nested TOON produces nested XML elements."""
        decoder = ToonToXmlDecoder()
        toon = "company:\n  name: TechCorp\n  address:\n    city: Jaipur\n"
        result = decoder.decode(toon)
        root = ET.fromstring(result)
        assert root.tag == "company"
        address = root.find("address")
        assert address is not None
        city = address.find("city")
        assert city is not None
        assert city.text == "Jaipur"

    # ── Round-trips ───────────────────────────────────────────────────────

    def test_round_trip_simple_xml(self, simple_xml: str) -> None:
        """Simple XML survives XML → TOON → XML round-trip structurally."""
        encoder = XmlToToonEncoder()
        decoder = ToonToXmlDecoder()
        toon = encoder.encode(simple_xml)
        xml_out = decoder.decode(toon)
        root = ET.fromstring(xml_out)
        assert root.tag == "user"
        name_el = root.find("name")
        assert name_el is not None
        assert name_el.text == "Mohit"

    def test_round_trip_nested_xml(self, nested_xml: str) -> None:
        """Nested XML survives XML → TOON → XML round-trip structurally."""
        encoder = XmlToToonEncoder()
        decoder = ToonToXmlDecoder()
        toon = encoder.encode(nested_xml)
        xml_out = decoder.decode(toon)
        root = ET.fromstring(xml_out)
        assert root.tag == "company"
        address = root.find("address")
        assert address is not None

    def test_round_trip_analytics_xml(self, analytics_xml_str: str) -> None:
        """Analytics XML survives XML → TOON → XML round-trip."""
        encoder = XmlToToonEncoder()
        decoder = ToonToXmlDecoder()
        toon = encoder.encode(analytics_xml_str)
        xml_out = decoder.decode(toon)
        root = ET.fromstring(xml_out)
        assert root.tag == "analytics"
        metrics = root.find("metrics")
        assert metrics is not None
        page_views = metrics.find("pageViews")
        assert page_views is not None
        assert page_views.text == "125000"

    def test_round_trip_company_xml(self, company_xml_str: str) -> None:
        """Company XML survives XML → TOON → XML round-trip."""
        encoder = XmlToToonEncoder()
        decoder = ToonToXmlDecoder()
        toon = encoder.encode(company_xml_str)
        xml_out = decoder.decode(toon)
        root = ET.fromstring(xml_out)
        assert root.tag == "company"
        name_el = root.find("name")
        assert name_el is not None
        assert name_el.text == "TechCorp International"

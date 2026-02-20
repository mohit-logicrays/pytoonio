"""
ToonIO Test Fixtures (conftest.py).

Shared pytest fixtures for loading JSON and XML test data from
the fixtures/ directory.

Author: Mohit
License: MIT
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Root of the fixtures directory
FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"


# ─────────────────────────────────────────────
# Raw file content fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def users_json_str() -> str:
    """Raw JSON string for the users dataset."""
    return (FIXTURES_DIR / "users.json").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def analytics_json_str() -> str:
    """Raw JSON string for the analytics dataset."""
    return (FIXTURES_DIR / "analytics.json").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def catalog_json_str() -> str:
    """Raw JSON string for the catalog dataset."""
    return (FIXTURES_DIR / "catalog.json").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def company_json_str() -> str:
    """Raw JSON string for the company dataset."""
    return (FIXTURES_DIR / "company.json").read_text(encoding="utf-8")


# ─────────────────────────────────────────────
# Parsed dict fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def users_data(users_json_str: str) -> dict:
    """Parsed Python dict for the users dataset."""
    return json.loads(users_json_str)


@pytest.fixture(scope="session")
def analytics_data(analytics_json_str: str) -> dict:
    """Parsed Python dict for the analytics dataset."""
    return json.loads(analytics_json_str)


@pytest.fixture(scope="session")
def catalog_data(catalog_json_str: str) -> dict:
    """Parsed Python dict for the catalog dataset."""
    return json.loads(catalog_json_str)


@pytest.fixture(scope="session")
def company_data(company_json_str: str) -> dict:
    """Parsed Python dict for the company dataset."""
    return json.loads(company_json_str)


# ─────────────────────────────────────────────
# XML file content fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def users_xml_str() -> str:
    """Raw XML string for the users dataset."""
    return (FIXTURES_DIR / "users.xml").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def analytics_xml_str() -> str:
    """Raw XML string for the analytics dataset."""
    return (FIXTURES_DIR / "analytics.xml").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def catalog_xml_str() -> str:
    """Raw XML string for the catalog dataset."""
    return (FIXTURES_DIR / "catalog.xml").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def company_xml_str() -> str:
    """Raw XML string for the company dataset."""
    return (FIXTURES_DIR / "company.xml").read_text(encoding="utf-8")


# ─────────────────────────────────────────────
# Simple inline fixtures for unit tests
# ─────────────────────────────────────────────

@pytest.fixture
def simple_dict() -> dict:
    """A simple flat Python dictionary."""
    return {"name": "Mohit", "age": 25, "active": True, "score": None}


@pytest.fixture
def nested_dict() -> dict:
    """A nested Python dictionary."""
    return {
        "user": {
            "name": "Mohit",
            "address": {
                "city": "Jaipur",
                "country": "India",
            },
        }
    }


@pytest.fixture
def tabular_data() -> dict:
    """A dict containing a uniform object list (renders as table in TOON)."""
    return {
        "contributors": [
            {"name": "Alice", "role": "Maintainer", "id": 1},
            {"name": "Bob", "role": "Contributor", "id": 2},
            {"name": "Charlie", "role": "Reviewer", "id": 3},
        ]
    }


@pytest.fixture
def primitive_list_data() -> dict:
    """A dict with a list of primitives."""
    return {"skills": ["Python", "Django", "REST"]}


@pytest.fixture
def simple_xml() -> str:
    """A minimal XML string."""
    return "<user><name>Mohit</name><age>25</age><active>true</active></user>"


@pytest.fixture
def nested_xml() -> str:
    """A nested XML string."""
    return (
        "<company>"
        "<name>TechCorp</name>"
        "<address><city>Jaipur</city><country>India</country></address>"
        "</company>"
    )

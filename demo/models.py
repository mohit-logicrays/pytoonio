"""
ToonIO Demo — Pydantic Request/Response Models.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Request body for the /ask streaming endpoint."""

    data: Any = Field(
        ...,
        description=(
            "The data to analyse. Can be:\n"
            "- A Python **dict or list** (JSON-compatible)\n"
            "- A **JSON string**\n"
            "- An **XML string** (set `format='xml'`)\n"
            "- A pre-converted **TOON string** (set `format='toon'`)"
        ),
        examples=[{"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}],
    )
    question: str = Field(
        default="Explain this data",
        description="What you want the LLM to answer about the data.",
        examples=["Summarise this data", "How many users are there?"],
    )
    format: str = Field(
        default="json",
        description="Input format: 'json', 'xml', or 'toon'.",
    )
    indent: int = Field(default=2, description="TOON indent size: 2 or 4.")
    delimiter: str = Field(
        default="comma",
        description="TOON table delimiter: 'comma', 'tab', or 'pipe'.",
    )


class ToonRequest(BaseModel):
    """Request body for the /toon conversion endpoint."""

    data: Any = Field(..., description="JSON dict/list/string or XML string to convert.")
    format: str = Field(default="json", description="'json' or 'xml'.")
    indent: int = Field(default=2)
    delimiter: str = Field(default="comma")


class ToonResponse(BaseModel):
    """Response from the /toon endpoint."""

    toon: str = Field(..., description="The TOON-formatted string.")
    tokens_approx: int = Field(..., description="Approximate token count (chars / 4).")

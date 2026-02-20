"""
ToonIO × Grok Streaming Service.

Converts structured data (JSON / XML / TOON) to TOON format using the
ToonIO package, then passes those TOON tokens as context to Grok via
LiteLLM and streams the response back to the client.

Why TOON?
---------
TOON is more token-efficient than JSON/XML for LLMs:
  - No curly braces, brackets, or verbose tags
  - Compact table notation for repeated objects
  - Cleaner, fewer tokens consumed

Flow
----
  User data (JSON/XML)
       │
       ▼
  ToonIO → TOON string          ← token-efficient context
       │
       ▼
  Grok (xai/grok-2-latest)      ← LiteLLM streaming
       │
       ▼
  Stream chunks → HTTP client

Endpoints
---------
  POST /ask          Stream Grok response with TOON context
  POST /toon         Just convert data to TOON (no LLM)
  GET  /health       Health check

Usage
-----
  # Set your key in .env
  echo "GROK_API_KEY=xai-..." > .env

  # Run
  uvicorn demo.service:app --reload

  # Test
  curl -N -X POST http://127.0.0.1:8000/ask \\
    -H "Content-Type: application/json" \\
    -d '{"data": {"users": [{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]},
         "question": "Summarise this user data"}'

Author: Mohit
License: MIT
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, AsyncGenerator

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

import litellm
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from toonio import convert

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

MODEL: str = os.getenv("LITELLM_MODEL", "groq/openai/gpt-oss-20b")

SYSTEM_PROMPT: str = (
    "You are a helpful data analyst. "
    "The user will provide data in TOON format — a compact, human-readable "
    "alternative to JSON and XML. TOON uses key: value pairs for objects, "
    "key[N]{col1,col2}: for uniform tables, and key[N]: with - blocks for "
    "mixed lists. Answer the user's question about the data clearly and concisely."
)

# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ToonIO × Grok Streaming",
    description=(
        "Pass JSON or XML data → ToonIO converts it to **TOON tokens** → "
        "Grok receives the compact TOON context and streams an answer."
    ),
    version="0.0.1",
)

# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────


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
        description="What you want Grok to answer about the data.",
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

    data: Any = Field(
        ..., description="JSON dict/list/string or XML string to convert."
    )
    format: str = Field(default="json", description="'json' or 'xml'.")
    indent: int = Field(default=2)
    delimiter: str = Field(default="comma")


class ToonResponse(BaseModel):
    """Response from the /toon endpoint."""

    toon: str = Field(..., description="The TOON-formatted string.")
    tokens_approx: int = Field(..., description="Approximate token count (chars / 4).")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def to_toon(data: Any, fmt: str, indent: int, delimiter: str) -> str:
    """Convert data to TOON format using ToonIO.

    Args:
        data: The input data (dict, list, str).
        fmt: Input format — 'json', 'xml', or 'toon'.
        indent: Indentation size.
        delimiter: Table delimiter.

    Returns:
        TOON-formatted string.

    Raises:
        ValueError: If the format is unknown or conversion fails.
    """
    if fmt == "toon":
        return str(data)  # already TOON, pass through
    if fmt == "xml":
        return convert.xml_to_toon(str(data), indent=indent, delimiter=delimiter)
    # Default: json
    return convert.json_to_toon(data, indent=indent, delimiter=delimiter)


async def stream_grok(toon_context: str, question: str) -> AsyncGenerator[str, None]:
    """Stream Grok's response with the TOON data as context."""
    prompt = (
        f"Here is the data in TOON format:\n\n"
        f"```\n{toon_context}```\n\n"
        f"{question}"
    )

    response = litellm.completion(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        stream=True,
    )

    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta



# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/health")
def health() -> dict:
    """Health check — returns model name and key status."""
    return {
        "status": "ok",
        "model": MODEL,
        "key_set": bool(os.getenv("XAI_API_KEY")),
    }


@app.post("/toon", response_model=ToonResponse)
def convert_to_toon(request: ToonRequest) -> ToonResponse:
    """Convert JSON or XML data to TOON format (no LLM call).

    Use this to preview what TOON tokens will be sent to Grok.

    Args:
        request: Conversion parameters.

    Returns:
        The TOON string and approximate token count.
    """
    try:
        toon = to_toon(request.data, request.format, request.indent, request.delimiter)
        return ToonResponse(toon=toon, tokens_approx=len(toon) // 4)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ask")
async def ask(request: AskRequest) -> StreamingResponse:
    """Convert data to TOON and stream Grok's answer.

    Flow:
    1. Your data (JSON / XML / TOON) → ToonIO → compact TOON tokens
    2. TOON tokens are embedded in the LLM prompt as context
    3. Grok streams its answer token-by-token

    Args:
        request: The ask request body.

    Returns:
        A streaming plain-text response from Grok.
    """

    try:
        toon = to_toon(request.data, request.format, request.indent, request.delimiter)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"TOON conversion failed: {exc}"
        ) from exc

    return StreamingResponse(
        stream_grok(toon, request.question),
        media_type="text/plain",
    )



# ─────────────────────────────────────────────────────────────────────────────
# Run directly
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀  ToonIO × Grok Streaming  →  http://{host}:{port}/docs")
    uvicorn.run("demo.service:app", host=host, port=port, reload=True)

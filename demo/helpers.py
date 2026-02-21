"""
PyToonIO Demo — Helpers.

- ``to_toon``    : convert JSON / XML / TOON data to a TOON string.
- ``stream_groq``: async generator that streams LLM response via LiteLLM/Groq.
"""

from __future__ import annotations

from typing import Any, AsyncGenerator

import litellm

from pytoonio import convert
from demo.constants import MODEL, SYSTEM_PROMPT


def to_toon(data: Any, fmt: str, indent: int, delimiter: str) -> str:
    """Convert data to TOON format using PyToonIO.

    Args:
        data: Input data — dict, list, JSON string, or XML string.
        fmt: Input format: ``'json'``, ``'xml'``, or ``'toon'``.
        indent: Indentation size (2 or 4).
        delimiter: Table delimiter (``'comma'``, ``'tab'``, ``'pipe'``).

    Returns:
        TOON-formatted string.
    """
    if fmt == "toon":
        return str(data)
    if fmt == "xml":
        return convert.xml_to_toon(str(data), indent=indent, delimiter=delimiter)
    return convert.json_to_toon(data, indent=indent, delimiter=delimiter)


async def stream_groq(toon_context: str, question: str) -> AsyncGenerator[str, None]:
    """Stream Groq's response with TOON-formatted data as context.

    Passes the TOON string as user context to the LLM via LiteLLM
    and yields response text chunks as they arrive.

    Args:
        toon_context: Data expressed in TOON format.
        question: The user's question about the data.

    Yields:
        Response text chunks from Groq.
    """
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

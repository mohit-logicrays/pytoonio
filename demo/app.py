"""
ToonIO × Groq Streaming Service — FastAPI App.

Converts structured data (JSON / XML / TOON) to TOON format using the
ToonIO package, then passes those TOON tokens as context to an LLM via
LiteLLM (Groq) and streams the response back to the client.

Endpoints
---------
  POST /ask    — Stream LLM response with TOON context
  POST /toon   — Convert data to TOON (no LLM call)
  GET  /health — Health check

Usage
-----
  uvicorn demo.app:app --reload
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from demo.constants import MODEL          # loads .env, sets API keys
from demo.helpers import stream_groq, to_toon
from demo.models import AskRequest, ToonRequest, ToonResponse

# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ToonIO × Groq Streaming",
    description=(
        "Pass JSON or XML data → ToonIO converts it to **TOON tokens** → "
        "Groq receives the compact TOON context and streams an answer."
    ),
    version="0.0.1",
)

# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/health")
def health() -> dict:
    """Health check — returns model name and key status."""
    return {
        "status": "ok",
        "model": MODEL,
        "key_set": bool(os.getenv("GROQ_API_KEY")),
    }


@app.post("/toon", response_model=ToonResponse)
def convert_to_toon(request: ToonRequest) -> ToonResponse:
    """Convert JSON or XML data to TOON format (no LLM call).

    Use this to preview the exact TOON tokens that will be sent to Groq.
    """
    try:
        toon = to_toon(request.data, request.format, request.indent, request.delimiter)
        return ToonResponse(toon=toon, tokens_approx=len(toon) // 4)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ask")
async def ask(request: AskRequest) -> StreamingResponse:
    """Convert data to TOON, then stream Groq's answer.

    Flow:
    1. Data (JSON / XML / TOON) → ToonIO → compact TOON tokens
    2. TOON tokens embedded in the LLM prompt as context
    3. Groq streams its answer token-by-token
    """
    try:
        toon = to_toon(request.data, request.format, request.indent, request.delimiter)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"TOON conversion failed: {exc}"
        ) from exc

    return StreamingResponse(
        stream_groq(toon, request.question),
        media_type="text/plain",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Run directly
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀  ToonIO × Groq  →  http://{host}:{port}/docs")
    uvicorn.run("demo.app:app", host=host, port=port, reload=True)

"""
ToonIO Demo — Constants.

Centralised configuration for the streaming service.
Uses Groq as the LLM inference provider via LiteLLM.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from demo/ then project root
_here = Path(__file__).parent
_root = _here.parent
load_dotenv(_here / ".env", override=False)
load_dotenv(_root / ".env", override=False)

# ── Groq (inference provider) ─────────────────────────────────────────────────
# LiteLLM uses GROQ_API_KEY for groq/* models.
# Get your key from: https://console.groq.com/
# Add to .env:  GROQ_API_KEY=gsk_...

# ── LLM model ─────────────────────────────────────────────────────────────────
MODEL: str = os.getenv("LITELLM_MODEL", "groq/llama-3.3-70b-versatile")

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT: str = (
    "You are a helpful data analyst. "
    "The user will provide data in TOON format — a compact, human-readable "
    "alternative to JSON and XML. TOON uses key: value pairs for objects, "
    "key[N]{col1,col2}: for uniform tables, and key[N]: with - blocks for "
    "mixed lists. Answer the user's question about the data clearly and concisely."
)

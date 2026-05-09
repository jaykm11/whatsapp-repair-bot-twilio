"""
Gemini connectivity test.
Uses the exact same client setup and API call as app/services/gemini.py.

Run from anywhere — repo root OR the tests/ folder:
    python tests/test_gemini.py
    python test_gemini.py
    python test_gemini.py "What causes a pipe to burst?"
"""

import asyncio
import os
import sys

# ---------------------------------------------------------------------------
# Load .env — search this file's directory, then one level up (repo root)
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))
for _folder in [_here, os.path.dirname(_here)]:
    _env_path = os.path.join(_folder, ".env")
    if os.path.exists(_env_path):
        with open(_env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
        break

from google import genai  # noqa: E402

# Must match app/services/gemini.py exactly
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TIMEOUT_SECONDS = 50
API_KEY = os.environ.get("GEMINI_API_KEY", "")


def _run_sync(question: str) -> str:
    """Mirrors the sync client.models.generate_content call in GeminiService."""
    client = genai.Client(api_key=API_KEY)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=question)
    return response.text.strip()


async def _run_async(question: str) -> str:
    """Mirrors the production asyncio.to_thread + wait_for path in GeminiService."""
    client = genai.Client(api_key=API_KEY)
    response = await asyncio.wait_for(
        asyncio.to_thread(
            client.models.generate_content,
            model=GEMINI_MODEL,
            contents=question,
        ),
        timeout=GEMINI_TIMEOUT_SECONDS,
    )
    return response.text.strip()


def main():
    if not API_KEY:
        print("ERROR: GEMINI_API_KEY not found — check your .env file")
        sys.exit(1)

    question = " ".join(sys.argv[1:]) or "How are you?"

    print(f"Model   : {GEMINI_MODEL}")
    print(f"Timeout : {GEMINI_TIMEOUT_SECONDS}s")
    print(f"API key : {API_KEY[:8]}...")
    print(f"Question: {question}")
    print("-" * 50)

    print("[1/2] Sync call...")
    print(f"Response: {_run_sync(question)}\n")

    print("[2/2] Async call (mirrors production code path)...")
    print(f"Response: {asyncio.run(_run_async(question))}\n")

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()

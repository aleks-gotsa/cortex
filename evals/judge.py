"""Judge helper — direct httpx calls to a local OpenAI-compatible endpoint.

Judging deliberately does NOT route through the pipeline's LLM client: the
judge must stay independent of the system under test. The judge model should
be a different family from the generator (llama3.1:8b vs qwen3:8b here).
"""

import json
import logging
import os
import re

import httpx

logger = logging.getLogger(__name__)

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "llama3.1:8b")
JUDGE_BASE_URL = os.environ.get("LOCAL_BASE_URL", "http://localhost:11434/v1").rstrip("/")

_TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)

JUDGE_SYSTEM = """\
You are a strict fact-checking judge. Given a CLAIM and the SOURCE content it cites, decide whether the source supports the claim.

Verdicts:
- "supported": the source directly states or clearly implies the full claim
- "partial": the source supports part of the claim, but the claim overstates, generalizes, or adds specifics the source does not contain
- "unsupported": the source does not support the claim, or says something different

Judge ONLY against the provided source content. Do not use outside knowledge.
Respond with a single JSON object: {"verdict": "supported" | "partial" | "unsupported", "reason": "<one sentence>"}"""

VERDICTS = ("supported", "partial", "unsupported")


def _parse_json(text: str) -> dict:
    """Extract and parse JSON from model output, stripping markdown fences."""
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    stripped = re.sub(r"\n?```\s*$", "", stripped).strip()
    if stripped:
        return json.loads(stripped)
    raise ValueError("Empty response text")


async def ollama_json(
    client: httpx.AsyncClient,
    system: str,
    user_message: str,
    model: str = JUDGE_MODEL,
    max_tokens: int = 512,
) -> dict:
    """One JSON-constrained chat completion at temperature 0, retried once."""
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "seed": 42,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
    }
    for attempt in (1, 2):
        try:
            response = await client.post(f"{JUDGE_BASE_URL}/chat/completions", json=payload)
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Cannot reach judge endpoint at {JUDGE_BASE_URL} — is Ollama running?"
            ) from exc
        text = (response.json()["choices"][0]["message"]["content"] or "").strip()
        try:
            return _parse_json(text)
        except (json.JSONDecodeError, ValueError):
            if attempt == 2:
                raise
            logger.warning("judge JSON parse failed — retrying once")
    raise RuntimeError("unreachable")


async def ensure_context(
    client: httpx.AsyncClient,
    model: str = "llama3.2:3b",
    min_prompt_tokens: int = 9000,
) -> None:
    """Fail loudly if the server clips long prompts.

    Ollama defaults to a 4,096-token context; synthesis and verification
    prompts here run 6-10k tokens, which a small window silently truncates
    (invalidating every result). Fix: OLLAMA_CONTEXT_LENGTH=16384 on the
    server (macOS app: `launchctl setenv OLLAMA_CONTEXT_LENGTH 16384`,
    then restart Ollama).
    """
    filler = "The quick brown fox jumps over the lazy dog. " * (min_prompt_tokens // 8)
    response = await client.post(
        f"{JUDGE_BASE_URL}/chat/completions",
        json={
            "model": model,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": filler + "\nSay OK."}],
        },
    )
    response.raise_for_status()
    prompt_tokens = int((response.json().get("usage") or {}).get("prompt_tokens") or 0)
    if prompt_tokens < min_prompt_tokens:
        raise RuntimeError(
            f"server context window clips prompts ({prompt_tokens} tokens seen, "
            f"≥{min_prompt_tokens} required) — set OLLAMA_CONTEXT_LENGTH=16384 and restart Ollama"
        )
    logger.info("context preflight ok: %d prompt tokens accepted", prompt_tokens)


async def judge_claim(
    client: httpx.AsyncClient,
    claim: str,
    sources_block: str,
    model: str = JUDGE_MODEL,
) -> dict:
    """Return {"verdict": ..., "reason": ...} for one claim against its cited sources."""
    user_message = f"CLAIM:\n{claim}\n\nCITED SOURCE CONTENT:\n{sources_block}"
    data = await ollama_json(client, JUDGE_SYSTEM, user_message, model=model)
    verdict = str(data.get("verdict", "")).strip().lower()
    if verdict not in VERDICTS:
        logger.warning("judge returned unknown verdict %r — treating as unsupported", verdict)
        verdict = "unsupported"
    return {"verdict": verdict, "reason": str(data.get("reason", ""))}

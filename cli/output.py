"""File saving and stats footer."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from rich.console import Console
from rich.text import Text

from .theme import DIM, GREEN, LIGHT_BLUE


def save_document(query: str, document: str, output_dir: str) -> str:
    """Save markdown document to file. Returns the filepath."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    slug = _slugify(query)
    path = out / f"{slug}.md"

    # Deduplicate: append -2, -3, etc.
    counter = 2
    while path.exists():
        path = out / f"{slug}-{counter}.md"
        counter += 1

    path.write_text(document, encoding="utf-8")
    return str(path)


def print_footer(
    filepath: str,
    cost_usd: float,
    sources_count: int,
    elapsed_seconds: float,
    console: Console,
) -> None:
    """Print the stats footer after a research run."""
    console.print()

    check = Text("  \u2713 ", style=GREEN)
    saved_label = Text("Saved to ", style=DIM)
    saved_path = Text(filepath, style=LIGHT_BLUE)
    console.print(Text.assemble(check, saved_label, saved_path))

    check2 = Text("  \u2713 ", style=GREEN)
    stats = Text(
        f"Cost: ${cost_usd:.2f} \u2502 Sources: {sources_count} \u2502 Time: {elapsed_seconds:.0f}s",
        style=DIM,
    )
    console.print(Text.assemble(check2, stats))


def _slugify(query: str, max_words: int = 5) -> str:
    """Turn a query into a filename-safe slug. Supports unicode."""
    # Normalize unicode to decomposed form, strip combining marks for basic transliteration
    normalized = unicodedata.normalize("NFKD", query.lower())
    # Keep letters (including unicode), digits, spaces, hyphens
    cleaned = re.sub(r"[^\w\s-]", "", normalized)
    # Replace whitespace with hyphens
    words = cleaned.split()[:max_words]
    slug = "-".join(words)
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "research"

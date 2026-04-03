"""Cortex color theme, shared console, and separators."""

from __future__ import annotations

from rich.console import Console
from rich.rule import Rule

# ── Color theme ──────────────────────────────────────────────────────────────

NAVY = "#1e3a5f"
BLUE = "#3b82f6"
LIGHT_BLUE = "#60a5fa"
GREEN = "#22c55e"
DIM = "#6b7280"
WHITE = "#f9fafb"

# ── Shared console ───────────────────────────────────────────────────────────

console = Console()


# ── Separators ───────────────────────────────────────────────────────────────


def print_separator() -> None:
    """Print a thin navy separator line."""
    console.print(Rule(style=NAVY))

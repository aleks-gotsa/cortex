"""Cortex CLI — terminal interface for the deep research engine."""

from __future__ import annotations

import asyncio
import os

import click
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

# ── Color theme ──────────────────────────────────────────────────────────────

NAVY = "#1e3a5f"
BLUE = "#3b82f6"
LIGHT_BLUE = "#60a5fa"
GREEN = "#22c55e"
DIM = "#6b7280"
WHITE = "#f9fafb"

# ── Config ───────────────────────────────────────────────────────────────────

BACKEND_URL = os.environ.get("CORTEX_BACKEND_URL", "http://localhost:8000")
OUTPUT_DIR = os.environ.get("CORTEX_OUTPUT_DIR", "./cortex_output")

console = Console()


# ── Branding ─────────────────────────────────────────────────────────────────


def print_header(subtitle: str | None = None) -> None:
    """Print the Cortex header panel."""
    width = min(console.width, 60)
    title = Text("◈  Cortex", style=f"bold {BLUE}")
    sub = Text(
        subtitle or "Deep research engine — search, verify, remember.",
        style=DIM,
    )
    content = Text.assemble(title, "\n", sub)
    console.print(
        Panel(content, border_style=f"bold {NAVY}", padding=(0, 2), width=width)
    )


def print_separator() -> None:
    """Print a thin navy separator line."""
    console.print(Rule(style=NAVY))


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _do_research(
    query: str,
    depth: str,
    use_memory: bool,
    backend_url: str,
) -> None:
    """Run a single research query against the backend."""
    from .connection import ConnectionError, StreamError, check_backend, stream_research

    print_header()
    console.print()

    if not await check_backend(backend_url):
        console.print(
            f"  [{DIM}]✗[/{DIM}] [red]Cannot connect to backend at[/red] "
            f"[{LIGHT_BLUE}]{backend_url}[/{LIGHT_BLUE}]"
        )
        console.print(
            f"    [{DIM}]Start with: uvicorn backend.main:app --reload[/{DIM}]"
        )
        return

    try:
        async for event in stream_research(backend_url, query, depth, use_memory):
            # Placeholder — steps 3-5 will consume events here
            pass
    except ConnectionError:
        console.print(f"  [red]✗ Connection lost to {backend_url}[/red]")
    except StreamError as exc:
        console.print(f"  [red]✗ {exc}[/red]")


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.group(invoke_without_command=True)
@click.argument("query", nargs=-1)
@click.option(
    "--depth",
    default="standard",
    type=click.Choice(["quick", "standard", "deep"]),
    help="Research depth (default: standard)",
)
@click.option("--no-memory", is_flag=True, default=False, help="Don't use/store memory")
@click.option("--backend", default=None, help="Backend URL override")
@click.option("--output", default=None, help="Output directory override")
@click.pass_context
def cli(
    ctx: click.Context,
    query: tuple[str, ...],
    depth: str,
    no_memory: bool,
    backend: str | None,
    output: str | None,
) -> None:
    """Deep research engine — search, verify, remember."""
    ctx.ensure_object(dict)
    ctx.obj["backend_url"] = backend or BACKEND_URL
    ctx.obj["output_dir"] = output or OUTPUT_DIR
    ctx.obj["depth"] = depth
    ctx.obj["use_memory"] = not no_memory

    if ctx.invoked_subcommand is not None:
        return

    query_str = " ".join(query).strip()
    if not query_str:
        # No query and no subcommand — placeholder for REPL (step 7)
        console.print(f"[{DIM}]No query provided. Use: cortex \"your query\"[/{DIM}]")
        return

    asyncio.run(
        _do_research(query_str, depth, not no_memory, ctx.obj["backend_url"])
    )

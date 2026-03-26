"""Cortex CLI — terminal interface for the deep research engine."""

from __future__ import annotations

import asyncio
import os
import time

import click
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
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
    output_dir: str = OUTPUT_DIR,
    show_header: bool = True,
) -> None:
    """Run a single research query against the backend."""
    from .connection import ConnectionError, StreamError, check_backend, stream_research
    from .output import print_footer, save_document
    from .progress import ProgressDisplay
    from .renderer import render_document

    t0 = time.monotonic()

    if show_header:
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

    progress = ProgressDisplay(console)
    progress.start()

    complete_data: dict | None = None
    try:
        async for event in stream_research(backend_url, query, depth, use_memory):
            if event.event == "complete":
                complete_data = event.data
            progress.handle_event(event.event, event.data)
    except ConnectionError:
        progress.stop()
        console.print(f"  [red]✗ Connection lost to {backend_url}[/red]")
        return
    except StreamError as exc:
        progress.stop()
        err_msg = str(exc)
        console.print(f"  [red]✗ {err_msg}[/red]")
        if "Timed out" in err_msg:
            console.print(f"    [{DIM}]Try --depth quick for faster results.[/{DIM}]")
        else:
            console.print(f"    [{DIM}]Partial results may be incomplete.[/{DIM}]")
        return
    except KeyboardInterrupt:
        progress.stop()
        console.print(f"\n  [{DIM}]Research interrupted.[/{DIM}]")
        return
    finally:
        progress.stop()

    if not complete_data:
        console.print(f"  [red]✗ Research ended without a result.[/red]")
        return

    elapsed = time.monotonic() - t0
    document = complete_data.get("document", "")
    sources = complete_data.get("sources", [])
    cost_usd = complete_data.get("cost_usd", 0.0)

    console.print()
    print_separator()
    render_document(document, console)
    print_separator()

    filepath = save_document(query, document, output_dir)
    print_footer(filepath, cost_usd, len(sources), elapsed, console)


# ── REPL ─────────────────────────────────────────────────────────────────────


def _repl(
    depth: str,
    use_memory: bool,
    backend_url: str,
    output_dir: str,
) -> None:
    """Interactive REPL mode."""
    print_header("Type a query or 'exit' to quit.")
    console.print()

    research_count = 0

    while True:
        try:
            query = console.input(f"  [{BLUE}]❯[/{BLUE}] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
            break

        if not query or query in ("exit", "quit"):
            break

        if query == "history":
            asyncio.run(_show_history(backend_url))
            console.print()
            continue

        try:
            asyncio.run(
                _do_research(
                    query, depth, use_memory, backend_url, output_dir,
                    show_header=False,
                )
            )
            research_count += 1
        except KeyboardInterrupt:
            console.print(f"\n  [{DIM}]Research interrupted.[/{DIM}]")

        console.print()

    console.print(
        f"  [{DIM}]Session complete. {research_count} research(es) "
        f"saved to {output_dir}[/{DIM}]"
    )


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option(
    "--depth",
    default="standard",
    type=click.Choice(["quick", "standard", "deep"]),
    help="Research depth (default: standard)",
)
@click.option("--no-memory", is_flag=True, default=False, help="Don't use/store memory")
@click.option("--backend", default=None, help="Backend URL override")
@click.option("--output", default=None, help="Output directory override")
@click.option("--version", is_flag=True, help="Show version")
@click.pass_context
def cli(
    ctx: click.Context,
    depth: str,
    no_memory: bool,
    backend: str | None,
    output: str | None,
    version: bool,
) -> None:
    """Deep research engine — search, verify, remember."""
    if version:
        console.print("cortex 0.1.0")
        return

    backend_url = backend or BACKEND_URL
    output_dir = output or OUTPUT_DIR
    use_memory = not no_memory

    args = ctx.args
    if not args:
        _repl(depth, use_memory, backend_url, output_dir)
        return

    # Route subcommands manually.
    cmd = args[0]
    if cmd == "history":
        asyncio.run(_show_history(backend_url))
        return
    if cmd == "view":
        if len(args) < 2:
            console.print(f"[red]Usage: cortex view <research_id>[/red]")
            return
        asyncio.run(_show_detail(args[1], backend_url))
        return

    # Everything else is a research query.
    query = " ".join(args)
    asyncio.run(_do_research(query, depth, use_memory, backend_url, output_dir))


async def _show_history(backend_url: str) -> None:
    from .connection import fetch_history

    try:
        runs = await fetch_history(backend_url)
    except Exception:
        console.print(f"  [red]✗ Cannot connect to backend at {backend_url}[/red]")
        return

    if not runs:
        console.print(f"  [{DIM}]No research history yet.[/{DIM}]")
        return

    table = Table(
        title="Research History",
        title_style=f"bold {BLUE}",
        border_style=NAVY,
        header_style=f"bold {BLUE}",
    )
    table.add_column("ID", style=WHITE, max_width=8)
    table.add_column("Query", style=WHITE, max_width=40)
    table.add_column("Depth", style=DIM, justify="center")
    table.add_column("Cost", style=DIM, justify="right")
    table.add_column("Date", style=DIM, justify="right")

    for run in runs:
        run_id = str(run.get("id", ""))[:8]
        query = str(run.get("query", ""))[:40]
        depth = str(run.get("depth", ""))
        cost = run.get("cost_usd")
        cost_str = f"${cost:.2f}" if cost is not None else "-"
        date_str = _relative_time(run.get("created_at", ""))
        table.add_row(run_id, query, depth, cost_str, date_str)

    console.print(table)


async def _show_detail(research_id: str, backend_url: str) -> None:
    from .connection import fetch_detail
    from .renderer import render_document

    try:
        detail = await fetch_detail(backend_url, research_id)
    except Exception:
        console.print(f"  [red]✗ Cannot connect to backend at {backend_url}[/red]")
        return

    if detail is None:
        console.print(f"  [red]Research not found: {research_id}[/red]")
        return

    run = detail.get("run", {})
    result = detail.get("result", {})

    document = result.get("document_md", "")
    if not document:
        console.print(f"  [{DIM}]No document found for this research.[/{DIM}]")
        return

    print_header()
    console.print(
        f"  [{DIM}]Query: {run.get('query', '')}[/{DIM}]"
    )
    console.print()
    print_separator()
    render_document(document, console)
    print_separator()

    cost = run.get("cost_usd", 0)
    sources_json = result.get("sources_json")
    sources_count = len(sources_json) if isinstance(sources_json, list) else 0
    console.print(
        f"  [{DIM}]Cost: ${cost:.2f} \u2502 Sources: {sources_count}[/{DIM}]"
    )


def _relative_time(date_str: str) -> str:
    """Convert an ISO date string to a relative time like '2h ago'."""
    if not date_str:
        return "-"
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            return f"{seconds // 60}m ago"
        if seconds < 86400:
            return f"{seconds // 3600}h ago"
        return f"{seconds // 86400}d ago"
    except (ValueError, TypeError):
        return str(date_str)[:10]

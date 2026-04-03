"""Cortex CLI — terminal interface for the deep research engine."""

from __future__ import annotations

import asyncio
import os
import time

import click
import httpx
import pyfiglet
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .theme import BLUE, DIM, GREEN, LIGHT_BLUE, NAVY, WHITE, console, print_separator

# ── Config ───────────────────────────────────────────────────────────────────

BACKEND_URL = os.environ.get("CORTEX_BACKEND_URL", "http://localhost:8000")
OUTPUT_DIR = os.environ.get("CORTEX_OUTPUT_DIR", "./cortex_output")


# ── Branding ─────────────────────────────────────────────────────────────────


async def print_header() -> None:
    """Print the Cortex ASCII art header with system info."""
    console.print()

    art = pyfiglet.figlet_format("cortex", font="ansi_shadow").rstrip("\n")
    console.print(Text(art, style=BLUE))

    # Subtitle left + version right on one line.
    left = " Deep research engine — search, verify, remember."
    right = "v0.1.0"
    width = console.width
    pad = max(1, width - len(left) - len(right))
    line = Text()
    line.append(left, style=DIM)
    line.append(" " * pad)
    line.append(right, style=DIM)
    console.print(line)

    console.print(Rule(style="#1e3a5f"))

    # Ping backend for status + research count.
    connected = False
    research_count = "unknown"
    backend_url = BACKEND_URL
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{backend_url}/research/history")
            if resp.status_code == 200:
                connected = True
                history = resp.json()
                research_count = str(len(history))
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        pass

    def _info(label: str, parts: list[tuple[str, str]]) -> Text:
        t = Text()
        t.append(f"  {label:<12}", style=LIGHT_BLUE)
        for text, style in parts:
            t.append(text, style=style)
        return t

    status_text = "connected" if connected else "offline"
    status_style = GREEN if connected else "red"
    display_url = backend_url.removeprefix("http://").removeprefix("https://")
    console.print(_info("backend", [(f"{display_url} · ", DIM), (status_text, status_style)]))
    console.print(_info("search", [("serper + tavily", DIM)]))
    console.print(_info("memory", [(f"qdrant · {research_count} researches", DIM)]))
    console.print(_info("models", [("haiku (plan) · sonnet (synth/verify)", DIM)]))

    console.print(Rule(style="#1e3a5f"))
    console.print()


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
        await print_header()

    if not await check_backend(backend_url):
        console.print(
            f"  [{DIM}]\u2717[/{DIM}] [red]Cannot connect to backend at[/red] "
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
        console.print(f"  [red]\u2717 Connection lost to {backend_url}[/red]")
        return
    except StreamError as exc:
        progress.stop()
        err_msg = str(exc)
        console.print(f"  [red]\u2717 {err_msg}[/red]")
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
        console.print(f"  [red]\u2717 Research ended without a result.[/red]")
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
    asyncio.run(print_header())

    research_count = 0

    while True:
        try:
            query = console.input(f"  [{BLUE}]\u276f[/{BLUE}] ").strip()
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


@click.group(invoke_without_command=True)
@click.version_option("0.1.0", prog_name="cortex")
@click.option(
    "--depth",
    default="standard",
    type=click.Choice(["quick", "standard", "deep"]),
    help="Research depth (default: standard)",
)
@click.option("--backend", default=None, help="Backend URL override")
@click.option("--no-memory", is_flag=True, default=False, help="Don't use/store memory")
@click.option("--output", default=None, help="Output directory override")
@click.pass_context
def cli(
    ctx: click.Context,
    depth: str,
    backend: str | None,
    no_memory: bool,
    output: str | None,
) -> None:
    """Deep research engine — search, verify, remember."""
    ctx.ensure_object(dict)
    ctx.obj["depth"] = depth
    ctx.obj["backend_url"] = backend or BACKEND_URL
    ctx.obj["output_dir"] = output or OUTPUT_DIR
    ctx.obj["use_memory"] = not no_memory

    if ctx.invoked_subcommand is None:
        _repl(
            depth=ctx.obj["depth"],
            use_memory=ctx.obj["use_memory"],
            backend_url=ctx.obj["backend_url"],
            output_dir=ctx.obj["output_dir"],
        )


@cli.command()
@click.argument("query", nargs=-1, required=True)
@click.option(
    "--depth",
    default=None,
    type=click.Choice(["quick", "standard", "deep"]),
    help="Research depth (overrides group-level --depth)",
)
@click.pass_context
def research(ctx: click.Context, query: tuple[str, ...], depth: str | None) -> None:
    """Run a single research query."""
    query_str = " ".join(query)
    asyncio.run(
        _do_research(
            query_str,
            depth or ctx.obj["depth"],
            ctx.obj["use_memory"],
            ctx.obj["backend_url"],
            ctx.obj["output_dir"],
        )
    )


@cli.command()
@click.pass_context
def history(ctx: click.Context) -> None:
    """Show research history."""
    asyncio.run(_show_history(ctx.obj["backend_url"]))


@cli.command()
@click.argument("research_id")
@click.pass_context
def view(ctx: click.Context, research_id: str) -> None:
    """View a past research by ID."""
    asyncio.run(_show_detail(research_id, ctx.obj["backend_url"]))


# ── History / Detail ─────────────────────────────────────────────────────────


async def _show_history(backend_url: str) -> None:
    from .connection import fetch_history

    try:
        runs = await fetch_history(backend_url)
    except Exception:
        console.print(f"  [red]\u2717 Cannot connect to backend at {backend_url}[/red]")
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
        console.print(f"  [red]\u2717 Cannot connect to backend at {backend_url}[/red]")
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

    await print_header()
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

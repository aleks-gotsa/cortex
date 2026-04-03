"""Benchmark runner for Cortex research engine.

Usage: python -m benchmarks.runner --url http://localhost:8000 --n 5 --depth mixed
"""

import asyncio
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import click
import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from benchmarks.queries import QUERIES
from benchmarks.report import generate

console = Console()

load_dotenv()


def _select_queries(n: int, depth: str) -> list[dict[str, str]]:
    """Select and filter queries based on depth and count."""
    if depth == "mixed":
        selected = QUERIES[:n]
    else:
        filtered = [q for q in QUERIES if q["depth"] == depth]
        selected = filtered[:n]
    return selected


def _atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON atomically: write to .tmp then rename."""
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, suffix=".tmp", prefix=path.stem
    )
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


async def _run_single_query(
    client: httpx.AsyncClient,
    url: str,
    query: str,
    depth: str,
    api_keys: dict[str, str],
) -> dict:
    """Execute a single research query and collect metrics."""
    payload = {
        "query": query,
        "depth": depth,
        "use_memory": False,
        **api_keys,
    }

    t0 = time.monotonic()
    ttff: float | None = None
    stage_times: dict[str, float] = {}
    total_time: float | None = None
    cost_usd: float | None = None
    research_id: str | None = None
    error: str | None = None

    try:
        async with client.stream("POST", f"{url}/research", json=payload) as response:
            if response.status_code != 200:
                body = await response.aread()
                return {
                    "query": query,
                    "depth": depth,
                    "success": False,
                    "error": f"HTTP {response.status_code}: {body.decode(errors='replace')[:500]}",
                    "ttff": None,
                    "total_time": None,
                    "cost_usd": None,
                    "stage_times": {},
                    "research_id": None,
                    "tokens_in": None,
                    "tokens_out": None,
                }

            current_event: str | None = None
            current_data: str = ""

            async for line in response.aiter_lines():
                if line.startswith("event: "):
                    current_event = line[7:].strip()
                    current_data = ""
                elif line.startswith("data: "):
                    current_data = line[6:]
                elif line == "" and current_event is not None:
                    elapsed = time.monotonic() - t0

                    if ttff is None:
                        ttff = round(elapsed, 4)

                    stage_times[current_event] = round(elapsed, 4)

                    if current_data:
                        try:
                            event_data = json.loads(current_data)
                        except json.JSONDecodeError:
                            event_data = {}

                        if current_event == "complete":
                            total_time = round(elapsed, 4)
                            cost_usd = event_data.get("cost_usd")
                            research_id = event_data.get("research_id")

                    current_event = None
                    current_data = ""

    except httpx.TimeoutException:
        error = "Request timed out"
    except httpx.HTTPError as e:
        error = f"HTTP error: {e}"
    except Exception as e:
        error = f"Unexpected error: {e}"

    if total_time is None and error is None:
        total_time = round(time.monotonic() - t0, 4)

    success = error is None and total_time is not None

    return {
        "query": query,
        "depth": depth,
        "success": success,
        "error": error,
        "ttff": ttff,
        "total_time": total_time,
        "cost_usd": cost_usd,
        "stage_times": stage_times,
        "research_id": research_id,
        "tokens_in": None,
        "tokens_out": None,
    }


async def _run_benchmark(url: str, n: int, depth: str, output: str) -> None:
    """Run the full benchmark suite."""
    queries = _select_queries(n, depth)

    if not queries:
        console.print(f"[red]No queries found for depth '{depth}'[/red]")
        return

    console.print(f"\n[bold]Cortex Benchmark[/bold]")
    console.print(f"  Backend: {url}")
    console.print(f"  Queries: {len(queries)} ({depth})")
    console.print(f"  Output:  {output}\n")

    api_keys: dict[str, str] = {}
    for env_var, field in [
        ("ANTHROPIC_API_KEY", "anthropic_api_key"),
        ("SERPER_API_KEY", "serper_api_key"),
        ("TAVILY_API_KEY", "tavily_api_key"),
    ]:
        val = os.environ.get(env_var)
        if val:
            api_keys[field] = val

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    results: list[dict] = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Running queries...", total=len(queries))

            for i, q in enumerate(queries):
                truncated = q["query"][:60] + ("..." if len(q["query"]) > 60 else "")
                progress.update(task, description=f"[{i+1}/{len(queries)}] {truncated}")

                result = await _run_single_query(
                    client, url, q["query"], q["depth"], api_keys
                )
                result["index"] = i
                result["timestamp"] = datetime.now(timezone.utc).isoformat()
                results.append(result)

                raw_path = output_dir / f"raw_{timestamp}_{i}.json"
                _atomic_write_json(raw_path, result)

                status = "[green]OK[/green]" if result["success"] else f"[red]FAIL: {result.get('error', 'unknown')}[/red]"
                progress.console.print(f"  {status} ({result.get('total_time', '?')}s)")
                progress.advance(task)

    console.print(f"\n[bold]Saved {len(results)} raw results to {output_dir}[/bold]")
    console.print("[bold]Generating report...[/bold]\n")
    generate(str(output_dir))


@click.command()
@click.option("--url", default="http://localhost:8000", help="Backend URL")
@click.option("--n", default=5, type=int, help="Number of queries to run (max 20)")
@click.option(
    "--depth",
    default="mixed",
    type=click.Choice(["quick", "standard", "deep", "mixed"]),
    help="Force a specific depth level",
)
@click.option("--output", default="benchmarks/results", help="Output directory")
def main(url: str, n: int, depth: str, output: str) -> None:
    """Run Cortex benchmark suite."""
    n = min(n, 20)
    asyncio.run(_run_benchmark(url, n, depth, output))


if __name__ == "__main__":
    main()

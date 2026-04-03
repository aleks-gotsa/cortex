"""Benchmark report generator for Cortex research runs."""

import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from benchmarks.metrics import compute_summary

console = Console()


def _atomic_write_text(path: Path, content: str) -> None:
    """Write text atomically: write to .tmp then rename."""
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, suffix=".tmp", prefix=path.stem
    )
    try:
        with os.fdopen(tmp_fd, "w") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _load_raw_results(results_dir: str) -> list[dict]:
    """Load all raw_*.json files from the results directory."""
    results_path = Path(results_dir)
    raw_files = sorted(results_path.glob("raw_*.json"))
    results: list[dict] = []
    for f in raw_files:
        try:
            data = json.loads(f.read_text())
            results.append(data)
        except (json.JSONDecodeError, OSError) as e:
            console.print(f"[yellow]Warning: skipping {f.name}: {e}[/yellow]")
    return results


def _build_markdown(results: list[dict], summary: dict, results_dir: str) -> str:
    """Build markdown report content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    succeeded = summary["succeeded"]
    failed = summary["failed"]
    total = summary["count"]

    lines = [
        "# Cortex Baseline Benchmark",
        f"Date: {now}",
        f"Backend: (local)",
        f"Queries run: {total} ({succeeded} succeeded, {failed} failed)",
        "",
        "## Summary",
        "| Metric | Value |",
        "|--------|-------|",
        f"| TTFF p50 | {summary['ttff']['p50']}s |",
        f"| TTFF p95 | {summary['ttff']['p95']}s |",
        f"| Total time p50 | {summary['total_time']['p50']}s |",
        f"| Total time p95 | {summary['total_time']['p95']}s |",
        f"| Mean cost/query | ${summary['cost_usd']['mean']:.4f} |",
        f"| Throughput | {summary['throughput_qpm']} queries/min |",
        f"| Success rate | {summary['success_rate']}% |",
        "",
        "## Per-query results",
        "| # | Query (truncated) | Depth | TTFF | Total | Cost |",
        "|---|------------------|-------|------|-------|------|",
    ]

    for i, r in enumerate(results):
        query_trunc = r["query"][:50] + ("..." if len(r["query"]) > 50 else "")
        if r.get("success"):
            ttff = f"{r.get('ttff', '?')}s"
            total_t = f"{r.get('total_time', '?')}s"
            cost = f"${r.get('cost_usd', 0) or 0:.4f}"
        else:
            ttff = "FAIL"
            total_t = "FAIL"
            cost = "-"
        lines.append(f"| {i+1} | {query_trunc} | {r['depth']} | {ttff} | {total_t} | {cost} |")

    return "\n".join(lines) + "\n"


def _write_csv(path: Path, results: list[dict]) -> None:
    """Write per-query results as CSV atomically."""
    fieldnames = ["index", "query", "depth", "success", "ttff", "total_time", "cost_usd", "error"]
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, suffix=".tmp", prefix=path.stem
    )
    try:
        with os.fdopen(tmp_fd, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for i, r in enumerate(results):
                row = {**r, "index": i}
                writer.writerow(row)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _print_rich_table(results: list[dict], summary: dict) -> None:
    """Print summary and per-query table to stdout."""
    st = Table(title="Benchmark Summary", show_header=True)
    st.add_column("Metric", style="bold")
    st.add_column("Value", justify="right")
    st.add_row("TTFF p50", f"{summary['ttff']['p50']}s")
    st.add_row("TTFF p95", f"{summary['ttff']['p95']}s")
    st.add_row("Total time p50", f"{summary['total_time']['p50']}s")
    st.add_row("Total time p95", f"{summary['total_time']['p95']}s")
    st.add_row("Mean cost/query", f"${summary['cost_usd']['mean']:.4f}")
    st.add_row("Total cost", f"${summary['cost_usd']['total']:.4f}")
    st.add_row("Throughput", f"{summary['throughput_qpm']} q/min")
    st.add_row("Success rate", f"{summary['success_rate']}%")
    console.print(st)

    qt = Table(title="Per-Query Results", show_header=True)
    qt.add_column("#", justify="right")
    qt.add_column("Query", max_width=50)
    qt.add_column("Depth")
    qt.add_column("TTFF", justify="right")
    qt.add_column("Total", justify="right")
    qt.add_column("Cost", justify="right")

    for i, r in enumerate(results):
        query_trunc = r["query"][:50] + ("..." if len(r["query"]) > 50 else "")
        if r.get("success"):
            ttff = f"{r.get('ttff', '?')}s"
            total_t = f"{r.get('total_time', '?')}s"
            cost = f"${r.get('cost_usd', 0) or 0:.4f}"
            style = ""
        else:
            ttff = "FAIL"
            total_t = "FAIL"
            cost = "-"
            style = "red"
        qt.add_row(str(i + 1), query_trunc, r["depth"], ttff, total_t, cost, style=style)

    console.print(qt)


def generate(results_dir: str) -> None:
    """Generate benchmark report from raw results."""
    results = _load_raw_results(results_dir)
    if not results:
        console.print("[red]No raw result files found.[/red]")
        return

    summary = compute_summary(results)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = Path(results_dir)

    md_path = output_path / f"report_{timestamp}.md"
    csv_path = output_path / f"report_{timestamp}.csv"

    md_content = _build_markdown(results, summary, results_dir)
    _atomic_write_text(md_path, md_content)
    _write_csv(csv_path, results)

    _print_rich_table(results, summary)

    console.print(f"\n[green]Report saved:[/green]")
    console.print(f"  Markdown: {md_path}")
    console.print(f"  CSV:      {csv_path}")

"""Stage-by-stage progress display using rich.live."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from .cortex_cli import BLUE, DIM, GREEN

# ── Stage metadata ───────────────────────────────────────────────────────────

_STAGE_LABELS: dict[str, str] = {
    "planning": "Planning",
    "gathering": "Gathering",
    "gap_detection": "Gap detection",
    "synthesizing": "Synthesizing",
    "verifying": "Verifying",
    "memory": "Memory",
}

# Events that complete the "Synthesizing" row instead of creating a new one.
_COMPLETES_SYNTHESIZING = {"synthesis"}


def _format_label(event_name: str, data: dict[str, Any]) -> str:
    """Human-readable stage label."""
    if event_name == "gathering":
        pass_num = data.get("pass", 1)
        return f"Gathering (pass {pass_num})"
    return _STAGE_LABELS.get(event_name, event_name.replace("_", " ").title())


def _extract_metric(event_name: str, data: dict[str, Any]) -> str:
    """Short metric string for a completed stage."""
    if event_name == "planning":
        n = len(data.get("sub_questions", []))
        return f"{n} sub-questions"
    if event_name == "gathering":
        n = data.get("sources_found", 0)
        return f"{n} sources"
    if event_name == "gap_detection":
        gaps = data.get("gaps", [])
        return f"{len(gaps)} gaps" if gaps else "no gaps"
    if event_name in ("synthesizing", "synthesis"):
        return "done"
    if event_name == "verifying":
        c = data.get("confirmed", 0)
        w = data.get("weakened", 0)
        return f"{c} confirmed, {w} weakened"
    if event_name == "memory":
        n = data.get("chunks_stored", 0)
        return f"{n} chunks stored"
    return ""


# ── Data ─────────────────────────────────────────────────────────────────────


@dataclass
class _Stage:
    label: str
    metric: str = ""
    elapsed: float = 0.0
    completed: bool = False
    started_at: float = field(default_factory=time.monotonic)


# ── Renderable ───────────────────────────────────────────────────────────────


class _ProgressRenderable:
    """Rich renderable that draws all stages."""

    def __init__(self, stages: list[_Stage], width: int) -> None:
        self._stages = stages
        self._width = width
        self._spinner = Spinner("dots", style=BLUE)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        for stage in self._stages:
            if stage.completed:
                yield self._render_complete(stage)
            else:
                yield self._render_active(stage)

    def _render_complete(self, stage: _Stage) -> Text:
        diamond = Text("  ◆ ", style=BLUE)
        label = Text(stage.label, style=BLUE)
        elapsed_str = f"{stage.elapsed:.1f}s"
        metric = Text(f"  {stage.metric}", style=DIM)
        timing = Text(f"  {elapsed_str}", style=DIM)
        return Text.assemble(diamond, label, metric, timing)

    def _render_active(self, stage: _Stage) -> Text:
        diamond = Text("  ◇ ", style=BLUE)
        label = Text(stage.label, style=BLUE)
        dots = Text("  ...", style=DIM)
        return Text.assemble(diamond, label, dots)


# ── Public API ───────────────────────────────────────────────────────────────


class ProgressDisplay:
    """Manages a live-updating stage progress display."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._stages: list[_Stage] = []
        self._width = min(console.width, 60)
        self._live = Live(
            _ProgressRenderable(self._stages, self._width),
            console=console,
            refresh_per_second=10,
            transient=False,
        )

    def start(self) -> None:
        self._live.start()

    def stop(self) -> None:
        self._live.stop()

    def handle_event(self, event_name: str, data: dict[str, Any]) -> None:
        """Process an SSE event and update the display."""
        if event_name == "complete":
            self._complete_active()
            self._refresh()
            return

        # "synthesis" completes the existing "Synthesizing" row.
        if event_name in _COMPLETES_SYNTHESIZING:
            self._complete_active(metric=_extract_metric(event_name, data))
            self._refresh()
            return

        # Complete previous active stage, then start a new one.
        self._complete_active(metric="")
        label = _format_label(event_name, data)
        metric = _extract_metric(event_name, data)

        stage = _Stage(label=label)
        self._stages.append(stage)
        self._refresh()

        # For events that arrive with their data already complete,
        # immediately mark them done (all except synthesizing).
        if event_name != "synthesizing":
            stage.completed = True
            stage.elapsed = time.monotonic() - stage.started_at
            stage.metric = metric
            self._refresh()

    def _complete_active(self, metric: str | None = None) -> None:
        """Mark the current active (last incomplete) stage as done."""
        for stage in reversed(self._stages):
            if not stage.completed:
                stage.completed = True
                stage.elapsed = time.monotonic() - stage.started_at
                if metric is not None:
                    stage.metric = metric
                break

    def _refresh(self) -> None:
        self._live.update(_ProgressRenderable(self._stages, self._width))

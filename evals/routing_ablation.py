"""Experiment B: routing ablation over the frozen corpus.

Hypothesis (mechanism form): routing bounded, structured-output stages
(planning, gap detection) to a small model does not degrade final document
quality, while cutting large-model token throughput.

Two configs run the plan → gap-detect → synthesize → verify chain per fixture
query, selected purely through the LOCAL_MODEL_* env-map surface — no
pipeline code changes:
- ROUTED: planning + gap detection on the small model, synthesis +
  verification on the decode model.
- MONO:   all four stages on the decode model.

Stated limitation: search is frozen, so plan differences flow only into the
synthesis prompt (sub-question list), not into retrieval.

Quality is judged blind and pairwise (ROUTED vs MONO per query) by the judge
model, position-swapped: each pair is judged A/B and B/A, and counts as a win
only when both orderings agree; otherwise it is a tie.

Usage:
    python -m evals.routing_ablation --resume       # run everything (resumable)
    python -m evals.routing_ablation --limit 2      # smoke: first 2 queries
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

os.environ["LLM_BACKEND"] = "local"  # must win before backend.config is imported

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from backend.config import settings  # noqa: E402
from backend.llm.openai_compat_client import OpenAICompatLLMClient  # noqa: E402
from backend.pipeline.gap_detector import detect_gaps  # noqa: E402
from backend.pipeline.planner import plan  # noqa: E402
from backend.pipeline.synthesizer import synthesize  # noqa: E402
from backend.pipeline.verifier import verify  # noqa: E402
from evals.judge import JUDGE_MODEL, ensure_context, ollama_json  # noqa: E402
from evals.verifier_ablation import load_fixtures, _write_json  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("evals.routing_ablation")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RESULTS_DIR = _REPO_ROOT / "benchmarks" / "results" / "routing_ablation"

_SEED = 42
_SMALL_MODEL = os.environ.get("ROUTING_SMALL_MODEL", "llama3.2:3b")
_DECODE_MODEL = os.environ.get("ROUTING_DECODE_MODEL", "qwen3:8b")
_JUDGE_DOC_CHARS = 12_000

CONFIGS: dict[str, dict[str, str]] = {
    "routed": {
        "PLANNING": _SMALL_MODEL,
        "GAP_DETECTION": _SMALL_MODEL,
        "SYNTHESIS": _DECODE_MODEL,
        "VERIFICATION": _DECODE_MODEL,
    },
    "mono": {
        "PLANNING": _DECODE_MODEL,
        "GAP_DETECTION": _DECODE_MODEL,
        "SYNTHESIS": _DECODE_MODEL,
        "VERIFICATION": _DECODE_MODEL,
    },
}

_PAIRWISE_SYSTEM = """\
You are a strict evaluator of research documents. Given a research query and two candidate documents A and B, decide which better answers the query.

Criteria, in order of importance:
1. Factual grounding — claims are supported and carry inline citations [N]
2. Coverage — how completely the query is answered
3. Citation discipline — no uncited factual claims, no orphan citations
4. Clarity and structure

Judge only what is in the documents. Respond with a single JSON object:
{"winner": "A" | "B" | "tie", "reason": "<one sentence>"}"""


def _apply_config(models: dict[str, str]) -> None:
    for task, model in models.items():
        setattr(settings, f"LOCAL_MODEL_{task}", model)


async def _run_stage(name: str, coro, client: OpenAICompatLLMClient, stats: dict):
    """Run one pipeline stage, recording tokens, retries, and failures."""
    client.reset_usage()
    result, failed = None, False
    try:
        result = await coro
    except (ValueError, json.JSONDecodeError) as exc:
        failed = True
        logger.error("stage %s failed: %s", name, exc)
    usage = client.get_usage()
    stats[name] = {
        "model": next(iter(client.get_usage_by_model()), None),
        **usage,
        "json_retries": client.json_retries,
        "failed": failed,
    }
    return result


async def run_configs(fixtures: list[dict]) -> None:
    for config_name, models in CONFIGS.items():
        config_dir = _RESULTS_DIR / config_name
        config_dir.mkdir(parents=True, exist_ok=True)
        _apply_config(models)
        client = OpenAICompatLLMClient(temperature=0.0, seed=_SEED)
        try:
            for fx in fixtures:
                name = fx["name"]
                doc_path = config_dir / f"{name}_verified.md"
                stats_path = config_dir / f"{name}_stats.json"
                if doc_path.exists() and stats_path.exists():
                    continue
                logger.info("[%s] %s: running pipeline stages…", config_name, name)
                stats: dict = {"config": config_name, "models": models}

                research_plan = await _run_stage(
                    "planning", plan(fx["query"], client=client), client, stats
                )
                # Keep downstream comparable when a plan fails outright: fall
                # back to the fixture's single sub-question, flagged in stats.
                sub_questions = research_plan.sub_questions if research_plan else fx["sub_questions"]
                stats["plan_fallback"] = research_plan is None

                await _run_stage(
                    "gap_detection",
                    detect_gaps(sub_questions, fx["sources"], client=client),
                    client,
                    stats,
                )

                document = await _run_stage(
                    "synthesis",
                    synthesize(fx["query"], sub_questions, fx["sources"], client=client),
                    client,
                    stats,
                )
                if document is None:
                    _write_json(stats_path, stats)
                    continue

                verification = await _run_stage(
                    "verification", verify(document, fx["sources"], client=client), client, stats
                )
                _write_json(stats_path, stats)
                if verification is not None:
                    doc_path.write_text(verification.verified_document)
        finally:
            await client.close()


async def judge_pairs(fixtures: list[dict]) -> None:
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=10.0)) as http:
        for fx in fixtures:
            name = fx["name"]
            pair_path = _RESULTS_DIR / f"{name}_pairwise.json"
            if pair_path.exists():
                continue
            routed_path = _RESULTS_DIR / "routed" / f"{name}_verified.md"
            mono_path = _RESULTS_DIR / "mono" / f"{name}_verified.md"
            if not routed_path.exists() or not mono_path.exists():
                logger.warning("%s: missing verified document(s) — skipping pair", name)
                continue
            routed_doc = routed_path.read_text()[:_JUDGE_DOC_CHARS]
            mono_doc = mono_path.read_text()[:_JUDGE_DOC_CHARS]

            async def _ask(doc_a: str, doc_b: str) -> str:
                user = (
                    f"RESEARCH QUERY: {fx['query']}\n\n"
                    f"DOCUMENT A:\n{doc_a}\n\n"
                    f"DOCUMENT B:\n{doc_b}"
                )
                data = await ollama_json(http, _PAIRWISE_SYSTEM, user, max_tokens=256)
                winner = str(data.get("winner", "tie")).strip().upper()
                return winner if winner in ("A", "B") else "TIE"

            logger.info("%s: pairwise judging (both orderings)…", name)
            first = await _ask(routed_doc, mono_doc)   # A=routed, B=mono
            second = await _ask(mono_doc, routed_doc)  # A=mono, B=routed

            if first == "A" and second == "B":
                outcome = "routed"
            elif first == "B" and second == "A":
                outcome = "mono"
            else:
                outcome = "tie"
            _write_json(pair_path, {
                "outcome": outcome,
                "ordering_1_routed_first": first,
                "ordering_2_mono_first": second,
            })


def compute_metrics(fixtures: list[dict]) -> dict:
    wtl = {"routed": 0, "tie": 0, "mono": 0}
    decode_tokens = {"routed": 0, "mono": 0}
    reliability: dict[str, dict] = {}
    per_query = []

    for fx in fixtures:
        name = fx["name"]
        row: dict = {"query": name}
        pair_path = _RESULTS_DIR / f"{name}_pairwise.json"
        if pair_path.exists():
            pair = json.loads(pair_path.read_text())
            wtl[pair["outcome"]] += 1
            row["pairwise"] = pair["outcome"]
        for config_name in CONFIGS:
            stats_path = _RESULTS_DIR / config_name / f"{name}_stats.json"
            if not stats_path.exists():
                continue
            stats = json.loads(stats_path.read_text())
            for stage in ("planning", "gap_detection", "synthesis", "verification"):
                s = stats.get(stage)
                if not s:
                    continue
                bucket = reliability.setdefault(config_name, {}).setdefault(
                    stage, {"json_retries": 0, "failures": 0, "calls": 0}
                )
                bucket["json_retries"] += s["json_retries"]
                bucket["failures"] += int(s["failed"])
                bucket["calls"] += s["calls"]
                if s.get("model") == _DECODE_MODEL:
                    decode_tokens[config_name] += s["input_tokens"] + s["output_tokens"]
        per_query.append(row)

    ratio = (
        round(decode_tokens["routed"] / decode_tokens["mono"], 4)
        if decode_tokens["mono"] else None
    )
    metrics = {
        "models": {"small": _SMALL_MODEL, "decode": _DECODE_MODEL, "judge": JUDGE_MODEL},
        "temperature": 0.0,
        "seed": _SEED,
        "pairwise_w_t_l": wtl,
        "decode_model_tokens": decode_tokens,
        "decode_token_ratio_routed_over_mono": ratio,
        "decode_tokens_moved_off_pct": round((1 - ratio) * 100, 2) if ratio is not None else None,
        "reliability": reliability,
        "frozen_search_note": (
            "search is frozen to the corpus fixtures; plan differences flow only "
            "into the synthesis prompt, not into retrieval"
        ),
        "per_query": per_query,
    }
    _write_json(_RESULTS_DIR / "metrics.json", metrics)
    return metrics


def print_metrics(metrics: dict) -> None:
    w = metrics["pairwise_w_t_l"]
    print(f"\npairwise (blind, position-swapped): ROUTED {w['routed']} / TIE {w['tie']} / MONO {w['mono']}")
    print(f"decode-model tokens — routed: {metrics['decode_model_tokens']['routed']}, mono: {metrics['decode_model_tokens']['mono']}")
    print(f"ratio routed/mono: {metrics['decode_token_ratio_routed_over_mono']}  (moved off decode model: {metrics['decode_tokens_moved_off_pct']}%)")
    print("\nreliability (json_retries/failures per stage):")
    for config_name, stages in metrics["reliability"].items():
        for stage, s in stages.items():
            print(f"  {config_name:<8}{stage:<15}retries={s['json_retries']}  failures={s['failures']}  calls={s['calls']}")


async def run(limit: int | None) -> None:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = load_fixtures(limit)
    logger.info("running routing ablation over %d fixtures", len(fixtures))
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)) as http:
        await ensure_context(http)
    await run_configs(fixtures)
    await judge_pairs(fixtures)
    print_metrics(compute_metrics(fixtures))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true", help="resume (default behavior — flag kept for documentation)")
    parser.add_argument("--limit", type=int, default=None, help="only the first N fixtures")
    args = parser.parse_args()
    asyncio.run(run(args.limit))


if __name__ == "__main__":
    main()

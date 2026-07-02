"""Experiment A: verifier ablation over the frozen corpus.

Hypothesis under test: a verification pass measurably reduces unsupported /
overclaimed content. For every fixture query, synthesize() runs on the frozen
sources (arm RAW), verify() runs on that document (arm VERIFIED), and an
independent judge model scores every cited claim against only its cited
source content. All inference is local (Ollama); everything is resumable —
each artifact is skipped when its output file already exists.

Usage:
    python -m evals.verifier_ablation --resume          # generate, judge, metrics
    python -m evals.verifier_ablation --limit 2         # smoke: first 2 queries
    python -m evals.verifier_ablation --sample-labels   # write human-labeling CSVs
    python -m evals.verifier_ablation --agreement       # judge–human agreement stats
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import random
import re
import sys
from pathlib import Path

os.environ["LLM_BACKEND"] = "local"  # must win before backend.config is imported

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from backend.llm.openai_compat_client import OpenAICompatLLMClient  # noqa: E402
from backend.models import Source, SubQuestion  # noqa: E402
from backend.pipeline.synthesizer import synthesize  # noqa: E402
from backend.pipeline.verifier import verify  # noqa: E402
from evals.judge import JUDGE_MODEL, ensure_context, judge_claim  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("evals.verifier_ablation")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FIXTURE_DIR = _REPO_ROOT / "evals" / "fixtures" / "corpus"
_RESULTS_DIR = _REPO_ROOT / "benchmarks" / "results" / "verifier_ablation"
_LABELS_DIR = _REPO_ROOT / "evals" / "labels"

_SEED = 42
_JACCARD_THRESHOLD = 0.6

# ── Claim extraction ─────────────────────────────────────────────────────

_CITATION_RE = re.compile(r"\[(\d{1,2})\]")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_SOURCES_HEADING = re.compile(r"^#{1,6}\s*(?:\d+[.)]\s*)?sources\b.*$", re.IGNORECASE | re.MULTILINE)
_MD_DECOR = re.compile(r"^[#>\s]*(?:[-*+]\s+)?(?:\d+[.)]\s+)?")


def document_body(document: str) -> str:
    """Everything before the trailing Sources section."""
    matches = list(_SOURCES_HEADING.finditer(document))
    return document[: matches[-1].start()] if matches else document


def extract_claims(document: str) -> list[dict]:
    """Cited claims = sentences containing [N] markers, with their source ids."""
    claims: list[dict] = []
    for line in document_body(document).splitlines():
        line = _MD_DECOR.sub("", line).strip()
        if not line:
            continue
        for sentence in _SENT_SPLIT.split(line):
            sentence = sentence.strip()
            ids = sorted({int(m) for m in _CITATION_RE.findall(sentence)})
            if ids:
                claims.append({"claim": sentence, "source_ids": ids})
    return claims


def citation_count(document: str) -> int:
    return len(_CITATION_RE.findall(document_body(document)))


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", _CITATION_RE.sub("", text.lower())))


def jaccard(a: str, b: str) -> float:
    sa, sb = _token_set(a), _token_set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ── Fixtures ─────────────────────────────────────────────────────────────

def load_fixtures(limit: int | None = None) -> list[dict]:
    fixtures = []
    for path in sorted(_FIXTURE_DIR.glob("q*.json")):
        raw = json.loads(path.read_text())
        fixtures.append({
            "name": path.stem,
            "query": raw["query"],
            "sub_questions": [SubQuestion(**sq) for sq in raw["sub_questions"]],
            "sources": [Source(**s) for s in raw["sources"]],
        })
    return fixtures[:limit] if limit else fixtures


def ranked_sources(sources: list[Source]) -> list[Source]:
    """The exact citation-number ordering used by synthesizer and verifier."""
    return sorted(sources, key=lambda s: (-s.relevance_score, s.url))


def _write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(path)


# ── Arm generation ───────────────────────────────────────────────────────

async def generate_arms(fixtures: list[dict]) -> None:
    client = OpenAICompatLLMClient(temperature=0.0, seed=_SEED)
    try:
        for fx in fixtures:
            name = fx["name"]
            raw_path = _RESULTS_DIR / f"{name}_raw.md"
            verified_path = _RESULTS_DIR / f"{name}_verified.md"
            verification_path = _RESULTS_DIR / f"{name}_verification.json"
            error_path = _RESULTS_DIR / f"{name}_error.txt"

            if not raw_path.exists():
                logger.info("%s: synthesizing RAW arm…", name)
                document = await synthesize(
                    fx["query"], fx["sub_questions"], fx["sources"], client=client
                )
                raw_path.write_text(document)
            raw_document = raw_path.read_text()

            if not verified_path.exists() and not error_path.exists():
                logger.info("%s: running verifier (VERIFIED arm)…", name)
                try:
                    result = await verify(raw_document, fx["sources"], client=client)
                except (ValueError, json.JSONDecodeError) as exc:
                    logger.error("%s: verifier failed: %s", name, exc)
                    error_path.write_text(f"verify() failed: {exc}\n")
                    continue
                verified_path.write_text(result.verified_document)
                _write_json(verification_path, result.summary.model_dump())
    finally:
        await client.close()


# ── Judging ──────────────────────────────────────────────────────────────

def _sources_block(ids: list[int], ranked: list[Source]) -> tuple[str, bool]:
    """Cited source content for the judge; flags citations with no target."""
    blocks: list[str] = []
    invalid = False
    for n in ids:
        if 1 <= n <= len(ranked):
            s = ranked[n - 1]
            blocks.append(f"SOURCE [{n}] ({s.title}):\n{s.full_content or s.snippet}")
        else:
            invalid = True
    return "\n\n".join(blocks), invalid


async def judge_all(fixtures: list[dict]) -> None:
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)) as http:
        for fx in fixtures:
            name = fx["name"]
            judged_path = _RESULTS_DIR / f"{name}_judged.json"
            if judged_path.exists():
                continue
            raw_path = _RESULTS_DIR / f"{name}_raw.md"
            verified_path = _RESULTS_DIR / f"{name}_verified.md"
            if not raw_path.exists() or not verified_path.exists():
                logger.warning("%s: arms incomplete — skipping judging", name)
                continue

            ranked = ranked_sources(fx["sources"])
            judged: dict = {"judge_model": JUDGE_MODEL}

            for arm, path in (("raw", raw_path), ("verified", verified_path)):
                results = []
                claims = extract_claims(path.read_text())
                logger.info("%s/%s: judging %d claims…", name, arm, len(claims))
                for item in claims:
                    block, invalid = _sources_block(item["source_ids"], ranked)
                    if invalid and not block:
                        verdict = {"verdict": "unsupported", "reason": "citation points to a nonexistent source"}
                    else:
                        verdict = await judge_claim(http, item["claim"], block)
                    results.append({**item, **verdict, "invalid_citation": invalid})
                judged[arm] = results

            # Verifier precision probe: judge the claims the verifier itself
            # marked confirmed, against the source it says they cite.
            verification_path = _RESULTS_DIR / f"{name}_verification.json"
            confirmed_results = []
            if verification_path.exists():
                details = json.loads(verification_path.read_text()).get("details", [])
                confirmed = [d for d in details if d.get("verdict") == "confirmed"]
                logger.info("%s: judging %d verifier-confirmed claims…", name, len(confirmed))
                for d in confirmed:
                    block, invalid = _sources_block([d["source_id"]], ranked)
                    if invalid and not block:
                        verdict = {"verdict": "unsupported", "reason": "citation points to a nonexistent source"}
                    else:
                        verdict = await judge_claim(http, d["claim"], block)
                    confirmed_results.append({"claim": d["claim"], "source_ids": [d["source_id"]], **verdict, "invalid_citation": invalid})
            judged["verifier_confirmed"] = confirmed_results

            _write_json(judged_path, judged)


# ── Metrics ──────────────────────────────────────────────────────────────

def compute_metrics(fixtures: list[dict]) -> dict:
    per_query = []
    totals = {arm: {"supported": 0, "partial": 0, "unsupported": 0} for arm in ("raw", "verified")}
    confirmed_total = {"supported": 0, "partial": 0, "unsupported": 0}
    verify_failures = []

    for fx in fixtures:
        name = fx["name"]
        if (_RESULTS_DIR / f"{name}_error.txt").exists():
            verify_failures.append(name)
            continue
        judged_path = _RESULTS_DIR / f"{name}_judged.json"
        raw_path = _RESULTS_DIR / f"{name}_raw.md"
        verified_path = _RESULTS_DIR / f"{name}_verified.md"
        if not judged_path.exists():
            continue
        judged = json.loads(judged_path.read_text())
        raw_doc = raw_path.read_text()
        verified_doc = verified_path.read_text()

        row: dict = {"query": name}
        for arm in ("raw", "verified"):
            counts = {"supported": 0, "partial": 0, "unsupported": 0}
            for item in judged[arm]:
                counts[item["verdict"]] += 1
                totals[arm][item["verdict"]] += 1
            n = sum(counts.values())
            row[arm] = {
                "claims": n,
                **counts,
                "overclaim_rate": round((counts["partial"] + counts["unsupported"]) / n, 4) if n else None,
            }
        for item in judged["verifier_confirmed"]:
            confirmed_total[item["verdict"]] += 1

        # Safety invariants of the verifier itself.
        raw_claims = extract_claims(raw_doc)
        invented = 0
        for item in judged["verified"]:
            best = max((jaccard(item["claim"], rc["claim"]) for rc in raw_claims), default=0.0)
            if best < _JACCARD_THRESHOLD:
                invented += 1
        row["length_ratio"] = round(len(verified_doc) / len(raw_doc), 4) if raw_doc else None
        row["citation_delta"] = citation_count(verified_doc) - citation_count(raw_doc)
        row["invented_claims"] = invented
        per_query.append(row)

    def _overall(counts: dict) -> dict:
        n = sum(counts.values())
        return {
            "claims": n,
            **counts,
            "overclaim_rate": round((counts["partial"] + counts["unsupported"]) / n, 4) if n else None,
        }

    n_confirmed = sum(confirmed_total.values())
    metrics = {
        "generator_models": {
            "synthesis": os.environ.get("LOCAL_MODEL_SYNTHESIS", "qwen3:8b"),
            "verification": os.environ.get("LOCAL_MODEL_VERIFICATION", "qwen3:8b"),
        },
        "judge_model": JUDGE_MODEL,
        "temperature": 0.0,
        "seed": _SEED,
        "n_queries_judged": len(per_query),
        "verify_failures": verify_failures,
        "overall": {arm: _overall(totals[arm]) for arm in ("raw", "verified")},
        "verifier_precision": round(confirmed_total["supported"] / n_confirmed, 4) if n_confirmed else None,
        "verifier_confirmed_judged": {**confirmed_total, "total": n_confirmed},
        "length_ratio_min": min((r["length_ratio"] for r in per_query if r["length_ratio"]), default=None),
        "invented_claims_total": sum(r["invented_claims"] for r in per_query),
        "per_query": per_query,
    }
    _write_json(_RESULTS_DIR / "metrics.json", metrics)
    return metrics


def print_metrics(metrics: dict) -> None:
    print(f"\nqueries judged: {metrics['n_queries_judged']}  verify failures: {metrics['verify_failures'] or 'none'}")
    print(f"{'arm':<10}{'claims':>8}{'supported':>11}{'partial':>9}{'unsupported':>13}{'overclaim':>11}")
    for arm in ("raw", "verified"):
        o = metrics["overall"][arm]
        print(f"{arm:<10}{o['claims']:>8}{o['supported']:>11}{o['partial']:>9}{o['unsupported']:>13}{o['overclaim_rate'] if o['overclaim_rate'] is not None else '—':>11}")
    print(f"\nverifier precision (judge-supported / verifier-confirmed): {metrics['verifier_precision']}")
    print(f"min length ratio: {metrics['length_ratio_min']}   invented claims: {metrics['invented_claims_total']}")


# ── Human labeling ───────────────────────────────────────────────────────

def sample_labels(target: int = 100) -> None:
    """Stratified sample of judged claims into a labeling CSV (verdicts hidden)."""
    pool: dict[str, list[dict]] = {"supported": [], "partial": [], "unsupported": []}
    fixtures = {fx["name"]: fx for fx in load_fixtures()}
    for judged_path in sorted(_RESULTS_DIR.glob("q*_judged.json")):
        name = judged_path.name.split("_")[0]
        judged = json.loads(judged_path.read_text())
        ranked = ranked_sources(fixtures[name]["sources"])
        for arm in ("raw", "verified"):
            for i, item in enumerate(judged[arm]):
                block, _ = _sources_block(item["source_ids"], ranked)
                pool[item["verdict"]].append({
                    "claim_id": f"{name}:{arm}:{i}",
                    "claim": item["claim"],
                    "source_excerpt": block[:1500],
                    "judge_verdict": item["verdict"],
                })

    total = sum(len(v) for v in pool.values())
    rng = random.Random(_SEED)
    sampled: list[dict] = []
    for verdict, items in pool.items():
        if not items:
            continue
        share = max(10, round(target * len(items) / total)) if len(items) >= 10 else len(items)
        sampled.extend(rng.sample(items, min(share, len(items))))
    rng.shuffle(sampled)
    sampled = sampled[:target + 10]

    _LABELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(_LABELS_DIR / "to_label.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["claim_id", "claim", "source_excerpt", "my_label"])
        writer.writeheader()
        for row in sampled:
            writer.writerow({k: row.get(k, "") for k in ("claim_id", "claim", "source_excerpt")} | {"my_label": ""})
    with open(_LABELS_DIR / "judge_verdicts_hidden.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["claim_id", "judge_verdict"])
        writer.writeheader()
        for row in sampled:
            writer.writerow({"claim_id": row["claim_id"], "judge_verdict": row["judge_verdict"]})
    print(f"wrote {len(sampled)} claims to {_LABELS_DIR / 'to_label.csv'} (judge verdicts hidden separately)")


def agreement() -> None:
    """Judge–human agreement %, Cohen's kappa, and a confusion table."""
    human: dict[str, str] = {}
    with open(_LABELS_DIR / "to_label.csv") as f:
        for row in csv.DictReader(f):
            label = row["my_label"].strip().lower()
            if label:
                human[row["claim_id"]] = label
    judge: dict[str, str] = {}
    with open(_LABELS_DIR / "judge_verdicts_hidden.csv") as f:
        for row in csv.DictReader(f):
            judge[row["claim_id"]] = row["judge_verdict"]

    ids = [cid for cid in human if cid in judge]
    if not ids:
        print("no labeled rows found — fill my_label in to_label.csv first")
        return
    labels = ("supported", "partial", "unsupported")
    bad = {cid: human[cid] for cid in ids if human[cid] not in labels}
    if bad:
        print(f"unrecognized labels (use supported/partial/unsupported): {bad}")
        return

    n = len(ids)
    agree = sum(1 for cid in ids if human[cid] == judge[cid])
    po = agree / n
    pe = sum(
        (sum(1 for c in ids if judge[c] == lab) / n) * (sum(1 for c in ids if human[c] == lab) / n)
        for lab in labels
    )
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0

    confusion = {j: {h: 0 for h in labels} for j in labels}
    for cid in ids:
        confusion[judge[cid]][human[cid]] += 1

    result = {"n_labeled": n, "agreement": round(po, 4), "cohens_kappa": round(kappa, 4), "confusion_judge_rows_human_cols": confusion}
    _write_json(_LABELS_DIR / "agreement.json", result)

    print(f"n={n}  agreement={po:.1%}  Cohen's kappa={kappa:.3f}")
    print(f"{'judge \\ human':<16}" + "".join(f"{lab:>13}" for lab in labels))
    for j in labels:
        print(f"{j:<16}" + "".join(f"{confusion[j][h]:>13}" for h in labels))

    metrics_path = _RESULTS_DIR / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())
        metrics["human_agreement"] = result
        _write_json(metrics_path, metrics)


# ── Entrypoint ───────────────────────────────────────────────────────────

async def run(limit: int | None) -> None:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = load_fixtures(limit)
    logger.info("running verifier ablation over %d fixtures", len(fixtures))
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)) as http:
        await ensure_context(http)
    await generate_arms(fixtures)
    await judge_all(fixtures)
    print_metrics(compute_metrics(fixtures))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true", help="resume (default behavior — flag kept for documentation)")
    parser.add_argument("--limit", type=int, default=None, help="only the first N fixtures")
    parser.add_argument("--sample-labels", action="store_true")
    parser.add_argument("--agreement", action="store_true")
    args = parser.parse_args()

    if args.sample_labels:
        sample_labels()
    elif args.agreement:
        agreement()
    else:
        asyncio.run(run(args.limit))


if __name__ == "__main__":
    main()

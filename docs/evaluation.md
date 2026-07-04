# Evaluation

This document reports two experiments that test Cortex's load-bearing claims
on committed data with committed code. Everything here runs offline on local
open-weight models — no API keys, no inference spend — and every number traces
back to an artifact in `benchmarks/results/`. The findings validate the
pipeline's *mechanisms*; they are measured on local 3B–8B models, not the
Claude models the project was originally developed against, so they do not
reproduce vendor-specific cost or quality figures. See *Threats to validity*.

## Setup

**Hardware.** Apple M4 (fanless MacBook Air), 24 GB unified memory, macOS
26.5.1. All models served locally by [Ollama](https://ollama.com) over its
OpenAI-compatible API at `http://localhost:11434/v1`.

**Models** (Ollama tags, `Q4_K_M` quantization):

| Role | Model | Digest | Params | Notes |
|------|-------|--------|--------|-------|
| Planning, gap detection (small) | `llama3.2:3b` | `a80c4f17acd5` | 3.2B | bounded JSON stages |
| Synthesis, verification (decode) | `qwen2.5:7b-instruct` | *(see `ollama show`)* | 7B | see model-choice note |
| Judge | `llama3.1:8b` | `46e0c10c039e` | 8.0B | different family from the generator |

**Model-choice note.** The generator was intended to be `qwen3:8b`. In
practice its reasoning-style decoding runs to the token cap when asked to
regenerate an entire document as a single JSON object — the verifier's
contract — yielding truncated, unparseable JSON. `qwen2.5:7b-instruct` (the
project's sanctioned non-reasoning fallback) returns valid JSON with sensible
verdicts in a few minutes per document, so it is the tested decode model. This
is archival evaluation infrastructure, not a change to the product: the
Reference (Claude API) configuration is unchanged.

**Decoding.** Temperature 0 and a fixed seed (42) on every call. Ollama's
context window is raised to 16,384 tokens (`OLLAMA_CONTEXT_LENGTH=16384`); its
4,096 default silently truncates the 6–10k-token synthesis and verification
prompts, so both harnesses preflight the window and abort loudly if it is too
small.

**Thermal pacing.** Sustained back-to-back generation drives this fanless
machine into deep thermal throttle (measured: ~19 tok/s collapsing to ~0.3
tok/s after roughly eight minutes of continuous load, with no recovery until
load stops). The harnesses insert a configurable cooldown between expensive
generation calls (`EVAL_COOLDOWN_S`, default 60s) to hold the chip in its
healthy band. This changes wall-clock only, not results.

**Corpus.** A frozen evidence pool of 20 queries (from `benchmarks/queries.py`)
under `evals/fixtures/corpus/`, one fixture per query, built once by
`scripts/build_corpus.py` from a hand-curated, license-reviewed URL list
(Wikipedia CC BY-SA, official docs, arXiv abstracts, canonical GitHub READMEs;
see `evals/fixtures/ATTRIBUTION.md`). Sources are capped at 2,000 characters
and reranked with the pipeline's own cross-encoder so `relevance_score` matches
runtime. Freezing the corpus isolates the LLM-stage variables under test from
search variance. Build provenance is in `evals/fixtures/corpus/manifest.json`.

## Method

### Experiment A — verifier ablation

**Claim under test.** A verification pass reduces unsupported/overclaimed
content — rigor at synthesis time beats volume at gather time. Locally we test
the first half: does verification measurably reduce unsupported content?

- **Arms.** For each fixture query, `synthesize()` runs on the frozen sources
  to produce arm **RAW**; `verify()` runs on that document to produce arm
  **VERIFIED**. Both documents and the verifier's own summary are persisted per
  query.
- **Claim extraction.** Cited claims are sentences containing `[N]` citation
  markers (multi-citation sentences handled); each claim keeps its cited source
  ids.
- **Judging.** Every extracted claim is judged `supported | partial |
  unsupported` by `llama3.1:8b` — a different model family from the generator —
  given only the claim and the content of its cited source(s), at temperature
  0. Judging uses direct HTTP calls (`evals/judge.py`), never the pipeline
  client, so the judge is independent of the system under test.
- **Metrics.** Overclaim rate per arm (share judged `partial|unsupported`);
  verifier precision (of claims the verifier marked `confirmed`, the share the
  judge marks `supported`); and the verifier's own safety invariants —
  VERIFIED/RAW length ratio, citation-count delta, and an invented-content
  count (claims in VERIFIED with no ≥0.6 Jaccard-token-overlap counterpart in
  RAW).
- **Human anchor.** A stratified ~100-claim sample is hand-labeled blind (judge
  verdicts held in a separate file); agreement %, Cohen's kappa, and a
  per-verdict confusion table bound the judge's reliability.

### Experiment B — routing ablation

**Claim under test.** Routing bounded, structured-output stages (planning, gap
detection) to a small model does not degrade final document quality while
cutting large-model token throughput.

- **Configs**, selected purely through the `LOCAL_MODEL_*` env map (no pipeline
  code changes): **ROUTED** runs planning + gap detection on `llama3.2:3b` and
  synthesis + verification on the decode model; **MONO** runs all four stages
  on the decode model.
- **Quality.** Blind pairwise judging of the final verified documents (ROUTED
  vs MONO per query) by the judge model, position-swapped — each pair is judged
  A/B and B/A, and counts as a win only when both orderings agree, else a tie.
- **Cost proxy.** Share of decode-model tokens in ROUTED vs MONO, from the
  client's per-model accounting (no fabricated dollar figure).
- **Reliability.** JSON-parse retry and failure counts per stage per config.
- **Stated limitation.** Search is frozen, so plan differences flow only into
  the synthesis prompt (the sub-question list), not into retrieval.

## Results

### Experiment A — verifier ablation

17 of 20 queries completed; 3 verifies (q01, q09, q11) produced invalid JSON
and are excluded (see *Failure cases*). Judge: `llama3.1:8b`. Source data:
`benchmarks/results/verifier_ablation/metrics.json`.

| Arm | Cited claims | Supported | Partial | Unsupported | Overclaim rate |
|-----|-------------|-----------|---------|-------------|----------------|
| RAW (pre-verification) | 91 | 47 | 19 | 25 | **48.4%** |
| VERIFIED (post-verification) | 91 | 46 | 20 | 25 | **49.5%** |

**The verification pass did not reduce overclaiming.** The overclaim rate was
flat-to-slightly-worse, and per query the two arms were near-identical: of the
14 queries with cited claims, 13 had an *identical* overclaim rate before and
after verification; the one that changed (q07) got worse (0.43 → 0.57). This
is a negative result for the mechanism on local 3B–8B models. It does not
reproduce — and is not evidence for — the original Claude-specific development
observation that verification catches more hallucinations than extra search;
that claim is labeled as unbenchmarked in the README.

**Verifier precision: 0.49.** Of 80 claims the verifier itself marked
`confirmed`, the independent judge rated only 39 `supported` (14 `partial`, 27
`unsupported`). The verifier's confirmations are close to a coin flip against
an independent reader.

**Safety invariants.** No invented content (0 claims in any VERIFIED document
lacked a ≥0.6 Jaccard match in its RAW counterpart). Citation counts were
stable (delta 0 on all but q07, which dropped 2). But the VERIFIED/RAW length
ratio ranged down to **0.685** (q08), i.e. the verifier dropped nearly a third
of the document — see *Failure cases* and the guard note below.

**Human agreement.** 99 claims were sampled stratified across verdicts and
hand-labeled blind (judge verdicts held separately). Six were flagged
un-adjudicable — the cited source excerpt was empty or boilerplate, including
two claims (q05) that cite a source index the fixture does not contain — and
are excluded. Over the remaining **93**, the judge agreed with the human on
**59.1%**, Cohen's kappa **0.326** ("fair"):

| judge ↓ / human → | supported | partial | unsupported |
|-------------------|-----------|---------|-------------|
| **supported**     | 34 | 9 | 8 |
| **partial**       | 9 | 6 | 5 |
| **unsupported**   | 5 | 2 | 15 |

The judge is a noisy adjudicator — it over-calls `supported` (17 claims it
passed were partial or unsupported to the human), and the `partial` middle
category is where most disagreement sits. This bounds the results above two
ways. The **absolute** overclaim rates (~48%) are only as trustworthy as
kappa 0.33 allows and should be read as approximate. But the **central
finding** — that RAW and VERIFIED overclaim rates are near-identical — is
robust to judge noise, because both arms are scored by the same judge and any
systematic judge bias cancels in the within-pair comparison. In other words:
even a fair-only judge is enough to show that verification did not move the
needle, though not enough to pin the needle's exact position.

**Calibration disclosure.** Four of the 93 labels — `q13:raw:0`, `q06:raw:2`,
`q05:verified:9`, `q06:raw:3` — were adjudicated in discussion with an LLM
assistant during annotator calibration, before the rest were labeled solo and
blind; they are not fully independent human judgments. Recomputing over the
committed labels without these four (n=89) gives 58.4% agreement and Cohen's
kappa 0.318, against 59.1% and 0.326 over the full 93. The delta is within
rounding and changes nothing above: the judge remains a fair-only adjudicator,
and the within-pair comparison that carries the central result is unaffected.

### Experiment B — routing ablation

Configs: ROUTED (planning + gap detection on `llama3.2:3b`, synthesis +
verification on `qwen2.5:7b-instruct`) vs MONO (all four stages on
`qwen2.5:7b-instruct`). Judge: `llama3.1:8b`. Source data:
`benchmarks/results/routing_ablation/metrics.json`.

**Quality — routing did not degrade the final document.** Blind
position-swapped pairwise judging over the 14 queries where both configs
produced a valid document (6 excluded — one config's verify failed, see
reliability):

| Outcome | Count |
|---------|-------|
| ROUTED wins (both orderings agree) | 1 |
| Tie | 13 |
| MONO wins | 0 |

Thirteen of fourteen pairs were judged equivalent and the one decisive pair
favored ROUTED. Sending the bounded, structured-output stages to a 3B model
cost nothing measurable in final quality.

**Cost — ~10% of decode-model tokens moved off the large model.** ROUTED spent
249,562 tokens on `qwen2.5:7b-instruct` against MONO's 277,931 (ratio 0.898),
i.e. **10.2%** of large-model throughput shifted to the small model. The
saving is bounded because synthesis and verification — which stay on the
decode model in both configs — dominate the token budget; only planning and
gap detection move. No dollar figure is claimed.

**Reliability — the small model handled the bounded stages flawlessly.** Across
40 planning and 40 gap-detection calls on `llama3.2:3b`, there were zero JSON
retries and zero failures. Every failure fell in the verification stage
(whole-document regeneration) regardless of config: ROUTED 5/20, MONO 1/20.
This reinforces Experiment A — the fragile part is the verifier's
one-completion design, not the model size of the bounded stages.

**Caveat (stated limitation).** Search is frozen, so the two configs differ
only in the planning output feeding the synthesis prompt, not in what was
retrieved. That the ROUTED plans (from a 3B model) yielded documents judged
equal to MONO's is the finding; it does not exercise plan quality's effect on
retrieval.

## Failure cases

**The verifier fabricates its summary counts.** 12 of the 17 verifier summaries
reported the exact numbers printed in the prompt's JSON schema *example* —
`confirmed: 15, weakened: 2, removed: 1` — across unrelated documents with
different claim counts. The small model copies the illustration instead of
counting. This alone makes the verifier's self-reported summary untrustworthy
on local models, independent of the judge.

**It confirms unsupported claims.** In q00 the verifier marked as `confirmed`
the claim *"RAG improves the reliability of generated text by mitigating 'gen
AI hallucinations'"*; the judge, reading the cited source, found it *"does not
mention anything related to 'gen AI hallucinations' or the reliability of
generated text."* This is the precision=0.49 result made concrete.

**It silently truncates.** On q08 the verified document was 3,743 characters
against the RAW document's 5,464 — a 0.685 length ratio, nearly a third of the
content dropped, with no error raised. Because the measured minimum fell below
0.7, `verify()` now guards against this: when the regenerated document is under
70% of the original length it logs a warning and returns the unverified
document instead of shipping a truncated one. The metrics above record the
pre-guard behavior — they are the evidence for the guard.

**It fails outright ~15% of the time — persistently.** 3 of 20 verifies (q01,
q09, q11) never produced a usable result, and re-running them with the client's
JSON-retry budget raised to 3 attempts did not recover any: they fail for
structural reasons, not transient noise. Two distinct signatures appeared:
q01 emitted malformed JSON on every attempt (the model degenerated into a
whitespace-repetition loop and truncated mid-object); q09 and q11 emitted
*well-formed* JSON that simply omitted the required `summary` object. Both are
failure modes of asking a small model to regenerate an entire document as a
single JSON completion. They are recorded as error files and excluded from the
tables above, not silently dropped.

## Threats to validity

- **Judge-model bias.** A single model family judges claims; position-swapped
  pairwise comparison cancels order bias, and the human-agreement stats
  (agreement %, Cohen's kappa) bound how far the judge can be trusted. The
  judge is a different family (`llama3.1`) from the generator (`qwen2.5`) to
  reduce self-preference.
- **Frozen search.** The corpus is fixed, so Experiment B's plan differences
  never reach retrieval — a stated, not hidden, limitation. It isolates the
  synthesis/verification variables at the cost of not exercising the gather
  loop.
- **External validity.** All numbers come from local 3B–8B open-weight models,
  not the Claude models the original project targeted. They validate the
  pipeline's mechanisms — does verification reduce overclaiming, does routing
  preserve quality — not vendor-specific cost or quality magnitudes.
- **Small n.** 20 queries is enough to show direction, not to publish tight
  confidence intervals.

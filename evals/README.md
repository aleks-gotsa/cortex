# Evals

Offline, reproducible evaluation of the pipeline's two load-bearing claims,
run entirely on local models — zero API keys, zero inference spend.

- **Experiment A — verifier ablation** (`evals/verifier_ablation.py`): does the
  verification pass measurably reduce unsupported/overclaimed content? Every
  cited claim in the pre-verification (RAW) and post-verification (VERIFIED)
  documents is judged against only its cited source content by a judge model
  from a different family than the generator. Also probes the verifier's own
  safety invariants: output/input length ratio, citation-count delta, and
  invented-content count.
- **Experiment B — routing ablation** (`evals/routing_ablation.py`): does
  routing the bounded, structured-output stages (planning, gap detection) to a
  small model degrade final document quality? Blind pairwise judging,
  position-swapped so order bias cancels; also reports the share of tokens
  moved off the large model and per-stage JSON reliability.

Both experiments run over the frozen evidence corpus in `evals/fixtures/`
(committed; see `ATTRIBUTION.md` for every source URL and license basis), at
temperature 0 with a fixed seed, and are resumable — rerunning skips every
artifact that already exists.

Stated limitation: search is frozen to the corpus, so plan differences in
Experiment B flow only into the synthesis prompt, not into retrieval.

## Reproduction

Prereqs: [Ollama](https://ollama.com), Python 3.12, ~15 GB free memory.

```bash
# 1. Models (~12 GB of downloads)
ollama pull qwen3:8b       # decode/generator
ollama pull llama3.2:3b    # prefill/small
ollama pull llama3.1:8b    # judge (different family from the generator)

# 2. Ollama must serve a ≥16k-token context window — its 4,096 default
#    silently truncates these prompts. Both harnesses preflight this and
#    abort with instructions when the window is too small.
launchctl setenv OLLAMA_CONTEXT_LENGTH 16384   # macOS app; then restart Ollama
# (or run the server directly: OLLAMA_CONTEXT_LENGTH=16384 ollama serve)

# 3. Python deps
pip install -r requirements.txt

# 4. Validate the committed corpus (no network needed)
python scripts/build_corpus.py --check

# 5. Experiment A (hours on laptop hardware; resumable — rerun to continue)
python -m evals.verifier_ablation --resume

# 6. Experiment B (hours; resumable)
python -m evals.routing_ablation --resume
```

Results land in `benchmarks/results/verifier_ablation/metrics.json` and
`benchmarks/results/routing_ablation/metrics.json`. Every intermediate
artifact — both document arms, per-claim judgments, pairwise verdicts,
per-stage token stats — is persisted alongside, so any number in
`docs/evaluation.md` can be traced back to its inputs.

## Human labels (credibility anchor for the judge)

```bash
python -m evals.verifier_ablation --sample-labels   # writes evals/labels/to_label.csv
# … fill the my_label column (supported | partial | unsupported) …
python -m evals.verifier_ablation --agreement       # agreement %, Cohen's kappa, confusion table
```

Judge verdicts are kept in a separate hidden file so labeling stays blind.

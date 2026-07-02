"""Build the frozen evidence corpus for offline evals.

No-search-key path: scrapes a hand-curated, licensing-reviewed URL list per
benchmark query with the existing crawl4ai scraper, chunks each page into
Source objects (full_content capped at 2,000 chars), reranks locally with
the pipeline's cross-encoder so relevance_score is honest, and writes one
fixture per query to evals/fixtures/corpus/q{NN}.json plus a manifest and
an ATTRIBUTION.md.

Resumable: fixtures that already exist are skipped unless --force is given.

Usage:
    python scripts/build_corpus.py            # build missing fixtures
    python scripts/build_corpus.py --check    # validate fixtures, print stats
    python scripts/build_corpus.py --force    # rebuild everything
"""

import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmarks.queries import QUERIES  # noqa: E402
from backend.models import Source, SubQuestion  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CORPUS_DIR = _REPO_ROOT / "evals" / "fixtures" / "corpus"
_ATTRIBUTION_PATH = _REPO_ROOT / "evals" / "fixtures" / "ATTRIBUTION.md"
_MANIFEST_PATH = _CORPUS_DIR / "manifest.json"

_MAX_CHUNK_CHARS = 2000
_MAX_SOURCES_PER_QUERY = 12
_MAX_CHUNKS_PER_PAGE = 4
_TARGET_MIN_SOURCES = 8

# Successful scrapes are cached outside the repo so iterating on chunking
# never re-fetches (and never hammers) the origin sites.
_SCRAPE_CACHE_DIR = Path.home() / ".cache" / "cortex-corpus"

# (url, short title, kind, license basis) per query index. Hand-curated and
# link-checked; every entry lands in evals/fixtures/ATTRIBUTION.md.
_WIKI = "CC BY-SA 4.0"
_ARXIV = "arXiv abstract page, quoted with attribution"
_HF_DOCS = "official Apache-2.0 project docs"
_VENDOR = "vendor documentation, short excerpt with attribution"

CORPUS_SOURCES: dict[int, list[tuple[str, str, str, str]]] = {
    0: [
        ("https://en.wikipedia.org/wiki/Retrieval-augmented_generation", "Retrieval-augmented generation — Wikipedia", "wikipedia", _WIKI),
        ("https://arxiv.org/abs/2005.11401", "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks — arXiv", "paper-abstract", _ARXIV),
        ("https://huggingface.co/docs/transformers/model_doc/rag", "RAG — Hugging Face Transformers docs", "official-docs", _HF_DOCS),
        ("https://cloud.google.com/use-cases/retrieval-augmented-generation", "What is Retrieval-Augmented Generation? — Google Cloud", "official-docs", _VENDOR),
    ],
    1: [
        ("https://en.wikipedia.org/wiki/Attention_(machine_learning)", "Attention (machine learning) — Wikipedia", "wikipedia", _WIKI),
        ("https://arxiv.org/abs/1706.03762", "Attention Is All You Need — arXiv", "paper-abstract", _ARXIV),
        ("https://d2l.ai/chapter_attention-mechanisms-and-transformers/index.html", "Attention Mechanisms and Transformers — Dive into Deep Learning", "official-docs", "open-source textbook (CC BY-SA), short excerpt with attribution"),
        ("https://nlp.seas.harvard.edu/annotated-transformer/", "The Annotated Transformer — Harvard NLP", "official-docs", "MIT-licensed project page, short excerpt with attribution"),
    ],
    2: [
        ("https://en.wikipedia.org/wiki/GPT-4", "GPT-4 — Wikipedia", "wikipedia", _WIKI),
        ("https://en.wikipedia.org/wiki/Claude_(language_model)", "Claude (language model) — Wikipedia", "wikipedia", _WIKI),
        ("https://docs.anthropic.com/en/docs/about-claude/models/overview", "Models overview — Anthropic docs", "official-docs", _VENDOR),
        ("https://arxiv.org/abs/2303.08774", "GPT-4 Technical Report — arXiv", "paper-abstract", _ARXIV),
        ("https://platform.openai.com/docs/models/gpt-4", "GPT-4 — OpenAI Platform docs", "official-docs", _VENDOR),
    ],
    3: [
        ("https://docs.nvidia.com/dynamo/design-docs/disaggregated-serving", "Disaggregated Serving — NVIDIA Dynamo design docs", "official-docs", _VENDOR),
        ("https://github.com/ai-dynamo/dynamo", "ai-dynamo/dynamo — GitHub README", "github-readme", "official Apache-2.0 project README"),
        ("https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/", "Introducing NVIDIA Dynamo — NVIDIA Developer Blog", "vendor-blog", "canonical vendor engineering blog, short excerpt with attribution"),
        ("https://arxiv.org/abs/2401.09670", "DistServe: Disaggregating Prefill and Decoding — arXiv", "paper-abstract", _ARXIV),
    ],
    4: [
        ("https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)", "Transformer (deep learning architecture) — Wikipedia", "wikipedia", _WIKI),
        ("https://huggingface.co/docs/transformers/kv_cache", "KV cache strategies — Hugging Face Transformers docs", "official-docs", _HF_DOCS),
        ("https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/", "Mastering LLM Techniques: Inference Optimization — NVIDIA Developer Blog", "vendor-blog", "canonical vendor engineering blog, short excerpt with attribution"),
        ("https://arxiv.org/abs/2309.06180", "Efficient Memory Management for LLM Serving with PagedAttention — arXiv", "paper-abstract", _ARXIV),
    ],
    5: [
        ("https://en.wikipedia.org/wiki/Vector_database", "Vector database — Wikipedia", "wikipedia", _WIKI),
        ("https://qdrant.tech/documentation/overview/", "Qdrant documentation overview", "official-docs", "official Apache-2.0 project docs"),
        ("https://weaviate.io/developers/weaviate/concepts/vector-index", "Vector indexing — Weaviate docs", "official-docs", "official BSD-3 project docs"),
        ("https://arxiv.org/abs/1603.09320", "Efficient and robust approximate nearest neighbor search using HNSW — arXiv", "paper-abstract", _ARXIV),
    ],
    6: [
        ("https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)", "Transformer (deep learning architecture) — Wikipedia", "wikipedia", _WIKI),
        ("https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/", "Mastering LLM Techniques: Inference Optimization — NVIDIA Developer Blog", "vendor-blog", "canonical vendor engineering blog, short excerpt with attribution"),
        ("https://docs.vllm.ai/en/latest/features/disagg_prefill.html", "Disaggregated prefill — vLLM docs", "official-docs", "official Apache-2.0 project docs"),
        ("https://docs.nvidia.com/dynamo/user-guides/disaggregated-serving", "Disaggregated serving — NVIDIA Dynamo user guide", "official-docs", _VENDOR),
    ],
    7: [
        ("https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/architecture.html", "Triton architecture — NVIDIA Triton user guide", "official-docs", _VENDOR),
        ("https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html", "Triton Inference Server — NVIDIA user guide index", "official-docs", _VENDOR),
        ("https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/model_repository.html", "Model repository — NVIDIA Triton user guide", "official-docs", _VENDOR),
        ("https://github.com/triton-inference-server/server", "triton-inference-server/server — GitHub README", "github-readme", "official BSD-3 project README"),
    ],
    8: [
        ("https://en.wikipedia.org/wiki/MLOps", "MLOps — Wikipedia", "wikipedia", _WIKI),
        ("https://huggingface.co/docs/text-generation-inference/index", "Text Generation Inference — Hugging Face docs", "official-docs", _HF_DOCS),
        ("https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/concept-llmops-maturity", "LLMOps maturity model — Microsoft Learn", "official-docs", _VENDOR),
        ("https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/", "Mastering LLM Techniques: Inference Optimization — NVIDIA Developer Blog", "vendor-blog", "canonical vendor engineering blog, short excerpt with attribution"),
    ],
    9: [
        ("https://en.wikipedia.org/wiki/Reinforcement_learning_from_human_feedback", "Reinforcement learning from human feedback — Wikipedia", "wikipedia", _WIKI),
        ("https://huggingface.co/blog/rlhf", "Illustrating RLHF — Hugging Face blog", "vendor-blog", "canonical Hugging Face engineering blog, short excerpt with attribution"),
        ("https://huggingface.co/docs/trl/ppo_trainer", "PPO Trainer — Hugging Face TRL docs", "official-docs", _HF_DOCS),
        ("https://arxiv.org/abs/2203.02155", "Training language models to follow instructions (InstructGPT) — arXiv", "paper-abstract", _ARXIV),
    ],
    10: [
        ("https://en.wikipedia.org/wiki/Speculative_decoding", "Speculative decoding — Wikipedia", "wikipedia", _WIKI),
        ("https://docs.vllm.ai/en/latest/features/spec_decode.html", "Speculative decoding — vLLM docs", "official-docs", "official Apache-2.0 project docs"),
        ("https://arxiv.org/abs/2211.17192", "Fast Inference from Transformers via Speculative Decoding — arXiv", "paper-abstract", _ARXIV),
        ("https://huggingface.co/blog/assisted-generation", "Assisted generation — Hugging Face blog", "vendor-blog", "canonical Hugging Face engineering blog, short excerpt with attribution"),
    ],
    11: [
        ("https://en.wikipedia.org/wiki/FlashAttention", "FlashAttention — Wikipedia", "wikipedia", _WIKI),
        ("https://arxiv.org/abs/2205.14135", "FlashAttention: Fast and Memory-Efficient Exact Attention — arXiv", "paper-abstract", _ARXIV),
        ("https://github.com/Dao-AILab/flash-attention", "Dao-AILab/flash-attention — GitHub README", "github-readme", "official BSD-3 project README"),
        ("https://huggingface.co/docs/transformers/perf_infer_gpu_one", "GPU inference — Hugging Face Transformers docs", "official-docs", _HF_DOCS),
    ],
    12: [
        ("https://huggingface.co/docs/optimum/concept_guides/quantization", "Quantization concepts — Hugging Face Optimum docs", "official-docs", _HF_DOCS),
        ("https://docs.pytorch.org/docs/stable/quantization.html", "Quantization — PyTorch docs", "official-docs", "official BSD-3 project docs"),
        ("https://arxiv.org/abs/2106.08295", "A White Paper on Neural Network Quantization — arXiv", "paper-abstract", _ARXIV),
    ],
    13: [
        ("https://en.wikipedia.org/wiki/Mixture_of_experts", "Mixture of experts — Wikipedia", "wikipedia", _WIKI),
        ("https://huggingface.co/blog/moe", "Mixture of Experts Explained — Hugging Face blog", "vendor-blog", "canonical Hugging Face engineering blog, short excerpt with attribution"),
        ("https://arxiv.org/abs/1701.06538", "Outrageously Large Neural Networks (sparse MoE) — arXiv", "paper-abstract", _ARXIV),
        ("https://arxiv.org/abs/2401.04088", "Mixtral of Experts — arXiv", "paper-abstract", _ARXIV),
    ],
    14: [
        ("https://en.wikipedia.org/wiki/List_of_large_language_models", "List of large language models — Wikipedia", "wikipedia", _WIKI),
        ("https://huggingface.co/docs/leaderboards/open_llm_leaderboard/about", "Open LLM Leaderboard — Hugging Face docs", "official-docs", _HF_DOCS),
        ("https://github.com/deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-V3 — GitHub README", "github-readme", "official MIT-licensed project README"),
        ("https://github.com/QwenLM/Qwen3", "QwenLM/Qwen3 — GitHub README", "github-readme", "official Apache-2.0 project README"),
    ],
    15: [
        ("https://docs.nvidia.com/nim/large-language-models/latest/introduction.html", "NIM for LLMs: introduction — NVIDIA docs", "official-docs", _VENDOR),
        ("https://docs.nvidia.com/nim/large-language-models/latest/getting-started.html", "NIM for LLMs: getting started — NVIDIA docs", "official-docs", _VENDOR),
        ("https://developer.nvidia.com/blog/nvidia-nim-offers-optimized-inference-microservices-for-deploying-ai-models-at-scale/", "NVIDIA NIM inference microservices — NVIDIA Developer Blog", "vendor-blog", "canonical vendor engineering blog, short excerpt with attribution"),
    ],
    16: [
        ("https://en.wikipedia.org/wiki/Large_language_model", "Large language model — Wikipedia", "wikipedia", _WIKI),
        ("https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/", "Mastering LLM Techniques: Inference Optimization — NVIDIA Developer Blog", "vendor-blog", "canonical vendor engineering blog, short excerpt with attribution"),
        ("https://docs.vllm.ai/en/latest/configuration/optimization.html", "Optimization and tuning — vLLM docs", "official-docs", "official Apache-2.0 project docs"),
        ("https://arxiv.org/abs/2309.06180", "Efficient Memory Management for LLM Serving with PagedAttention — arXiv", "paper-abstract", _ARXIV),
    ],
    17: [
        ("https://www.anyscale.com/blog/continuous-batching-llm-inference", "Continuous batching in LLM inference — Anyscale blog", "vendor-blog", "canonical vendor engineering blog, short excerpt with attribution"),
        ("https://en.wikipedia.org/wiki/VLLM", "vLLM — Wikipedia", "wikipedia", _WIKI),
        ("https://www.usenix.org/conference/osdi22/presentation/yu", "Orca: A Distributed Serving System (OSDI '22) — USENIX abstract", "paper-abstract", "USENIX abstract page, quoted with attribution"),
        ("https://arxiv.org/abs/2309.06180", "Efficient Memory Management for LLM Serving with PagedAttention — arXiv", "paper-abstract", _ARXIV),
    ],
    18: [
        ("https://docs.pytorch.org/tutorials/intermediate/TP_tutorial.html", "Large Scale Transformer model training with Tensor Parallel — PyTorch tutorials", "official-docs", "official BSD-3 project docs"),
        ("https://docs.vllm.ai/en/stable/serving/parallelism_scaling.html", "Parallelism and scaling — vLLM docs", "official-docs", "official Apache-2.0 project docs"),
        ("https://github.com/NVIDIA/Megatron-LM", "NVIDIA/Megatron-LM — GitHub README", "github-readme", "official BSD-3 project README"),
        ("https://arxiv.org/abs/1909.08053", "Megatron-LM: Training Multi-Billion Parameter Models — arXiv", "paper-abstract", _ARXIV),
    ],
    19: [
        ("https://en.wikipedia.org/wiki/VLLM", "vLLM — Wikipedia", "wikipedia", _WIKI),
        ("https://docs.vllm.ai/en/latest/design/paged_attention/", "PagedAttention design — vLLM docs", "official-docs", "official Apache-2.0 project docs"),
        ("https://blog.vllm.ai/2023/06/20/vllm.html", "vLLM: Easy, Fast, and Cheap LLM Serving — vLLM blog", "vendor-blog", "canonical project blog, short excerpt with attribution"),
        ("https://arxiv.org/abs/2309.06180", "Efficient Memory Management for LLM Serving with PagedAttention — arXiv", "paper-abstract", _ARXIV),
    ],
}


def _cache_path(url: str) -> Path:
    import hashlib

    return _SCRAPE_CACHE_DIR / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".md")


# Everything before these site-specific markers is header chrome, not content.
_CONTENT_START_MARKERS = {
    "wikipedia.org": "From Wikipedia, the free encyclopedia",
    "arxiv.org": "Title:",
    "github.com": "Repository files navigation",
}


def _strip_chrome(text: str, url: str) -> str:
    for domain, marker in _CONTENT_START_MARKERS.items():
        if domain in url:
            idx = text.find(marker)
            if idx >= 0:
                return text[idx + len(marker):]
    return text


def _strip_links(text: str) -> str:
    """Reduce markdown links/images to their anchor text.

    Scraped markdown spends most of its characters on URLs; stripping them
    keeps the 2,000-char content budget for actual prose. Source URLs stay
    on the Source objects and in ATTRIBUTION.md.
    """
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"https?://\S+", "", text)


def _chunk_markdown(text: str) -> list[str]:
    """Greedily pack paragraphs into chunks of at most _MAX_CHUNK_CHARS."""
    paragraphs = [p.strip() for p in _strip_links(text).split("\n\n") if p.strip()]
    chunks: list[str] = []
    buffer: list[str] = []
    size = 0
    for para in paragraphs:
        para = para[:_MAX_CHUNK_CHARS]
        if size + len(para) + 2 > _MAX_CHUNK_CHARS and buffer:
            chunks.append("\n\n".join(buffer))
            buffer, size = [], 0
        buffer.append(para)
        size += len(para) + 2
    if buffer:
        chunks.append("\n\n".join(buffer))
    return chunks


def _is_substantive(chunk: str) -> bool:
    """Filter out navigation chunks that survive scraping.

    After link stripping, nav blocks decay into stacks of 1-4 word lines
    ("Main menu", "Contents", …) while prose keeps long lines — so average
    words-per-line separates them cleanly.
    """
    words = len(chunk.split())
    if words < 40:
        return False
    if "arXivLabs: experimental projects" in chunk:  # arXiv footer boilerplate
        return False
    lines = [ln for ln in chunk.splitlines() if ln.strip()]
    if not lines:
        return False
    # Bare file/commit tables (GitHub repo chrome) are pipe-heavy without prose.
    if sum(1 for ln in lines if ln.lstrip().startswith("|")) / len(lines) > 0.6:
        return False
    if words / len(lines) >= 8:
        return True
    # Code-heavy tutorial chunks have short lines but real sentences around
    # the code; nav stacks have neither.
    return len(re.findall(r"[.!?](?:\s|$)", chunk)) >= 3


async def _build_fixture(index: int, query: str, scraped: dict[str, str | None]) -> dict:
    """Assemble one fixture dict from pre-scraped page content."""
    from backend.pipeline.gatherer import _rerank

    entries = CORPUS_SOURCES[index]
    candidates: list[Source] = []
    failed_urls: list[str] = []

    for url, title, _kind, _license in entries:
        content = scraped.get(url)
        if not content:
            failed_urls.append(url)
            continue
        chunks = [c for c in _chunk_markdown(_strip_chrome(content, url)) if _is_substantive(c)]
        for i, chunk in enumerate(chunks):
            part = f" (part {i + 1})" if len(chunks) > 1 else ""
            snippet = " ".join(chunk.split())[:200]
            candidates.append(
                Source(
                    url=url,
                    title=title + part,
                    snippet=snippet,
                    full_content=chunk,
                    relevance_score=0.0,
                    sub_question_id="sq1",
                    search_engine="fixture",
                )
            )

    # Rerank every candidate chunk, then keep the top slice with a per-page
    # cap so one long page cannot crowd out the rest.
    ranked = _rerank(query, candidates)
    sources: list[Source] = []
    per_url: dict[str, int] = {}
    for src in ranked:
        if per_url.get(src.url, 0) >= _MAX_CHUNKS_PER_PAGE:
            continue
        per_url[src.url] = per_url.get(src.url, 0) + 1
        sources.append(src)
        if len(sources) >= _MAX_SOURCES_PER_QUERY:
            break

    return {
        "index": index,
        "query": query,
        "sub_questions": [
            SubQuestion(id="sq1", question=query, search_terms=[]).model_dump()
        ],
        "sources": [s.model_dump() for s in sources],
        "failed_urls": failed_urls,
    }


async def build(force: bool = False) -> None:
    from backend.search.scraper import scrape_many

    _CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    pending: list[tuple[int, str]] = []
    for index, item in enumerate(QUERIES):
        fixture_path = _CORPUS_DIR / f"q{index:02d}.json"
        if fixture_path.exists() and not force:
            print(f"skip q{index:02d} (exists)")
            continue
        pending.append((index, item["query"]))

    if pending:
        urls = list(dict.fromkeys(
            url for index, _ in pending for url, *_ in CORPUS_SOURCES[index]
        ))
        scraped: dict[str, str | None] = {}
        to_fetch: list[str] = []
        for url in urls:
            cached = _cache_path(url)
            if cached.exists():
                scraped[url] = cached.read_text()
            else:
                to_fetch.append(url)
        print(f"{len(urls) - len(to_fetch)} cached, scraping {len(to_fetch)} URLs for {len(pending)} fixtures…")
        if to_fetch:
            # The pipeline's 4,000-char cap keeps prompts small at runtime;
            # fixture pages need far more room — Wikipedia/GitHub body text
            # starts 13-16k characters in, after the navigation chrome.
            fetched = await scrape_many(to_fetch, max_concurrent=5, max_chars=60_000)
            for url, content in fetched.items():
                if content:
                    _SCRAPE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    _cache_path(url).write_text(content)
                scraped[url] = content

        for index, query in pending:
            fixture = await _build_fixture(index, query, scraped)
            path = _CORPUS_DIR / f"q{index:02d}.json"
            path.write_text(json.dumps(fixture, indent=2, ensure_ascii=False))
            n = len(fixture["sources"])
            flag = "" if n >= _TARGET_MIN_SOURCES else "  ⚠ under target"
            print(f"built q{index:02d}: {n} sources, {len(fixture['failed_urls'])} failed urls{flag}")

    _write_attribution()
    _write_manifest()


def _write_attribution() -> None:
    lines = [
        "# Corpus attribution",
        "",
        "Every source URL in `corpus/` with its license basis. Content excerpts",
        "are capped at 2,000 characters per source and are included solely as",
        "frozen evaluation fixtures for this repository.",
        "",
    ]
    for index in sorted(CORPUS_SOURCES):
        lines.append(f"## q{index:02d} — {QUERIES[index]['query']}")
        lines.append("")
        for url, title, kind, license_basis in CORPUS_SOURCES[index]:
            lines.append(f"- {url} — {title} ({kind}; {license_basis})")
        lines.append("")
    _ATTRIBUTION_PATH.write_text("\n".join(lines))
    print(f"wrote {_ATTRIBUTION_PATH.relative_to(_REPO_ROOT)}")


def _write_manifest() -> None:
    entries = []
    total_sources = 0
    total_bytes = 0
    for path in sorted(_CORPUS_DIR.glob("q*.json")):
        fixture = json.loads(path.read_text())
        n = len(fixture["sources"])
        total_sources += n
        total_bytes += path.stat().st_size
        entries.append({
            "file": path.name,
            "query": fixture["query"],
            "n_sources": n,
            "failed_urls": fixture.get("failed_urls", []),
        })
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "n_queries": len(entries),
        "total_sources": total_sources,
        "total_bytes": total_bytes,
        "max_chunk_chars": _MAX_CHUNK_CHARS,
        "queries": entries,
    }
    _MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"wrote manifest: {len(entries)} fixtures, {total_sources} sources, {total_bytes / 1024:.0f} KiB")


def check() -> int:
    """Validate every fixture against the Pydantic models; print corpus stats."""
    failures = 0
    counts: list[int] = []
    total_bytes = 0
    fixture_paths = sorted(_CORPUS_DIR.glob("q*.json"))
    if not fixture_paths:
        print("no fixtures found — run scripts/build_corpus.py first")
        return 1

    for path in fixture_paths:
        fixture = json.loads(path.read_text())
        total_bytes += path.stat().st_size
        try:
            assert fixture["query"] == QUERIES[fixture["index"]]["query"], "query/index mismatch with benchmarks/queries.py"
            for sq in fixture["sub_questions"]:
                SubQuestion(**sq)
            sources = [Source(**s) for s in fixture["sources"]]
            assert sources, "no sources"
            for s in sources:
                assert s.full_content and len(s.full_content) <= _MAX_CHUNK_CHARS, f"full_content cap violated for {s.url}"
            counts.append(len(sources))
            status = "ok" if len(sources) >= _TARGET_MIN_SOURCES else "ok (under target)"
            print(f"{path.name}: {len(sources):2d} sources — {status}")
        except Exception as exc:  # noqa: BLE001 — report every invalid fixture
            failures += 1
            print(f"{path.name}: INVALID — {exc}")

    print(
        f"\ncorpus: {len(fixture_paths)} fixtures, {sum(counts)} sources "
        f"(min {min(counts)}, max {max(counts)}), {total_bytes / 1024:.0f} KiB total"
    )
    if total_bytes > 2 * 1024 * 1024:
        print("WARNING: corpus exceeds 2 MB budget")
        failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    asyncio.run(build(force="--force" in sys.argv))

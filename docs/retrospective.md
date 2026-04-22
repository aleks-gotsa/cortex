# Cortex: Six Months Building a Deep Research Engine

### What Cortex is

Cortex is a multi-pass research pipeline. A query flows through six stages: a planner decomposes it into sub-questions (Haiku), a gatherer fans out across Serper and Tavily and scrapes results with crawl4ai, a reranker (ms-marco-MiniLM cross-encoder, local) scores the candidate pool, a gap detector runs coverage analysis (Sonnet) and either triggers another gather pass or promotes the evidence forward, a synthesizer writes a document with inline citations (Sonnet), and a verifier checks every citation against its source (Sonnet). The final document, its sources, and small embedded chunks get written to a Qdrant collection so future runs can pull prior context. Model routing is explicit: planning and gap detection on Haiku, synthesis and verification on Sonnet. The frontend is a Next.js app consuming an SSE stream from a FastAPI backend; the same pipeline is exposed through a CLI and an MCP server.

### Why I built it

The original hypothesis was that existing AI search tools — Perplexity, ChatGPT with browsing, various Copilot-style extensions — are shallow in a specific, consistent way. They do one search pass, they let the model cite without checking, and they have no memory of what you researched yesterday. For casual questions this is fine. For actual investigative work — anything where you are building a position over days, or where a wrong citation costs you real credibility — the shallowness shows up as false confidence. You read a plausible summary and you cannot tell which parts are load-bearing and which parts the model made up.

The bet was that three things, composed, would close that gap. First, multi-pass search with explicit gap detection, so that the second and third passes go after what the first pass actually missed rather than repeating the first pass at higher temperature. Second, claim-level verification against the retrieved sources, so that the synthesizer's habit of over-claiming gets corrected before the document reaches the user. Third, cross-session memory, so that the second time you ask about a topic you are building on the first time rather than re-running cold. Each piece alone is a known idea. The bet was on the composition.

### What worked better than expected

**The verification pass was the most impactful stage by a wide margin.** My initial assumption was that more search volume was the way to improve output quality — if the synthesizer was making things up, it must be because there was not enough grounding. This turned out to be wrong. Looking at the verifier's output across real queries, the dominant failure mode was not missing evidence; it was the synthesizer subtly overstating what the evidence said. `backend/pipeline/verifier.py` walks each cited claim in the document, finds the matching source in the pool, and classifies the claim as confirmed, weakened, or unsupported. A surprising fraction of synthesized claims came back weakened — the source did say *something* about the topic, but the synthesizer had generalized past what was on the page. Adding a fourth gather pass would not have caught any of that. A single verification pass caught most of it.

**Haiku-for-planning, Sonnet-for-synthesis cut cost 3-4x with no quality loss I could measure.** Planning and gap detection are bounded tasks — they take a query and produce structured JSON. Haiku handles that cleanly. Synthesis and verification are unbounded — they need to produce and scrutinize long prose. Sonnet earns its price there. The router is a fifteen-line file; the savings are enormous. I expected some quality regression and did not see one.

**Verifying at claim granularity beat reviewing at document granularity.** An earlier iteration had the verifier read the whole document and return "looks good" or "needs revision." That was useless — the verdict had no leverage. Dropping to per-claim verdicts with an explicit source ID ("claim X cites source 3; does source 3 support it?") turned verification into a mechanical task that the model could actually do well. Granularity converted a judgment call into a lookup.

### What did not work

**End-to-end latency.** Individual stages are reasonable — a planning call completes in a couple of seconds, synthesis in ten or fifteen. But six stages compose, and in deep mode you do the gatherer twice more. A thirty-to-ninety-second total wait is genuinely fine for a long investigation, and genuinely terrible for the in-between case where you have a half-formed question and just want to poke at it. The UX problem is not the absolute time; it is that the tool forces you to commit to a heavy interaction before you know whether the question is worth that commitment.

**I stopped using my own tool.** This is the clearest signal I have. Somewhere around the third month I noticed I was reaching for ChatGPT for quick lookups and only opening Cortex for explicitly-framed research sessions. Over the next month the explicitly-framed sessions got rarer too. By month five I was maintaining a system I was not using. That is diagnostic information. A tool whose author does not use it daily has a fit problem, not a capability problem.

**The depth selector is a UX tax.** The frontend asks the user to choose quick, standard, or deep before the query runs. This sounded like user control when I designed it; in practice it is asking the user to predict how hard their own question is before they have seen any evidence. The right behavior is to start with one pass, inspect coverage, and escalate automatically. The depth selector exists because the gap detector was built second and I did not refactor the UI around it.

### One technical insight worth keeping

Cross-session memory in a Qdrant-backed RAG works well as an explicit recall tool and works poorly as automatic pipeline context. This is not what I expected going in, and it took a while to see clearly.

The orchestrator, in `backend/pipeline/orchestrator.py`, takes a `use_memory` flag. When it is on, the very first thing the pipeline does is call `recall(query)` against the Qdrant collection, pull the top chunks from prior research, and hand them to the planner as `prior_context`. The intent was that the system should always benefit from what it already knew. In practice, this created uncontrolled context drift. If I had researched topic A in depth on Monday and asked a different, adjacent question on Tuesday, Monday's chunks would bleed into Tuesday's planner prompt and bias the sub-questions toward Monday's framing. The effect was subtle — the output still looked fine — but the research was quietly narrower than it should have been. The more prior research the system had, the worse the drift got.

The MCP server, by contrast, exposes `recall` as its own tool at `mcp_server.py` alongside `research`. From Claude Desktop or any MCP client, the user can call `recall("RAG evaluation")` explicitly, see the prior chunks, and decide whether to use them. This pattern worked. The difference is that the user is the one making the relevance judgment about whether yesterday's context belongs in today's question. The automatic path cannot make that judgment — it has a similarity score and nothing else. Similarity is a necessary condition for context being useful, but it is nowhere near sufficient.

The principle underneath this: a RAG retrieval call is a judgment about *this question's* scope, and the judgment belongs with the agent that understands the scope. In a multi-pass pipeline, that agent is the human asking, not the orchestrator running the pass. If I were to keep building on Cortex, `use_memory=True` would be off by default, and the planner would emit an optional "recall these topics" signal that the user confirms before retrieval runs.

### Why I am archiving this

I stopped using Cortex myself. That is the short version, and it is the version I trust most. I can construct theories about why — the latency, the depth selector, the friction of a dedicated research app when I mostly want quick lookups — and they are probably all true. But the diagnostic fact is that the author of a tool abandoning it daily is a signal that outweighs any feature I could still add. Deep research, framed as a standalone workflow you sit down for, is not a daily pain point for me. It is an occasional one, and an occasional workflow does not sustain a product.

I am moving focus to offensive security tooling for AI coding agents. That area resonates with how I actually think about systems — I spend more time looking for the unexpected failure modes of a system than looking for more things to summarize from one. Cortex as an engineering artifact stands on its own: the pipeline architecture is clean, the verification approach is load-bearing, the Cortex-D routing experiment is a real piece of work. The decision to stop is about fit between the problem and how I actually spend my time, not about the project failing on its own terms.

### What is next

Offensive security tooling for AI coding agents. More when there is something to show.

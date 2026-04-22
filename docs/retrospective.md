# Cortex: Six Months Building a Deep Research Engine

### What Cortex is

Six stages. Planner decomposes the query into sub-questions (Haiku). Gatherer fans out across Serper, Tavily, and crawl4ai. A local cross-encoder reranks the pool. Gap detector scores coverage (Sonnet) and either triggers another gather pass or lets evidence through. Synthesizer writes a document with inline citations (Sonnet). Verifier checks every citation against its source (Sonnet). Document, sources, and embedded chunks write to Qdrant so future runs can recall. Model routing is explicit: Haiku where the task is bounded, Sonnet where it is not. Next.js frontend consumes an SSE stream from FastAPI. The same pipeline is exposed through a CLI and an MCP server.

### Why I built it

Perplexity, ChatGPT with browsing, the Copilot-style extensions — all shallow in the same specific way. One pass, no verification, no memory. Fine for casual questions. For work where a wrong citation costs you, shallowness wears the face of confidence. That is the bug.

The bet was that three pieces, composed, close the gap. Multi-pass search with explicit gap detection, so the second pass goes after what the first pass actually missed. Claim-level verification against retrieved sources, correcting the synthesizer's habit of over-claiming before the user sees the document. Cross-session memory, so Tuesday's question builds on Monday's research instead of re-running cold. None of the three is a new idea. The composition was the bet.

### What held up

**Verification is the load-bearing stage.** My prior was that quality comes from search volume — if the output is wrong, retrieve more. Wrong prior. The dominant failure mode was not missing evidence. The synthesizer was over-claiming on evidence it had. Page said X; document claimed X-plus-context. `backend/pipeline/verifier.py` walks each cited claim, finds the source in the pool, returns confirmed / weakened / unsupported. Weakened dominates. A fourth gather pass would not have caught a line of it. One verification pass does.

**Haiku plans, Sonnet writes.** Bounded tasks belong to Haiku — take a query, return structured JSON. Unbounded tasks belong to Sonnet — produce and scrutinize prose. The router is fifteen lines. Cost drops 3-4x. No quality regression I could measure. I expected one.

**Claim-level verdicts beat document-level review.** An earlier iteration had the verifier read the whole document and return "looks good" or "needs revision." Useless. The verdict had no leverage — nowhere to point, nothing to patch. Dropping to per-claim verdicts with explicit source IDs converted judgment into lookup. Models are good at lookup. They are worse at judgment.

### What broke

**Latency compounds.** Individual stages are fine — planning in two seconds, synthesis in ten or fifteen. Six stages compose. Deep mode runs gather twice more. Thirty to ninety seconds total. Fine for a long investigation. Terrible for the half-formed question where you want to poke at something before you know it deserves a session. The absolute time is not the problem. The commitment gate in front of it is.

**I stopped using my own tool.** Month three I noticed I was opening ChatGPT for quick lookups. Month four the explicit-research sessions got rare. Month five I was maintaining a system I was not using. The author abandoning the tool daily outweighs any feature the roadmap could still produce.

**The depth selector is a tax.** Quick / standard / deep, before the query runs — asking the user to predict how hard their own question is before they have seen any evidence. The gap detector makes it redundant. It got built second and I never refactored the UI around it. A product decision calcified into a user-facing control.

### What I got wrong about memory

Cross-session memory in a Qdrant-backed RAG works as an explicit recall tool. It does not work as automatic pipeline context. The failure was subtle enough that it took months to see clearly.

The orchestrator (`backend/pipeline/orchestrator.py`) takes a `use_memory` flag. On, the pipeline's first action is `recall(query)` against the Qdrant collection — top chunks from prior research, handed to the planner as `prior_context`. Intent: the system should always benefit from what it already knew. Effect: Monday's topic bleeds into Tuesday's planner prompt and biases Tuesday's sub-questions toward Monday's framing. The output still looks fine. The research is quietly narrower than it should be. The more history the system has, the worse the drift.

The MCP server treats `recall` as its own tool alongside `research`. From Claude Desktop, the user calls `recall("RAG evaluation")` explicitly, reads the chunks, decides. That pattern works. The difference is not the retrieval. It is who makes the relevance judgment about whether yesterday's context belongs in today's question. A similarity score can tell you two queries are near each other in embedding space. It cannot tell you whether they are near each other in intent.

The principle underneath: a RAG retrieval call is a judgment about this question's scope, and the judgment belongs with the agent that holds the scope. In a multi-pass pipeline, the agent holding scope is the human asking. The orchestrator cannot hold scope — it holds vectors.

Shipped default is `use_memory=True` on both the orchestrator and the MCP `research` tool. I did not flip it. The drift is subtle enough that reasonable engineers looking at the code would disagree about the fix, and I was not going to resolve that argument in an archive commit. Flipping the default would be the first change if the project continued. The second would be an optional signal the planner emits — "these prior topics might be relevant, confirm?" — surfaced before retrieval runs. Recall as a suggestion the user approves. Not a behavior the system assumes on their behalf.

### Why I am archiving

I stopped using Cortex. That is the answer I trust most. The supporting reasons — latency, the depth selector, the friction of a dedicated research app when most of what I want is quick lookups — are likely all true. The diagnostic fact sits underneath them: an author who does not use their tool daily is a signal that outweighs any roadmap. Deep research as a standalone workflow is an occasional pain point, not a daily one. Occasional pain points do not sustain products.

Next is offensive security tooling for AI coding agents. That area matches how I actually think about systems — more time on unexpected failure modes, less time summarizing more things from one. Cortex stands on its own as an engineering artifact. The pipeline is clean, the verification approach is load-bearing, the Cortex-D routing experiment is real work. The decision to stop is about fit. Not failure.

### What is next

Offensive security tooling for AI coding agents. More when there is something to show.

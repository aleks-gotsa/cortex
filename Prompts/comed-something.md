# Cortex — Citation Popover + Collapsible Sources Prompt

Two UI features for ResearchDocument.tsx. Do not change any backend files or SSE logic.

## Part 1 — Citation popover

### Data flow
1. Update ResearchResult type in lib/research.ts to include:
   sources: Array<{ url: string; title: string; snippet: string }> | null

2. In useResearch.ts — populate sources from the complete event:
   const sources = Array.isArray(data.sources) ? data.sources : []
   setResult({ ..., sources })

3. In app/page.tsx — pass sources to ResearchDocument:
   <ResearchDocument markdown={result.document} sources={result.sources} />

4. In app/research/[id]/page.tsx — parse sources_json from GET /api/research/{id} response and pass to ResearchDocument.

### Popover behavior
- Click on [1] → popover appears anchored to that citation
- Click anywhere else → popover closes
- Only one popover open at a time

### Popover styling
- Background: var(--bg)
- Border: 1px solid var(--border)
- Shadow: 0 4px 16px rgba(0,0,0,0.08)
- Padding: 14px 16px
- Max width: 320px
- Position: absolute, appears above citation if near bottom of viewport, below otherwise

### Popover content
- Source number: DM Mono 10px uppercase muted — "SOURCE 1"
- Title: DM Sans 13px weight 500, color var(--fg) — clickable link, opens _blank
- Snippet: DM Sans 12px, color var(--fg-muted), line-height 1.5, max 3 lines, overflow hidden
- URL: DM Mono 11px, color var(--accent), truncated to 40 chars

### Fallback
If sources array is null or source [N] not found — keep original anchor scroll behavior.

---

## Part 2 — Collapsible sources panel

### Strip markdown sources section
Remove everything from "## Sources" onward from the markdown before rendering.
Render sources only via the new collapsible panel below.

### Toggle bar
- Full width, borderTop: "1px solid var(--border)", marginTop: 32, padding: "12px 0"
- Left side: source count — DM Mono 12px, color var(--fg-muted) — e.g. "20 sources"
- Right side: chevron ↓ / ↑ — rotates on open/close, transition 0.2s
- Cursor pointer, hover: color var(--fg)
- Default state: collapsed

### Expanded list
- Each source: padding "8px 0", borderBottom "1px solid var(--border)"
- Format: [N] — clickable title or URL, opens _blank, color var(--accent), DM Mono 12px
- Snippet below: DM Sans 12px, color var(--fg-muted), max 2 lines, overflow hidden

---

## Do NOT change
- useHistory.ts
- lib/research.ts SSE parsing logic
- Any backend files
- PipelineProgress.tsx
- SearchInput.tsx

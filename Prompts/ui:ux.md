# Cortex — Frontend Redesign Prompt

Rebuild the frontend visual design. Do NOT touch any backend files, SSE logic, API calls, or hooks. Only change styling and layout in the frontend directory.

## Design reference

The target design is "Takeover" style — editorial NY aesthetic:
- Light cream base: #faf8f5
- Dark mode: #0f0f0f (already working via html.dark class)
- Typography: Source Serif 4 (headlines, body), DM Sans (UI), DM Mono (metadata, labels)
- No gradients, no glows, no heavy shadows
- Black and cream do 95% of the work
- One accent: #3b5998 for citation links
- Generous whitespace

## Three UI states

### State 1 — IDLE
- Centered vertically (~30vh from top)
- "Cortex" — Source Serif 4, 36px, weight 700, letterSpacing -0.03em
- Tagline below: "Search, verify, remember." — DM Mono, 13px, uppercase, muted (#888)
- Search input: full-width, bottom-border only (no box border), serif font 18px, placeholder color #bbb
- Depth selector: three plain text options "Quick · Standard · Deep" — NOT a <select>. Active option underlined. DM Mono 12px uppercase.
- Submit: plain "→" button or Enter key
- History list below: minimal — query text + time ago + cost, no cards, no borders, hover underline

### State 2 — RESEARCHING (Takeover)
- Input fades up and out (opacity 0, translateY -16px)
- Query text appears centered in italic serif: `"Architecture of 90s New York"`
- Pipeline stages stack vertically below, appearing one by one:
  - Done stages: ✓ + label (DM Mono uppercase 11.5px, muted) + detail text (10.5px, #999)
  - Active stage: pulsing dot + label (bold, #0a0a0a) + detail
  - Future stages: opacity 0.25
- No spinners, no progress bars, no percentages

### State 3 — COMPLETE
- Thin top bar slides in: query text left, cost + sources + passes right — DM Mono 11px, #999
- "New research" link far right in top bar
- Document fills page below bar
- Editorial prose: Source Serif 4, 15.5px, line-height 1.75, color #2a2a2a
- Citations [1][2] as superscript muted blue (#3b5998), clickable anchor links
- Sources section: DM Mono, smaller, each is an anchor target

## Specific file changes

### app/globals.css
Keep all existing CSS variables and prose-editorial classes — they are correct. Only add:

```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeOutUp {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(-16px); }
}

.animate-fade-in { animation: fadeIn 0.5s ease forwards; }
.animate-fade-out-up { animation: fadeOutUp 0.4s ease forwards; }

input::placeholder { color: #b0aaa0; }
```

### components/SearchInput.tsx
Replace the current box-style input with:
- Single bottom border only: `borderBottom: "1px solid var(--border)"`, no other border
- Background transparent
- Source Serif 4, 18px
- Depth selector: three inline text buttons (Quick / Standard / Deep), active one has `borderBottom: "1px solid var(--fg)"`, DM Mono 12px uppercase
- Submit button: plain text "→", no background, no border

### app/page.tsx
Keep all existing logic (useResearch, useHistory, phase state machine, SSE, history loading). Only change the JSX rendering for each phase:

IDLE phase:
- paddingTop: clamp(80px, 30vh, 38vh)
- "Cortex" in Source Serif 4, 36px, weight 700
- Tagline: DM Mono, 13px, uppercase, color var(--fg-muted)
- History list below with 80px margin-top

RESEARCHING phase:
- Full screen flex center
- Query in italic serif 18px, marginBottom 32px
- Stages list below — use the StageIndicator pattern from the mockup

COMPLETE phase:
- Thin top bar: position fixed top 0, full width, borderBottom 1px solid var(--border), background var(--bg), padding 12px 24px
- DM Mono 11px for all top bar text
- Document in max-w-3xl mx-auto, pt-16 (to clear fixed bar)

### components/PipelineProgress.tsx
Rebuild to match Takeover stage indicator:
- Query shown in italic serif above stages
- Each stage: dot indicator (✓ done / pulsing dot active / grey dot future) + DM Mono uppercase label + detail text
- Future stages at opacity 0.25
- No rich library, no spinners — pure CSS dots

## Do NOT change
- useResearch.ts
- useHistory.ts  
- lib/research.ts
- ResearchDocument.tsx
- hooks/
- backend/
- Any API or SSE logic

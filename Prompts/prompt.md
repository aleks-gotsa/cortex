# Task: Cortex Frontend P0 Fixes

<context>
You are fixing the frontend of Cortex — a deep research engine built with Next.js 14, App Router, TypeScript, Tailwind CSS. The backend is untouched. You are only modifying frontend files.

The frontend uses an editorial NY aesthetic: cream base (#faf8f5), dark mode (#0f0f0f), Source Serif 4 for headlines, DM Sans for body, DM Mono for metadata. No gradients, no glows, no shadows. The design is intentionally minimal — every change must preserve this.

The app has three phases: idle (search input centered), researching (full-screen pipeline stages), complete (TopBar + document). Transitions use fade-in/fade-out-up animations.
</context>

<codebase>
All files are in `./frontend/`. Key files you will modify:

- `app/globals.css` — CSS variables, prose-editorial styles, animations
- `app/layout.tsx` — HTML head, fonts, metadata
- `components/SearchInput.tsx` — query input + depth selector
- `components/PipelineProgress.tsx` — research stages display
- `components/ResearchDocument.tsx` — markdown renderer
- `components/TopBar.tsx` — sticky bar on complete phase
- `components/HistoryList.tsx` — past research list
- `components/ThemeToggle.tsx` — light/dark toggle
- `lib/research.ts` — types, SSE parser, stage labels/metrics
- `hooks/useResearch.ts` — research SSE hook
- `hooks/useHistory.ts` — history fetch hook
- `app/page.tsx` — main page with phase management
</codebase>

<fixes>
There are exactly 6 fixes. Do them in this order. Do NOT add anything beyond what is specified.

<!-- ═══════════════════════════════════════════════════ -->
<!-- FIX 1: Touch-safe tap targets                      -->
<!-- ═══════════════════════════════════════════════════ -->

<fix id="1" file="components/SearchInput.tsx, components/HistoryList.tsx, components/ThemeToggle.tsx">
<problem>
Interactive elements are too small for mobile touch:
- Depth selector buttons have no padding, dots are 8px apart — impossible to tap accurately
- HistoryList items have py-2.5 (~40px) — below Apple's 44px minimum
- ThemeToggle is 11px text with no touch padding
</problem>

<changes>
**SearchInput.tsx — depth selector:**
- Add `min-height: 44px` to each depth button via inline style
- Add `padding: 8px 12px` to each depth button
- Increase dot separator margin from `0 8px` to `0 4px` (visual stays tight, but buttons themselves have padding)
- The button text stays 13px — only the hit area grows

**HistoryList.tsx — history items:**
- Change `py-2.5` to `py-3.5` on the button element
- This gives ~48px touch height

**ThemeToggle.tsx — toggle button:**
- Add `padding: 12px 16px` to the button style
- Keep font-size at 11px — the text stays small, the tap area grows
- Adjust bottom/right to account for new padding: bottom: 4, right: 4
</changes>

<preserve>
- Do NOT change font sizes in this fix — that's fix 2
- Do NOT change the visual appearance — only invisible padding/hit areas
- Do NOT add hover effects, background colors, or borders to enlarged areas
</preserve>
</fix>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FIX 2: Font scaling on mobile                      -->
<!-- ═══════════════════════════════════════════════════ -->

<fix id="2" file="app/globals.css">
<problem>
DM Mono at 11px is unreadable on mobile screens. Affects: pipeline stages, TopBar metadata, history timestamps/costs, ThemeToggle, citation links.
</problem>

<changes>
Add a single media query block at the end of globals.css (before the scrollbar/selection sections):

```css
/* ── Mobile typography ───────────────────────────────── */

@media (max-width: 640px) {
  .font-mono,
  [style*="font-family: var(--font-mono)"] {
    font-size: 13px !important;
  }
}
```

BUT — this selector won't catch inline styles reliably. Instead, use targeted class overrides:

Add a utility class in globals.css:
```css
.meta-text {
  font-family: var(--font-mono);
  font-size: 11px;
}

@media (max-width: 640px) {
  .meta-text {
    font-size: 13px;
  }
}
```

Then replace all `font-mono text-[11px]` and inline `fontSize: 11` patterns with the `meta-text` class in these components:
- `PipelineProgress.tsx` — stage name span (currently `font-mono text-[11px]`) and metric span
- `TopBar.tsx` — metadata span (currently `font-mono text-[11px]`) and "New research" button
- `HistoryList.tsx` — timestamp/cost span (currently `font-mono text-[11px]`)
- `ThemeToggle.tsx` — button text (currently inline fontSize: 11)

Also add a mobile override for citation links:
```css
@media (max-width: 640px) {
  .citation-link {
    font-size: 0.85em;
  }
}
```
</changes>

<preserve>
- Desktop stays at 11px — the editorial minimalism is intentional on large screens
- Do NOT change serif or sans font sizes — only monospace metadata
- Do NOT change the prose-editorial body text size (15.5px is fine on mobile)
- The breakpoint is 640px (Tailwind's `sm`) — be consistent
</preserve>
</fix>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FIX 3: Safe area insets                            -->
<!-- ═══════════════════════════════════════════════════ -->

<fix id="3" file="app/layout.tsx, app/globals.css, components/TopBar.tsx, components/ThemeToggle.tsx">
<problem>
No viewport-fit=cover. ThemeToggle (fixed bottom-right) gets hidden behind iPhone home bar. TopBar clips under Dynamic Island in landscape.
</problem>

<changes>
**layout.tsx:**
Replace the existing viewport meta tag (or add if missing) in the `<head>`:
```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
```

**globals.css:**
Add at the very top, after the @tailwind directives:
```css
/* ── Safe areas ──────────────────────────────────────── */

body {
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}
```

**TopBar.tsx:**
Add safe area padding to the sticky top bar. On the outer div, add:
```
paddingTop: env(safe-area-inset-top)
```
Use inline style or add a class. The simplest approach:
```tsx
<div className="sticky top-0 z-10 bg-[var(--bg)] border-b border-[var(--border)] animate-slide-down"
     style={{ paddingTop: "env(safe-area-inset-top)" }}>
```

**ThemeToggle.tsx:**
Change fixed positioning to respect safe areas:
```tsx
style={{
  bottom: "calc(16px + env(safe-area-inset-bottom))",
  right: "calc(16px + env(safe-area-inset-right))",
  ...rest
}}
```

**page.tsx — idle phase:**
Add bottom safe area padding to the idle container:
```tsx
<div className={`min-h-screen flex flex-col items-center px-6 ${anim}`}
     style={{ paddingTop: "38vh", paddingBottom: "calc(20px + env(safe-area-inset-bottom))" }}>
```
</changes>

<preserve>
- Do NOT add padding that breaks the layout on non-notch devices — env() returns 0px when not applicable
- Do NOT change z-index values
- Do NOT modify the animation classes
</preserve>
</fix>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FIX 4: Reranking stage display                     -->
<!-- ═══════════════════════════════════════════════════ -->

<fix id="4" file="lib/research.ts">
<problem>
The CLAUDE.md spec defines an `event: reranking` SSE event with `top_sources` and `dropped` data fields. But STAGE_LABELS in research.ts doesn't include "reranking", and getStageName/getStageMetric don't handle it. If the backend emits this event, the frontend shows raw text with no metric.
</problem>

<changes>
**STAGE_LABELS** — add entry:
```ts
reranking: "RERANKING",
```

**getStageName** — add case before the default return:
```ts
if (stage === "reranking") {
  return "RERANKING";
}
```
(This is technically handled by STAGE_LABELS already, but being explicit is safer.)

**getStageMetric** — add case in the switch:
```ts
case "reranking": {
  const top = data.top_sources;
  const dropped = data.dropped;
  if (typeof top === "number" && typeof dropped === "number") {
    return `${top} kept, ${dropped} dropped`;
  }
  if (typeof top === "number") {
    return `${top} sources reranked`;
  }
  return "";
}
```
</changes>

<preserve>
- Do NOT modify any other stage labels or metrics
- Do NOT change the parseSSEChunk function
- Do NOT modify any other file for this fix
</preserve>
</fix>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FIX 5: Theme persistence                           -->
<!-- ═══════════════════════════════════════════════════ -->

<fix id="5" file="components/ThemeToggle.tsx, app/layout.tsx">
<problem>
ThemeToggle uses useState(false). Every page refresh resets to light mode. Does not respect system prefers-color-scheme preference. User's choice is lost.
</problem>

<changes>
**ThemeToggle.tsx — full rewrite:**
```tsx
"use client";

import { useState, useEffect, useCallback } from "react";

function getInitialTheme(): boolean {
  if (typeof window === "undefined") return false;
  const stored = localStorage.getItem("cortex-theme");
  if (stored === "dark") return true;
  if (stored === "light") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export default function ThemeToggle() {
  const [dark, setDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Hydration-safe: read preference only after mount
  useEffect(() => {
    const initial = getInitialTheme();
    setDark(initial);
    document.documentElement.classList.toggle("dark", initial);
    setMounted(true);
  }, []);

  const toggle = useCallback(() => {
    setDark((prev) => {
      const next = !prev;
      document.documentElement.classList.toggle("dark", next);
      localStorage.setItem("cortex-theme", next ? "dark" : "light");
      return next;
    });
  }, []);

  // Don't render until mounted to prevent hydration flash
  if (!mounted) return null;

  return (
    <button
      onClick={toggle}
      className="fixed z-50 cursor-pointer meta-text"
      style={{
        bottom: "calc(4px + env(safe-area-inset-bottom))",
        right: "calc(4px + env(safe-area-inset-right))",
        padding: "12px 16px",
        color: "var(--fg-faint)",
        background: "none",
        border: "none",
      }}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {dark ? "Light" : "Dark"}
    </button>
  );
}
```

**layout.tsx — flash prevention:**
Add an inline script in `<head>` BEFORE the stylesheet link, to apply the theme class before first paint:
```html
<script dangerouslySetInnerHTML={{ __html: `
  (function() {
    try {
      var stored = localStorage.getItem('cortex-theme');
      var dark = stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (dark) document.documentElement.classList.add('dark');
    } catch(e) {}
  })();
`}} />
```

Place this script tag BEFORE the Google Fonts `<link>` tags inside `<head>`.
</changes>

<preserve>
- Do NOT change the CSS variables in globals.css — the dark mode values are already correct
- Do NOT add a system theme "auto" option — keep it simple: toggle between light and dark
- Do NOT use cookies for theme — localStorage is fine for a client-side app
- The `mounted` check prevents SSR hydration mismatch — do NOT remove it
</preserve>
</fix>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FIX 6: Table styles in prose                       -->
<!-- ═══════════════════════════════════════════════════ -->

<fix id="6" file="app/globals.css">
<problem>
prose-editorial has no styles for table, thead, th, td. When the Sonnet synthesizer outputs comparison tables in markdown, they render with browser defaults — ugly, wrong font, no padding, no borders.
</problem>

<changes>
Add these styles inside the `/* ── Editorial prose */` section, after the existing `hr` rule and before the `/* ── Citations */` section:

```css
.prose-editorial table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
  font-family: var(--font-sans);
  font-size: 14px;
}

.prose-editorial thead {
  border-bottom: 1.5px solid var(--fg);
}

.prose-editorial th {
  font-weight: 600;
  text-align: left;
  padding: 8px 12px;
  color: var(--fg);
  font-size: 12px;
  font-family: var(--font-mono);
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.prose-editorial td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--fg-secondary);
  vertical-align: top;
}

.prose-editorial tr:last-child td {
  border-bottom: none;
}

.prose-editorial tbody tr:hover {
  background: rgba(0, 0, 0, 0.02);
}

html.dark .prose-editorial tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

/* Responsive table: horizontal scroll on small screens */
@media (max-width: 640px) {
  .prose-editorial table {
    display: block;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    white-space: nowrap;
  }

  .prose-editorial th,
  .prose-editorial td {
    padding: 6px 8px;
    font-size: 13px;
  }
}
```
</changes>

<preserve>
- Do NOT change any existing prose-editorial styles
- Do NOT add JavaScript for table handling — CSS only
- Table headers use mono font (matches metadata aesthetic), body uses sans
- The hover effect is intentionally subtle (2% opacity) — do NOT make it stronger
- white-space: nowrap on mobile prevents table cells from wrapping into unreadable strips — tables scroll horizontally instead
</preserve>
</fix>

</fixes>

<verification>
After all 6 fixes, verify:

1. `npx tsc --noEmit` — no TypeScript errors
2. `npm run build` — builds successfully
3. Open in Chrome DevTools mobile emulator (iPhone 14 Pro):
   - Search input visible without scrolling
   - Depth buttons tappable without mis-tapping
   - History items have adequate touch height
   - ThemeToggle not hidden behind home bar
   - Pipeline stages show readable text
4. Toggle dark mode, reload page — dark mode persists
5. Toggle to light mode, reload — light mode persists
6. Clear localStorage, reload — system preference applies
7. Check that "RERANKING" appears in STAGE_LABELS (code review — backend may not emit this event in all modes)
</verification>

<do_not>
- Do NOT install new npm packages
- Do NOT modify any backend files
- Do NOT modify hooks/useResearch.ts or hooks/useHistory.ts
- Do NOT change the three-phase (idle/researching/complete) flow
- Do NOT change colors, fonts, or the editorial aesthetic
- Do NOT add new components or pages
- Do NOT add animations beyond what already exists
- Do NOT modify the page.tsx phase logic or transition system
- Do NOT change the API proxy in next.config.mjs
</do_not>

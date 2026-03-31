# Task: Cortex Frontend P2 Polish

<context>
You are adding final polish to the Cortex frontend — a deep research engine built with Next.js 14, App Router, TypeScript, Tailwind CSS. The backend is untouched.

P0 (touch targets, font scaling, safe areas, reranking stage, theme persistence, table styles) and P1 (adaptive padding, TopBar mobile metadata, export Copy MD / Print PDF, OG image, error boundary, scroll-to-top) are already applied. Do NOT redo any of those.

The app uses an editorial NY aesthetic: cream base (#faf8f5), dark mode (#0f0f0f), Source Serif 4 headlines, DM Sans body, DM Mono metadata. Three phases: idle → researching → complete.

Existing components you should know about (from P0/P1):
- `meta-text` CSS class — monospace 11px desktop, 13px mobile
- `data-no-print` attribute — hides elements during print
- `ScrollToTop` component — fixed bottom-right, above ThemeToggle
- `ErrorBoundary` component — wraps ResearchDocument
- Print stylesheet — already in globals.css
- Theme persistence — localStorage + system preference
</context>

<codebase>
All files in `./frontend/`. You will modify existing files and create new ones as specified.

Key files:
- `app/globals.css` — all styles
- `app/page.tsx` — main page, phase management
- `app/layout.tsx` — head, metadata
- `components/TopBar.tsx` — sticky bar (complete phase)
- `components/PipelineProgress.tsx` — stage display (researching phase)
- `components/HistoryList.tsx` — past research list (idle phase)
- `components/ThemeToggle.tsx` — fixed bottom-right toggle
- `components/ScrollToTop.tsx` — fixed bottom-right, above toggle
- `components/ResearchDocument.tsx` — markdown renderer
- `lib/research.ts` — types, helpers
- `hooks/useResearch.ts` — SSE hook
- `hooks/useHistory.ts` — history hook
</codebase>

<features>
There are exactly 6 features. Do them in this order.

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 1: Keyboard hints                          -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="1" file="app/page.tsx">
<problem>
Escape key cancels research (researching phase) and returns to idle (complete phase) — but no visual hint exists. The shortcut is undiscoverable without reading source code.
</problem>

<changes>
Add a hint element at the bottom of the researching and complete phases. Desktop only — hidden on mobile (no physical keyboard).

**Researching phase — add after PipelineProgress:**
```tsx
<p
  className="meta-text hidden sm:block"
  style={{
    position: "fixed",
    bottom: 24,
    left: "50%",
    transform: "translateX(-50%)",
    color: "var(--fg-faint)",
  }}
  data-no-print
>
  esc to cancel
</p>
```

**Complete phase — add after ScrollToTop, before closing `</div>`:**
```tsx
<p
  className="meta-text hidden sm:block"
  style={{
    position: "fixed",
    bottom: 24,
    left: "50%",
    transform: "translateX(-50%)",
    color: "var(--fg-faint)",
  }}
  data-no-print
>
  esc to return
</p>
```

Both use `hidden sm:block` — invisible on mobile (no keyboard), visible on 640px+.
Both use `data-no-print` — hidden during print.
Both use fixed positioning centered at bottom — doesn't interfere with ThemeToggle (bottom-right) or ScrollToTop (bottom-right above toggle).
</changes>

<preserve>
- Do NOT change the existing keyboard event handler in page.tsx
- Do NOT add keyboard hints in idle phase
- Do NOT add any animation to the hints — static text, always visible on desktop
- Do NOT change the font or color — meta-text + fg-faint is the pattern
- Hints are purely informational — no click handlers
</preserve>
</feature>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 2: Depth indicator in history              -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="2" file="components/HistoryList.tsx">
<problem>
History list shows query + cost + relative time, but not the depth level. The depth field exists in HistoryRun data but isn't displayed. User can't tell if a past research was a quick scan or deep dive without clicking into it.
</problem>

<changes>
Add a tiny depth badge next to the cost in each history item.

In the timestamp/cost span area, add the depth indicator before the cost:

```tsx
<span className="meta-text text-[var(--fg-faint)] flex-shrink-0 whitespace-nowrap">
  {run.depth && (
    <span
      style={{
        marginRight: 6,
        opacity: 0.7,
      }}
    >
      {run.depth === "quick" ? "Q" : run.depth === "deep" ? "D" : "S"}
    </span>
  )}
  {run.cost_usd != null && (
    <span style={{ marginRight: 8 }}>${run.cost_usd.toFixed(4)}</span>
  )}
  {formatRelativeTime(run.created_at)}
</span>
```

The depth shows as a single letter: Q (quick), S (standard), D (deep). Same mono font, same faint color, slightly more transparent. Minimal — doesn't compete with the query text.
</changes>

<preserve>
- Do NOT change the HistoryRun type — depth field already exists
- Do NOT add a tooltip or expanded label — single letter is enough
- Do NOT change the layout or spacing of history items
- Do NOT add color coding to the depth indicator — all same faint color
- If depth is missing or null, show nothing (graceful degradation)
</preserve>
</feature>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 3: History loading skeleton                -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="3" file="app/globals.css, app/page.tsx">
<problem>
Clicking a history item shows "Loading…" text replacement while fetching the document. No transition, no visual feedback beyond text change. Breaks the editorial confidence — the app should feel alive during loading, not frozen.
</problem>

<changes>
**globals.css — add skeleton animation:**
Add after the existing keyframes section or near the mobile typography section:

```css
/* ── Skeleton ────────────────────────────────────────── */

@keyframes shimmer {
  0% { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}

.skeleton-line {
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--border) 25%, transparent 50%, var(--border) 75%);
  background-size: 400px 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
```

**page.tsx — add a loading state between phases:**
Currently, clicking history calls `handleHistorySelect` which calls `loadDocument(id)` and transitions to complete phase only after the document is loaded. During this gap, the idle phase shows "Loading…" text on the history item.

Add a new visual state: when `loadingId` is set (from useHistory), show a skeleton in the document area instead of keeping the idle phase visible.

Create a simple skeleton component inline in page.tsx (not a separate file — it's small):

```tsx
function DocumentSkeleton() {
  return (
    <div className="max-w-3xl mx-auto px-6 pt-16 pb-24 animate-fade-in">
      {/* Title skeleton */}
      <div className="skeleton-line" style={{ width: "60%", height: 28, marginBottom: 32 }} />
      {/* Paragraph skeletons */}
      <div className="skeleton-line" style={{ width: "100%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "95%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "88%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "92%", marginBottom: 24 }} />
      {/* Second paragraph */}
      <div className="skeleton-line" style={{ width: "100%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "85%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "90%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "70%", marginBottom: 32 }} />
      {/* Section heading */}
      <div className="skeleton-line" style={{ width: "40%", height: 22, marginBottom: 20 }} />
      {/* More lines */}
      <div className="skeleton-line" style={{ width: "100%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "93%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "87%", marginBottom: 10 }} />
    </div>
  );
}
```

To use it: in `handleHistorySelect`, transition to a skeleton view immediately instead of waiting for data. The cleanest approach without adding a new phase:

Add a `loadingSkeleton` state:
```tsx
const [loadingSkeleton, setLoadingSkeleton] = useState(false);
```

Modify `handleHistorySelect`:
```tsx
const handleHistorySelect = useCallback(
  async (id: string) => {
    setLoadingSkeleton(true);
    transitionTo("complete"); // transition immediately — show skeleton

    const doc = await loadDocument(id);
    if (doc) {
      setDisplayResult({
        document: doc.markdown,
        query: doc.query,
        costUsd: doc.costUsd,
        sourcesCount: 0,
        passCount: 0,
        researchId: id,
      });
      setActiveQuery(doc.query);
    } else {
      // Failed to load — go back
      transitionTo("idle");
    }
    setLoadingSkeleton(false);
  },
  [loadDocument, transitionTo]
);
```

In the complete phase render, conditionally show skeleton or document:
```tsx
{phase === "complete" && (
  <div className={anim}>
    {!loadingSkeleton && displayResult && (
      <TopBar result={displayResult} onNewResearch={handleNewResearch} />
    )}
    <main className="max-w-3xl mx-auto px-6 pt-10 pb-24">
      {loadingSkeleton ? (
        <DocumentSkeleton />
      ) : (
        displayResult && (
          <ErrorBoundary onReset={handleNewResearch}>
            <div className="print-header hidden" style={{ display: "none" }}>
              Cortex Research — {displayResult.query}
              {displayResult.costUsd !== null && ` — $${displayResult.costUsd.toFixed(4)}`}
            </div>
            <ResearchDocument markdown={displayResult.document} />
          </ErrorBoundary>
        )
      )}
    </main>
    {!loadingSkeleton && <ScrollToTop />}
  </div>
)}
```

The skeleton has the same max-width and padding as the real document — the transition from skeleton to content feels like the page "filling in" rather than a layout jump.
</changes>

<preserve>
- Do NOT create a separate file for DocumentSkeleton — define it in page.tsx above the Home component
- Do NOT add skeleton to the researching phase — PipelineProgress already handles that
- Do NOT change the shimmer colors — uses var(--border) which adapts to light/dark mode
- Do NOT make skeleton lines random widths on each render — fixed widths for consistent appearance
- The skeleton gradient uses linear-gradient which normally I'd avoid, but it's in a non-critical decorative context and the shimmer effect requires it
- Do NOT show TopBar during skeleton loading — no data to display yet
</preserve>
</feature>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 4: Reading progress indicator              -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="4" file="components/ReadingProgress.tsx (new), app/page.tsx">
<problem>
Long research documents (10-15K chars) give no sense of scroll position. Standard editorial pattern is a thin progress bar below the header. Reinforces the editorial/magazine aesthetic.
</problem>

<changes>
**Create `components/ReadingProgress.tsx`:**
```tsx
"use client";

import { useState, useEffect } from "react";

export default function ReadingProgress() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    function onScroll() {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (docHeight <= 0) {
        setProgress(0);
        return;
      }
      setProgress(Math.min(Math.round((scrollTop / docHeight) * 100), 100));
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (progress <= 0) return null;

  return (
    <div
      data-no-print
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: `${progress}%`,
        height: 2,
        backgroundColor: "var(--accent)",
        zIndex: 20,
        transition: "width 0.1s linear",
        pointerEvents: "none",
      }}
    />
  );
}
```

**Add to page.tsx:**
Import at top:
```tsx
import ReadingProgress from "@/components/ReadingProgress";
```

Render only in complete phase, inside the outer div, before TopBar:
```tsx
{phase === "complete" && (
  <div className={anim}>
    <ReadingProgress />
    {!loadingSkeleton && displayResult && (
      <TopBar ... />
    )}
    ...
  </div>
)}
```

The bar sits at the very top of the viewport (above TopBar's sticky position since TopBar has `top: 0` but the progress bar is `fixed` with `z-index: 20` while TopBar is `z-10`). 2px height. Accent color (#3b5998 light / #7b9dd4 dark). Invisible at 0% (returns null). No animation on appear — just grows with scroll.
</changes>

<preserve>
- Do NOT show progress bar in idle or researching phases
- Do NOT change TopBar z-index — progress bar sits above it at z-20
- Do NOT make the bar thicker than 2px — it should be barely noticeable
- Do NOT add a percentage label or tooltip
- Do NOT use a library — vanilla scroll listener
- Passive listener for performance
- pointer-events: none so it doesn't intercept clicks
- Uses var(--accent) which already adapts to dark mode
- transition: width is intentionally short (0.1s) to feel responsive, not laggy
</preserve>
</feature>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 5: prefers-reduced-motion                  -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="5" file="app/globals.css">
<problem>
All animations (fade-in, fade-out-up, pulse-dot, slide-down, shimmer) run regardless of user preference. Some users get motion sickness. Budget devices drop frames. This is an accessibility requirement and a portfolio quality signal.
</problem>

<changes>
Add at the very end of globals.css (after the print section, before the closing):

```css
/* ── Reduced motion ──────────────────────────────────── */

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

This single block disables all animations app-wide when the user has "Reduce motion" enabled in their OS settings. The 0.01ms (not 0ms) ensures animation-end events still fire — prevents JavaScript that depends on animationend from breaking.
</changes>

<preserve>
- Do NOT add individual animation overrides per class — the wildcard selector handles everything
- Do NOT remove existing animations — they still run for users who haven't requested reduced motion
- Do NOT change scroll-behavior in other parts of the CSS
- This MUST be the last rule in the file so it wins specificity ties
</preserve>
</feature>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 6: Shareable research URLs                 -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="6" file="app/research/[id]/page.tsx (new), app/page.tsx">
<problem>
All researches live at "/" — no unique URL per research. Can't bookmark, can't share a link to a specific result. Makes Cortex feel like a demo, not a product.
</problem>

<changes>
**Create `app/research/[id]/page.tsx`:**
```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import type { ResearchResult } from "@/lib/research";
import TopBar from "@/components/TopBar";
import ResearchDocument from "@/components/ResearchDocument";
import ThemeToggle from "@/components/ThemeToggle";
import ErrorBoundary from "@/components/ErrorBoundary";
import ScrollToTop from "@/components/ScrollToTop";
import ReadingProgress from "@/components/ReadingProgress";

export default function ResearchPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [result, setResult] = useState<ResearchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/research/${id}`);
        if (!res.ok) {
          setError(res.status === 404 ? "Research not found." : "Failed to load research.");
          return;
        }
        const detail: unknown = await res.json();
        const d = detail as Record<string, unknown>;

        if (
          d?.result &&
          typeof (d.result as Record<string, unknown>).document_md === "string" &&
          d?.run &&
          typeof (d.run as Record<string, unknown>).query === "string"
        ) {
          const run = d.run as Record<string, unknown>;
          const r = d.result as Record<string, unknown>;
          setResult({
            document: r.document_md as string,
            query: run.query as string,
            costUsd: typeof run.cost_usd === "number" ? run.cost_usd : null,
            sourcesCount: 0,
            passCount: 0,
            researchId: id,
          });
        } else {
          setError("Invalid research data.");
        }
      } catch {
        setError("Failed to load research.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const handleNewResearch = useCallback(() => {
    router.push("/");
  }, [router]);

  // Loading state
  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-6 pt-16 pb-24 animate-fade-in">
        <div className="skeleton-line" style={{ width: "60%", height: 28, marginBottom: 32 }} />
        <div className="skeleton-line" style={{ width: "100%", marginBottom: 10 }} />
        <div className="skeleton-line" style={{ width: "95%", marginBottom: 10 }} />
        <div className="skeleton-line" style={{ width: "88%", marginBottom: 10 }} />
        <div className="skeleton-line" style={{ width: "92%", marginBottom: 24 }} />
        <div className="skeleton-line" style={{ width: "100%", marginBottom: 10 }} />
        <div className="skeleton-line" style={{ width: "85%", marginBottom: 10 }} />
        <div className="skeleton-line" style={{ width: "90%", marginBottom: 10 }} />
        <ThemeToggle />
      </div>
    );
  }

  // Error state
  if (error || !result) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "80vh",
          padding: "2rem",
          textAlign: "center",
        }}
      >
        <h2
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: 22,
            fontWeight: 700,
            color: "var(--fg)",
            marginBottom: 8,
          }}
        >
          {error || "Research not found"}
        </h2>
        <button
          onClick={handleNewResearch}
          className="meta-text"
          style={{
            marginTop: 16,
            color: "var(--fg-muted)",
            background: "none",
            border: "none",
            cursor: "pointer",
            textDecoration: "underline",
            textUnderlineOffset: 3,
          }}
        >
          New research
        </button>
        <ThemeToggle />
      </div>
    );
  }

  // Document view
  return (
    <div className="animate-fade-in">
      <ReadingProgress />
      <TopBar result={result} onNewResearch={handleNewResearch} />
      <main className="max-w-3xl mx-auto px-6 pt-10 pb-24">
        <ErrorBoundary onReset={handleNewResearch}>
          <div className="print-header hidden" style={{ display: "none" }}>
            Cortex Research — {result.query}
            {result.costUsd !== null && ` — $${result.costUsd.toFixed(4)}`}
          </div>
          <ResearchDocument markdown={result.document} />
        </ErrorBoundary>
      </main>
      <ScrollToTop />
      <ThemeToggle />
      <p
        className="meta-text hidden sm:block"
        style={{
          position: "fixed",
          bottom: 24,
          left: "50%",
          transform: "translateX(-50%)",
          color: "var(--fg-faint)",
        }}
        data-no-print
      >
        esc to return
      </p>
    </div>
  );
}
```

**Add keyboard handler for Escape in the research page:**
Add inside the ResearchPage component, after the state declarations:
```tsx
useEffect(() => {
  function onKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") router.push("/");
  }
  window.addEventListener("keydown", onKeyDown);
  return () => window.removeEventListener("keydown", onKeyDown);
}, [router]);
```

**Update page.tsx — push URL on research completion and history selection:**

When a research completes, update the URL without navigation:
In the `useEffect` that watches for `researchResult`, after `setDisplayResult(researchResult)` and before/after `transitionTo("complete")`, add:
```tsx
if (researchResult.researchId) {
  window.history.replaceState(null, "", `/research/${researchResult.researchId}`);
}
```

When loading from history, in `handleHistorySelect`, after `setDisplayResult(...)`:
```tsx
window.history.replaceState(null, "", `/research/${id}`);
```

When returning to idle (in `handleNewResearch`):
```tsx
window.history.replaceState(null, "", "/");
```

This uses `replaceState` not `pushState` — doesn't pollute browser history. The URL updates to `/research/abc123` when viewing a result, and back to `/` when starting a new research. If someone bookmarks or shares `/research/abc123`, the new page component loads it directly.
</changes>

<preserve>
- Do NOT use Next.js router.push for URL updates on the main page — use window.history.replaceState to avoid full page transitions
- Do NOT duplicate the DocumentSkeleton component — use the skeleton-line CSS class directly (same visual result)
- Do NOT add loading state to TopBar on the research page — either show the full TopBar with data or don't show it at all
- Do NOT modify the API proxy in next.config.mjs — `/api/research/:id` already proxies correctly
- Do NOT add any authentication or access control to the research page
- The research page is a standalone page that works independently of the main page — it fetches its own data
- The error state uses the same editorial aesthetic: serif heading, mono button
- Escape key on research page navigates to "/" (home) using router.push (full navigation is fine here)
</preserve>
</feature>

</features>

<verification>
After all 6 features:

1. `npx tsc --noEmit` — no TypeScript errors
2. `npm run build` — builds successfully
3. Desktop checks:
   - Researching phase: "esc to cancel" visible at bottom center
   - Complete phase: "esc to return" visible at bottom center
   - Press Escape in complete → returns to idle
   - Both hints invisible in mobile emulator (<640px)
4. History list:
   - Each item shows Q/S/D before cost
   - Items without depth show nothing (no crash)
5. History loading:
   - Click history item → immediate transition to skeleton shimmer
   - Skeleton fills in with real document when loaded
   - Failed load → returns to idle (no white screen)
6. Reading progress:
   - Scroll down on complete phase → thin blue bar grows at top
   - Bar sits above TopBar visually
   - Bar not visible at scroll position 0
   - Bar hidden during print
7. Reduced motion:
   - Enable "Reduce motion" in OS settings
   - Reload page → no fade-in animations, no skeleton shimmer, no pulse-dot
   - All functionality still works (transitions are instant instead of animated)
8. Shareable URLs:
   - Complete a research → URL changes to /research/{id}
   - Copy that URL, open in new tab → document loads directly with skeleton then content
   - Navigate to /research/nonexistent → shows "Research not found" with "New research" link
   - Press Escape on research page → navigates to /
   - Click "New research" on research page → navigates to /
   - Return to idle from complete phase → URL changes back to /
9. Mobile emulator: all features work, no layout breaks
</verification>

<do_not>
- Do NOT install any new npm packages
- Do NOT modify backend files
- Do NOT modify lib/research.ts or hooks/ files
- Do NOT modify components that aren't listed in the feature specs
- Do NOT change colors, fonts, or the editorial aesthetic
- Do NOT add a sidebar or navigation menu
- Do NOT add user accounts or authentication
- Do NOT add sharing via API (no share buttons, no link shortener) — URL sharing is implicit (copy URL from address bar)
- Do NOT add analytics or tracking
- Do NOT modify the print stylesheet from P1
- Do NOT change existing P0/P1 functionality
</do_not>

# Task: Cortex Frontend P1 Features

<context>
You are adding P1 features to the Cortex frontend — a deep research engine built with Next.js 14, App Router, TypeScript, Tailwind CSS. The backend is untouched.

P0 fixes are already applied: touch targets, font scaling (meta-text class), safe area insets, reranking stage, theme persistence (localStorage + system preference), table styles in prose-editorial. Do NOT redo any of those.

The app uses an editorial NY aesthetic: cream base (#faf8f5), dark mode (#0f0f0f), Source Serif 4 headlines, DM Sans body, DM Mono metadata. Three phases: idle → researching → complete. The design is intentionally minimal.
</context>

<codebase>
All files in `./frontend/`. You will modify existing files and create a few new ones.

Existing key files:
- `app/globals.css` — styles (includes meta-text class from P0)
- `app/layout.tsx` — head, fonts, theme flash prevention script
- `app/page.tsx` — main page with phase management
- `components/TopBar.tsx` — sticky bar on complete phase
- `components/SearchInput.tsx` — query input + depth
- `components/ResearchDocument.tsx` — markdown renderer
- `components/ThemeToggle.tsx` — persistent theme toggle
- `components/HistoryList.tsx` — past research list
- `components/PipelineProgress.tsx` — stage display
- `lib/research.ts` — types, SSE parser, helpers
- `hooks/useResearch.ts` — research SSE hook
- `hooks/useHistory.ts` — history fetch hook
</codebase>

<features>
There are exactly 6 features. Do them in this order.

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 1: Adaptive idle padding                   -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="1" file="app/page.tsx">
<problem>
The idle phase has `paddingTop: "38vh"` which pushes the search input below the fold on short screens (iPhone SE at 667px, any phone in landscape). User sees only the "Cortex" title and has to scroll to find the input.
</problem>

<changes>
Replace the fixed `paddingTop: "38vh"` on the idle phase container with a responsive value:

```tsx
style={{ paddingTop: "clamp(80px, 30vh, 38vh)" }}
```

This gives:
- Desktop: 38vh (same as before — no visual change)
- Mobile portrait: ~30vh (input visible without scrolling)
- Very short screens / landscape: bottoms out at 80px (always reachable)

That's it. One line change.
</changes>

<preserve>
- Do NOT change any other styles in page.tsx
- Do NOT modify the phase logic
- Do NOT add media queries for this — clamp() handles it
</preserve>
</feature>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 2: TopBar mobile metadata                  -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="2" file="components/TopBar.tsx">
<problem>
TopBar hides ALL metadata on mobile with `hidden sm:inline`. This includes cost — the single most important metric for Cortex ("$0.08 for this deep research"). The cost is the product's punchline and it's invisible on mobile.
</problem>

<changes>
Split the metadata display: cost is always visible, sources and passes are hidden on mobile.

Replace the current metadata span:
```tsx
{meta.length > 0 && (
  <span className="font-mono text-[11px] text-[var(--fg-muted)] hidden sm:inline">
    {meta.join(" \u00b7 ")}
  </span>
)}
```

With separate spans:
```tsx
{result.costUsd !== null && (
  <span className="meta-text text-[var(--fg-muted)]">
    ${result.costUsd.toFixed(4)}
  </span>
)}
{(result.sourcesCount > 0 || result.passCount > 0) && (
  <span className="meta-text text-[var(--fg-muted)] hidden sm:inline">
    {[
      result.sourcesCount > 0 ? `${result.sourcesCount} sources` : null,
      result.passCount > 0 ? `${result.passCount} pass${result.passCount > 1 ? "es" : ""}` : null,
    ].filter(Boolean).join(" \u00b7 ")}
  </span>
)}
```

Remove the `meta` array construction at the top of the component — it's no longer needed. Build the display inline.

Make sure the "New research" button also uses `meta-text` class instead of `font-mono text-[11px]` (consistent with P0 pattern).
</changes>

<preserve>
- Do NOT change the TopBar layout structure (sticky, max-w-3xl, flex)
- Do NOT change the "New research" button behavior
- Do NOT add new visual elements to TopBar beyond what's specified
- Cost format stays as `$X.XXXX` (4 decimal places)
</preserve>
</feature>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 3: Export (Copy MD + Download PDF)          -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="3" file="components/TopBar.tsx, app/globals.css">
<problem>
Cortex generates full research documents with citations, but users can only read them in the browser. No way to save, share, or reference offline. This is the #1 feature that turns Cortex from a demo into a tool people actually use.
</problem>

<changes>
Add two export buttons to TopBar, between the metadata and "New research" button.

**Button 1: "Copy MD"**
- On click: copy `result.document` (raw markdown string) to clipboard via `navigator.clipboard.writeText()`
- After copy: button text changes to "Copied" for 2 seconds, then reverts
- Style: same as "New research" — `meta-text text-[var(--fg-muted)] hover:text-[var(--fg)] transition-colors underline underline-offset-2`

**Button 2: "Export PDF"**
- On click: trigger `window.print()` — uses the print stylesheet (see below) to produce a clean PDF via browser's "Save as PDF"
- Style: same as above

**Print stylesheet (globals.css):**
Add at the end of globals.css:

```css
/* ── Print ───────────────────────────────────────────── */

@media print {
  /* Hide all UI chrome */
  .no-print,
  button,
  [data-no-print] {
    display: none !important;
  }

  /* Reset backgrounds */
  body {
    background: #fff !important;
    color: #1a1a1a !important;
    padding: 0 !important;
  }

  /* Document fills the page */
  .prose-editorial {
    max-width: 100% !important;
    font-size: 12pt !important;
    line-height: 1.6 !important;
    color: #1a1a1a !important;
  }

  .prose-editorial h1 {
    font-size: 18pt !important;
    page-break-after: avoid;
  }

  .prose-editorial h2 {
    font-size: 14pt !important;
    page-break-after: avoid;
  }

  .prose-editorial h3 {
    font-size: 12pt !important;
    page-break-after: avoid;
  }

  .prose-editorial p,
  .prose-editorial li {
    orphans: 3;
    widows: 3;
  }

  .prose-editorial blockquote {
    border-left-color: #888 !important;
  }

  .prose-editorial a {
    color: #1a1a1a !important;
    text-decoration: none !important;
  }

  .prose-editorial a[href]::after {
    content: " (" attr(href) ")";
    font-size: 9pt;
    color: #666;
    font-family: var(--font-mono);
  }

  .citation-link::after {
    content: "" !important;
  }

  .prose-editorial table {
    page-break-inside: avoid;
  }

  /* Print header: show query at top */
  .print-header {
    display: block !important;
    font-family: var(--font-mono);
    font-size: 9pt;
    color: #888;
    border-bottom: 0.5px solid #ccc;
    padding-bottom: 8px;
    margin-bottom: 24px;
  }
}
```

**TopBar — add print header:**
Add a hidden div inside the `<main>` wrapper in page.tsx (complete phase), just before ResearchDocument:
```tsx
<div className="print-header hidden" style={{ display: "none" }}>
  Cortex Research — {displayResult.query}
  {displayResult.costUsd !== null && ` — $${displayResult.costUsd.toFixed(4)}`}
</div>
```

The print stylesheet makes this visible (`display: block !important`) only when printing.

**TopBar — mark as no-print:**
Add `data-no-print` attribute to the TopBar outer div so it's hidden during print:
```tsx
<div className="sticky top-0 z-10 ..." data-no-print>
```

Also add `data-no-print` to the ThemeToggle button and the scroll-to-top button (feature 6).

**Implementation for the Copy MD button:**
```tsx
const [copied, setCopied] = useState(false);

const handleCopyMd = useCallback(async () => {
  try {
    await navigator.clipboard.writeText(result.document ?? "");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  } catch {
    // Fallback for older browsers
    const ta = document.createElement("textarea");
    ta.value = result.document ?? "";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }
}, [result.document]);
```

Add the required import at the top of TopBar.tsx:
```tsx
import { useState, useCallback } from "react";
```

The `result` prop needs the `document` field. Update the ResearchResult type if needed — but check first: `result.document` is likely already passed through since it's in the ResearchResult interface. If TopBar doesn't currently receive the document string, you need to pass it. Check page.tsx — `displayResult` has a `document` field. The TopBar prop type `ResearchResult` in lib/research.ts already includes `document: string`. So it should work. If not, add `document` to the props.
</changes>

<preserve>
- Do NOT install any npm packages (no html2pdf, no jspdf) — use window.print() for PDF
- Do NOT change the document rendering in ResearchDocument.tsx
- Do NOT add a separate export modal or dialog — two inline buttons, that's it
- Do NOT change the sticky positioning or z-index of TopBar
- Export PDF button calls window.print() directly — the browser handles Save as PDF
- The print stylesheet handles URL expansion for links — shows href in parentheses after link text
- Citation links do NOT get href expansion (would be ugly with #source-N)
</preserve>
</feature>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 4: OG / social meta tags                   -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="4" file="app/layout.tsx">
<problem>
No Open Graph or Twitter Card meta tags. Sharing the Cortex URL on Twitter/LinkedIn/Slack shows a blank preview with no image, no description. The preview card IS the marketing — without it, link shares get ~70% less engagement.
</problem>

<changes>
Add meta tags inside the Next.js `metadata` export in layout.tsx. Replace the existing metadata object:

```tsx
export const metadata: Metadata = {
  title: "Cortex — Deep Research Engine",
  description: "Multi-pass research with gap detection, source verification, and cumulative memory. Cheaper than Perplexity. Gets smarter with each use.",
  metadataBase: new URL("https://cortex.example.com"), // placeholder — update when deployed
  openGraph: {
    title: "Cortex — Deep Research Engine",
    description: "Search, verify, remember. Open-source deep research at ~10x lower cost.",
    type: "website",
    siteName: "Cortex",
  },
  twitter: {
    card: "summary_large_image",
    title: "Cortex — Deep Research Engine",
    description: "Search, verify, remember. Open-source deep research at ~10x lower cost.",
  },
};
```

**Create an OG image:**
Create a simple static SVG file at `frontend/public/og-image.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#faf8f5"/>
  <text x="600" y="270" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="64" font-weight="700" fill="#1a1a1a" letter-spacing="-2">Cortex</text>
  <text x="600" y="330" text-anchor="middle" font-family="'Courier New', monospace" font-size="16" fill="#888" letter-spacing="3" text-transform="uppercase">SEARCH, VERIFY, REMEMBER.</text>
  <line x1="500" y1="370" x2="700" y2="370" stroke="#e5e2dd" stroke-width="1"/>
  <text x="600" y="410" text-anchor="middle" font-family="'Courier New', monospace" font-size="14" fill="#bbb">open-source deep research engine</text>
</svg>
```

Then convert it to a PNG for better social media compatibility. Since we can't run image conversion in the frontend build, create the OG image as a simple HTML-to-static approach:

Actually, the simplest approach — create a static PNG. Use Next.js built-in OG image generation:

Create `frontend/app/opengraph-image.tsx`:
```tsx
import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Cortex — Deep Research Engine";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OGImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#faf8f5",
          fontFamily: "serif",
        }}
      >
        <div
          style={{
            fontSize: 64,
            fontWeight: 700,
            color: "#1a1a1a",
            letterSpacing: "-2px",
            marginBottom: 12,
          }}
        >
          Cortex
        </div>
        <div
          style={{
            fontSize: 16,
            color: "#888",
            letterSpacing: "3px",
            textTransform: "uppercase",
            fontFamily: "monospace",
            marginBottom: 32,
          }}
        >
          SEARCH, VERIFY, REMEMBER.
        </div>
        <div
          style={{
            width: 200,
            height: 1,
            backgroundColor: "#e5e2dd",
            marginBottom: 32,
          }}
        />
        <div
          style={{
            fontSize: 14,
            color: "#bbb",
            fontFamily: "monospace",
          }}
        >
          open-source deep research engine
        </div>
      </div>
    ),
    { ...size }
  );
}
```

This auto-generates the OG image at build time. Next.js 14 handles the routing — `/opengraph-image` serves the PNG and the metadata automatically includes it.

Also create `frontend/app/twitter-image.tsx` — same file, just copy it:
```tsx
// Exact same content as opengraph-image.tsx
```
</changes>

<preserve>
- Do NOT install any image generation packages — Next.js ImageResponse is built-in
- Do NOT create a static PNG file manually — let Next.js generate it
- Do NOT change the layout structure or fonts loading
- The metadataBase URL is a placeholder — leave a comment to update it on deployment
- Keep the editorial aesthetic in the OG image: cream bg, serif title, mono tagline
</preserve>
</feature>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 5: Error boundary                          -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="5" file="components/ErrorBoundary.tsx (new), app/page.tsx">
<problem>
If ResearchDocument throws (malformed markdown, unexpected data shape from API), the entire page white-screens with no recovery. No error boundary exists. This is a production-grade gap that signals "demo, not real app" to anyone reviewing the code.
</problem>

<changes>
**Create `components/ErrorBoundary.tsx`:**
```tsx
"use client";

import { Component, type ReactNode, type ErrorInfo } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[Cortex] Component error:", error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "50vh",
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
            Something went wrong
          </h2>
          <p
            className="meta-text"
            style={{
              color: "var(--fg-muted)",
              marginBottom: 24,
              maxWidth: 400,
            }}
          >
            {this.state.error?.message || "An unexpected error occurred while rendering the document."}
          </p>
          <button
            onClick={this.handleReset}
            className="meta-text"
            style={{
              color: "var(--fg-muted)",
              background: "none",
              border: "none",
              cursor: "pointer",
              textDecoration: "underline",
              textUnderlineOffset: 3,
            }}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Wrap content in page.tsx:**
Import ErrorBoundary at the top:
```tsx
import ErrorBoundary from "@/components/ErrorBoundary";
```

Wrap the complete phase content (the ResearchDocument specifically) in an ErrorBoundary:
```tsx
{phase === "complete" && displayResult && (
  <div className={anim}>
    <TopBar result={displayResult} onNewResearch={handleNewResearch} />
    <main className="max-w-3xl mx-auto px-6 pt-10 pb-24">
      <ErrorBoundary onReset={handleNewResearch}>
        <div className="print-header hidden" style={{ display: "none" }}>
          Cortex Research — {displayResult.query}
          {displayResult.costUsd !== null && ` — $${displayResult.costUsd.toFixed(4)}`}
        </div>
        <ResearchDocument markdown={displayResult.document} />
      </ErrorBoundary>
    </main>
  </div>
)}
```

The `onReset` calls `handleNewResearch` — returns user to idle phase so they can try again.
</changes>

<preserve>
- Do NOT use functional error boundaries (not supported in React 18 without libraries)
- Do NOT install any error boundary packages — write the class component directly
- Do NOT add error tracking/reporting services (Sentry, etc.)
- Do NOT wrap the entire app — only wrap the document rendering area
- Do NOT catch errors in the research/streaming phase — those are already handled by useResearch hook
- The error boundary is a class component — this is required by React, not a style choice
- The fallback UI uses the same editorial aesthetic: serif heading, mono text, underlined button
</preserve>
</feature>

<!-- ═══════════════════════════════════════════════════ -->
<!-- FEATURE 6: Scroll-to-top button                    -->
<!-- ═══════════════════════════════════════════════════ -->

<feature id="6" file="components/ScrollToTop.tsx (new), app/page.tsx">
<problem>
Deep research produces 10-15K character documents. After reading to the Sources section at the bottom, getting back to TopBar requires extensive scrolling, especially on mobile. No navigation affordance exists.
</problem>

<changes>
**Create `components/ScrollToTop.tsx`:**
```tsx
"use client";

import { useState, useEffect, useCallback } from "react";

export default function ScrollToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    function onScroll() {
      setVisible(window.scrollY > 500);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollUp = useCallback(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  if (!visible) return null;

  return (
    <button
      onClick={scrollUp}
      data-no-print
      className="fixed z-40 cursor-pointer meta-text"
      style={{
        bottom: "calc(48px + env(safe-area-inset-bottom))",
        right: "calc(4px + env(safe-area-inset-right))",
        padding: "12px 16px",
        color: "var(--fg-faint)",
        background: "none",
        border: "none",
        transition: "color 0.2s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--fg-muted)")}
      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--fg-faint)")}
      aria-label="Scroll to top"
    >
      ↑
    </button>
  );
}
```

**Add to page.tsx:**
Import at the top:
```tsx
import ScrollToTop from "@/components/ScrollToTop";
```

Render it only in the complete phase, inside the `{phase === "complete" && ...}` block, after `</main>`:
```tsx
{phase === "complete" && displayResult && (
  <div className={anim}>
    <TopBar result={displayResult} onNewResearch={handleNewResearch} />
    <main className="max-w-3xl mx-auto px-6 pt-10 pb-24">
      <ErrorBoundary onReset={handleNewResearch}>
        ...
      </ErrorBoundary>
    </main>
    <ScrollToTop />
  </div>
)}
```

Position: bottom-right, above the ThemeToggle (48px + safe area vs ThemeToggle's 16px + safe area). Same editorial style — monospace, faint, minimal. Only appears after 500px scroll. Hidden during print via `data-no-print`.
</changes>

<preserve>
- Do NOT use a library for scroll-to-top
- Do NOT add scroll animation to ThemeToggle — only ScrollToTop
- Do NOT show ScrollToTop in idle or researching phases
- Do NOT change the ThemeToggle position — ScrollToTop sits above it
- The arrow character ↑ is intentional — no icon library, no SVG, just a character in mono font
- Passive scroll listener for performance
- Do NOT add a background/border/shadow to the button — text only, matches ThemeToggle style
</preserve>
</feature>

</features>

<verification>
After all 6 features:

1. `npx tsc --noEmit` — no TypeScript errors
2. `npm run build` — builds successfully, OG image generates
3. Mobile emulator (iPhone 14 Pro):
   - Idle: search input visible without scrolling (clamp padding)
   - Complete: cost visible in TopBar on mobile
   - Complete: "Copy MD" and "Export PDF" buttons visible and functional
   - Complete: scroll down 500px+ → "↑" button appears bottom-right
   - Complete: tap "↑" → smooth scroll to top
4. Desktop:
   - Complete: click "Copy MD" → markdown in clipboard, button shows "Copied" for 2s
   - Complete: click "Export PDF" → print dialog opens, clean document without UI chrome
   - Complete: print preview shows query header at top, URLs after links, no buttons/toggles
5. OG image: check `/opengraph-image` route returns a PNG with cream bg, "Cortex" serif title
6. Error boundary: temporarily throw in ResearchDocument render → should show "Something went wrong" with "Try again" button, not white screen
7. View page source → og:title, og:description, twitter:card tags present
</verification>

<do_not>
- Do NOT install any new npm packages
- Do NOT modify backend files
- Do NOT modify hooks/useResearch.ts or hooks/useHistory.ts
- Do NOT modify lib/research.ts
- Do NOT change the three-phase flow or transition logic
- Do NOT change colors, fonts, or the editorial aesthetic
- Do NOT modify PipelineProgress.tsx, SearchInput.tsx, or HistoryList.tsx
- Do NOT add routing (no /research/[id] page — that's P2)
- Do NOT add a modal, dialog, or dropdown for export — two inline buttons in TopBar
- Do NOT use any external image generation service for OG image
</do_not>

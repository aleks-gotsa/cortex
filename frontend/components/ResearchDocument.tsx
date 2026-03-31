"use client";

import { useState, useMemo, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import type { SourceInfo } from "@/lib/research";

interface ResearchDocumentProps {
  markdown: string;
  sources?: readonly SourceInfo[] | null;
}

interface ActiveCitation {
  num: number;
  rect: DOMRect;
}

/* ── Markdown helpers ──────────────────────────────────── */

function processCitations(text: string): (string | JSX.Element)[] {
  const parts: (string | JSX.Element)[] = [];
  const regex = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const num = match[1];
    parts.push(
      <a
        key={`${match.index}-${num}`}
        href={`#source-${num}`}
        data-citation={num}
        className="citation-link"
      >
        [{num}]
      </a>
    );
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

function processSourceLine(
  text: string
): { num: string; url: string; title: string } | null {
  const match = text.match(/^(?:\[(\d+)\]|(\d+)\.)\s+(https?:\/\/\S+)(.*)/);
  if (match) {
    const num = match[1] || match[2];
    const url = match[3];
    const rest = (match[4] || "").trim().replace(/^[-\u2013\u2014:]\s*/, "");
    let title = rest;
    if (!title) {
      try {
        title = new URL(url).hostname.replace(/^www\./, "");
      } catch {
        title = url;
      }
    }
    return { num, url, title };
  }
  return null;
}

function processChildren(children: React.ReactNode): React.ReactNode {
  if (typeof children === "string") {
    const parts = processCitations(children);
    return parts.length === 1 && typeof parts[0] === "string"
      ? parts[0]
      : parts;
  }

  if (Array.isArray(children)) {
    return children.map((child, i) => {
      if (typeof child === "string") {
        const parts = processCitations(child);
        return parts.length === 1 && typeof parts[0] === "string" ? (
          parts[0]
        ) : (
          <span key={i}>{parts}</span>
        );
      }
      return child;
    });
  }

  return children;
}

function extractText(children: React.ReactNode): string {
  if (typeof children === "string") return children;
  if (typeof children === "number") return String(children);
  if (Array.isArray(children)) return children.map(extractText).join("");
  if (
    children &&
    typeof children === "object" &&
    "props" in children &&
    (children as { props?: { children?: React.ReactNode } }).props
  ) {
    return extractText(
      (children as { props: { children?: React.ReactNode } }).props.children
    );
  }
  return "";
}

function truncateUrl(url: string, max: number): string {
  if (url.length <= max) return url;
  return url.slice(0, max - 1) + "\u2026";
}

function stripSourcesSection(md: string): string {
  return md.replace(/\n##\s+(?:Sources|References)\b[\s\S]*$/, "");
}

/* ── Component ─────────────────────────────────────────── */

export default function ResearchDocument({
  markdown,
  sources,
}: ResearchDocumentProps) {
  const [activeCitation, setActiveCitation] = useState<ActiveCitation | null>(
    null
  );
  const [sourcesExpanded, setSourcesExpanded] = useState(false);

  const hasSources = Boolean(sources?.length);

  const displayMarkdown = useMemo(
    () => (hasSources ? stripSourcesSection(markdown) : markdown),
    [markdown, hasSources]
  );

  // Close popover on scroll
  useEffect(() => {
    if (!activeCitation) return;
    const onScroll = () => setActiveCitation(null);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [activeCitation]);

  // Close popover on click outside
  useEffect(() => {
    if (!activeCitation) return;
    function onMouseDown(e: MouseEvent) {
      const target = e.target as HTMLElement;
      if (
        target.closest(".citation-popover") ||
        target.closest("[data-citation]")
      )
        return;
      setActiveCitation(null);
    }
    document.addEventListener("mousedown", onMouseDown);
    return () => document.removeEventListener("mousedown", onMouseDown);
  }, [activeCitation]);

  // Citation click via event delegation
  const handleContainerClick = useCallback(
    (e: React.MouseEvent) => {
      const target = e.target as HTMLElement;
      const citationEl = target.closest(
        "[data-citation]"
      ) as HTMLElement | null;
      if (!citationEl) return;

      const num = parseInt(citationEl.getAttribute("data-citation")!, 10);

      if (hasSources && sources![num - 1]) {
        e.preventDefault();
        if (activeCitation?.num === num) {
          setActiveCitation(null);
        } else {
          setActiveCitation({
            num,
            rect: citationEl.getBoundingClientRect(),
          });
        }
      }
      // else: default anchor scroll to #source-N
    },
    [hasSources, sources, activeCitation]
  );

  const activeSource = activeCitation
    ? sources?.[activeCitation.num - 1] ?? null
    : null;

  const popoverStyle = useMemo((): React.CSSProperties | null => {
    if (!activeCitation) return null;
    const { rect } = activeCitation;
    const ESTIMATE = 140;
    const above = rect.bottom + ESTIMATE + 16 > window.innerHeight;
    const left = Math.max(16, Math.min(rect.left, window.innerWidth - 336));

    const base: React.CSSProperties = {
      position: "fixed",
      left,
      background: "var(--bg)",
      border: "1px solid var(--border)",
      boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
      padding: "14px 16px",
      maxWidth: 320,
      zIndex: 1000,
    };

    return above
      ? { ...base, bottom: window.innerHeight - rect.top + 8 }
      : { ...base, top: rect.bottom + 8 };
  }, [activeCitation]);

  const components: Components = useMemo(
    () => ({
      p({ children, ...props }) {
        return <p {...props}>{processChildren(children)}</p>;
      },
      li({ children, ...props }) {
        if (!hasSources) {
          const textContent = extractText(children);
          const sourceLine = processSourceLine(textContent);
          if (sourceLine) {
            return (
              <li
                id={`source-${sourceLine.num}`}
                className="source-item"
                {...props}
              >
                <span className="text-[var(--fg-faint)]">
                  [{sourceLine.num}]
                </span>{" "}
                <a
                  href={sourceLine.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {sourceLine.title}
                </a>
              </li>
            );
          }
        }
        return <li {...props}>{processChildren(children)}</li>;
      },
      strong({ children, ...props }) {
        return <strong {...props}>{processChildren(children)}</strong>;
      },
      em({ children, ...props }) {
        return <em {...props}>{processChildren(children)}</em>;
      },
      h2({ children, ...props }) {
        const text = extractText(children);
        const id = text.toLowerCase().replace(/[^a-z0-9]+/g, "-");
        const isSourcesHeading =
          text.toLowerCase() === "sources" ||
          text.toLowerCase() === "references";
        return (
          <h2 id={isSourcesHeading ? "sources-section" : id} {...props}>
            {children}
          </h2>
        );
      },
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      a({ href, children, node, ...props }) {
        return (
          <a {...props} href={href} target="_blank" rel="noopener noreferrer">
            {children}
          </a>
        );
      },
    }),
    [hasSources]
  );

  return (
    <>
      <div className="prose-editorial" onClick={handleContainerClick}>
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
          {displayMarkdown}
        </ReactMarkdown>
      </div>

      {/* ── Citation popover ───────────────────────────── */}
      {activeCitation && activeSource && popoverStyle && (
        <div className="citation-popover" style={popoverStyle}>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              textTransform: "uppercase",
              color: "var(--fg-muted)",
              marginBottom: 6,
            }}
          >
            SOURCE {activeCitation.num}
          </div>
          <a
            href={activeSource.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: 13,
              fontWeight: 500,
              color: "var(--fg)",
              textDecoration: "none",
              display: "block",
            }}
          >
            {activeSource.title || activeSource.url}
          </a>
          {activeSource.snippet && (
            <p
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: 12,
                color: "var(--fg-muted)",
                lineHeight: 1.5,
                margin: "4px 0 6px",
                display: "-webkit-box",
                WebkitLineClamp: 3,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}
            >
              {activeSource.snippet}
            </p>
          )}
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              color: "var(--accent)",
              marginTop: 6,
            }}
          >
            {truncateUrl(activeSource.url, 40)}
          </div>
        </div>
      )}

      {/* ── Collapsible sources panel ──────────────────── */}
      {hasSources && (
        <div style={{ borderTop: "1px solid var(--border)", marginTop: 32 }}>
          <button
            onClick={() => setSourcesExpanded((prev) => !prev)}
            style={{
              width: "100%",
              padding: "12px 0",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              background: "none",
              border: "none",
              cursor: "pointer",
              fontFamily: "var(--font-mono)",
              fontSize: 12,
              color: "var(--fg-muted)",
              transition: "color 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--fg)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--fg-muted)";
            }}
          >
            <span>{sources!.length} sources</span>
            <span
              style={{
                transition: "transform 0.2s",
                transform: sourcesExpanded
                  ? "rotate(180deg)"
                  : "rotate(0deg)",
                fontSize: 14,
              }}
            >
              ↓
            </span>
          </button>
          {sourcesExpanded && (
            <div>
              {sources!.map((s, i) => (
                <div
                  key={i}
                  style={{
                    padding: "8px 0",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 12,
                      color: "var(--accent)",
                      textDecoration: "none",
                    }}
                  >
                    [{i + 1}] {s.title || s.url}
                  </a>
                  {s.snippet && (
                    <p
                      style={{
                        fontFamily: "var(--font-sans)",
                        fontSize: 12,
                        color: "var(--fg-muted)",
                        margin: "4px 0 0",
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                        lineHeight: 1.5,
                      }}
                    >
                      {s.snippet}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}

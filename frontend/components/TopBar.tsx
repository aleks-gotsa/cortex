"use client";

import { useState, useCallback } from "react";
import type { ResearchResult } from "@/lib/research";

interface TopBarProps {
  result: ResearchResult;
  onNewResearch: () => void;
}

export default function TopBar({ result, onNewResearch }: TopBarProps) {
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

  const handleExportPdf = useCallback(() => {
    window.print();
  }, []);

  return (
    <div className="sticky top-0 z-10 bg-[var(--bg)] border-b border-[var(--border)] animate-slide-down"
         style={{ paddingTop: "env(safe-area-inset-top)" }}
         data-no-print>
      <div className="max-w-3xl mx-auto px-6 py-3 flex flex-wrap items-center justify-between gap-x-6 gap-y-1">
        <span className="font-serif text-sm text-[var(--fg)] truncate min-w-0">
          {result.query}
        </span>

        <div className="flex items-center gap-4 flex-shrink-0">
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
          <button
            onClick={handleCopyMd}
            className="meta-text text-[var(--fg-muted)] hover:text-[var(--fg)] transition-colors underline underline-offset-2"
          >
            {copied ? "Copied" : "Copy MD"}
          </button>
          <button
            onClick={handleExportPdf}
            className="meta-text text-[var(--fg-muted)] hover:text-[var(--fg)] transition-colors underline underline-offset-2"
          >
            Export PDF
          </button>
          <button
            onClick={onNewResearch}
            className="meta-text text-[var(--fg-muted)] hover:text-[var(--fg)] transition-colors underline underline-offset-2"
          >
            New research
          </button>
        </div>
      </div>
    </div>
  );
}

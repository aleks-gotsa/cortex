"use client";

import type { ResearchResult } from "@/lib/research";

interface TopBarProps {
  result: ResearchResult;
  onNewResearch: () => void;
}

export default function TopBar({ result, onNewResearch }: TopBarProps) {
  const meta: string[] = [];
  if (result.sourcesCount > 0) meta.push(`${result.sourcesCount} sources`);
  if (result.passCount > 0)
    meta.push(`${result.passCount} pass${result.passCount > 1 ? "es" : ""}`);
  if (result.costUsd !== null) meta.push(`$${result.costUsd.toFixed(4)}`);

  return (
    <div className="sticky top-0 z-10 bg-[var(--bg)] border-b border-[var(--border)] animate-slide-down"
         style={{ paddingTop: "env(safe-area-inset-top)" }}>
      <div className="max-w-3xl mx-auto px-6 py-3 flex flex-wrap items-center justify-between gap-x-6 gap-y-1">
        <span className="font-serif text-sm text-[var(--fg)] truncate min-w-0">
          {result.query}
        </span>

        <div className="flex items-center gap-4 flex-shrink-0">
          {meta.length > 0 && (
            <span className="meta-text text-[var(--fg-muted)] hidden sm:inline">
              {meta.join(" \u00b7 ")}
            </span>
          )}
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

"use client";

import { useState, useCallback } from "react";
import type { ResearchResult } from "@/lib/research";
import SettingsModal from "@/components/SettingsModal";

interface TopBarProps {
  result: ResearchResult;
  onNewResearch: () => void;
}

export default function TopBar({ result, onNewResearch }: TopBarProps) {
  const [copied, setCopied] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

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
    <>
    <div className="fixed top-0 left-0 right-0 z-10 bg-[var(--bg)] border-b border-[var(--border)] animate-slide-down"
         style={{ paddingTop: "env(safe-area-inset-top)" }}
         data-no-print>
      <div className="max-w-3xl mx-auto px-6 py-3 flex flex-wrap items-center justify-between gap-x-6 gap-y-1">
        <span className="meta-text text-[var(--fg)] truncate min-w-0">
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
          <button
            onClick={() => setSettingsOpen(true)}
            className="text-[var(--fg-muted)] hover:text-[var(--fg)] transition-colors"
            aria-label="Settings"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
    <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}

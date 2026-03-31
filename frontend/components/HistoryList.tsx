"use client";

import { useState, useCallback, useEffect } from "react";
import type { HistoryRun } from "@/lib/research";
import { formatRelativeTime } from "@/lib/research";

interface HistoryListProps {
  runs: readonly HistoryRun[];
  loading: boolean;
  loadingId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function HistoryList({
  runs,
  loading,
  loadingId,
  onSelect,
  onDelete,
}: HistoryListProps) {
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const handleConfirmDelete = useCallback(() => {
    if (deleteId) {
      onDelete(deleteId);
      setDeleteId(null);
    }
  }, [deleteId, onDelete]);

  useEffect(() => {
    if (!deleteId) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setDeleteId(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [deleteId]);

  const completedRuns = runs.filter((r) => r.status === "completed");

  if (loading) {
    return (
      <p className="meta-text text-[var(--fg-faint)]">
        Loading&hellip;
      </p>
    );
  }

  if (completedRuns.length === 0) return null;

  return (
    <>
    <div className="space-y-0">
      {completedRuns.map((run) => (
        <div
          key={run.id}
          className="flex items-center gap-1 border-b border-transparent hover:border-[var(--border)] group/row"
        >
          <button
            onClick={() => onSelect(run.id)}
            disabled={loadingId === run.id}
            className="flex-1 min-w-0 text-left py-3.5 group transition-colors disabled:opacity-40"
          >
            <div className="flex items-baseline justify-between gap-4">
              <span className="font-serif text-sm text-[var(--fg-muted)] group-hover:text-[var(--fg)] transition-colors leading-snug truncate">
                {loadingId === run.id ? "Loading\u2026" : run.query}
              </span>
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
            </div>
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setDeleteId(run.id);
            }}
            className="flex-shrink-0 px-1.5 py-1 opacity-0 group-hover/row:opacity-100 transition-opacity"
            style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "#bbb" }}
            onMouseEnter={(e) => { (e.currentTarget.style.color = "#c53030"); }}
            onMouseLeave={(e) => { (e.currentTarget.style.color = "#bbb"); }}
            aria-label="Delete research"
          >
            &#x2715;
          </button>
        </div>
      ))}
    </div>

    {/* ── Delete confirmation dialog ─────────────────── */}
    {deleteId && (
      <div
        onClick={() => setDeleteId(null)}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 9999,
        }}
      >
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            background: "var(--bg)",
            border: "1px solid var(--border)",
            padding: 24,
            borderRadius: 4,
            width: "100%",
            maxWidth: 360,
          }}
        >
          <h2
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: 18,
              fontWeight: 700,
              color: "var(--fg)",
              margin: 0,
            }}
          >
            Delete research
          </h2>
          <p
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: 14,
              color: "var(--fg-muted)",
              margin: "12px 0 24px",
            }}
          >
            This cannot be undone.
          </p>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
            <button
              onClick={() => setDeleteId(null)}
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 12,
                textTransform: "uppercase",
                padding: "8px 16px",
                background: "transparent",
                border: "1px solid var(--border)",
                color: "var(--fg-muted)",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleConfirmDelete}
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 12,
                textTransform: "uppercase",
                padding: "8px 16px",
                background: "#1a1a1a",
                border: "none",
                color: "var(--bg)",
                cursor: "pointer",
              }}
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    )}
    </>
  );
}

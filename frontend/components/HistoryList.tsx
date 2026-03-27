"use client";

import type { HistoryRun } from "@/lib/research";
import { formatRelativeTime } from "@/lib/research";

interface HistoryListProps {
  runs: readonly HistoryRun[];
  loading: boolean;
  loadingId: string | null;
  onSelect: (id: string) => void;
}

export default function HistoryList({
  runs,
  loading,
  loadingId,
  onSelect,
}: HistoryListProps) {
  const completedRuns = runs.filter((r) => r.status === "completed");

  if (loading) {
    return (
      <p className="font-mono text-[11px] text-[var(--fg-faint)]">
        Loading&hellip;
      </p>
    );
  }

  if (completedRuns.length === 0) return null;

  return (
    <div className="space-y-0">
      {completedRuns.map((run) => (
        <button
          key={run.id}
          onClick={() => onSelect(run.id)}
          disabled={loadingId === run.id}
          className="w-full text-left py-2.5 group transition-colors disabled:opacity-40 border-b border-transparent hover:border-[var(--border)]"
        >
          <div className="flex items-baseline justify-between gap-4">
            <span className="font-serif text-sm text-[var(--fg-muted)] group-hover:text-[var(--fg)] transition-colors leading-snug truncate">
              {loadingId === run.id ? "Loading\u2026" : run.query}
            </span>
            <span className="font-mono text-[11px] text-[var(--fg-faint)] flex-shrink-0 whitespace-nowrap">
              {run.cost_usd != null && (
                <span className="mr-2">${run.cost_usd.toFixed(4)}</span>
              )}
              {formatRelativeTime(run.created_at)}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}

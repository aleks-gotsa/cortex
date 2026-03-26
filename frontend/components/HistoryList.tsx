"use client";

import { useState, useEffect, useCallback } from "react";

// Uses Next.js rewrite proxy: /api/* → http://localhost:8000/*

interface HistoryRun {
  id: string;
  query: string;
  depth: string;
  status: string;
  cost_usd: number | null;
  created_at: string;
  completed_at: string | null;
}

interface HistoryListProps {
  onSelect: (markdown: string, query: string) => void;
  refreshTrigger: number;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;

  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function truncateQuery(query: string, maxLen: number = 60): string {
  if (query.length <= maxLen) return query;
  return query.slice(0, maxLen).trimEnd() + "\u2026";
}

export default function HistoryList({
  onSelect,
  refreshTrigger,
}: HistoryListProps) {
  const [runs, setRuns] = useState<readonly HistoryRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(true);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch("/api/research/history");
      if (!res.ok) return;
      const data: unknown = await res.json();
      if (Array.isArray(data)) {
        setRuns(data as HistoryRun[]);
      }
    } catch {
      // silently fail — history is non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory, refreshTrigger]);

  const handleClick = useCallback(
    async (runId: string) => {
      if (loadingId) return;
      setLoadingId(runId);

      try {
        const res = await fetch(`/api/research/${runId}`);
        if (!res.ok) return;
        const detail: unknown = await res.json();
        const d = detail as Record<string, unknown>;

        if (
          d &&
          typeof d === "object" &&
          d.result &&
          typeof (d.result as Record<string, unknown>).document_md === "string" &&
          d.run &&
          typeof (d.run as Record<string, unknown>).query === "string"
        ) {
          onSelect(
            (d.result as Record<string, unknown>).document_md as string,
            (d.run as Record<string, unknown>).query as string
          );
        }
      } catch {
        // silently fail
      } finally {
        setLoadingId(null);
      }
    },
    [loadingId, onSelect]
  );

  const completedRuns = runs.filter((r) => r.status === "completed");

  if (loading) {
    return (
      <div className="text-sm text-zinc-500 px-3 py-4">
        Loading history...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with collapse toggle (mobile) */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center justify-between px-3 py-3 text-sm font-medium text-zinc-400 hover:text-zinc-200 transition-colors lg:cursor-default"
      >
        <span>History</span>
        <span className="lg:hidden text-zinc-600">
          {isOpen ? (
            <ChevronUp />
          ) : (
            <span className="flex items-center gap-1.5">
              <span className="text-xs text-zinc-500">
                {completedRuns.length}
              </span>
              <ChevronDown />
            </span>
          )}
        </span>
      </button>

      {/* List */}
      <div
        className={`overflow-y-auto flex-1 ${
          isOpen ? "block" : "hidden lg:block"
        }`}
      >
        {completedRuns.length === 0 ? (
          <div className="px-3 py-2 text-xs text-zinc-600">
            No research yet
          </div>
        ) : (
          <div className="space-y-0.5 px-1">
            {completedRuns.map((run) => (
              <button
                key={run.id}
                onClick={() => handleClick(run.id)}
                disabled={loadingId === run.id}
                className="w-full text-left rounded-md px-2.5 py-2 hover:bg-zinc-800/60 transition-colors group disabled:opacity-50"
              >
                <div className="text-sm text-zinc-300 group-hover:text-zinc-100 leading-snug">
                  {loadingId === run.id ? (
                    <span className="text-zinc-500">Loading...</span>
                  ) : (
                    truncateQuery(run.query)
                  )}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-zinc-600">
                    {formatDate(run.created_at)}
                  </span>
                  {run.cost_usd != null && (
                    <span className="text-xs text-zinc-600">
                      ${run.cost_usd.toFixed(4)}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ChevronUp() {
  return (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
    </svg>
  );
}

function ChevronDown() {
  return (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

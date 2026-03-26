"use client";

import { useState, useCallback, useRef } from "react";
import ProgressStream, {
  StageInfo,
  getStageName,
  getStageMetric,
} from "@/components/ProgressStream";

type Depth = "quick" | "standard" | "deep";

interface ParsedSSEEvent {
  event: string;
  data: Record<string, unknown>;
}

interface ResearchInputProps {
  onComplete: (markdown: string, query: string) => void;
}

function parseSSEChunk(chunk: string): ParsedSSEEvent | null {
  let event = "";
  let dataLine = "";

  for (const line of chunk.split("\n")) {
    if (line.startsWith("event: ")) {
      event = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      dataLine = dataLine ? dataLine + "\n" + line.slice(6) : line.slice(6);
    }
  }

  if (!event || !dataLine) return null;

  try {
    return { event, data: JSON.parse(dataLine) };
  } catch {
    return null;
  }
}

export function ResearchInput({ onComplete }: ResearchInputProps) {
  const [query, setQuery] = useState("");
  const [depth, setDepth] = useState<Depth>("standard");
  const [isRunning, setIsRunning] = useState(false);
  const [stages, setStages] = useState<StageInfo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = query.trim();
      if (!trimmed || isRunning) return;

      setStages([]);
      setError(null);
      setIsRunning(true);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const res = await fetch("/api/research", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: trimmed, depth, use_memory: true }),
          signal: controller.signal,
        });

        if (!res.ok || !res.body) {
          throw new Error(`Request failed: ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";

          for (const part of parts) {
            const parsed = parseSSEChunk(part);
            if (!parsed) continue;

            const { event, data } = parsed;

            if (event === "complete") {
              setStages((prev) => {
                const updated = prev.map((s) =>
                  s.status === "active"
                    ? { ...s, status: "done" as const }
                    : s
                );
                return [
                  ...updated,
                  {
                    stage: "complete",
                    displayName: "Complete",
                    metric: getStageMetric("complete", data),
                    status: "done" as const,
                  },
                ];
              });

              if (typeof data.document === "string") {
                onComplete(data.document, trimmed);
              }
              setIsRunning(false);
              reader.cancel();
              break;
            }

            const newStage: StageInfo = {
              stage: event,
              displayName: getStageName(event, data),
              metric: getStageMetric(event, data),
              status: "active",
            };

            setStages((prev) => {
              const updated = prev.map((s) =>
                s.status === "active"
                  ? { ...s, status: "done" as const }
                  : s
              );
              return [...updated, newStage];
            });
          }
        }

        // Stream ended without a complete event — surface error.
        setStages((prev) => {
          const hasComplete = prev.some((s) => s.stage === "complete");
          if (!hasComplete && prev.length > 0) {
            setError("Research stream ended unexpectedly.");
            return prev.map((s) =>
              s.status === "active" ? { ...s, status: "done" as const } : s
            );
          }
          return prev;
        });
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        const msg =
          err instanceof Error ? err.message : "An unknown error occurred";
        setError(msg);
      } finally {
        setIsRunning(false);
        abortRef.current = null;
      }
    },
    [query, depth, isRunning, onComplete]
  );

  return (
    <div className="w-full space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isRunning}
            placeholder="What do you want to research?"
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-3 text-lg text-white placeholder-gray-500 outline-none transition focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={depth}
            onChange={(e) => setDepth(e.target.value as Depth)}
            disabled={isRunning}
            className="rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-300 outline-none transition focus:border-blue-500 disabled:opacity-50"
          >
            <option value="quick">Quick (1 pass)</option>
            <option value="standard">Standard (2 passes)</option>
            <option value="deep">Deep (3 passes)</option>
          </select>

          <button
            type="submit"
            disabled={isRunning || !query.trim()}
            className="rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isRunning ? "Researching\u2026" : "Research"}
          </button>
        </div>
      </form>

      {error && (
        <div className="rounded-md border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <ProgressStream stages={stages} />
    </div>
  );
}

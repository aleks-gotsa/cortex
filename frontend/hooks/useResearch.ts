"use client";

import { useState, useCallback, useRef } from "react";
import {
  type Depth,
  type StageInfo,
  type ResearchResult,
  parseSSEChunk,
  getStageName,
  getStageMetric,
  apiUrl,
} from "@/lib/research";

interface UseResearchReturn {
  start: (query: string, depth: Depth) => void;
  cancel: () => void;
  isRunning: boolean;
  stages: StageInfo[];
  result: ResearchResult | null;
  error: string | null;
  reset: () => void;
}

export function useResearch(): UseResearchReturn {
  const [isRunning, setIsRunning] = useState(false);
  const [stages, setStages] = useState<StageInfo[]>([]);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const runningRef = useRef(false);

  const reset = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    runningRef.current = false;
    setStages([]);
    setResult(null);
    setError(null);
    setIsRunning(false);
  }, []);

  const cancel = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    runningRef.current = false;
    setIsRunning(false);
  }, []);

  const start = useCallback(
    async (query: string, depth: Depth) => {
      const trimmed = query.trim();
      if (!trimmed || runningRef.current) return;

      runningRef.current = true;
      setStages([]);
      setResult(null);
      setError(null);
      setIsRunning(true);

      const controller = new AbortController();
      abortRef.current = controller;
      let completed = false;

      try {
        const res = await fetch(apiUrl("/research"), {
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
        let gatheringCount = 0;
        let totalSources = 0;

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

            if (event === "gathering") {
              gatheringCount++;
              const sf = data.sources_found;
              if (typeof sf === "number") totalSources += sf;
            }

            if (event === "complete") {
              completed = true;

              setStages((prev) =>
                prev.map((s) =>
                  s.status === "active"
                    ? { ...s, status: "done" as const }
                    : s
                )
              );

              const doc =
                typeof data.document === "string" ? data.document : "";
              const costUsd =
                typeof data.cost_usd === "number" ? data.cost_usd : null;
              const sources = Array.isArray(data.sources) ? data.sources : [];
              const researchId =
                typeof data.research_id === "string"
                  ? data.research_id
                  : null;

              setResult({
                document: doc,
                query: trimmed,
                costUsd,
                sourcesCount: sources.length || totalSources,
                passCount: gatheringCount,
                researchId,
              });

              setIsRunning(false);
              runningRef.current = false;
              reader.cancel();
              break;
            }

            // Non-complete stage event
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

        if (!completed) {
          setStages((prev) =>
            prev.map((s) =>
              s.status === "active"
                ? { ...s, status: "done" as const }
                : s
            )
          );
          setError("Research stream ended unexpectedly.");
        }
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        const msg =
          err instanceof Error ? err.message : "An unknown error occurred";
        setError(msg);
      } finally {
        setIsRunning(false);
        runningRef.current = false;
        abortRef.current = null;
      }
    },
    [] // stable: uses only refs and setState
  );

  return { start, cancel, isRunning, stages, result, error, reset };
}

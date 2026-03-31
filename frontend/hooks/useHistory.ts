"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { type HistoryRun, apiUrl } from "@/lib/research";

interface LoadedDocument {
  markdown: string;
  query: string;
  costUsd: number | null;
}

interface UseHistoryReturn {
  runs: readonly HistoryRun[];
  loading: boolean;
  loadingId: string | null;
  loadDocument: (id: string) => Promise<LoadedDocument | null>;
  refresh: () => void;
}

export function useHistory(): UseHistoryReturn {
  const [runs, setRuns] = useState<readonly HistoryRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const loadingRef = useRef(false);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(apiUrl("/research/history"));
      if (!res.ok) return;
      const data: unknown = await res.json();
      if (Array.isArray(data)) {
        setRuns(data as HistoryRun[]);
      }
    } catch {
      // history is non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const loadDocument = useCallback(
    async (id: string): Promise<LoadedDocument | null> => {
      if (loadingRef.current) return null;
      loadingRef.current = true;
      setLoadingId(id);

      try {
        const res = await fetch(apiUrl(`/research/${id}`));
        if (!res.ok) return null;
        const detail: unknown = await res.json();
        const d = detail as Record<string, unknown>;

        if (
          d &&
          typeof d === "object" &&
          d.result &&
          typeof (d.result as Record<string, unknown>).document_md ===
            "string" &&
          d.run &&
          typeof (d.run as Record<string, unknown>).query === "string"
        ) {
          const run = d.run as Record<string, unknown>;
          const result = d.result as Record<string, unknown>;
          return {
            markdown: result.document_md as string,
            query: run.query as string,
            costUsd:
              typeof run.cost_usd === "number" ? run.cost_usd : null,
          };
        }
        return null;
      } catch {
        return null;
      } finally {
        loadingRef.current = false;
        setLoadingId(null);
      }
    },
    []
  );

  return { runs, loading, loadingId, loadDocument, refresh };
}

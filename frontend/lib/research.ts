function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  // In production without explicit URL, use relative paths (works with proxy/rewrites)
  if (typeof window !== "undefined" && window.location.hostname !== "localhost") {
    return "";
  }
  // Local development
  return "http://localhost:8000";
}

const API_BASE = getApiBase();

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export type Depth = "quick" | "standard" | "deep";

export interface StageInfo {
  stage: string;
  displayName: string;
  metric: string;
  status: "active" | "done";
}

export interface SourceInfo {
  url: string;
  title: string;
  snippet: string;
}

export interface ResearchResult {
  document: string;
  query: string;
  costUsd: number | null;
  sourcesCount: number;
  passCount: number;
  researchId: string | null;
  sources: SourceInfo[] | null;
}

export interface HistoryRun {
  id: string;
  query: string;
  depth: string;
  status: string;
  cost_usd: number | null;
  created_at: string;
  completed_at: string | null;
}

const STAGE_LABELS: Record<string, string> = {
  planning: "PLANNING",
  gathering: "GATHERING",
  gap_detection: "GAP DETECTION",
  synthesizing: "SYNTHESIZING",
  synthesis: "SYNTHESIZING",
  reranking: "RERANKING",
  verifying: "VERIFYING",
  memory: "MEMORY",
  complete: "COMPLETE",
};

export function getStageName(
  stage: string,
  data: Record<string, unknown>
): string {
  if (stage === "gathering") {
    const pass = data.pass as number | undefined;
    return pass ? `GATHERING \u00b7 PASS ${pass}` : "GATHERING";
  }
  if (stage === "reranking") {
    return "RERANKING";
  }
  return STAGE_LABELS[stage] ?? stage.toUpperCase();
}

export function getStageMetric(
  stage: string,
  data: Record<string, unknown>
): string {
  switch (stage) {
    case "planning": {
      const qs = data.sub_questions;
      return Array.isArray(qs) ? `${qs.length} sub-questions` : "";
    }
    case "gathering": {
      const n = data.sources_found;
      return typeof n === "number" ? `${n} sources found` : "";
    }
    case "gap_detection": {
      const gaps = data.gaps;
      if (Array.isArray(gaps)) {
        return gaps.length === 0
          ? "no gaps detected"
          : `${gaps.length} gap${gaps.length > 1 ? "s" : ""} detected`;
      }
      return "";
    }
    case "reranking": {
      const top = data.top_sources;
      const dropped = data.dropped;
      if (typeof top === "number" && typeof dropped === "number") {
        return `${top} kept, ${dropped} dropped`;
      }
      if (typeof top === "number") {
        return `${top} sources reranked`;
      }
      return "";
    }
    case "synthesizing":
    case "synthesis":
      return "building document";
    case "verifying": {
      const confirmed = data.confirmed;
      const weakened = data.weakened;
      if (typeof confirmed === "number" && typeof weakened === "number") {
        return `${confirmed} confirmed, ${weakened} weakened`;
      }
      return "";
    }
    case "memory": {
      const chunks = data.chunks_stored;
      return typeof chunks === "number" ? `${chunks} chunks stored` : "";
    }
    case "complete": {
      const cost = data.cost_usd;
      return typeof cost === "number" ? `$${cost.toFixed(4)}` : "";
    }
    default:
      return "";
  }
}

interface ParsedSSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export function parseSSEChunk(chunk: string): ParsedSSEEvent | null {
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

export function formatRelativeTime(dateStr: string): string {
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

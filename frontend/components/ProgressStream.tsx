export interface StageInfo {
  stage: string;
  displayName: string;
  metric: string;
  status: "active" | "done";
}

const STAGE_DISPLAY_NAMES: Record<string, string> = {
  planning: "Planning",
  gathering: "Gathering",
  gap_detection: "Gap Detection",
  synthesizing: "Synthesizing",
  verifying: "Verifying",
  memory: "Memory",
  complete: "Complete",
};

export function getStageName(
  stage: string,
  data: Record<string, unknown>
): string {
  if (stage === "gathering") {
    const pass = data.pass as number | undefined;
    return pass ? `Gathering (Pass ${pass})` : "Gathering";
  }
  return STAGE_DISPLAY_NAMES[stage] ?? stage;
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
          ? "No gaps detected"
          : `${gaps.length} gap${gaps.length > 1 ? "s" : ""} detected`;
      }
      return "";
    }
    case "synthesizing":
      return "Building document\u2026";
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
      return typeof cost === "number" ? `Done \u2014 $${cost.toFixed(4)}` : "Done";
    }
    default:
      return "";
  }
}

function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin text-blue-400"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

function Checkmark() {
  return (
    <svg
      className="h-4 w-4 text-emerald-400"
      viewBox="0 0 20 20"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
        clipRule="evenodd"
      />
    </svg>
  );
}

interface ProgressStreamProps {
  stages: readonly StageInfo[];
}

export default function ProgressStream({ stages }: ProgressStreamProps) {
  if (stages.length === 0) return null;

  return (
    <div className="w-full max-w-2xl space-y-1">
      {stages.map((s, i) => (
        <div
          key={`${s.stage}-${i}`}
          className={`flex items-center gap-3 rounded-md px-3 py-2 animate-fade-in ${
            s.status === "active"
              ? "border-l-2 border-blue-500 bg-white/[0.03]"
              : "border-l-2 border-transparent"
          }`}
        >
          <div className="flex-shrink-0 w-5 flex justify-center">
            {s.status === "active" ? <Spinner /> : <Checkmark />}
          </div>
          <span className="text-sm font-medium text-zinc-200 min-w-[140px]">
            {s.displayName}
          </span>
          <span className="text-sm text-zinc-500">{s.metric}</span>
        </div>
      ))}
    </div>
  );
}

"use client";

import type { StageInfo } from "@/lib/research";

interface PipelineProgressProps {
  query: string;
  stages: readonly StageInfo[];
}

const CANONICAL = [
  { key: "planning", label: "PLANNING" },
  { key: "gathering", label: "GATHERING" },
  { key: "reranking", label: "RERANKING" },
  { key: "gap_detection", label: "GAP DETECTION" },
  { key: "synthesizing", label: "SYNTHESIZING" },
  { key: "verifying", label: "VERIFYING" },
  { key: "memory", label: "MEMORY" },
];

function normalize(key: string): string {
  return key === "synthesis" ? "synthesizing" : key;
}

export default function PipelineProgress({
  query,
  stages,
}: PipelineProgressProps) {
  const seen = new Set(stages.map((s) => normalize(s.stage)));

  let lastIdx = -1;
  for (const s of stages) {
    const idx = CANONICAL.findIndex((c) => c.key === normalize(s.stage));
    if (idx > lastIdx) lastIdx = idx;
  }

  const future =
    lastIdx >= 0
      ? CANONICAL.slice(lastIdx + 1).filter((c) => !seen.has(c.key))
      : [];

  return (
    <div className="w-full max-w-md text-center px-6">
      <p
        style={{
          fontFamily: "var(--font-serif)",
          fontStyle: "italic",
          fontSize: 18,
          color: "var(--fg)",
          marginBottom: 32,
          lineHeight: 1.6,
        }}
      >
        &ldquo;{query}&rdquo;
      </p>

      <div className="space-y-3 text-left">
        {stages.map((s, i) => (
          <div
            key={`${s.stage}-${i}`}
            className="flex items-baseline gap-3 animate-fade-in"
            style={{ animationDelay: `${i * 60}ms` }}
          >
            {s.status === "done" ? (
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  color: "var(--fg-muted)",
                  width: 14,
                  textAlign: "center",
                  flexShrink: 0,
                  display: "inline-block",
                }}
              >
                ✓
              </span>
            ) : (
              <span
                className="animate-pulse-dot"
                style={{
                  display: "inline-block",
                  width: 5,
                  height: 5,
                  borderRadius: "50%",
                  backgroundColor: "var(--fg)",
                  flexShrink: 0,
                  position: "relative",
                  top: "0.25em",
                  marginLeft: 4.5,
                  marginRight: 4.5,
                }}
              />
            )}

            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 11.5,
                fontWeight: s.status === "active" ? 500 : 400,
                color: s.status === "active" ? "var(--fg)" : "var(--fg-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                minWidth: 130,
              }}
            >
              {s.displayName}
            </span>

            {s.metric && (
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 10.5,
                  color: "var(--fg-muted)",
                }}
              >
                {s.metric}
              </span>
            )}
          </div>
        ))}

        {future.map((c) => (
          <div
            key={`future-${c.key}`}
            className="flex items-baseline gap-3"
            style={{ opacity: 0.25 }}
          >
            <span
              style={{
                display: "inline-block",
                width: 5,
                height: 5,
                borderRadius: "50%",
                backgroundColor: "var(--fg-muted)",
                flexShrink: 0,
                position: "relative",
                top: "0.25em",
                marginLeft: 4.5,
                marginRight: 4.5,
              }}
            />
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 11.5,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                color: "var(--fg-muted)",
              }}
            >
              {c.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

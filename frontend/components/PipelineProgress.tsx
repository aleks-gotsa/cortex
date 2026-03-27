"use client";

import type { StageInfo } from "@/lib/research";

interface PipelineProgressProps {
  query: string;
  stages: readonly StageInfo[];
}

export default function PipelineProgress({
  query,
  stages,
}: PipelineProgressProps) {
  return (
    <div className="w-full max-w-md text-center px-6">
      <h2 className="font-serif italic text-2xl text-[var(--fg)] mb-14 leading-relaxed">
        {query}
      </h2>

      <div className="space-y-3.5 text-left">
        {stages.map((s, i) => (
          <div
            key={`${s.stage}-${i}`}
            className="flex items-baseline gap-3 animate-fade-in"
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <span
              className={`inline-block w-[5px] h-[5px] rounded-full flex-shrink-0 relative top-[0.3em] ${
                s.status === "active"
                  ? "bg-[var(--fg)] animate-pulse-dot"
                  : "bg-[var(--fg-muted)]"
              }`}
            />
            <span className="font-mono text-[11px] tracking-widest text-[var(--fg)] min-w-[130px]">
              {s.displayName}
            </span>
            {s.metric && (
              <span className="font-mono text-[11px] text-[var(--fg-muted)]">
                {s.metric}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

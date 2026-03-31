"use client";

import type { Depth } from "@/lib/research";

interface SearchInputProps {
  query: string;
  onQueryChange: (query: string) => void;
  depth: Depth;
  onDepthChange: (depth: Depth) => void;
  onSubmit: () => void;
  disabled: boolean;
}

const DEPTHS: { value: Depth; label: string }[] = [
  { value: "quick", label: "Quick" },
  { value: "standard", label: "Standard" },
  { value: "deep", label: "Deep" },
];

export default function SearchInput({
  query,
  onQueryChange,
  depth,
  onDepthChange,
  onSubmit,
  disabled,
}: SearchInputProps) {
  function handleKeyDown(e: React.KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      onSubmit();
    }
    if (e.key === "Enter" && query.trim() && !disabled) {
      e.preventDefault();
      onSubmit();
    }
  }

  return (
    <div style={{ width: "100%", maxWidth: 520 }}>
      <div className="flex items-center" style={{ borderBottom: "1px solid var(--border)" }}>
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="What would you like to research?"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: 18,
            color: "var(--fg)",
            background: "transparent",
            border: "none",
            outline: "none",
            padding: "8px 0",
            flex: 1,
            minWidth: 0,
          }}
          className="placeholder:text-[#b0aaa0] disabled:opacity-40"
          autoFocus
        />
        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled || !query.trim()}
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: 18,
            color: "var(--fg)",
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: "8px 0 8px 12px",
            lineHeight: 1,
          }}
          className="disabled:opacity-20 hover:opacity-60 transition-opacity select-none"
          aria-label="Submit research"
        >
          &rarr;
        </button>
      </div>

      <div className="flex items-center gap-1 mt-4" style={{ fontFamily: "var(--font-mono)", fontSize: 12, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        {DEPTHS.map((d, i) => (
          <span key={d.value} className="flex items-center">
            {i > 0 && (
              <span style={{ color: "var(--fg-faint)", margin: "0 4px" }} className="select-none">
                &middot;
              </span>
            )}
            <button
              type="button"
              onClick={() => onDepthChange(d.value)}
              disabled={disabled}
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 12,
                fontWeight: depth === d.value ? 500 : 400,
                color: depth === d.value ? "var(--fg)" : "var(--fg-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                background: "none",
                border: "none",
                borderBottom: depth === d.value ? "1px solid var(--fg)" : "1px solid transparent",
                cursor: "pointer",
                padding: "8px 12px",
                minHeight: 44,
              }}
              className="disabled:opacity-40 transition-colors"
            >
              {d.label}
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}

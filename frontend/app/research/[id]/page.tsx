"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import type { ResearchResult } from "@/lib/research";
import TopBar from "@/components/TopBar";
import ResearchDocument from "@/components/ResearchDocument";
import ThemeToggle from "@/components/ThemeToggle";
import ErrorBoundary from "@/components/ErrorBoundary";
import ScrollToTop from "@/components/ScrollToTop";
import ReadingProgress from "@/components/ReadingProgress";

export default function ResearchPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [result, setResult] = useState<ResearchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/research/${id}`);
        if (!res.ok) {
          setError(res.status === 404 ? "Research not found." : "Failed to load research.");
          return;
        }
        const detail: unknown = await res.json();
        const d = detail as Record<string, unknown>;

        if (
          d?.result &&
          typeof (d.result as Record<string, unknown>).document_md === "string" &&
          d?.run &&
          typeof (d.run as Record<string, unknown>).query === "string"
        ) {
          const run = d.run as Record<string, unknown>;
          const r = d.result as Record<string, unknown>;
          setResult({
            document: r.document_md as string,
            query: run.query as string,
            costUsd: typeof run.cost_usd === "number" ? run.cost_usd : null,
            sourcesCount: 0,
            passCount: 0,
            researchId: id,
          });
        } else {
          setError("Invalid research data.");
        }
      } catch {
        setError("Failed to load research.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") router.push("/");
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [router]);

  const handleNewResearch = useCallback(() => {
    router.push("/");
  }, [router]);

  // Loading state
  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-6 pt-16 pb-24 animate-fade-in">
        <div className="skeleton-line" style={{ width: "60%", height: 28, marginBottom: 32 }} />
        <div className="skeleton-line" style={{ width: "100%", marginBottom: 10 }} />
        <div className="skeleton-line" style={{ width: "95%", marginBottom: 10 }} />
        <div className="skeleton-line" style={{ width: "88%", marginBottom: 10 }} />
        <div className="skeleton-line" style={{ width: "92%", marginBottom: 24 }} />
        <div className="skeleton-line" style={{ width: "100%", marginBottom: 10 }} />
        <div className="skeleton-line" style={{ width: "85%", marginBottom: 10 }} />
        <div className="skeleton-line" style={{ width: "90%", marginBottom: 10 }} />
        <ThemeToggle />
      </div>
    );
  }

  // Error state
  if (error || !result) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "80vh",
          padding: "2rem",
          textAlign: "center",
        }}
      >
        <h2
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: 22,
            fontWeight: 700,
            color: "var(--fg)",
            marginBottom: 8,
          }}
        >
          {error || "Research not found"}
        </h2>
        <button
          onClick={handleNewResearch}
          className="meta-text"
          style={{
            marginTop: 16,
            color: "var(--fg-muted)",
            background: "none",
            border: "none",
            cursor: "pointer",
            textDecoration: "underline",
            textUnderlineOffset: 3,
          }}
        >
          New research
        </button>
        <ThemeToggle />
      </div>
    );
  }

  // Document view
  return (
    <div className="animate-fade-in">
      <ReadingProgress />
      <TopBar result={result} onNewResearch={handleNewResearch} />
      <main className="max-w-3xl mx-auto px-6 pt-10 pb-24">
        <ErrorBoundary onReset={handleNewResearch}>
          <div className="print-header hidden" style={{ display: "none" }}>
            Cortex Research — {result.query}
            {result.costUsd !== null && ` — $${result.costUsd.toFixed(4)}`}
          </div>
          <ResearchDocument markdown={result.document} />
        </ErrorBoundary>
      </main>
      <ScrollToTop />
      <ThemeToggle />
      <p
        className="meta-text hidden sm:block"
        style={{
          position: "fixed",
          bottom: 24,
          left: "50%",
          transform: "translateX(-50%)",
          color: "var(--fg-faint)",
        }}
        data-no-print
      >
        esc to return
      </p>
    </div>
  );
}

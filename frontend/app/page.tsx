"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import type { Depth, ResearchResult } from "@/lib/research";
import { useResearch } from "@/hooks/useResearch";
import { useHistory } from "@/hooks/useHistory";
import SearchInput from "@/components/SearchInput";
import PipelineProgress from "@/components/PipelineProgress";
import ResearchDocument from "@/components/ResearchDocument";
import TopBar from "@/components/TopBar";
import HistoryList from "@/components/HistoryList";
import ThemeToggle from "@/components/ThemeToggle";
import ErrorBoundary from "@/components/ErrorBoundary";
import ScrollToTop from "@/components/ScrollToTop";
import ReadingProgress from "@/components/ReadingProgress";

function DocumentSkeleton() {
  return (
    <div className="max-w-3xl mx-auto px-6 pt-16 pb-24 animate-fade-in">
      {/* Title skeleton */}
      <div className="skeleton-line" style={{ width: "60%", height: 28, marginBottom: 32 }} />
      {/* Paragraph skeletons */}
      <div className="skeleton-line" style={{ width: "100%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "95%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "88%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "92%", marginBottom: 24 }} />
      {/* Second paragraph */}
      <div className="skeleton-line" style={{ width: "100%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "85%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "90%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "70%", marginBottom: 32 }} />
      {/* Section heading */}
      <div className="skeleton-line" style={{ width: "40%", height: 22, marginBottom: 20 }} />
      {/* More lines */}
      <div className="skeleton-line" style={{ width: "100%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "93%", marginBottom: 10 }} />
      <div className="skeleton-line" style={{ width: "87%", marginBottom: 10 }} />
    </div>
  );
}

type Phase = "idle" | "researching" | "complete";

export default function Home() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [exiting, setExiting] = useState(false);
  const [query, setQuery] = useState("");
  const [depth, setDepth] = useState<Depth>("standard");
  const [displayResult, setDisplayResult] = useState<ResearchResult | null>(
    null
  );
  const [activeQuery, setActiveQuery] = useState("");
  const [loadingSkeleton, setLoadingSkeleton] = useState(false);

  const {
    start: startResearch,
    cancel: cancelResearch,
    isRunning,
    stages,
    result: researchResult,
    error: researchError,
    reset: resetResearch,
  } = useResearch();

  const {
    runs: historyRuns,
    loading: historyLoading,
    loadingId,
    loadDocument,
    deleteRun,
    refresh: refreshHistory,
  } = useHistory();

  const transitionRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const completionRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Transition helper ──────────────────────────────────
  const transitionTo = useCallback((newPhase: Phase, delay = 400) => {
    if (transitionRef.current) clearTimeout(transitionRef.current);
    setExiting(true);
    transitionRef.current = setTimeout(() => {
      transitionRef.current = null;
      setExiting(false);
      setPhase(newPhase);
      window.scrollTo(0, 0);
    }, delay);
  }, []);

  // ── Start research ─────────────────────────────────────
  const handleSubmit = useCallback(() => {
    const trimmed = query.trim();
    if (!trimmed || isRunning) return;
    setActiveQuery(trimmed);
    startResearch(trimmed, depth);
    transitionTo("researching");
  }, [query, depth, isRunning, startResearch, transitionTo]);

  // ── Watch for completion ───────────────────────────────
  useEffect(() => {
    if (researchResult && phase === "researching") {
      completionRef.current = setTimeout(() => {
        completionRef.current = null;
        setDisplayResult(researchResult);
        if (researchResult.researchId) {
          window.history.replaceState(null, "", `/research/${researchResult.researchId}`);
        }
        transitionTo("complete", 500);
      }, 800);
      return () => {
        if (completionRef.current) {
          clearTimeout(completionRef.current);
          completionRef.current = null;
        }
      };
    }
  }, [researchResult, phase, transitionTo]);

  // ── Watch for errors during research ───────────────────
  useEffect(() => {
    if (researchError && phase === "researching") {
      transitionTo("idle");
    }
  }, [researchError, phase, transitionTo]);

  // ── Return to idle ─────────────────────────────────────
  const handleNewResearch = useCallback(() => {
    resetResearch();
    setDisplayResult(null);
    setQuery("");
    setActiveQuery("");
    window.history.replaceState(null, "", "/");
    transitionTo("idle");
  }, [resetResearch, transitionTo]);

  // ── History selection ──────────────────────────────────
  const handleHistorySelect = useCallback(
    async (id: string) => {
      setLoadingSkeleton(true);
      transitionTo("complete");

      const doc = await loadDocument(id);
      if (doc) {
        setDisplayResult({
          document: doc.markdown,
          query: doc.query,
          costUsd: doc.costUsd,
          sourcesCount: 0,
          passCount: 0,
          researchId: id,
          sources: null,
        });
        setActiveQuery(doc.query);
        window.history.replaceState(null, "", `/research/${id}`);
      } else {
        transitionTo("idle");
      }
      setLoadingSkeleton(false);
    },
    [loadDocument, transitionTo]
  );

  // ── Keyboard ───────────────────────────────────────────
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        if (phase === "complete") handleNewResearch();
        else if (phase === "researching") {
          cancelResearch();
          transitionTo("idle");
        }
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [phase, handleNewResearch, cancelResearch, transitionTo]);

  // ── Refresh history on idle entry ──────────────────────
  useEffect(() => {
    if (phase === "idle") refreshHistory();
  }, [phase, refreshHistory]);

  // ── Render ─────────────────────────────────────────────
  const anim = exiting ? "animate-fade-out-up" : "animate-fade-in";

  return (
    <>
      {/* ── IDLE ──────────────────────────────────────── */}
      {phase === "idle" && (
        <div
          className={`min-h-screen flex flex-col items-center px-6 pb-20 ${anim}`}
          style={{ paddingTop: "clamp(80px, 30vh, 38vh)", paddingBottom: "calc(20px + env(safe-area-inset-bottom))" }}
        >
          <h1
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: 36,
              fontWeight: 700,
              letterSpacing: "-0.03em",
              color: "var(--fg)",
              marginBottom: 4,
            }}
          >
            Cortex
          </h1>
          <p
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 13,
              fontWeight: 400,
              letterSpacing: "0.04em",
              color: "var(--fg-muted)",
              textTransform: "uppercase",
              marginBottom: 48,
            }}
          >
            Search, verify, remember.
          </p>

          <SearchInput
            query={query}
            onQueryChange={setQuery}
            depth={depth}
            onDepthChange={setDepth}
            onSubmit={handleSubmit}
            disabled={isRunning}
          />

          {researchError && (
            <p
              className="mt-6 text-center"
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 12,
                color: "#c53030",
                maxWidth: 520,
              }}
            >
              {researchError}
            </p>
          )}

          <div className="mt-20 w-full" style={{ maxWidth: 520 }}>
            <HistoryList
              runs={historyRuns}
              loading={historyLoading}
              loadingId={loadingId}
              onSelect={handleHistorySelect}
              onDelete={deleteRun}
            />
          </div>
        </div>
      )}

      {/* ── RESEARCHING ───────────────────────────────── */}
      {phase === "researching" && (
        <div
          className={`min-h-screen flex items-center justify-center px-6 ${anim}`}
        >
          <PipelineProgress query={activeQuery} stages={stages} />
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
            esc to cancel
          </p>
        </div>
      )}

      {/* ── COMPLETE ──────────────────────────────────── */}
      {phase === "complete" && (
        <div className={anim}>
          <ReadingProgress />
          {!loadingSkeleton && displayResult && (
            <TopBar result={displayResult} onNewResearch={handleNewResearch} />
          )}
          <main className="max-w-3xl mx-auto px-6 pt-16 pb-24">
            {loadingSkeleton ? (
              <DocumentSkeleton />
            ) : (
              displayResult && (
                <ErrorBoundary onReset={handleNewResearch}>
                  <div className="print-header hidden" style={{ display: "none" }}>
                    Cortex Research — {displayResult.query}
                    {displayResult.costUsd !== null && ` — $${displayResult.costUsd.toFixed(4)}`}
                  </div>
                  <ResearchDocument markdown={displayResult.document} sources={displayResult.sources} />
                </ErrorBoundary>
              )
            )}
          </main>
          {!loadingSkeleton && <ScrollToTop />}
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
      )}

      <ThemeToggle />
    </>
  );
}

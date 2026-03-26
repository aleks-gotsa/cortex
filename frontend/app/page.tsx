"use client";

import { useState, useCallback } from "react";
import { ResearchInput } from "@/components/ResearchInput";
import DocumentView from "@/components/DocumentView";
import HistoryList from "@/components/HistoryList";

export default function Home() {
  const [documentMd, setDocumentMd] = useState<string | null>(null);
  const [activeQuery, setActiveQuery] = useState<string | null>(null);
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleResearchComplete = useCallback(
    (markdown: string, query: string) => {
      setDocumentMd(markdown);
      setActiveQuery(query);
      setHistoryRefresh((n) => n + 1);
    },
    []
  );

  const handleHistorySelect = useCallback(
    (markdown: string, query: string) => {
      setDocumentMd(markdown);
      setActiveQuery(query);
      setSidebarOpen(false);
    },
    []
  );

  return (
    <div className="min-h-screen flex">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:sticky top-0 left-0 z-40 h-screen w-72 border-r border-zinc-800 bg-zinc-950 flex-shrink-0 transition-transform lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <HistoryList
          onSelect={handleHistorySelect}
          refreshTrigger={historyRefresh}
        />
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0 px-4 py-16">
        <div className="mx-auto max-w-[800px]">
          {/* Header */}
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-1 -ml-1 text-zinc-400 hover:text-zinc-200"
              aria-label="Open history"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <h1 className="text-3xl font-bold tracking-tight text-white">
              Cortex
            </h1>
          </div>
          <p className="mb-10 text-sm text-gray-500">
            Deep research engine — search, verify, remember.
          </p>

          {/* Research input + progress */}
          <ResearchInput onComplete={handleResearchComplete} />

          {/* Document view */}
          {documentMd && (
            <div className="mt-10">
              {activeQuery && (
                <h2 className="text-lg font-semibold text-zinc-200 mb-4">
                  {activeQuery}
                </h2>
              )}
              <div className="rounded-md border border-zinc-800 bg-zinc-900/50 px-6 py-5">
                <DocumentView markdown={documentMd} />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

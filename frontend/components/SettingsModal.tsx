"use client";

import { useState, useEffect, useCallback } from "react";
import { getKeys, saveKeys, clearKeys, type ApiKeys } from "@/lib/keys";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function EyeIcon({ open }: { open: boolean }) {
  if (open) {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    );
  }
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [anthropicKey, setAnthropicKey] = useState("");
  const [serperKey, setSerperKey] = useState("");
  const [tavilyKey, setTavilyKey] = useState("");
  const [showAnthropic, setShowAnthropic] = useState(false);
  const [showSerper, setShowSerper] = useState(false);
  const [showTavily, setShowTavily] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      const existing = getKeys();
      if (existing) {
        setAnthropicKey(existing.anthropicApiKey);
        setSerperKey(existing.serperApiKey);
        setTavilyKey(existing.tavilyApiKey);
      }
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  const handleSave = useCallback(() => {
    const keys: ApiKeys = {
      anthropicApiKey: anthropicKey.trim(),
      serperApiKey: serperKey.trim(),
      tavilyApiKey: tavilyKey.trim(),
    };
    saveKeys(keys);
    onClose();
  }, [anthropicKey, serperKey, tavilyKey, onClose]);

  const handleClear = useCallback(() => {
    clearKeys();
    setAnthropicKey("");
    setSerperKey("");
    setTavilyKey("");
    setStatus("Keys cleared");
    setTimeout(() => setStatus(null), 2000);
  }, []);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: "rgba(0,0,0,0.3)" }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          background: "#faf8f5",
          border: "1px solid #e5e2dd",
          width: "100%",
          maxWidth: 440,
          padding: "32px 28px 24px",
          position: "relative",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h2
            style={{
              fontFamily: "var(--font-serif, Georgia, serif)",
              fontSize: 18,
              fontWeight: 600,
              letterSpacing: "0.06em",
              textTransform: "uppercase" as const,
              color: "#1a1a1a",
              margin: 0,
            }}
          >
            Settings
          </h2>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: 4,
              color: "#888",
              fontSize: 20,
              lineHeight: 1,
            }}
            aria-label="Close"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div style={{ height: 1, background: "#e5e2dd", marginBottom: 24 }} />

        {/* Fields */}
        {([
          { label: "Anthropic API Key", value: anthropicKey, set: setAnthropicKey, show: showAnthropic, toggle: () => setShowAnthropic((v) => !v) },
          { label: "Serper API Key", value: serperKey, set: setSerperKey, show: showSerper, toggle: () => setShowSerper((v) => !v) },
          { label: "Tavily API Key", value: tavilyKey, set: setTavilyKey, show: showTavily, toggle: () => setShowTavily((v) => !v) },
        ] as const).map((field) => (
          <div key={field.label} style={{ marginBottom: 18 }}>
            <label
              style={{
                display: "block",
                fontFamily: "monospace",
                fontSize: 11,
                fontWeight: 500,
                letterSpacing: "0.08em",
                textTransform: "uppercase" as const,
                color: "#888",
                marginBottom: 6,
              }}
            >
              {field.label}
            </label>
            <div style={{ position: "relative" }}>
              <input
                type={field.show ? "text" : "password"}
                value={field.value}
                onChange={(e) => field.set(e.target.value)}
                spellCheck={false}
                autoComplete="off"
                style={{
                  width: "100%",
                  padding: "8px 36px 8px 10px",
                  fontFamily: "monospace",
                  fontSize: 13,
                  background: "#faf8f5",
                  border: "1px solid #e5e2dd",
                  outline: "none",
                  color: "#1a1a1a",
                  borderRadius: 0,
                }}
              />
              <button
                type="button"
                onClick={field.toggle}
                style={{
                  position: "absolute",
                  right: 8,
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: 2,
                  color: "#aaa",
                  display: "flex",
                  alignItems: "center",
                }}
                aria-label={field.show ? "Hide key" : "Show key"}
              >
                <EyeIcon open={field.show} />
              </button>
            </div>
          </div>
        ))}

        {/* Footer note */}
        <p
          style={{
            fontFamily: "monospace",
            fontSize: 10,
            color: "#bbb",
            margin: "20px 0 16px",
          }}
        >
          Keys are stored locally and never leave your browser.
        </p>

        {/* Actions */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <button
            onClick={handleSave}
            style={{
              background: "#1a1a1a",
              color: "#fff",
              border: "none",
              padding: "8px 24px",
              fontFamily: "monospace",
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase" as const,
              cursor: "pointer",
              borderRadius: 0,
            }}
          >
            Save
          </button>

          {status ? (
            <span style={{ fontFamily: "monospace", fontSize: 12, color: "#888" }}>
              {status}
            </span>
          ) : (
            <button
              onClick={handleClear}
              style={{
                background: "none",
                border: "none",
                fontFamily: "monospace",
                fontSize: 12,
                color: "#888",
                cursor: "pointer",
                padding: 0,
                textDecoration: "none",
              }}
            >
              clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

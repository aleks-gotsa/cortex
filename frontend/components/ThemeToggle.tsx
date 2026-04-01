"use client";

import { useState, useEffect, useCallback } from "react";
import SettingsModal from "@/components/SettingsModal";

function getInitialTheme(): boolean {
  if (typeof window === "undefined") return false;
  const stored = localStorage.getItem("cortex-theme");
  if (stored === "dark") return true;
  if (stored === "light") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export default function ThemeToggle() {
  const [dark, setDark] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Hydration-safe: read preference only after mount
  useEffect(() => {
    const initial = getInitialTheme();
    setDark(initial);
    document.documentElement.classList.toggle("dark", initial);
    setMounted(true);
  }, []);

  const toggle = useCallback(() => {
    setDark((prev) => {
      const next = !prev;
      document.documentElement.classList.toggle("dark", next);
      localStorage.setItem("cortex-theme", next ? "dark" : "light");
      return next;
    });
  }, []);

  // Don't render until mounted to prevent hydration flash
  if (!mounted) return null;

  return (
    <>
      <div
        data-no-print
        style={{
          position: "fixed",
          bottom: "calc(4px + env(safe-area-inset-bottom))",
          right: "calc(4px + env(safe-area-inset-right))",
          display: "flex",
          alignItems: "center",
          zIndex: 50,
        }}
      >
        <button
          onClick={() => setSettingsOpen(true)}
          className="meta-text"
          style={{ padding: "12px 4px 12px 16px", background: "none", border: "none", cursor: "pointer", color: "var(--fg-faint)" }}
        >
          Settings
        </button>
        <button
          onClick={toggle}
          className="meta-text"
          style={{ padding: "12px 16px 12px 8px", background: "none", border: "none", cursor: "pointer", color: "var(--fg-faint)" }}
          aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
        >
          {dark ? "Light" : "Dark"}
        </button>
      </div>
      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}

"use client";

import { useState, useEffect, useCallback } from "react";

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
    <button
      onClick={toggle}
      data-no-print
      className="fixed z-50 cursor-pointer meta-text"
      style={{
        bottom: "calc(4px + env(safe-area-inset-bottom))",
        right: "calc(4px + env(safe-area-inset-right))",
        padding: "12px 16px",
        color: "var(--fg-faint)",
        background: "none",
        border: "none",
      }}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {dark ? "Light" : "Dark"}
    </button>
  );
}

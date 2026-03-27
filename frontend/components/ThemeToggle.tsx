"use client";

import { useState, useCallback } from "react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(false);

  const toggle = useCallback(() => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
  }, [dark]);

  return (
    <button
      onClick={toggle}
      className="fixed z-50 cursor-pointer"
      style={{
        bottom: 16,
        right: 16,
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        color: "var(--fg-faint)",
      }}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {dark ? "Light" : "Dark"}
    </button>
  );
}

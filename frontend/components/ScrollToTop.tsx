"use client";

import { useState, useEffect, useCallback } from "react";

export default function ScrollToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    function onScroll() {
      setVisible(window.scrollY > 500);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollUp = useCallback(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  if (!visible) return null;

  return (
    <button
      onClick={scrollUp}
      data-no-print
      className="fixed z-40 cursor-pointer meta-text"
      style={{
        bottom: "calc(48px + env(safe-area-inset-bottom))",
        right: "calc(4px + env(safe-area-inset-right))",
        padding: "12px 16px",
        color: "var(--fg-faint)",
        background: "none",
        border: "none",
        transition: "color 0.2s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--fg-muted)")}
      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--fg-faint)")}
      aria-label="Scroll to top"
    >
      &uarr;
    </button>
  );
}

import { useQuery } from "@tanstack/react-query";
import { Link, Outlet } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import { api } from "../api/client";

type Theme = "light" | "dark";

function storedTheme(): Theme | null {
  try {
    const value = localStorage.getItem("theme");
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

function systemTheme(): Theme {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => storedTheme() ?? systemTheme());

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  function toggle() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    try {
      localStorage.setItem("theme", next);
    } catch {
      // Private windows can refuse storage; the theme still applies for this visit.
    }
  }

  return (
    <button type="button" className="icon-button" onClick={toggle} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        {theme === "dark" ? (
          <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
          </>
        ) : (
          <path d="M21 13A9 9 0 1 1 11 3a7 7 0 0 0 10 10z" />
        )}
      </svg>
    </button>
  );
}

/** Every wait is zero while this shows (ADR-0019 amendment 2026-11-04); off unless the server says so. */
function TestModeBanner() {
  const features = useQuery({ queryKey: ["features"], queryFn: () => api.features(), staleTime: Infinity });
  if (!features.data?.test_mode) return null;
  return (
    <p className="test-mode-banner" role="status" aria-label="Test mode">
      Test mode: timers off
    </p>
  );
}

export function Layout() {
  return (
    <>
      <header className="top-bar">
        <Link to="/" className="wordmark">
          <span className="wordmark-mark" aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 20 12 4l8 16" />
              <path d="M7.5 13h9" />
            </svg>
          </span>
          <span className="wordmark-text">Aethelgard</span>
        </Link>
        <nav aria-label="Primary" className="primary-nav">
          <Link to="/courses" activeProps={{ className: "active", "aria-current": "page" }}>
            Courses
          </Link>
          <Link to="/concepts" aria-label="Concept library" activeProps={{ className: "active", "aria-current": "page" }}>
            <span className="on-wide">Concept library</span>
            <span className="on-narrow">Concepts</span>
          </Link>
          <Link to="/progress" activeProps={{ className: "active", "aria-current": "page" }}>
            My progress
          </Link>
        </nav>
        <div className="top-bar-end">
          <ThemeToggle />
        </div>
      </header>
      <TestModeBanner />
      <Outlet />
    </>
  );
}

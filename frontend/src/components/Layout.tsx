import { useQuery } from "@tanstack/react-query";
import { Link, Outlet, useRouter, useRouterState } from "@tanstack/react-router";
import { useEffect, useState, type MouseEvent } from "react";

import { api } from "../api/client";
import { parentPath } from "../lib/backPath";

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

/** The Quest & Crossfire cyan diamond, drawn in SVG so it follows the theme tokens. */
function DiamondMark({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <polygon points="5.2,3.8 18.8,3.8 23,8.7 12,20.2 1,8.7" fill="var(--brand-cyan)" stroke="var(--brand-edge)" strokeWidth="1" strokeLinejoin="round" />
      <path d="M1 8.7h22M5.2 3.8 6.8 8.7 12 3.8l5.2 4.9 1.6-4.9M6.8 8.7 12 20.2l5.2-11.5" fill="none" stroke="var(--surface)" strokeWidth="0.8" strokeLinejoin="round" />
    </svg>
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

/**
 * One back arrow for every page but the front page. It returns to the page the learner was on;
 * with no earlier page in this tab it goes to the page above (parentPath). The href is that
 * parent, so the link still works when opened in a new tab.
 */
function BackArrow() {
  const router = useRouter();
  const location = useRouterState({ select: (state) => state.location });
  const parent = parentPath(location.pathname, location.search as Record<string, unknown>);
  if (parent === null) return null;

  function goBack(event: MouseEvent<HTMLAnchorElement>) {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (router.history.canGoBack()) router.history.back();
    else router.history.push(parent!);
  }

  return (
    <div className="container shell-back">
      <a href={parent} className="back-link" aria-label="Go back" onClick={goBack}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M19 12H5M11 6l-6 6 6 6" />
        </svg>
        Back
      </a>
    </div>
  );
}

function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="container site-footer-inner">
        <DiamondMark className="footer-mark" />
        <span className="footer-name">Aethelgard</span>
        <span className="footer-credit">by Quest &amp; Crossfire</span>
        <span className="footer-tagline">Small fixes, big clarity.</span>
      </div>
    </footer>
  );
}

export function Layout() {
  return (
    <>
      <header className="top-bar">
        <Link to="/" className="wordmark">
          <DiamondMark className="wordmark-mark" />
          <span className="wordmark-text">
            <span className="wordmark-name">Aethelgard</span>
            <span className="wordmark-credit">by Quest &amp; Crossfire</span>
          </span>
        </Link>
        <nav aria-label="Primary" className="primary-nav">
          <Link to="/courses" activeProps={{ className: "active", "aria-current": "page" }}>
            Courses
          </Link>
          <Link to="/concepts" aria-label="Concept library" activeProps={{ className: "active", "aria-current": "page" }}>
            <span className="on-wide">Concept library</span>
            <span className="on-narrow">Concepts</span>
          </Link>
          <Link to="/progress" aria-label="My progress" activeProps={{ className: "active", "aria-current": "page" }}>
            <span className="on-wide">My progress</span>
            <span className="on-narrow">Progress</span>
          </Link>
          <Link to="/skills" aria-label="My skills" activeProps={{ className: "active", "aria-current": "page" }}>
            <span className="on-wide">My skills</span>
            <span className="on-narrow">Skills</span>
          </Link>
        </nav>
        <div className="top-bar-end">
          <Link to="/settings/models" className="icon-button" aria-label="AI model settings" title="AI model settings">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
            </svg>
          </Link>
          <ThemeToggle />
        </div>
      </header>
      <TestModeBanner />
      <BackArrow />
      <div className="shell-main">
        <Outlet />
      </div>
      <SiteFooter />
    </>
  );
}

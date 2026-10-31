import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";

import type { Decision } from "../api/client";
import { decisionLabel } from "../lib/format";

export function BackLink({ to, params, label }: { to: string; params?: Record<string, string>; label: string }) {
  return (
    <Link to={to} params={params} className="back-link" aria-label={`Back to ${label}`}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M19 12H5M11 6l-6 6 6 6" />
      </svg>
      {label}
    </Link>
  );
}

export function DecisionChip({ decision }: { decision: Decision }) {
  return <span className={`chip chip-${decision.toLowerCase()}`}>{decisionLabel(decision)}</span>;
}

export function Loading({ what }: { what: string }) {
  return (
    <p className="muted" role="status">
      Loading {what}…
    </p>
  );
}

export function ErrorNote({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : "Something went wrong.";
  return (
    <p className="error-note" role="alert">
      {message}
    </p>
  );
}

export function Panel({ title, id, children }: { title: string; id: string; children: ReactNode }) {
  return (
    <section className="card panel" aria-labelledby={id}>
      <h2 id={id} className="eyebrow">
        {title}
      </h2>
      {children}
    </section>
  );
}

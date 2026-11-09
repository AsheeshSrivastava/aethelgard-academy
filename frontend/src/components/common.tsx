import type { ReactNode } from "react";

import type { Decision } from "../api/client";
import { decisionLabel } from "../lib/format";

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

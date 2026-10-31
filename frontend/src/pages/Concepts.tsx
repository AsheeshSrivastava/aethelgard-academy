import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useSearch } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from "react";

import { api, type ConceptSummary } from "../api/client";
import { BackLink, ErrorNote, Loading } from "../components/common";

const SEARCH_WAIT_MS = 250;
const MAX_QUERY = 200;

const searchOptions = (q: string) => ({ queryKey: ["concepts", "search", q], queryFn: () => api.concepts(q) });

function ConceptCard({ concept, onOpen }: { concept: ConceptSummary; onOpen: (slug: string) => void }) {
  return (
    <Link to="/concepts/$slug" params={{ slug: concept.concept_id }} className="card concept-card" onClick={() => onOpen(concept.concept_id)}>
      <span className="concept-head">
        <span className="course-title">{concept.name}</span>
        {concept.status === "draft" && <span className="chip">Draft</span>}
      </span>
      <span className="muted small">{concept.category}</span>
      <span className="small">{concept.summary}</span>
    </Link>
  );
}

function Results({ q, onOpen }: { q: string; onOpen: (slug: string) => void }) {
  const results = useQuery({ ...searchOptions(q), placeholderData: keepPreviousData });

  if (results.isPending) return <Loading what="concepts" />;
  if (results.isError) return <ErrorNote error={results.error} />;

  const count = results.data.length;
  return (
    <>
      <p className="muted small" role="status">
        {count === 0 ? `No concept matches "${q}". Try a shorter word.` : `${count} ${count === 1 ? "concept" : "concepts"}`}
      </p>
      <div className="concept-list">
        {results.data.map((concept) => (
          <ConceptCard key={concept.concept_id} concept={concept} onOpen={onOpen} />
        ))}
      </div>
    </>
  );
}

function Recent({ onOpen }: { onOpen: (slug: string) => void }) {
  const recent = useQuery({ queryKey: ["recentConcepts"], queryFn: api.recentConcepts });

  if (recent.isPending) return <Loading what="your recent concepts" />;
  if (recent.isError) return <ErrorNote error={recent.error} />;
  if (recent.data.length === 0) {
    return <p className="muted">Search for something you met in a lesson, such as print or variables.</p>;
  }
  return (
    <section aria-labelledby="recent-concepts">
      <h2 id="recent-concepts" className="eyebrow">
        Recently opened
      </h2>
      <div className="concept-list">
        {recent.data.map((concept) => (
          <ConceptCard key={concept.concept_id} concept={concept} onOpen={onOpen} />
        ))}
      </div>
    </section>
  );
}

export function Concepts() {
  const { q = "" } = useSearch({ from: "/concepts" });
  const navigate = useNavigate();
  const client = useQueryClient();
  const [text, setText] = useState(q);
  const area = useRef<HTMLDivElement>(null);

  const setQuery = useCallback(
    (value: string) => void navigate({ to: "/concepts", search: value ? { q: value } : {}, replace: true }),
    [navigate],
  );

  useEffect(() => {
    const value = text.trim();
    if (value === q) return;
    const timer = setTimeout(() => setQuery(value), SEARCH_WAIT_MS);
    return () => clearTimeout(timer);
  }, [text, q, setQuery]);

  // The address can change without typing, through Back or the top bar.
  useEffect(() => {
    if (q !== text.trim()) setText(q);
    // Typing is handled above; only a new address should reach the box.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  const record = useCallback(
    (slug: string) => {
      void api
        .conceptOpened(slug)
        .catch(() => undefined) // The note still opens; it just misses the recent list.
        .finally(() => client.invalidateQueries({ queryKey: ["recentConcepts"] }));
    },
    [client],
  );

  async function openTopResult() {
    const value = text.trim();
    if (!value) return;
    const results = await client.fetchQuery(searchOptions(value)).catch(() => []);
    const top = results[0];
    if (!top) {
      setQuery(value);
      return;
    }
    record(top.concept_id);
    void navigate({ to: "/concepts/$slug", params: { slug: top.concept_id } });
  }

  function moveFocus(event: KeyboardEvent) {
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
    const stops = [...(area.current?.querySelectorAll<HTMLElement>("input, a") ?? [])];
    const next = stops[stops.indexOf(document.activeElement as HTMLElement) + (event.key === "ArrowDown" ? 1 : -1)];
    if (next) {
      event.preventDefault();
      next.focus();
    }
  }

  return (
    <main className="container page">
      <BackLink to="/" label="Home" />
      <h1 className="page-title">Concept library</h1>
      <p className="lead">Short notes on the ideas in your lessons.</p>
      <div ref={area} className="concept-area" onKeyDown={moveFocus}>
        <form
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            void openTopResult();
          }}
        >
          <label className="field">
            <span>Search concepts</span>
            <input
              type="search"
              value={text}
              maxLength={MAX_QUERY}
              autoComplete="off"
              autoFocus={window.matchMedia?.("(pointer: fine)").matches}
              onChange={(event) => setText(event.target.value)}
            />
          </label>
        </form>
        {q ? <Results q={q} onOpen={record} /> : <Recent onOpen={record} />}
      </div>
    </main>
  );
}

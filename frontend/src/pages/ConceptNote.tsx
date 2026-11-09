import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";

import { api, ApiError } from "../api/client";
import { ErrorNote, Loading, Panel } from "../components/common";
import { Prose } from "../lesson/Prose";

export function ConceptNote() {
  const { slug } = useParams({ from: "/concepts/$slug" });
  const note = useQuery({ queryKey: ["concept", slug], queryFn: () => api.concept(slug) });
  const missing = note.error instanceof ApiError && note.error.status === 404;
  const related = note.data?.related ?? [];
  const usedIn = note.data?.used_in ?? [];

  return (
    <main className="container page concept-page">
      {note.isPending && <Loading what="the note" />}
      {missing && <p>There is no concept note here.</p>}
      {note.isError && !missing && <ErrorNote error={note.error} />}
      {note.data && (
        <>
          <div className="concept-head">
            <h1 className="page-title">{note.data.name}</h1>
            {note.data.status === "draft" && <span className="chip">Draft</span>}
          </div>
          <p className="muted small">{note.data.category}</p>
          <p className="lead">{note.data.summary}</p>
          <article className="card lesson-card">
            <Prose wikiLinks>{note.data.content_markdown ?? ""}</Prose>
          </article>
          {related.length > 0 && (
            <Panel title="Related concepts" id="related-concepts">
              <ul className="plain-list">
                {related.map((concept) => (
                  <li key={concept.concept_id}>
                    <Link to="/concepts/$slug" params={{ slug: concept.concept_id }}>
                      {concept.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
          {usedIn.length > 0 && (
            <Panel title="Used in units" id="used-in-units">
              <ul className="plain-list">
                {usedIn.map((unit) => (
                  <li key={unit.unit_id}>
                    <Link to="/units/$unitId" params={{ unitId: unit.unit_id }}>
                      {unit.unit_id}: {unit.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
          {note.data.doc_url && (
            <p className="small">
              <a href={note.data.doc_url} target="_blank" rel="noreferrer">
                Official documentation
              </a>
            </p>
          )}
        </>
      )}
    </main>
  );
}

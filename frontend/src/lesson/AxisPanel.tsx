import { useEffect, useRef, useState, type FormEvent } from "react";

import { answerNote, fetchCourseReference, KEYWORD_ONLY_NOTE, statusLine } from "./axisNotices";
import { streamAxis, streamSafe, type SseEvent } from "./axisStream";
import { Prose } from "./Prose";
import { activityFor } from "./steps";

const MODES = ["Socratic", "Hybrid", "Coach"] as const;
type Mode = (typeof MODES)[number];

interface Citation {
  concept_id: string;
  title: string;
  doc_url: string;
}

interface Message {
  id: number;
  role: "you" | "axis";
  text: string;
  citations: Citation[];
  sourceState?: string;
  keywordOnly?: boolean;
  error?: string;
}

export function AxisPanel({
  unitId,
  step,
  exerciseId,
  getCode,
  socraticOnly = false,
}: {
  unitId: string;
  step: string;
  exerciseId?: string;
  getCode: () => string | undefined;
  socraticOnly?: boolean;
}) {
  const [mode, setMode] = useState<Mode>("Socratic");
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [courseReference, setCourseReference] = useState<string | undefined>(undefined);
  const nextId = useRef(0);

  useEffect(() => {
    let live = true;
    void fetchCourseReference().then((value) => live && setCourseReference(value));
    return () => {
      live = false;
    };
  }, []);

  function update(id: number, change: (message: Message) => Message) {
    setMessages((current) => current.map((message) => (message.id === id ? change(message) : message)));
  }

  function onEvent(id: number, { event, data }: SseEvent) {
    if (event === "token") update(id, (m) => ({ ...m, text: m.text + String(data.text) }));
    if (event === "citation") update(id, (m) => ({ ...m, citations: [...m.citations, data as unknown as Citation] }));
    if (event === "done" && data.retrieval_downgraded === true) {
      update(id, (m) => ({ ...m, keywordOnly: true }));
    }
    if (event === "done" && typeof data.source_state === "string") {
      const state = data.source_state;
      update(id, (m) => ({ ...m, sourceState: state }));
    }
    if (event === "error") update(id, (m) => ({ ...m, error: String(data.message) }));
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    const question = draft.trim();
    if (!question || busy) return;
    setDraft("");
    await ask(question, { learner_code: getCode(), exercise_id: exerciseId, page: step });
  }

  async function ask(shown: string, request: { user_prompt?: string; learner_code?: string; exercise_id?: string; page: string }) {
    const askId = nextId.current++;
    const replyId = nextId.current++;
    setBusy(true);
    setMessages((current) => [
      ...current,
      { id: askId, role: "you", text: shown, citations: [] },
      { id: replyId, role: "axis", text: "", citations: [] },
    ]);
    try {
      await streamAxis(
        {
          unit_id: unitId,
          mode: socraticOnly ? "Socratic" : mode,
          current_activity: activityFor(step),
          user_prompt: request.user_prompt ?? shown,
          learner_code: request.learner_code,
          exercise_id: request.exercise_id,
          page: request.page,
        },
        (sse) => onEvent(replyId, sse),
      );
    } catch {
      update(replyId, (m) => ({ ...m, error: "AXIS is unavailable right now." }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <aside className="card axis-panel" aria-label="AXIS facilitator">
      <div className="axis-head">
        <span className="axis-title">AXIS</span>
        {socraticOnly ? (
          <span className="small muted">Socratic during builds</span>
        ) : (
          <div className="mode-picker" role="group" aria-label="Facilitation mode">
            {MODES.map((name) => (
              <label key={name} className={mode === name ? "mode mode-chosen" : "mode"}>
                <input type="radio" name="axis-mode" checked={mode === name} onChange={() => setMode(name)} />
                {name}
              </label>
            ))}
          </div>
        )}
      </div>
      {statusLine(courseReference) && (
        <p className="axis-status small" role="status">
          {statusLine(courseReference)}
        </p>
      )}
      <div className="axis-messages" aria-live="polite">
        {messages.length === 0 && <p className="small muted">Stuck? Ask about what you are doing here. AXIS can see this step and your code.</p>}
        {messages.map((message, index) => (
          <div key={message.id} className={`message message-${message.role}`}>
            {message.text &&
              (message.role === "axis" ? (
                <Prose>{busy && index === messages.length - 1 ? streamSafe(message.text) : message.text}</Prose>
              ) : (
                <p>{message.text}</p>
              ))}
            {message.role === "axis" && !message.text && !message.error && busy && <p className="muted">Thinking…</p>}
            {message.error && (
              <p className="error-note" role="alert">
                {message.error}
              </p>
            )}
            {message.role === "axis" && answerNote(message.sourceState) && (
              <p className="axis-source-note small muted">{answerNote(message.sourceState)}</p>
            )}
            {message.role === "axis" && message.keywordOnly && (
              <p className="axis-source-note small muted">{KEYWORD_ONLY_NOTE}</p>
            )}
            {message.citations.length > 0 && (
              <div className="citations">
                {message.citations.map((citation) =>
                  citation.doc_url ? (
                    <a key={citation.concept_id} href={citation.doc_url} target="_blank" rel="noreferrer" className="citation">
                      {citation.title}
                    </a>
                  ) : (
                    <span key={citation.concept_id} className="citation">
                      {citation.title}
                    </span>
                  ),
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      <form className="axis-form" onSubmit={send}>
        <label className="sr-only" htmlFor="axis-input">
          Message AXIS
        </label>
        <input id="axis-input" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask AXIS…" autoComplete="off" />
        <button type="submit" className="button button-primary button-small" disabled={busy || !draft.trim()}>
          Send
        </button>
      </form>
      <p className="axis-note">
        Help is logged against this exercise. Looking up syntax is fine. If AXIS gives you the reasoning, the work counts as practice, not as proof.
      </p>
    </aside>
  );
}

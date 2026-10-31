import { useRef, useState, type FormEvent } from "react";

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
  error?: string;
}

export function AxisPanel({
  unitId,
  step,
  exerciseId,
  getCode,
}: {
  unitId: string;
  step: string;
  exerciseId?: string;
  getCode: () => string | undefined;
}) {
  const [mode, setMode] = useState<Mode>("Socratic");
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const nextId = useRef(0);

  function update(id: number, change: (message: Message) => Message) {
    setMessages((current) => current.map((message) => (message.id === id ? change(message) : message)));
  }

  function onEvent(id: number, { event, data }: SseEvent) {
    if (event === "token") update(id, (m) => ({ ...m, text: m.text + String(data.text) }));
    if (event === "citation") update(id, (m) => ({ ...m, citations: [...m.citations, data as unknown as Citation] }));
    if (event === "error") update(id, (m) => ({ ...m, error: String(data.message) }));
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    const question = draft.trim();
    if (!question || busy) return;
    const askId = nextId.current++;
    const replyId = nextId.current++;
    setDraft("");
    setBusy(true);
    setMessages((current) => [
      ...current,
      { id: askId, role: "you", text: question, citations: [] },
      { id: replyId, role: "axis", text: "", citations: [] },
    ]);
    try {
      await streamAxis(
        {
          unit_id: unitId,
          mode,
          current_activity: activityFor(step),
          user_prompt: question,
          learner_code: getCode(),
          exercise_id: exerciseId,
          page: step,
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
        <div className="mode-picker" role="group" aria-label="Facilitation mode">
          {MODES.map((name) => (
            <label key={name} className={mode === name ? "mode mode-chosen" : "mode"}>
              <input type="radio" name="axis-mode" checked={mode === name} onChange={() => setMode(name)} />
              {name}
            </label>
          ))}
        </div>
      </div>
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

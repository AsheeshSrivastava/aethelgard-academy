import { useState } from "react";

import { api, type Schemas } from "../api/client";

type Point = Schemas["FeedbackPoint"];
type Feedback = Schemas["BuildFeedbackResult"];

const STATUS_WORDS: Record<Point["status"], string> = {
  not_met: "Not found",
  not_checked: "Not checked yet",
  met: "Found",
};

function count(points: Point[], status: Point["status"]) {
  return points.filter((point) => point.status === status).length;
}

function PointCard({ point }: { point: Point }) {
  const [wrong, setWrong] = useState(false);
  const [reason, setReason] = useState("");
  const [sent, setSent] = useState(false);

  function send() {
    void api.logEvent({
      event_type: "feedback_disputed",
      payload: { point: point.requirement_id, reason: reason.trim().slice(0, 200) },
    });
    setSent(true);
    setWrong(false);
  }

  return (
    <details className="feedback-point">
      <summary>
        <strong>{STATUS_WORDS[point.status]}:</strong> {point.why}
      </summary>
      <dl className="small">
        <dt>Where</dt>
        <dd>{point.where}</dd>
        <dt>What the check found</dt>
        <dd>{point.found}</dd>
        <dt>What the check looked for</dt>
        <dd>{point.looked_for}</dd>
        <dt>Where to look</dt>
        <dd>{point.look}</dd>
      </dl>
      {point.status !== "met" && !sent && !wrong && (
        <button type="button" className="button button-small" onClick={() => setWrong(true)}>
          This is wrong
        </button>
      )}
      {wrong && (
        <div className="actions">
          <label className="small">
            Why? (one line)
            <input type="text" maxLength={200} value={reason} onChange={(e) => setReason(e.target.value)} />
          </label>
          <button type="button" className="button button-small button-primary" onClick={send}>
            Send
          </button>
        </div>
      )}
      {sent && (
        <p className="small muted" role="status">
          Thanks. Your note is saved. Nothing about your progress changed.
        </p>
      )}
    </details>
  );
}

/** Build feedback (SPEC-15 section 10): one summary line, open points first, met points folded. */
export function FeedbackPanel({ feedback }: { feedback: Feedback }) {
  const { points } = feedback;
  const open = points.filter((point) => point.status !== "met");
  const met = points.filter((point) => point.status === "met");
  return (
    <section className="card feedback-panel" aria-label="Build feedback">
      <p role="status">
        <strong>
          {count(points, "met")} found, {count(points, "not_met")} not found, {count(points, "not_checked")} not checked
          yet.
        </strong>{" "}
        These come from rule-based checks, not a judgement of your work.
      </p>
      {feedback.summary && <p className="small">{feedback.summary}</p>}
      {feedback.summary_error && <p className="small muted">{feedback.summary_error}</p>}
      {open.map((point) => (
        <PointCard key={point.requirement_id} point={point} />
      ))}
      {met.length > 0 && (
        <details>
          <summary>{met.length} found</summary>
          {met.map((point) => (
            <PointCard key={point.requirement_id} point={point} />
          ))}
        </details>
      )}
    </section>
  );
}

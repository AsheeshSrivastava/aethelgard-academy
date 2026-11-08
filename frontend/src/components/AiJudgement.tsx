import { useState } from "react";

import type { ExplainResponse } from "../api/client";

/** The shared verdict shape (SPEC-18 section 2). Other screens reuse it for README, ADR and spec feedback. */
export type AiJudgementData = Omit<ExplainResponse, "unit_id" | "evidence_logged">;

interface Props {
  judgement: AiJudgementData;
  /** Called once when the learner says the verdict seems wrong. Omit to hide the button. */
  onDispute?: () => Promise<unknown> | void;
}

/** Shown under a written answer: either the AI's verdict, or why there is none (SPEC-18 section 7). */
export function AiJudgement({ judgement, onDispute }: Props) {
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  if (judgement.status !== "judged") {
    return (
      <div className="result ai-judgement ai-not-judged" role="status">
        <p className="result-title">Not judged</p>
        <p className="small">{judgement.message}</p>
      </div>
    );
  }

  async function dispute() {
    if (!onDispute || sent || busy) return;
    setBusy(true);
    setFailed(false);
    try {
      await onDispute();
      setSent(true);
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  const solid = judgement.verdict === "Solid";
  return (
    <div className={`result ai-judgement ${solid ? "result-passed" : "result-failed"}`}>
      <p className="result-title">{judgement.verdict}</p>
      <ul className="ai-ideas" aria-label="Ideas">
        {(judgement.ideas ?? []).map((idea) => (
          <li key={idea.id} className={idea.met ? "idea-met" : "idea-missed"}>
            <strong>{idea.met ? "Met" : "Missed"}</strong> {idea.text}
          </li>
        ))}
      </ul>
      {judgement.feedback && <p className="small">{judgement.feedback}</p>}
      <p className="small muted">Judged by AXIS ({judgement.model}). AI can be wrong.</p>
      {onDispute &&
        (sent ? (
          <p className="small" role="status">
            Thanks. Noted for review.
          </p>
        ) : (
          <>
            <button type="button" className="button button-small" disabled={busy} onClick={dispute}>
              This seems wrong
            </button>
            {failed && (
              <p className="small" role="alert">
                That did not send. Try again.
              </p>
            )}
          </>
        ))}
    </div>
  );
}

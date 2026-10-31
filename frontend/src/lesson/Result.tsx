import { Link } from "@tanstack/react-router";

import type { AttemptResult } from "../api/client";
import { stepName } from "../lib/format";
import { Prose } from "./Prose";
import { revealText } from "./steps";

export function NextLink({ unitId, step }: { unitId: string; step: string | null }) {
  if (!step) return null;
  return (
    <Link to="/units/$unitId/$step" params={{ unitId, step }} className="button button-primary">
      Next: {stepName(step)}
    </Link>
  );
}

export function Result({ result, unitId, next }: { result: AttemptResult; unitId: string; next: string | null }) {
  const passed = result.outcome === "passed";
  return (
    <div className={`result ${passed ? "result-passed" : "result-failed"}`} role="status" aria-label="Result">
      <p className="result-title">{passed ? "Passed" : "Not yet"}</p>
      <p className="small">{result.feedback}</p>
      {result.score && (
        <p className="small">
          Score: <strong>{`${result.score.passed} of ${result.score.total}`}</strong>
        </p>
      )}
      {result.checks && (
        <ul className="plain-list check-list">
          {result.checks.map((check) => (
            <li key={check.label} className="small">
              {check.passed ? "Passed" : "Failed"}: {check.label}
              {check.detail ? ` (${check.detail})` : ""}
            </li>
          ))}
        </ul>
      )}
      {result.reveal && (
        <div className="small">
          <p>
            Answer: <span className="mono">{revealText(result.reveal.correct)}</span>
          </p>
          {result.reveal.why?.map((reason) => <Prose key={reason}>{reason}</Prose>)}
        </div>
      )}
      <NextLink unitId={unitId} step={next} />
    </div>
  );
}

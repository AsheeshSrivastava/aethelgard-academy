import { useRef, useState } from "react";

type Vote = "up" | "down" | "clear";

async function postVote(turnId: string, vote: Vote): Promise<boolean> {
  try {
    const response = await fetch("/api/v1/learners/me/interactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_type: "axis_feedback", payload: { turn_id: turnId, vote } }),
    });
    return response.ok;
  } catch {
    return false;
  }
}

/** SPEC-29 R27: one rating per finished AXIS answer. State is a tick and bold text, never colour alone. */
export function AxisFeedback({ turnId }: { turnId: string }) {
  const [chosen, setChosen] = useState<"up" | "down" | null>(null);
  const [status, setStatus] = useState("");
  const latest = useRef(0);
  const saved = useRef<"up" | "down" | null>(null); // the last vote the server confirmed

  async function press(button: "up" | "down") {
    const vote: Vote = chosen === button ? "clear" : button;
    const mine = ++latest.current;
    setChosen(vote === "clear" ? null : vote);
    setStatus("");
    const ok = await postVote(turnId, vote);
    if (ok) saved.current = vote === "clear" ? null : vote;
    if (mine !== latest.current) return; // A later press superseded this one: the last press wins.
    if (ok) {
      setStatus("Thanks, noted.");
    } else {
      setChosen(saved.current);
      setStatus("Could not save your vote. Try again.");
    }
  }

  const buttons: { value: "up" | "down"; label: string }[] = [
    { value: "up", label: "Helpful" },
    { value: "down", label: "Not helpful" },
  ];

  return (
    <div className="axis-rate">
      <div role="group" aria-label="Rate this answer" className="axis-rate-buttons">
        {buttons.map(({ value, label }) => (
          <button
            key={value}
            type="button"
            className={chosen === value ? "button button-small axis-rate-chosen" : "button button-small"}
            aria-pressed={chosen === value}
            onClick={() => void press(value)}
          >
            {chosen === value ? `✓ ${label}` : label}
          </button>
        ))}
      </div>
      <p className="small muted axis-rate-status" role="status" aria-live="polite">
        {status}
      </p>
    </div>
  );
}

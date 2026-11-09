import { useMutation } from "@tanstack/react-query";
import { Fragment, useState, type ReactNode } from "react";

import { api, ApiError } from "../api/client";

/* SPEC-19 sections 2 and 3: the two fenced blocks a lesson may hold. The rules mirror the
   server's checks (src/lms/adapters/curriculum/quick_checks.py); an invalid block returns null
   and is shown as an ordinary code block. */

interface Step {
  title: string;
  code?: string;
  result?: string;
  note?: string;
}

export interface StepsBlock {
  caption?: string;
  steps: Step[];
}

export interface QuickCheckBlock {
  id: string;
  question: string;
  options: [string, string][];
}

const STEP_KEYS = ["title", "code", "result", "note"] as const;
const LETTERS = "ABCD";

function pairs(text: string): [string, string][] {
  return text
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => {
      const at = line.indexOf(": ");
      return at < 0 ? [line.replace(/:$/, "").trim(), ""] : [line.slice(0, at).trim(), line.slice(at + 2).trim()];
    });
}

export function parseSteps(text: string): StepsBlock | null {
  const block: StepsBlock = { steps: [] };
  for (const [key, value] of pairs(text)) {
    if (key === "caption") {
      if (block.caption !== undefined) return null;
      block.caption = value;
    } else if (key === "title") {
      block.steps.push({ title: value });
    } else if ((STEP_KEYS as readonly string[]).includes(key)) {
      const step = block.steps.at(-1);
      if (!step) return null;
      step[key as Exclude<(typeof STEP_KEYS)[number], "title">] = value;
    } else {
      return null;
    }
  }
  return block.steps.length >= 2 && block.steps.length <= 5 && block.steps.every((step) => step.title) ? block : null;
}

export function parseQuickCheck(text: string): QuickCheckBlock | null {
  const values: Record<string, string> = {};
  for (const [key, value] of pairs(text)) {
    // A public block never carries the key; if one slipped in, the server reports it and nothing shows it.
    if (key === "answer" || key === "why") continue;
    if (!["id", "question", ...LETTERS].includes(key)) return null;
    values[key] = value;
  }
  const letters = [...LETTERS].filter((letter) => letter in values);
  const valid =
    /^[a-z0-9][a-z0-9.-]*$/.test(values.id ?? "") &&
    !!values.question &&
    letters.length >= 2 &&
    letters.join("") === LETTERS.slice(0, letters.length) &&
    letters.every((letter) => values[letter]);
  return valid ? { id: values.id!, question: values.question!, options: letters.map((letter) => [letter, values[letter]!]) } : null;
}

/** Text with `backticks` shown as code; nothing else is interpreted. */
function Inline({ text }: { text: string }) {
  return (
    <>
      {text.split(/(`[^`]+`)/).map((piece, index) =>
        piece.startsWith("`") && piece.endsWith("`") && piece.length > 1 ? (
          <code key={index}>{piece.slice(1, -1)}</code>
        ) : (
          <Fragment key={index}>{piece}</Fragment>
        ),
      )}
    </>
  );
}

export function StepsFigure({ block }: { block: StepsBlock }) {
  return (
    <figure className="steps-figure">
      <ol className="steps-row">
        {block.steps.map((step, index) => (
          <li key={index} className="steps-item">
            {index > 0 && (
              <span className="steps-arrow" aria-hidden="true">
                →
              </span>
            )}
            <div className="steps-card">
              <span className="steps-title">
                <span className="steps-number" aria-hidden="true">
                  {index + 1}
                </span>
                {step.title}
              </span>
              {step.code && <code className="steps-code">{step.code}</code>}
              {step.result && (
                <span className="steps-result">
                  <span className="sr-only">Result: </span>
                  <code>{step.result}</code>
                </span>
              )}
              {step.note && <span className="steps-note">{step.note}</span>}
            </div>
          </li>
        ))}
      </ol>
      {block.caption && <figcaption className="steps-caption">{block.caption}</figcaption>}
    </figure>
  );
}

type Mark = { kind: "right"; why: string } | { kind: "wrong" } | { kind: "unavailable" };

export function QuickCheckBox({ unitId, block }: { unitId: string; block: QuickCheckBlock }) {
  const [mark, setMark] = useState<Mark | null>(null);
  const [tried, setTried] = useState<string[]>([]);
  const check = useMutation({
    mutationFn: (choice: string) => api.quickCheck(unitId, block.id, choice),
    onSuccess: (result, choice) => {
      if (result.correct) setMark({ kind: "right", why: result.why ?? "" });
      else {
        setMark({ kind: "wrong" });
        setTried((list) => [...list, choice]);
      }
    },
    onError: (error) => {
      if (error instanceof ApiError) setMark({ kind: "unavailable" });
    },
  });
  const done = mark?.kind === "right" || mark?.kind === "unavailable";
  const labelId = `quick-check-${block.id}`;

  let message: ReactNode = null;
  if (mark?.kind === "right") message = <>Right. {mark.why}</>;
  if (mark?.kind === "wrong") message = "Not quite. Try another.";
  if (mark?.kind === "unavailable") message = "This check can't be marked here.";

  return (
    <div className="quick-check" role="group" aria-labelledby={labelId}>
      <div className="quick-check-head">
        <span className="chip quick-check-chip">Quick check</span>
        <span className="small muted">Not graded. Just for you.</span>
      </div>
      <p id={labelId} className="quick-check-question">
        <Inline text={block.question} />
      </p>
      <div className="quick-check-options">
        {block.options.map(([letter, text]) => (
          <button
            key={letter}
            type="button"
            className={`quick-option${tried.includes(letter) ? " quick-option-wrong" : ""}${
              mark?.kind === "right" && check.variables === letter ? " quick-option-right" : ""
            }`}
            disabled={done || check.isPending || tried.includes(letter)}
            aria-label={`${letter}: ${text.replace(/`/g, "")}`}
            onClick={() => check.mutate(letter)}
          >
            <span className="quick-letter" aria-hidden="true">
              {letter}
            </span>
            <Inline text={text} />
          </button>
        ))}
      </div>
      <p className={`quick-check-mark${mark?.kind === "right" ? " quick-check-right" : ""}`} role="status">
        {message}
      </p>
    </div>
  );
}

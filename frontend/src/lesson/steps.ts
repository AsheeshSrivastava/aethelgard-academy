const ACTIVITY_NAMES: Record<string, string> = {
  video: "Explain",
  explain: "Explain",
  predict: "Predict",
  trace: "Trace",
  specify: "Specify",
  decompose: "Decompose",
  modify: "Modify",
  "debug-validate": "Debug & Validate",
  build: "Build",
  evaluate: "Evaluate",
  direct: "Direct",
  playground: "Modify",
};

/** The ActivityType AXIS expects for a lesson step. */
export const activityFor = (step: string) => ACTIVITY_NAMES[step] ?? "Explain";

export function nextStep(steps: string[], step: string): string | null {
  const index = steps.indexOf(step);
  return index >= 0 ? (steps[index + 1] ?? null) : null;
}

export function revealText(correct: unknown): string {
  if (Array.isArray(correct)) return correct.join(" / ");
  if (correct && typeof correct === "object" && "output" in correct) {
    // A practice trace: the printed lines, then the state table (ADR-0031).
    const full = correct as { output: string[]; states?: { line: number; state: Record<string, unknown> }[] };
    const cells = (full.states ?? []).flatMap((row) =>
      Object.entries(row.state).map(([name, value]) => `line ${row.line}: ${name} = ${String(value)}`),
    );
    return [full.output.join(" / "), ...cells].join(". ");
  }
  if (correct && typeof correct === "object") {
    const key = correct as { line?: number; error_type?: string };
    return `Line ${key.line}, ${key.error_type}`;
  }
  return String(correct);
}

// The video has its own step, and the app replaces the command-line workflow.
const SECTIONS_SHOWN_ELSEWHERE = /^## .*(Video Walkthrough|Local (Editor|Workflow) Instructions)/;

export interface ExplainPart {
  title: string;
  body: string;
}

/**
 * Explain as parts (SPEC-19 section 1): each "## " section is a part named by its heading, and
 * text before the first heading belongs to part 1. "Say it back" is added by the page, not here.
 */
export function explainParts(markdown: string): ExplainPart[] {
  const text = splitLessonForExplain(markdown);
  if (!text) return [];
  const chunks = text.split(/^(?=## )/m);
  const intro = chunks[0]?.startsWith("## ") ? "" : (chunks.shift() ?? "").trim();
  if (chunks.length === 0) return [{ title: "Read", body: intro }];
  return chunks.map((chunk, index) => {
    const [heading = "", ...rest] = chunk.split("\n");
    const body = rest.join("\n").trim();
    return { title: heading.replace(/^##\s+/, "").trim(), body: index === 0 && intro ? `${intro}\n\n${body}` : body };
  });
}

/** The lesson text for Explain, without the sections other steps already cover. */
export function splitLessonForExplain(markdown: string): string {
  const parts = markdown.split(/^(?=## )/m);
  return parts
    .filter((part) => !SECTIONS_SHOWN_ELSEWHERE.test(part))
    .join("")
    .replace(/^# .*\n/, "")
    .replace(/^---\s*$/gm, "")
    .trim();
}

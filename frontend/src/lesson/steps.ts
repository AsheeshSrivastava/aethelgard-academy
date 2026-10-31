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
  if (correct && typeof correct === "object") {
    const key = correct as { line?: number; error_type?: string };
    return `Line ${key.line}, ${key.error_type}`;
  }
  return String(correct);
}

// The video has its own step, and the app replaces the command-line workflow.
const SECTIONS_SHOWN_ELSEWHERE = /^## .*(Video Walkthrough|Local (Editor|Workflow) Instructions)/;

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

import type { ColdCheckStatus, Decision, Schemas } from "../api/client";

export const LEVELS = ["Understand", "Apply", "Adapt", "Own"] as const;

const STEP_NAMES: Record<string, string> = {
  video: "Video",
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
  playground: "Playground",
  cold_check: "Cold Check",
};

const STEP_DESCRIPTIONS: Record<string, string> = {
  video: "A short walkthrough of the idea.",
  explain: "Say the concept in your own words.",
  predict: "Commit to what happens before you run anything.",
  trace: "Follow the program step by step.",
  specify: "Pin down what the program must do.",
  decompose: "Split the work into checked pieces.",
  modify: "Change working code in small steps.",
  "debug-validate": "Find the fault and prove the fix.",
  build: "Put the pieces together yourself.",
  evaluate: "Judge an answer and say why.",
  direct: "Work with a tool on purpose.",
  playground: "Try things freely. This practice is not graded.",
  cold_check: "A delayed check, with no AXIS help.",
};

const COURSE_PREFIXES: Record<string, string> = { PY: "python", BE: "backend", AI: "ai-engineering" };

export const stepName = (step: string) => STEP_NAMES[step] ?? step;
export const stepDescription = (step: string) => STEP_DESCRIPTIONS[step] ?? "";
export const courseOfUnit = (unitId: string) => COURSE_PREFIXES[unitId.slice(0, 2)] ?? "python";

/** A fresh start is not a verdict, so "Undecided" is shown as not started. */
export const decisionLabel = (decision: Decision) => (decision === "Undecided" ? "Not started" : decision);

export function buildLockMessage(pending: string[]): string {
  if (pending.length === 1) return `Locked until ${pending[0]} passes its Cold Check`;
  if (pending.length === 2) return `Locked until ${pending[0]} and ${pending[1]} pass their Cold Checks`;
  return `Locked until ${pending.length} units pass their Cold Checks`;
}

/** Assessment stays invisible (AGENTS.md section 6): no system wording before any work exists. */
export function skillReason(decision: Decision, reason: string): string {
  return decision === "Undecided" ? "Nothing recorded yet." : reason;
}

export function nextActionMessage(action: Schemas["NextAction"]): string {
  if (action.decision !== "Undecided") return action.message;
  return `Start with ${stepName(action.activity)} in ${action.unit_id}.`;
}

export function countdown(availableAt: string, now: Date): string {
  const left = new Date(availableAt).getTime() - now.getTime();
  if (left <= 0) return "";
  const minutes = Math.ceil(left / 60_000);
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (hours === 0) return `${rest} min`;
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`;
}

export function coldCheckMessage(status: ColdCheckStatus, now: Date): string {
  const wait = status.available_at ? countdown(status.available_at, now) : "";
  switch (status.state) {
    case "waiting":
      return wait ? `Opens in ${wait}.` : "Ready now.";
    case "failed_waiting":
      return wait ? `Try again in ${wait}.` : "Ready to try again.";
    case "available":
      return "Ready now. No AXIS help, and one try for each skill.";
    case "passed":
      return "Passed.";
    default:
      return "Finish the activities to start the 24-hour wait.";
  }
}

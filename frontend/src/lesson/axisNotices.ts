/** What the AXIS panel says when an answer or the whole panel has no course source (SPEC-24 section 3).
 * The words come from the server's state, never from what the model wrote. */

const ANSWER_NOTES: Record<string, string> = {
  not_found: "No course source matched this question.",
  no_index: "Course reference not loaded. This answer was not checked against the course.",
  unavailable: "Course search unavailable. This answer was not checked against the course.",
};

const GENERIC_NOTE = "This answer was not checked against the course.";

/** The note under a reply; null when the reply was grounded or the state does not apply (mock). */
export function answerNote(sourceState: string | undefined): string | null {
  if (!sourceState || sourceState === "course") return null;
  return ANSWER_NOTES[sourceState] ?? GENERIC_NOTE;
}

/** The label under a reply that was found with keyword search only (SPEC-27 D2, ADR-0035 2.7). */
export const KEYWORD_ONLY_NOTE = "Keyword search only";

const STATUS_LINES: Record<string, string> = {
  not_loaded: "Course reference not loaded. AXIS can still talk with you, but its answers are not checked against the course.",
  unavailable: "Course search is not working right now. AXIS answers are not checked against the course.",
  mock: "Practice mode: AXIS replies are fixed examples, not checked against the course.",
};

/** The standing line under the AXIS header; null when ready or unknown. */
export function statusLine(courseReference: string | undefined): string | null {
  return (courseReference && STATUS_LINES[courseReference]) || null;
}

/** Ask once whether the course reference is loaded. Any failure shows nothing (SPEC-24 R11). */
export async function fetchCourseReference(): Promise<string | undefined> {
  try {
    const response = await fetch("/api/v1/axis/status");
    if (!response.ok) return undefined;
    const body = (await response.json()) as { course_reference?: unknown };
    return typeof body.course_reference === "string" ? body.course_reference : undefined;
  } catch {
    return undefined;
  }
}

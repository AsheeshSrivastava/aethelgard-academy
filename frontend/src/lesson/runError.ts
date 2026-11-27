import { createContext } from "react";

/** The latest run's error output, held by the page for AXIS (ADR-0041, SPEC-33 section 4: E1, section 12). */
export interface RunError {
  success: false;
  stdout: "";
  stderr: string;
  exit_code: number;
  duration_ms: number;
}

/** A run terminal says what its latest run left, and the reset actions say `undefined`. */
export type ReportRunError = (error: RunError | undefined) => void;

export const RunErrorContext = createContext<ReportRunError>(() => undefined);

/** How much of a long error the page holds and sends. The end is kept: the cause line is last. */
export const MAX_RUN_ERROR_CHARS = 20_000;

/** Add a piece of error output without letting what is held grow without bound. */
export function addRunError(held: string, piece: string): string {
  const all = held + piece;
  return all.length > 4 * MAX_RUN_ERROR_CHARS ? all.slice(-2 * MAX_RUN_ERROR_CHARS) : all;
}

/** The end of the output, starting on a whole line where there is one, so no path is sent cut in half. */
export function endOfRunError(text: string): string {
  if (text.length <= MAX_RUN_ERROR_CHARS) return text;
  const end = text.slice(-MAX_RUN_ERROR_CHARS);
  const line = end.indexOf("\n");
  // One very long last line: keep it, minus a half character left by the cut.
  return line >= 0 && line < end.length - 1 ? end.slice(line + 1) : end.replace(/^[\udc00-\udfff]/, "");
}

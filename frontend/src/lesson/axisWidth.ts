export const DEFAULT_AXIS_WIDTH = 340;
export const MIN_AXIS_WIDTH = 280;
export const MIN_CONTENT_WIDTH = 420;
export const AXIS_WIDTH_STEP = 24;
export const MAX_AXIS_SHARE = 0.6;

const STORAGE_KEY = "axis-width";

/** Keep the panel usable, and leave the lesson room beside it. */
export function clampAxisWidth(width: number, layoutWidth: number): number {
  const largest = Math.min(layoutWidth * MAX_AXIS_SHARE, layoutWidth - MIN_CONTENT_WIDTH);
  return Math.round(Math.max(MIN_AXIS_WIDTH, Math.min(width, largest)));
}

export function loadAxisWidth(): number {
  try {
    const saved = Number(localStorage.getItem(STORAGE_KEY));
    return saved >= MIN_AXIS_WIDTH ? saved : DEFAULT_AXIS_WIDTH;
  } catch {
    return DEFAULT_AXIS_WIDTH;
  }
}

export function saveAxisWidth(width: number): void {
  try {
    localStorage.setItem(STORAGE_KEY, String(width));
  } catch {
    // Private windows can refuse storage; the width still applies for this visit.
  }
}

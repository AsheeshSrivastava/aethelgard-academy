/**
 * A page can ask to return to a build (SPEC-15 section 9.5). Only this app's own build path is
 * honoured; anything else is ignored, so a link cannot send a learner somewhere else.
 */
const BUILD_PATH = /^\/courses\/([a-z0-9-]+)\/stages\/(\d+)\/build$/;

export function buildPath(courseId: string, stage: number | string): string {
  return `/courses/${courseId}/stages/${stage}/build`;
}

export function parseBuildPath(back: unknown): { courseId: string; stage: string } | null {
  if (typeof back !== "string") return null;
  const match = BUILD_PATH.exec(back);
  const [, courseId, stage] = match ?? [];
  return courseId && stage ? { courseId, stage } : null;
}

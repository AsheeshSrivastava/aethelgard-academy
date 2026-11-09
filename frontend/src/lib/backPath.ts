import { courseOfUnit } from "./format";

/**
 * Where "Go back" leads when the tab has no earlier page in this app (a deep link or a fresh
 * tab). It mirrors how the pages nest: lesson -> unit -> course map -> courses -> home.
 * Returns null on the front page, which has no back arrow.
 */
export function parentPath(pathname: string, search: Record<string, unknown> = {}): string | null {
  const parts = pathname.split("/").filter(Boolean);
  const [first, second, third] = parts;
  if (!first) return null;
  if (first === "courses") {
    if (!second) return "/";
    return parts.length > 2 ? `/courses/${second}` : "/courses";
  }
  if (first === "units" && second) {
    if (third) return `/units/${second}`;
    const build = parseBuildPath(search.back);
    return build ? buildPath(build.courseId, build.stage) : `/courses/${courseOfUnit(second)}`;
  }
  if (first === "concepts" && second) return "/concepts";
  if (first === "reviews") return "/progress";
  return "/";
}

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

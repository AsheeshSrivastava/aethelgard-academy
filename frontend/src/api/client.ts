import { newInteractionId } from "../lib/interaction";
import type { components } from "./schema";

export type Schemas = components["schemas"];
export type Course = Schemas["Course"];
export type CourseMap = Schemas["CourseMap"];
export type Unit = Schemas["Unit"];
export type ColdCheckStatus = Schemas["ColdCheckStatus"];
export type ProficiencyView = Schemas["ProficiencyView"];
export type EvidenceEntry = Schemas["EvidenceEntry"];
export type Decision = Schemas["ProgressionDecision"];
export type UnitState = Schemas["UnitState"];
export type Exercise = Schemas["Exercise"];
export type AttemptResult = Schemas["AttemptResult"];
export type ExplainResponse = Schemas["ExplainResponse"];
export type ConceptSummary = Schemas["ConceptSummary"];
export type ConceptDetail = Schemas["ConceptDetail"];
export type StageBuild = Schemas["StageBuild"];
export type StageReviewStatus = Schemas["StageReviewStatus"];
export type DueReview = Schemas["DueReview"];

interface StageRef {
  courseId: string;
  stage: number;
}

const BASE = "/api/v1";

/** One id per app visit, sent with every request so the interaction log can group a visit (ADR-0022). */
export const SESSION_ID = newInteractionId();

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("X-Session-Id", SESSION_ID);
  const response = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    const problem = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new ApiError(response.status, problem?.detail ?? `Request failed (${response.status}).`);
  }
  return (response.status === 204 ? undefined : await response.json()) as T;
}

function query(params: Record<string, string | number | undefined>): string {
  const pairs = Object.entries(params).filter(([, value]) => value !== undefined);
  const search = new URLSearchParams(pairs.map(([key, value]) => [key, String(value)]));
  return pairs.length ? `?${search}` : "";
}

function json(method: string, body: unknown): RequestInit {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export const api = {
  /** Fire and forget: a failed log write must never reach the page (ADR-0022). */
  logEvent: (event: Schemas["ClientEvent"]) =>
    request<void>("/learners/me/interactions", json("POST", event)).catch(() => undefined),
  features: () => request<Schemas["Features"]>("/features"),
  courses: () => request<Course[]>("/courses"),
  courseMap: (courseId: string) => request<CourseMap>(`/courses/${courseId}`),
  unit: (unitId: string) => request<Unit>(`/units/${unitId}`),
  coldCheck: (unitId: string) => request<ColdCheckStatus>(`/learners/me/units/${unitId}/cold-check`),
  coldCheckFeedback: (unitId: string) =>
    request<Schemas["ColdCheckFeedback"]>(`/learners/me/units/${unitId}/cold-check/feedback`),
  unitState: (unitId: string) => request<UnitState>(`/learners/me/units/${unitId}/state`),
  resetUnit: (unitId: string) => request<void>(`/learners/me/units/${unitId}/reset`, { method: "POST" }),
  proficiency: (params: { courseId?: string; stage?: number }) =>
    request<ProficiencyView>(
      `/learners/me/proficiency${query({ course_id: params.courseId, stage: params.stage })}`,
    ),
  ledger: (skillId?: string) => request<EvidenceEntry[]>(`/learners/me/ledger${query({ skill_id: skillId })}`),
  mySkills: () => request<Schemas["SkillsOverview"]>("/learners/me/skills"),
  saveUnitState: (unitId: string, state: UnitState) =>
    request<UnitState>(`/learners/me/units/${unitId}/state`, json("PUT", state)),
  exercise: (unitId: string, activity: string) =>
    request<Exercise>(`/learners/me/units/${unitId}/activities/${activity}/exercise`),
  regenerate: (unitId: string, activity: string) =>
    request<Exercise>(`/learners/me/units/${unitId}/activities/${activity}/exercises:regenerate`, { method: "POST" }),
  attempt: (attempt: Schemas["Attempt"]) => request<AttemptResult>("/learners/me/attempts", json("POST", attempt)),
  explain: (unitId: string, explanation: string) =>
    request<ExplainResponse>("/explain", json("POST", { unit_id: unitId, explanation })),
  disputeJudgement: (interactionId: string) =>
    request<void>(`/learners/me/judgements/${interactionId}:dispute`, { method: "POST" }),
  getDraft: (exerciseId: string) => request<Schemas["Draft"]>(`/learners/me/drafts/${exerciseId}`),
  saveDraft: (exerciseId: string, files: Record<string, string>) =>
    request<void>(`/learners/me/drafts/${exerciseId}`, json("PUT", { files })),
  stageBuild: ({ courseId, stage }: StageRef) => request<StageBuild>(`/courses/${courseId}/stages/${stage}/build`),
  checkBuild: ({ courseId, stage }: StageRef, body: Schemas["BuildCheckRequest"]) =>
    request<Schemas["BuildCheckResult"]>(`/learners/me/courses/${courseId}/stages/${stage}/build:check`, json("POST", body)),
  resetBuild: ({ courseId, stage }: StageRef) =>
    request<void>(`/learners/me/courses/${courseId}/stages/${stage}/build:reset`, { method: "POST" }),
  stageReview: ({ courseId, stage }: StageRef) =>
    request<StageReviewStatus>(`/learners/me/courses/${courseId}/stages/${stage}/review`),
  resetStageReview: ({ courseId, stage }: StageRef) =>
    request<void>(`/learners/me/courses/${courseId}/stages/${stage}/review:reset`, { method: "POST" }),
  stageReviewExercise: ({ courseId, stage }: StageRef) =>
    request<Exercise>(`/learners/me/courses/${courseId}/stages/${stage}/review/exercise`),
  dueReviews: () => request<DueReview[]>("/learners/me/reviews/due"),
  recheckExercise: (skillId: string, days: number) =>
    request<Exercise>(`/learners/me/reviews/${encodeURIComponent(skillId)}/${days}/exercise`),
  concepts: (q?: string) => request<ConceptSummary[]>(`/concepts${query({ q })}`),
  concept: (slug: string) => request<ConceptDetail>(`/concepts/${encodeURIComponent(slug)}`),
  recentConcepts: () => request<ConceptSummary[]>("/learners/me/concepts/recent"),
  conceptOpened: (slug: string) =>
    request<void>(`/learners/me/concepts/recent/${encodeURIComponent(slug)}`, { method: "PUT" }),
};

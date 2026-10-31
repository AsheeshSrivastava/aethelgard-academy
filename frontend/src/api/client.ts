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

const BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, init);
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
  courses: () => request<Course[]>("/courses"),
  courseMap: (courseId: string) => request<CourseMap>(`/courses/${courseId}`),
  unit: (unitId: string) => request<Unit>(`/units/${unitId}`),
  coldCheck: (unitId: string) => request<ColdCheckStatus>(`/learners/me/units/${unitId}/cold-check`),
  unitState: (unitId: string) => request<UnitState>(`/learners/me/units/${unitId}/state`),
  resetUnit: (unitId: string) => request<void>(`/learners/me/units/${unitId}/reset`, { method: "POST" }),
  proficiency: (params: { courseId?: string; stage?: number }) =>
    request<ProficiencyView>(
      `/learners/me/proficiency${query({ course_id: params.courseId, stage: params.stage })}`,
    ),
  ledger: (skillId?: string) => request<EvidenceEntry[]>(`/learners/me/ledger${query({ skill_id: skillId })}`),
  saveUnitState: (unitId: string, state: UnitState) =>
    request<UnitState>(`/learners/me/units/${unitId}/state`, json("PUT", state)),
  exercise: (unitId: string, activity: string) =>
    request<Exercise>(`/learners/me/units/${unitId}/activities/${activity}/exercise`),
  regenerate: (unitId: string, activity: string) =>
    request<Exercise>(`/learners/me/units/${unitId}/activities/${activity}/exercises:regenerate`, { method: "POST" }),
  attempt: (attempt: Schemas["Attempt"]) => request<AttemptResult>("/learners/me/attempts", json("POST", attempt)),
  explain: (unitId: string, explanation: string) =>
    request<ExplainResponse>("/explain", json("POST", { unit_id: unitId, explanation })),
  getDraft: (exerciseId: string) => request<Schemas["Draft"]>(`/learners/me/drafts/${exerciseId}`),
  saveDraft: (exerciseId: string, files: Record<string, string>) =>
    request<void>(`/learners/me/drafts/${exerciseId}`, json("PUT", { files })),
};

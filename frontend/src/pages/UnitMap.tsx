import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { ColdCheckStatus, Unit } from "../api/client";
import { BackLink, ErrorNote, Loading, Panel } from "../components/common";
import { ResetUnit } from "../components/ResetUnit";
import { coldCheckMessage, courseOfUnit, stepDescription, stepName } from "../lib/format";

const COURSE_NAMES: Record<string, string> = {
  python: "Python",
  backend: "Python for Backend/AI",
  "ai-engineering": "AI Engineering",
};

function useNow(intervalMs: number): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs]);
  return now;
}

function LessonPath({ unit, done, current, cold }: { unit: Unit; done: string[]; current: string | null; cold?: ColdCheckStatus }) {
  const now = useNow(60_000);
  return (
    <ol className="lesson-path" aria-label="Lesson path">
      {(unit.activities ?? []).map((step, index) => {
        const isDone = done.includes(step);
        const isCurrent = step === current && !isDone;
        return (
          <li key={step}>
            <Link to="/units/$unitId/$step" params={{ unitId: unit.unit_id, step }} className={isCurrent ? "path-row path-current" : "path-row"}>
            <span className={`path-dot${isDone ? " path-dot-done" : isCurrent ? " path-dot-current" : ""}`} aria-hidden="true">
              {isDone ? "✓" : index + 1}
            </span>
            <span className="path-text">
              <span className="path-name">{stepName(step)}</span>
              <span className="small muted">
                {step === "cold_check" && cold ? coldCheckMessage(cold, now) : stepDescription(step)}
              </span>
            </span>
            {isDone && <span className="path-state">Done</span>}
            {isCurrent && <span className="path-state path-state-current">In progress</span>}
            </Link>
          </li>
        );
      })}
    </ol>
  );
}

export function UnitMap() {
  const { unitId } = useParams({ from: "/units/$unitId" });
  const unit = useQuery({ queryKey: ["unit", unitId], queryFn: () => api.unit(unitId) });
  const cold = useQuery({ queryKey: ["coldCheck", unitId], queryFn: () => api.coldCheck(unitId) });
  const state = useQuery({ queryKey: ["unitState", unitId], queryFn: () => api.unitState(unitId) });

  const courseId = courseOfUnit(unitId);
  const courseName = COURSE_NAMES[courseId] ?? "Course";
  const back = <BackLink to="/courses/$courseId" params={{ courseId }} label={`${courseName} course map`} />;

  if (unit.isPending) {
    return (
      <main className="container page">
        <Loading what="the unit" />
      </main>
    );
  }
  if (unit.isError) {
    return (
      <main className="container page">
        {back}
        <ErrorNote error={unit.error} />
      </main>
    );
  }

  const data = unit.data;
  return (
    <main className="container page">
      {back}
      <div className="unit-head">
        <div>
          <span className="mono muted">
            {courseName} · {data.stage_label} · Unit {data.unit_id}
          </span>
          <h1 className="page-title">{data.title}</h1>
          <p className="lead">{data.concept_line}</p>
        </div>
        <div className="actions">
          <ResetUnit unitId={unitId} />
          <Link to="/units/$unitId/$step" params={{ unitId, step: state.data?.step ?? "video" }} className="button button-primary">
            {state.data?.step ? "Continue lesson" : "Start lesson"}
          </Link>
        </div>
      </div>

      <div className="unit-layout">
        <section className="card panel unit-path" aria-labelledby="path">
          <h2 id="path" className="panel-title">
            Lesson path
          </h2>
          <LessonPath unit={data} done={state.data?.done_steps ?? []} current={state.data?.step ?? null} cold={cold.data} />
        </section>
        <aside className="unit-aside">
          <Panel title="Skills this unit builds" id="skills">
            <ul className="plain-list">
              {data.target_skills.map((skill) => (
                <li key={skill.skill_id} className="skill-row">
                  <span>
                    <span className="mono">{skill.skill_id}</span> {skill.skill_name}
                  </span>
                  <span className="chip chip-level">{skill.goal_level}</span>
                </li>
              ))}
            </ul>
          </Panel>
          {(data.prerequisites ?? []).length > 0 && (
            <Panel title="Builds on" id="builds-on">
              <p className="small">{data.prerequisites?.join(", ")}</p>
            </Panel>
          )}
        </aside>
      </div>
    </main>
  );
}

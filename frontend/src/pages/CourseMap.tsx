import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";

import { api } from "../api/client";
import type { Schemas } from "../api/client";
import { BackLink, DecisionChip, ErrorNote, Loading } from "../components/common";
import { buildLockMessage, nextActionMessage } from "../lib/format";

type Stage = Schemas["StageView"];

function BuildTile({ stage }: { stage: Stage }) {
  const build = stage.build;
  if (!build) return null;
  return (
    <div className="build-tile">
      <span className="build-head">
        <span className="mono">{build.title}</span>
        <span className="chip chip-build">{build.kind === "script" ? "Script" : "Mini-project"}</span>
      </span>
      {build.locked ? (
        <span className="small">{buildLockMessage(build.pending_units)}</span>
      ) : (
        <span className="small">Unlocked</span>
      )}
    </div>
  );
}

function StageCard({ stage, current }: { stage: Stage; current: boolean }) {
  return (
    <div className={`card stage${current ? " stage-current" : ""}`}>
      <div className="stage-head">
        <span className="mono muted">Stage {stage.stage}</span>
        <h2>{stage.title}</h2>
        <span className="muted small stage-count">{stage.units.length} units</span>
      </div>
      <div className="unit-grid">
        {stage.units.map((unit) => (
          <Link key={unit.unit_id} to="/units/$unitId" params={{ unitId: unit.unit_id }} className="unit-tile">
            <span className="unit-tile-head">
              <span className="mono muted">{unit.unit_id}</span>
              <DecisionChip decision={unit.decision} />
            </span>
            <span className="unit-title">{unit.title}</span>
            <span className="skill-tags">
              {unit.target_skills.map((skill) => (
                <span key={skill.skill_id} className="skill-tag">
                  {skill.skill_id} {skill.goal_level}
                </span>
              ))}
            </span>
          </Link>
        ))}
        <BuildTile stage={stage} />
      </div>
    </div>
  );
}

export function CourseMap() {
  const { courseId } = useParams({ from: "/courses/$courseId" });
  const map = useQuery({ queryKey: ["courseMap", courseId], queryFn: () => api.courseMap(courseId) });
  const progress = useQuery({
    queryKey: ["proficiency", courseId],
    queryFn: () => api.proficiency({ courseId }),
    enabled: map.isSuccess,
  });

  if (map.isPending) {
    return (
      <main className="container page">
        <Loading what="the course map" />
      </main>
    );
  }
  if (map.isError) {
    return (
      <main className="container page">
        <BackLink to="/courses" label="Courses" />
        <ErrorNote error={map.error} />
      </main>
    );
  }

  const { course, stages } = map.data;
  const passed = stages.flatMap((s) => s.units).filter((u) => u.cold_check_state === "passed").length;
  const next = progress.data?.next_action;

  return (
    <main className="container page">
      <BackLink to="/courses" label="Courses" />
      <div className="course-layout">
        <aside className="course-aside">
          <div className="card panel">
            <span className="mono muted">Course map</span>
            <h1 className="page-title">{course.title}</h1>
            <p className="small">{course.summary}</p>
            <div className="counts">
              <span>
                <strong>{course.stage_count}</strong> stages
              </span>
              <span>
                <strong>{course.unit_count}</strong> units
              </span>
            </div>
            <div className="meter" role="img" aria-label={`${passed} of ${course.unit_count} units passed`}>
              <div style={{ width: `${(passed / Math.max(course.unit_count, 1)) * 100}%` }} />
            </div>
            <span className="muted small">{passed} passed their Cold Check</span>
          </div>
          {next && (
            <div className="card panel panel-warm">
              <span className="eyebrow">Next for you</span>
              <span className="small">{nextActionMessage(next)}</span>
              <Link to="/units/$unitId" params={{ unitId: next.unit_id }}>
                Open {next.unit_id}
              </Link>
            </div>
          )}
        </aside>
        <section className="stage-list" aria-label="Stages">
          {stages.map((stage) => (
            <StageCard key={stage.stage} stage={stage} current={stage.stage === progress.data?.stage} />
          ))}
        </section>
      </div>
    </main>
  );
}

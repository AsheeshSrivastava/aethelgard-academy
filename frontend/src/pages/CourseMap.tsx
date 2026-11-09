import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";

import { api } from "../api/client";
import type { Schemas } from "../api/client";
import { DecisionChip, ErrorNote, Loading } from "../components/common";
import { buildLockMessage, maturityLabel, nextActionMessage } from "../lib/format";

/* Course map (redesign step 4, owner-approved mock "CourseMap"). Every count and state comes from
   the course map and progress APIs. Learners read "Module" (ADR-0027); code keeps "stage".
   Class names stage, stage-head and build-tile are kept: tests find Modules and tiles by them. */

type Stage = Schemas["StageView"];
type Skill = Schemas["SkillView"];

const REVIEW_TILE_TEXT: Record<string, string> = {
  available: "Ready",
  failed_waiting: "Not yet. You can try again later.",
  passed: "Passed",
};

/** Supporting roadmaps slotted into a course (ADR-0020), named by their label prefix. */
const SLOTTED_NAMES: Record<string, string> = {
  TW: "Technical writing",
  DSA: "Data structures and algorithms",
  GIT: "Version control",
  SD: "Software design",
  AAE: "AI-assisted engineering",
  NET: "Networking",
  DB: "Databases",
};

const LEVELS = ["Understand", "Apply", "Adapt", "Own"] as const;

const isCoreModule = (stage: Stage) => stage.label.startsWith("Module");
const passedCount = (stage: Stage) => stage.units.filter((unit) => unit.cold_check_state === "passed").length;
const isDone = (stage: Stage) => stage.units.length > 0 && passedCount(stage) === stage.units.length;

function ReviewTile({ courseId, stage }: { courseId: string; stage: Stage }) {
  const state = stage.build?.review_state;
  if (!state || state === "unavailable" || (state === "not_ready" && !stage.build?.review_planned)) return null;
  const head = <span className="cm-tile-title">Module review</span>;
  if (state === "not_ready") {
    return (
      <div className="build-tile cm-review-tile">
        {head}
        <span className="small">Opens when every unit passes its Cold Check</span>
      </div>
    );
  }
  return (
    <Link
      to="/courses/$courseId/stages/$stage/review"
      params={{ courseId, stage: String(stage.stage) }}
      className={`build-tile cm-review-tile${state === "passed" ? " cm-review-passed" : ""}`}
    >
      {head}
      <span className="small">{REVIEW_TILE_TEXT[state]}</span>
    </Link>
  );
}

function BuildTile({ courseId, stage }: { courseId: string; stage: Stage }) {
  const build = stage.build;
  if (!build) return null;
  const open = !build.locked && build.authored;
  const head = (
    <span className="build-head">
      <span className="cm-tile-title">{build.title}</span>
      <span className="chip chip-build">{build.kind === "script" ? "Script" : "Mini-project"}</span>
      <span className="chip chip-maturity">{maturityLabel(build.maturity)}</span>
    </span>
  );
  if (open) {
    return (
      <Link to="/courses/$courseId/stages/$stage/build" params={{ courseId, stage: String(stage.stage) }} className="build-tile cm-build-open">
        {head}
        <span className="small">Unlocked</span>
      </Link>
    );
  }
  return (
    <div className="build-tile">
      {head}
      <span className="small">{build.locked ? buildLockMessage(build.pending_units) : "Not written yet"}</span>
    </div>
  );
}

function StageCard({ courseId, stage, current }: { courseId: string; stage: Stage; current: boolean }) {
  const passed = passedCount(stage);
  const slotted = SLOTTED_NAMES[stage.label.split(" ")[0] ?? ""];
  return (
    <section className={`card stage${current ? " stage-current" : ""}`} aria-labelledby={`module-${stage.stage}`}>
      <div className="stage-head">
        <span className="mono muted">{stage.label}</span>
        <h2 id={`module-${stage.stage}`}>{stage.title}</h2>
        {current && <span className="chip cm-chip-accent">Current</span>}
        {slotted && <span className="chip cm-chip-info">{slotted}</span>}
        <span className="cm-stage-progress">
          <span className="muted small">
            {passed} of {stage.units.length} units passed
          </span>
          <span className="cm-bar" aria-hidden="true">
            <span style={{ width: `${(passed / Math.max(stage.units.length, 1)) * 100}%` }} />
          </span>
        </span>
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
            {!unit.authored && <span className="muted small">Lesson not written yet</span>}
          </Link>
        ))}
      </div>
      {(stage.build?.review_state || stage.build) && (
        <div className="cm-tiles">
          <ReviewTile courseId={courseId} stage={stage} />
          <BuildTile courseId={courseId} stage={stage} />
        </div>
      )}
    </section>
  );
}

/** The core Modules in order, as a row of numbered steps. */
function ModulePath({ stages, current }: { stages: Stage[]; current?: number | null }) {
  const core = stages.filter(isCoreModule);
  if (core.length === 0) return null;
  const here = core.find((stage) => stage.stage === current);
  return (
    <nav className="cm-path" aria-label="Your path through the Modules">
      <div className="cm-path-head">
        <span className="cm-path-title">Your path through {core.length} Modules</span>
        {here && <span className="muted small">You are on {here.label}</span>}
      </div>
      <ol className="cm-steps">
        {core.map((stage) => {
          const state = stage.stage === current ? "current" : isDone(stage) ? "done" : "todo";
          return (
            <li key={stage.stage} className={`cm-step cm-step-${state}`}>
              {/* A button, not a #link: scrolling should not add a page to the Back arrow's history. */}
              <button
                type="button"
                aria-current={state === "current" ? "step" : undefined}
                aria-label={`${stage.label}: ${stage.title}`}
                onClick={() => document.getElementById(`module-${stage.stage}`)?.scrollIntoView({ behavior: "smooth", block: "start" })}
              >
                <span className="cm-step-dot" aria-hidden="true">
                  {state === "done" ? "✓" : stage.label.replace("Module ", "")}
                </span>
                <span className="cm-step-name">{stage.title}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function SkillsPanel({ skills, label }: { skills: Skill[]; label?: string }) {
  if (skills.length === 0) return null;
  return (
    <div className="card cm-side-card">
      <h2 className="cm-side-title">Skills in {label ?? "this Module"}</h2>
      <ul className="cm-skills">
        {skills.map((skill) => {
          const reached = skill.current_level ? LEVELS.indexOf(skill.current_level) + 1 : 0;
          return (
            <li key={skill.skill_id}>
              <span className="cm-skill-line">
                <span>
                  {skill.skill_id} {skill.skill_name}
                </span>
                <span className="muted">{skill.current_level ?? "Not yet"}</span>
              </span>
              <span className="cm-bar" role="img" aria-label={`${skill.skill_id}: ${reached} of 4 levels`}>
                <span style={{ width: `${(reached / LEVELS.length) * 100}%` }} />
              </span>
            </li>
          );
        })}
      </ul>
      <Link to="/skills" className="small">
        Open My skills
      </Link>
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
        <ErrorNote error={map.error} />
      </main>
    );
  }

  const { course, stages } = map.data;
  const passed = stages.flatMap((s) => s.units).filter((u) => u.cold_check_state === "passed").length;
  const percent = Math.round((passed / Math.max(course.unit_count, 1)) * 100);
  const current = progress.data?.stage;
  const currentLabel = stages.find((stage) => stage.stage === current)?.label;
  const next = progress.data?.next_action;

  return (
    <main className="container page cm-page">
      <header className="card cm-hero">
        <div className="cm-hero-copy">
          <span className="eyebrow cm-eyebrow">Course map</span>
          <h1 className="cm-title">{course.title}</h1>
          <p className="muted">{course.summary}</p>
        </div>
        <div className="cm-hero-stats">
          <div
            className="cm-ring"
            role="img"
            aria-label={`${passed} of ${course.unit_count} units passed`}
            style={{ background: `conic-gradient(var(--accent) 0 ${percent}%, var(--surface-muted) ${percent}% 100%)` }}
          >
            <span className="cm-ring-inner">
              <span className="cm-ring-value">{percent}%</span>
              {currentLabel && <span className="muted cm-ring-label">{currentLabel}</span>}
            </span>
          </div>
          <span className="cm-stat">
            <strong>{course.stage_count}</strong>
            <span className="muted small">modules</span>
          </span>
          <span className="cm-stat">
            <strong>{course.unit_count}</strong>
            <span className="muted small">units</span>
          </span>
          <span className="cm-stat">
            <strong className="cm-ok">{passed}</strong>
            <span className="muted small">passed their Cold Check</span>
          </span>
        </div>
      </header>

      <ModulePath stages={stages} current={current} />

      <div className="cm-body">
        <section className="stage-list cm-modules" aria-label="Modules">
          {stages.map((stage) => (
            <StageCard key={stage.stage} courseId={courseId} stage={stage} current={stage.stage === current} />
          ))}
        </section>

        <aside className="cm-side" aria-label="For you">
          {next && (
            <div className="card cm-side-card cm-next">
              <span className="eyebrow cm-eyebrow">Next for you</span>
              <span>{nextActionMessage(next)}</span>
              <Link to="/units/$unitId" params={{ unitId: next.unit_id }} className="button button-primary">
                Open {next.unit_id}
              </Link>
            </div>
          )}
          <SkillsPanel skills={progress.data?.skills ?? []} label={currentLabel} />
        </aside>
      </div>
    </main>
  );
}

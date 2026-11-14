import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useSearch } from "@tanstack/react-router";
import { useState } from "react";

import { api, type EvidenceEntry, type Schemas } from "../api/client";
import { ErrorNote, Loading, Panel } from "../components/common";
import { UnitCard } from "../components/UnitCard";
import { formatDate, formatDateTime, nextActionMessage, stepName, unitStateLabel } from "../lib/format";
import { DECISION_MEANINGS } from "../lib/meanings";

const ledgerActivity = (entry: EvidenceEntry) => {
  if (entry.review_kind === "stage_review") return "Module review";
  if (entry.review_kind === "recheck") return "Recheck";
  return entry.cold_check ? "Cold Check" : (entry.activity ?? "Concept check");
};

function DueForReview() {
  const due = useQuery({ queryKey: ["reviewsDue"], queryFn: () => api.dueReviews() });
  if (!due.data?.length) return null;
  return (
    <Panel title="Due for review" id="due-reviews">
      <ul className="plain-list">
        {due.data.map((review) => (
          <li key={review.skill_id}>
            <Link to="/reviews/$skillId/$days" params={{ skillId: review.skill_id, days: String(review.days) }}>
              {review.skill_id} {review.skill_name}
            </Link>
            <span className="muted small"> · {review.days}-day recheck</span>
          </li>
        ))}
      </ul>
    </Panel>
  );
}

function Ledger({ skills }: { skills: { skill_id: string; skill_name: string }[] }) {
  const [skillId, setSkillId] = useState("");
  const ledger = useQuery({
    queryKey: ["ledger", skillId],
    queryFn: () => api.ledger(skillId || undefined),
  });

  return (
    <details className="card panel evidence-log">
      <summary className="panel-title">Full evidence log</summary>
      <p className="muted small">Every result, newest first, with the help used. For checking, not for everyday use.</p>
      <div className="section-head">
        <label className="filter">
          <span>Filter by skill</span>
          <select value={skillId} onChange={(event) => setSkillId(event.target.value)}>
            <option value="">All skills</option>
            {skills.map((skill) => (
              <option key={skill.skill_id} value={skill.skill_id}>
                {skill.skill_id} {skill.skill_name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {ledger.isPending && <Loading what="the ledger" />}
      {ledger.isError && <ErrorNote error={ledger.error} />}
      {ledger.data?.length === 0 && <p className="muted small">No evidence yet. It appears here as you work.</p>}
      {!!ledger.data?.length && (
        <div className="table-scroll">
          <table aria-label="Evidence ledger">
            <thead>
              <tr>
                <th scope="col">When</th>
                <th scope="col">Unit</th>
                <th scope="col">Skill</th>
                <th scope="col">Activity</th>
                <th scope="col">Strength</th>
                <th scope="col">Help used</th>
              </tr>
            </thead>
            <tbody>
              {ledger.data.map((entry) => (
                <tr key={entry.entry_id}>
                  <td>{entry.recorded_at ? formatDate(entry.recorded_at) : ""}</td>
                  <td className="mono">{entry.unit_id}</td>
                  <td className="mono">{entry.skill_id}</td>
                  <td>{ledgerActivity(entry)}</td>
                  <td>{entry.evidence_strength}</td>
                  <td>{entry.assistance_level === "none" ? "None" : entry.assistance_level.replace("_", " ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </details>
  );
}

function WhereYouAre({ units }: { units: Schemas["UnitView"][] }) {
  const done = units.filter((unit) => unitStateLabel(unit.decision) === "Done for now").length;
  return (
    <section className="card panel where-you-are" aria-labelledby="where">
      <h2 id="where" className="eyebrow">
        Where you are
      </h2>
      <p className="where-summary">
        {done} of {units.length} units done for now.
        {done < units.length && " The rest need work before this module is finished."}
      </p>
      <ul className="plain-list progress-tiles">
        {units.map((unit) => (
          <li key={unit.unit_id} className={`progress-tile progress-tile-${unitStateLabel(unit.decision) === "Done for now" ? "done" : "open"}`}>
            <span className="mono">{unit.unit_id}</span>
            <span className="unit-state">{unitStateLabel(unit.decision)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function Progress() {
  const { course, stage } = useSearch({ from: "/progress" });
  const navigate = useNavigate({ from: "/progress" });
  const view = useQuery({
    queryKey: ["proficiency", "progress", course, stage],
    queryFn: () => api.proficiency({ courseId: course, stage }),
  });
  const map = useQuery({ queryKey: ["courseMap", course], queryFn: () => api.courseMap(course) });

  if (view.isPending) {
    return (
      <main className="container page">
        <Loading what="your progress" />
      </main>
    );
  }
  if (view.isError) {
    return (
      <main className="container page">
        <ErrorNote error={view.error} />
      </main>
    );
  }

  const { skills, units, next_action: next, stage: shownStage } = view.data;
  const shownLabel = map.data?.stages.find((s) => s.stage === shownStage)?.label ?? `Module ${shownStage}`;

  return (
    <main className="container page">
      <div className="section-head">
        <h1 className="page-title">My progress</h1>
        {map.data && (
          <label className="filter">
            <span>Module</span>
            <select
              value={shownStage ?? ""}
              onChange={(event) => navigate({ search: { course, stage: Number(event.target.value) } })}
            >
              {map.data.stages.map((s) => (
                <option key={s.stage} value={s.stage}>
                  {s.label}: {s.title}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      {next && (
        <section className="next-action" aria-labelledby="next">
          <h2 id="next" className="eyebrow eyebrow-light">
            Next learning action
          </h2>
          <p className="next-message">{nextActionMessage(next)}</p>
          {next.retry_at && (
            <p className="next-retry">
              Cold Check retry opens at {formatDateTime(next.retry_at)}.
              {next.activity !== "cold_check" && ` Meanwhile, try a new ${stepName(next.activity)} item.`}
            </p>
          )}
          <Link to="/units/$unitId/$step" params={{ unitId: next.unit_id, step: next.activity }} className="button button-primary">
            {stepName(next.activity)} in {next.unit_id}
          </Link>
        </section>
      )}

      <WhereYouAre units={units} />

      <section className="card panel ladder-legend" aria-label="How to read the ladders">
        <ul className="plain-list legend-list small">
          <li>
            <i className="swatch swatch-supported" /> Proven: 2 results, including a Cold Check
          </li>
          <li>
            <i className="swatch swatch-provisional" /> Seen once, not yet proven
          </li>
          <li>
            <i className="swatch swatch-target" /> This module's goal
          </li>
        </ul>
        <p className="muted small">
          A skill's level is overall, not per module: proof from another module still counts, and the note under a
          skill says where it came from.
        </p>
      </section>

      <div className="progress-layout">
        <div className="progress-main">
          <Panel title={`Units · ${shownLabel}`} id="units">
            <div className="unit-cards">
              {units.map((unit) => (
                <UnitCard
                  key={unit.unit_id}
                  unit={unit}
                  shownStage={shownStage}
                  skills={unit.skills.flatMap((target) =>
                    skills
                      .filter((skill) => skill.skill_id === target.skill_id)
                      // A skill can recur in several units: mark this unit's own goal on its ladder.
                      .map((skill) => ({ ...skill, target_level: target.goal_level })),
                  )}
                />
              ))}
            </div>
          </Panel>
          <Ledger skills={skills} />
        </div>
        <aside className="unit-aside">
          <DueForReview />
          <Panel title="What the labels mean" id="label-meanings">
            <dl className="meanings">
              {DECISION_MEANINGS.map(([label, meaning]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd className="small">{meaning}</dd>
                </div>
              ))}
            </dl>
          </Panel>
          <Panel title="How this is decided" id="how">
            <p className="small">
              Every decision comes from your evidence ledger, not from one click. A skill is supported once two
              different exercises and a passed Cold Check agree, and one weak attempt never erases what you have shown.
            </p>
          </Panel>
        </aside>
      </div>
    </main>
  );
}

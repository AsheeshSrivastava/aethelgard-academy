import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useSearch } from "@tanstack/react-router";
import { useState } from "react";

import { api } from "../api/client";
import { BackLink, DecisionChip, ErrorNote, Loading, Panel } from "../components/common";
import { SkillLadder } from "../components/SkillLadder";
import { nextActionMessage, stepName } from "../lib/format";

function Ledger({ skills }: { skills: { skill_id: string; skill_name: string }[] }) {
  const [skillId, setSkillId] = useState("");
  const ledger = useQuery({
    queryKey: ["ledger", skillId],
    queryFn: () => api.ledger(skillId || undefined),
  });

  return (
    <section className="card panel" aria-labelledby="ledger">
      <div className="section-head">
        <h2 id="ledger" className="panel-title">
          Evidence ledger
        </h2>
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
                  <td>{new Date(entry.recorded_at ?? "").toLocaleDateString()}</td>
                  <td className="mono">{entry.unit_id}</td>
                  <td className="mono">{entry.skill_id}</td>
                  <td>{entry.cold_check ? "Cold Check" : (entry.activity ?? "Concept check")}</td>
                  <td>{entry.evidence_strength}</td>
                  <td>{entry.assistance_level === "none" ? "None" : entry.assistance_level.replace("_", " ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
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

  const back = <BackLink to="/" label="Home" />;
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
        {back}
        <ErrorNote error={view.error} />
      </main>
    );
  }

  const { skills, units, next_action: next, stage: shownStage } = view.data;

  return (
    <main className="container page">
      {back}
      <div className="section-head">
        <h1 className="page-title">My progress</h1>
        {map.data && (
          <label className="filter">
            <span>Stage</span>
            <select
              value={shownStage ?? ""}
              onChange={(event) => navigate({ search: { course, stage: Number(event.target.value) } })}
            >
              {map.data.stages.map((s) => (
                <option key={s.stage} value={s.stage}>
                  {s.stage}: {s.title}
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
          <Link to="/units/$unitId/$step" params={{ unitId: next.unit_id, step: next.activity }} className="button button-primary">
            {stepName(next.activity)} in {next.unit_id}
          </Link>
        </section>
      )}

      <div className="progress-layout">
        <div className="progress-main">
          <section className="card panel" aria-labelledby="skills">
            <div className="section-head">
              <h2 id="skills" className="panel-title">
                Skills · Stage {shownStage}
              </h2>
              <span className="legend small muted">
                <span>
                  <i className="swatch swatch-supported" /> Supported
                </span>
                <span>
                  <i className="swatch swatch-provisional" /> Provisional
                </span>
                <span>
                  <i className="swatch swatch-target" /> Target
                </span>
              </span>
            </div>
            <ul className="plain-list ladder-list">
              {skills.map((skill) => (
                <SkillLadder key={skill.skill_id} skill={skill} />
              ))}
            </ul>
          </section>
          <Ledger skills={skills} />
        </div>
        <aside className="unit-aside">
          <Panel title={`Units · Stage ${shownStage}`} id="units">
            <ul className="plain-list">
              {units.map((unit) => (
                <li key={unit.unit_id}>
                  <Link to="/units/$unitId" params={{ unitId: unit.unit_id }} className="unit-decision">
                    <span className="mono">{unit.unit_id}</span>
                    <DecisionChip decision={unit.decision} />
                  </Link>
                </li>
              ))}
            </ul>
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

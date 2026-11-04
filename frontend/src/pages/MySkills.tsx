import { useQuery } from "@tanstack/react-query";

import { api, type Schemas } from "../api/client";
import { ErrorNote, Loading } from "../components/common";
import { courseName, formatDate } from "../lib/format";
import { LEVEL_MEANINGS } from "../lib/meanings";

type Skill = Schemas["SkillSummary"];

const LADDER = ["Understand", "Apply", "Adapt", "Own"];

/** Each framework skill once, by area, from all the learner's evidence (SPEC-12 section 6.1). */
export function MySkills() {
  const skills = useQuery({ queryKey: ["mySkills"], queryFn: () => api.mySkills() });

  return (
    <main className="container page">
      <div className="section-head">
        <h1 className="page-title">My skills</h1>
      </div>
      <p className="muted">
        The same 27 skills run through every course. Your level on each comes from all your evidence, in every course.
      </p>

      <section className="card panel" aria-labelledby="level-meanings">
        <h2 id="level-meanings" className="eyebrow">
          What the levels mean
        </h2>
        <dl className="meanings">
          {LEVEL_MEANINGS.map(([level, meaning]) => (
            <div key={level}>
              <dt>{level}</dt>
              <dd>{meaning}</dd>
            </div>
          ))}
        </dl>
      </section>

      {skills.isPending && <Loading what="your skills" />}
      {skills.isError && <ErrorNote error={skills.error} />}
      {skills.data?.areas.map((area) => (
        <section key={area.area_id} className="card panel" aria-labelledby={`area-${area.area_id}`}>
          <h2 id={`area-${area.area_id}`} className="panel-title">
            {area.name}
          </h2>
          <p className="small muted">The learner {area.owns}.</p>
          <ul className="plain-list skill-entries">
            {area.skills.map((skill) => (
              <SkillRow key={skill.skill_id} skill={skill} />
            ))}
          </ul>
        </section>
      ))}
    </main>
  );
}

function SkillRow({ skill }: { skill: Skill }) {
  const started = skill.level != null;
  const reached = started ? LADDER.indexOf(skill.level as string) : -1;
  const courses = Object.entries(skill.targeted_in)
    .map(([course, count]) => `${courseName(course)} ${count}`)
    .join(" · ");

  return (
    <li className={started ? "skill-entry" : "skill-entry skill-not-started"} aria-label={`${skill.skill_id} ${skill.skill_name}`}>
      <div className="skill-entry-head">
        <span className="mono">{skill.skill_id}</span>
        <span className="skill-name">{skill.skill_name}</span>
        <span className="skill-level">{started ? skill.level : "Not started"}</span>
      </div>
      <ol className="ladder" aria-label="Level ladder">
        {LADDER.map((level, index) => (
          <li key={level} className={index > reached ? "rung" : skill.confidence === "supported" ? "rung rung-supported" : "rung rung-provisional"}>
            {level}
          </li>
        ))}
      </ol>
      <p className="small muted">
        {started
          ? `Practised in ${skill.practised_in.join(", ")} · ${skill.evidence} pieces of evidence · last ${formatDate(skill.last_seen!)}`
          : "No evidence yet."}
      </p>
      {courses && <p className="small muted">Comes up in: {courses}</p>}
    </li>
  );
}

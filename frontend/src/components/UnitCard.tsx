import { Link } from "@tanstack/react-router";

import type { Schemas } from "../api/client";
import { proofNote, resetNote, unitStateLabel } from "../lib/format";
import { SkillLadder } from "./SkillLadder";

type Unit = Schemas["UnitView"];
type Skill = Schemas["SkillView"];

/** One unit on My progress: its state in plain words, the reset note, and its skills' ladders. */
export function UnitCard({ unit, skills, shownStage }: { unit: Unit; skills: Skill[]; shownStage?: number | null }) {
  const titleId = `unit-${unit.unit_id}`;
  const needsWork = unitStateLabel(unit.decision) === "Needs work";
  return (
    <article className={`unit-card${needsWork ? " unit-card-attention" : ""}`} aria-labelledby={titleId}>
      <header className="unit-card-head">
        <Link to="/units/$unitId" params={{ unitId: unit.unit_id }} className="unit-decision" id={titleId}>
          <span className="mono">{unit.unit_id}</span>
          <span className="unit-state">{unitStateLabel(unit.decision)}</span>
        </Link>
        <p className="unit-card-title">{unit.title}</p>
      </header>
      {unit.reset_at && (
        <p className="small muted">{resetNote(unit.reset_at, unit.activities_done, unit.activities_total)}</p>
      )}
      <ul className="plain-list ladder-list">
        {skills.map((skill) => (
          <SkillLadder key={skill.skill_id} skill={skill} note={proofNote(skill.proof_stages, shownStage)} />
        ))}
      </ul>
    </article>
  );
}

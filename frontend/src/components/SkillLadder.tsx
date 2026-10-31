import type { Schemas } from "../api/client";
import { DecisionChip } from "./common";
import { LEVELS, skillReason } from "../lib/format";

type Skill = Schemas["SkillView"];

function ladderLabel(skill: Skill): string {
  const start = `${skill.skill_id}: target ${skill.target_level}`;
  if (!skill.current_level) return `${start}, not yet established`;
  return `${start}, current ${skill.current_level}, ${skill.confidence}`;
}

export function SkillLadder({ skill }: { skill: Skill }) {
  const current = skill.current_level ? LEVELS.indexOf(skill.current_level) : -1;
  const target = LEVELS.indexOf(skill.target_level);
  const counts = skill.evidence_counts;

  return (
    <li className="ladder-row">
      <div className="ladder-head">
        <span>
          <span className="mono">{skill.skill_id}</span> {skill.skill_name}
        </span>
        <DecisionChip decision={skill.decision} />
      </div>
      <div role="img" aria-label={ladderLabel(skill)} className="ladder">
        {LEVELS.map((level, index) => (
          <span
            key={level}
            className={[
              "rung",
              index <= current ? `rung-${skill.confidence}` : "",
              index === target ? "rung-target" : "",
            ].join(" ")}
          >
            {level}
          </span>
        ))}
      </div>
      <p className="ladder-reason">{skillReason(skill.decision, skill.reason)}</p>
      <p className="ladder-counts">
        Evidence: {counts.explain} explain, {counts.perform} perform, {counts.diagnose} diagnose
      </p>
    </li>
  );
}

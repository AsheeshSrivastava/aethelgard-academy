import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Schemas } from "../api/client";
import { SkillLadder } from "./SkillLadder";

// SPEC-12 section 6 (2026-11-14): each rung is coloured by its own support.
const provenApplySeenAdapt: Schemas["SkillView"] = {
  skill_id: "CO-1",
  skill_name: "Predict before running",
  target_level: "Understand",
  current_level: "Adapt",
  confidence: "provisional",
  supported_levels: ["Understand", "Apply"],
  evidence_counts: { explain: 0, perform: 2, diagnose: 1 },
  decision: "Progress",
  reason: "Sufficient evidence for Understand: supported by 3 entries including a Cold Check.",
  entry_ids: ["e1"],
};

describe("SkillLadder", () => {
  it("keeps proven rungs supported under a provisional top rung", () => {
    render(
      <ul>
        <SkillLadder skill={provenApplySeenAdapt} />
      </ul>,
    );

    expect(screen.getByText("Understand")).toHaveClass("rung-supported");
    expect(screen.getByText("Apply")).toHaveClass("rung-supported");
    expect(screen.getByText("Adapt")).toHaveClass("rung-provisional");
    expect(screen.getByText("Own")).not.toHaveClass("rung-supported", "rung-provisional");
  });
});

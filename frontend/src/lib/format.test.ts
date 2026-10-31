import { describe, expect, it } from "vitest";

import {
  buildLockMessage,
  coldCheckMessage,
  countdown,
  courseOfUnit,
  decisionLabel,
  nextActionMessage,
  skillReason,
  stepName,
} from "./format";

const NOW = new Date("2026-06-01T09:00:00Z");

describe("countdown", () => {
  it("shows hours and minutes", () => {
    expect(countdown("2026-06-01T12:30:00Z", NOW)).toBe("3 h 30 min");
  });

  it("shows minutes alone under an hour", () => {
    expect(countdown("2026-06-01T09:45:00Z", NOW)).toBe("45 min");
  });

  it("never shows less than a minute while waiting", () => {
    expect(countdown("2026-06-01T09:00:20Z", NOW)).toBe("1 min");
  });

  it("is empty once the time has passed", () => {
    expect(countdown("2026-06-01T08:00:00Z", NOW)).toBe("");
  });
});

describe("coldCheckMessage", () => {
  const status = (state: string, available_at: string | null = null) =>
    ({ state, available_at, last_attempt_at: null }) as Parameters<typeof coldCheckMessage>[0];

  it("explains how to start the clock", () => {
    expect(coldCheckMessage(status("not_ready"), NOW)).toMatch(/finish/i);
  });

  it("counts down while waiting", () => {
    expect(coldCheckMessage(status("waiting", "2026-06-01T10:00:00Z"), NOW)).toContain("1 h");
  });

  it("counts down after a fail", () => {
    expect(coldCheckMessage(status("failed_waiting", "2026-06-01T10:00:00Z"), NOW)).toMatch(/try again.*1 h/i);
  });

  it("says when it is open", () => {
    expect(coldCheckMessage(status("available"), NOW)).toMatch(/ready/i);
  });

  it("says when it is passed", () => {
    expect(coldCheckMessage(status("passed"), NOW)).toMatch(/passed/i);
  });
});

describe("learner-facing wording", () => {
  it("reads naturally for one pending unit and for several", () => {
    expect(buildLockMessage(["PY-0.1"])).toBe("Locked until PY-0.1 passes its Cold Check");
    expect(buildLockMessage(["PY-0.4", "PY-0.1"])).toBe("Locked until PY-0.4 and PY-0.1 pass their Cold Checks");
    expect(buildLockMessage(["A", "B", "C"])).toBe("Locked until 3 units pass their Cold Checks");
  });

  it("never shows system wording for a skill with no evidence", () => {
    expect(skillReason("Undecided", "Insufficient evidence: collect the smallest next probe.")).toBe(
      "Nothing recorded yet.",
    );
    expect(skillReason("Strengthen", "Evidence shows Understand.")).toBe("Evidence shows Understand.");
  });

  it("gives a plain first step instead of system wording", () => {
    const action = { unit_id: "PY-0.4", skill_id: "CO-1", activity: "explain", decision: "Undecided" as const, message: "Insufficient evidence." };

    expect(nextActionMessage(action)).toBe("Start with Explain in PY-0.4.");
    expect(nextActionMessage({ ...action, decision: "Strengthen", message: "Apply is provisional." })).toBe("Apply is provisional.");
  });
});

describe("labels", () => {
  it("does not call a fresh start undecided", () => {
    expect(decisionLabel("Undecided")).toBe("Not started");
    expect(decisionLabel("Progress")).toBe("Progress");
  });

  it("finds a unit's course from its id", () => {
    expect(courseOfUnit("PY-0.1")).toBe("python");
    expect(courseOfUnit("BE-1.1")).toBe("backend");
    expect(courseOfUnit("AI-0.1")).toBe("ai-engineering");
  });

  it("names steps for people", () => {
    expect(stepName("debug-validate")).toBe("Debug & Validate");
    expect(stepName("cold_check")).toBe("Cold Check");
  });
});

import { describe, expect, it } from "vitest";

import {
  buildLockMessage,
  coldCheckMessage,
  countdown,
  courseOfUnit,
  decisionLabel,
  formatDate,
  formatDateTime,
  formatTime,
  maturityLabel,
  nextActionMessage,
  skillReason,
  stepName,
} from "./format";
import { newInteractionId } from "./interaction";

const NOW = new Date("2026-06-01T09:00:00Z");

describe("buildLockMessage with a stage review", () => {
  it("names the review when every unit has passed", () => {
    expect(buildLockMessage([])).toBe("Locked until you pass the stage review");
  });
});

describe("maturityLabel on the P0 to P4 ladder (ADR-0018)", () => {
  it.each([
    ["P0", "P0 · Make step"],
    ["P1", "P1 · Stage build"],
    ["P2", "P2 · Course project"],
    ["P3", "P3 · Course project"],
    ["P4", "P4 · Capstone"],
  ])("labels %s as %s", (maturity, label) => {
    expect(maturityLabel(maturity)).toBe(label);
  });

  it("shows an unknown level as it is", () => {
    expect(maturityLabel("P9")).toBe("P9");
  });
});

describe("courseOfUnit with slotted units", () => {
  it.each([
    ["DSA-0.1", "python"],
    ["GIT-2.1", "python"],
    ["SD-1.4", "python"],
    ["AAE-0.7", "python"],
    ["NET-0.1", "backend"],
    ["DB-1.6", "backend"],
    ["BE-2.1", "backend"],
  ])("%s belongs to %s", (unitId, course) => {
    expect(courseOfUnit(unitId)).toBe(course);
  });
});

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

describe("dates (SPEC-12 section 6)", () => {
  it("shows a day, a short month and a year", () => {
    expect(formatDate("2026-11-04T12:00:00Z")).toBe("4 Nov 2026");
  });

  it("shows a time with am or pm", () => {
    expect(formatTime("2026-11-04T12:00:00Z")).toMatch(/^\d{1,2}:\d{2} (am|pm)$/);
  });

  it("joins them for a retry time", () => {
    expect(formatDateTime("2026-11-04T12:00:00Z")).toMatch(/^\d{1,2} Nov 2026, \d{1,2}:\d{2} (am|pm)$/);
  });
});

describe("newInteractionId", () => {
  it("makes a ULID the server accepts", () => {
    const id = newInteractionId();
    expect(id).toMatch(/^[0-9A-HJKMNP-TV-Z]{26}$/);
    expect(id).toMatch(/^[A-Za-z0-9_-]{8,64}$/);
  });

  it("never repeats and sorts by time", () => {
    const ids = Array.from({ length: 50 }, () => newInteractionId());
    expect(new Set(ids).size).toBe(50);
    expect(newInteractionId(Date.UTC(2026, 0, 1)) < newInteractionId(Date.UTC(2027, 0, 1))).toBe(true);
  });
});

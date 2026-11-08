import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { courseMap, ledger, proficiency } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";

const ME = "/api/v1/learners/me";

const skills = {
  areas: [
    {
      area_id: "CO",
      name: "Comprehend",
      owns: "owns the mental model",
      skills: [
        {
          skill_id: "CO-1",
          skill_name: "Predict before running",
          level: "Apply",
          confidence: "supported",
          evidence: 5,
          last_seen: "2026-11-04T09:00:00Z",
          practised_in: ["PY-0.1", "PY-0.4"],
          targeted_in: { python: 12, backend: 10, "ai-engineering": 9 },
        },
        {
          skill_id: "CO-3",
          skill_name: "Read unfamiliar code",
          level: null,
          confidence: null,
          evidence: 0,
          last_seen: null,
          practised_in: [],
          targeted_in: { python: 8 },
        },
      ],
    },
    { area_id: "VE", name: "Verify", owns: "owns the verification", skills: [] },
  ],
};

describe("My skills (SPEC-12 section 6.1)", () => {
  it("is a tab next to My progress", async () => {
    stubApi({ [`GET ${ME}/skills`]: skills });
    renderAt("/skills");

    expect(await screen.findByRole("link", { name: "My skills" })).toHaveAttribute("aria-current", "page");
    expect(await screen.findByRole("heading", { level: 1, name: "My skills" })).toBeInTheDocument();
  });

  it("explains the four levels at the top", async () => {
    stubApi({ [`GET ${ME}/skills`]: skills });
    renderAt("/skills");

    const levels = await screen.findByRole("region", { name: "What the levels mean" });
    for (const level of ["Understand", "Apply", "Adapt", "Own"]) expect(within(levels).getByText(level)).toBeInTheDocument();
  });

  it("groups skills by area, not by course or stage", async () => {
    stubApi({ [`GET ${ME}/skills`]: skills });
    renderAt("/skills");

    const area = await screen.findByRole("region", { name: "Comprehend" });
    expect(within(area).getByText(/owns the mental model/)).toBeInTheDocument();
    expect(within(area).getByText("Predict before running")).toBeInTheDocument();
    expect(screen.queryByText(/Module 0/)).not.toBeInTheDocument();
  });

  it("shows the level, where it was practised and where it comes up", async () => {
    stubApi({ [`GET ${ME}/skills`]: skills });
    renderAt("/skills");

    const row = await screen.findByRole("listitem", { name: /CO-1/ });
    expect(within(row).getByText("Apply", { selector: ".skill-level" })).toBeInTheDocument();
    expect(within(row).getByText(/Practised in PY-0\.1, PY-0\.4/)).toBeInTheDocument();
    expect(within(row).getByText("Comes up in: Python 12 · Python for Backend/AI 10 · AI Engineering 9")).toBeInTheDocument();
  });

  it("greys out a skill not started", async () => {
    stubApi({ [`GET ${ME}/skills`]: skills });
    renderAt("/skills");

    const row = await screen.findByRole("listitem", { name: /CO-3/ });
    expect(row).toHaveClass("skill-not-started");
    expect(within(row).getByText("Not started")).toBeInTheDocument();
  });
});

describe("My progress explains its labels", () => {
  it("says what Progress, Accelerate, Strengthen, Rebuild and Undecided mean", async () => {
    stubApi({
      [`GET ${ME}/proficiency`]: proficiency,
      "GET /api/v1/courses/python": courseMap,
      [`GET ${ME}/ledger`]: ledger,
      [`GET ${ME}/reviews/due`]: [],
    });
    renderAt("/progress");

    const meanings = await screen.findByRole("region", { name: "What the labels mean" });
    for (const label of ["Progress", "Accelerate", "Strengthen", "Rebuild", "Undecided"]) {
      expect(within(meanings).getByText(label)).toBeInTheDocument();
    }
  });
});

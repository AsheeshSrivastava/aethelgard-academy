import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { courseMap, courses, ledger, proficiency, unit } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";

vi.mock("../lesson/CodeEditor", () => ({ CodeEditor: () => <textarea aria-label="code" /> }));
vi.mock("../lesson/RunTerminal", () => ({ RunTerminal: () => <div>Terminal</div> }));

/**
 * ADR-0027: learners read "Module"; code, routes and data keep "stage".
 * This guard renders each learner page and fails if "stage" shows up in text
 * or in the attributes a screen reader or tooltip reads out.
 */
const STAGE_WORD = /\bstages?\b/i;

function learnerWording(): string {
  const attributes = Array.from(document.body.querySelectorAll("[aria-label],[title],[alt],[placeholder]")).flatMap((el) =>
    ["aria-label", "title", "alt", "placeholder"].map((name) => el.getAttribute(name) ?? ""),
  );
  return [document.body.textContent ?? "", ...attributes].join("\n");
}

function expectNoStageWord() {
  const found = learnerWording().split("\n").filter((line) => STAGE_WORD.test(line));
  expect(found).toEqual([]);
}

const ME = "/api/v1/learners/me";
const REVIEW = `${ME}/courses/python/stages/0/review`;
const reviewBase = { available_at: null, last_attempt_at: null, pending_units: [], failed_units: [], items_total: 2, items_done: 0 };
const reviewItem = {
  exercise_id: "PY-0.1/cold-predict-1/v1",
  unit_id: "PY-0.1",
  activity: "predict",
  origin: "authored",
  variant_no: 1,
  item_type: "predict",
  prompt_markdown: "Question 1",
  predict: { code: ["print(1)"], options: [{ key: "A", text: "First" }, { key: "B", text: "Second" }] },
};

const build = {
  exercise_id: "python/stage-0/build",
  course_id: "python",
  stage: 0,
  stage_label: "Module 0",
  title: "Pantry intake check-in script",
  kind: "script",
  maturity: "P1",
  status: "draft",
  brief_markdown: "Write one script for the desk.",
  sample_run: ["Name: meera"],
  entry: "checkin.py",
  files: [{ path: "checkin.py", starter: ["# Starter"] }],
  requirements: [{ id: "plan", label: "Plan written as comments", unit_id: "PY-0.1" }],
  proves: [{ skill_id: "CO-1", unit_id: "PY-0.4", label: "Run a script" }],
  submitted: false,
};

const lessonRoutes = {
  "GET /api/v1/units/PY-0.1": unit,
  [`GET ${ME}/units/PY-0.1/cold-check`]: { state: "not_ready", available_at: null, last_attempt_at: null },
  [`GET ${ME}/units/PY-0.1/state`]: { step: "video", done_steps: [] },
  "GET /api/v1/courses/python": courseMap,
};

describe("learner pages say Module, never Stage (ADR-0027)", () => {
  it("front page", async () => {
    stubApi({ "GET /api/v1/courses": courses, [`GET ${ME}/proficiency`]: proficiency });
    renderAt("/");
    await screen.findAllByText(/modules · \d+ units/);
    expectNoStageWord();
  });

  it("courses list", async () => {
    stubApi({ "GET /api/v1/courses": courses });
    renderAt("/courses");
    await screen.findAllByText(/modules · \d+ units/);
    expectNoStageWord();
  });

  it("course map", async () => {
    stubApi({ "GET /api/v1/courses/python": courseMap, [`GET ${ME}/proficiency`]: proficiency });
    renderAt("/courses/python");
    await screen.findByText("Module 0");
    expectNoStageWord();
  });

  it("unit map", async () => {
    stubApi(lessonRoutes);
    renderAt("/units/PY-0.1");
    await screen.findByText(/Module 0/);
    expectNoStageWord();
  });

  it("lesson", async () => {
    stubApi(lessonRoutes);
    renderAt("/units/PY-0.1/video");
    await screen.findByRole("heading", { level: 1 });
    expectNoStageWord();
  });

  it("build page", async () => {
    const api = "/api/v1/courses/python/stages/0/build";
    stubApi({ [`GET ${api}`]: build, [`GET ${ME}/drafts/python/stage-0/build`]: { files: {} }, [`PUT ${ME}/drafts/python/stage-0/build`]: null });
    renderAt("/courses/python/stages/0/build");
    await screen.findByText("Module 0 build");
    expectNoStageWord();
  });

  it.each([
    ["available", () => screen.findByText("Question 1")],
    ["passed", () => screen.findByRole("button", { name: /restart/i })],
    ["failed_waiting", () => screen.findByRole("button", { name: /restart/i })],
    ["unavailable", () => screen.findByText(/no review yet/i)],
  ])("module review page (%s)", async (state, ready) => {
    stubApi({
      [`GET ${REVIEW}`]: { ...reviewBase, state },
      [`GET ${REVIEW}/exercise`]: reviewItem,
      "GET /api/v1/courses/python": courseMap,
    });
    renderAt("/courses/python/stages/0/review");
    await ready();
    await screen.findByRole("heading", { level: 1, name: "Module 0 review" });
    expectNoStageWord();
  });

  it("my progress", async () => {
    stubApi({ [`GET ${ME}/proficiency`]: proficiency, [`GET ${ME}/ledger`]: ledger, "GET /api/v1/courses/python": courseMap });
    renderAt("/progress");
    await screen.findByText("Module");
    expectNoStageWord();
  });
});

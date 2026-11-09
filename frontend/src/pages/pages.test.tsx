import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { renderAt, stubApi } from "../test/harness";
import { courseMap, courses, ledger, proficiency, unit } from "../test/fixtures";

const notReady = { state: "not_ready", available_at: null, last_attempt_at: null };

function homeRoutes() {
  return {
    "GET /api/v1/courses": courses,
    "GET /api/v1/learners/me/proficiency": proficiency,
  };
}

function unitRoutes(cold: object = notReady) {
  return {
    "GET /api/v1/units/PY-0.1": unit,
    "GET /api/v1/learners/me/units/PY-0.1/cold-check": cold,
    "GET /api/v1/learners/me/units/PY-0.1/state": { step: "predict", done_steps: ["video", "explain"] },
  };
}

function progressRoutes() {
  return {
    "GET /api/v1/learners/me/proficiency": proficiency,
    "GET /api/v1/learners/me/ledger": ledger,
    "GET /api/v1/courses/python": courseMap,
  };
}

describe("top bar", () => {
  it("has the wordmark, Courses and My progress", async () => {
    stubApi(homeRoutes());
    renderAt("/");

    const nav = await screen.findByRole("navigation", { name: "Primary" });
    expect(within(nav).getByRole("link", { name: "Courses" })).toHaveAttribute("href", "/courses");
    expect(within(nav).getByRole("link", { name: "My progress" })).toHaveAttribute("href", "/progress");
    expect(screen.getByRole("link", { name: /aethelgard/i })).toHaveAttribute("href", "/");
  });
});

describe("front page", () => {
  it("shows the hero, the lesson path, the AXIS modes and live course cards", async () => {
    stubApi(homeRoutes());
    renderAt("/");

    expect(await screen.findByRole("heading", { level: 1, name: /learn to build/i })).toBeInTheDocument();
    for (const step of ["Video", "Explain", "Activities", "Cold Check"]) {
      expect(screen.getByRole("heading", { name: step })).toBeInTheDocument();
    }
    for (const mode of ["Coach", "Hybrid", "Socratic"]) {
      expect(screen.getByRole("heading", { name: mode })).toBeInTheDocument();
    }
    expect(await screen.findByText("18 modules · 81 units")).toBeInTheDocument();
  });

  it("has no back arrow", async () => {
    stubApi(homeRoutes());
    renderAt("/");

    await screen.findByRole("heading", { level: 1 });
    expect(screen.queryByRole("link", { name: /^back/i })).not.toBeInTheDocument();
  });

  it("offers to continue from the next action", async () => {
    stubApi(homeRoutes());
    renderAt("/");

    expect(await screen.findByRole("link", { name: "Continue PY-0.1" })).toHaveAttribute("href", "/units/PY-0.1");
  });
});

describe("courses page", () => {
  it("lists the three courses with counts and a back arrow", async () => {
    stubApi(homeRoutes());
    renderAt("/courses");

    expect(await screen.findByRole("link", { name: /Python for Backend\/AI/ })).toHaveAttribute("href", "/courses/backend");
    expect(screen.getByText("22 modules · 111 units")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Home" })).toHaveAttribute("href", "/");
  });
});

describe("course map", () => {
  function routes() {
    return { "GET /api/v1/courses/python": courseMap, "GET /api/v1/learners/me/proficiency": proficiency };
  }

  it("shows stages with their approved titles", async () => {
    stubApi(routes());
    renderAt("/courses/python");

    expect(await screen.findByRole("heading", { name: "Running your first program" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Values, text and collections" })).toBeInTheDocument();
  });

  it("links units and shows their decision and targets", async () => {
    stubApi(routes());
    renderAt("/courses/python");

    const link = await screen.findByRole("link", { name: /PY-1\.2/ });
    expect(link).toHaveAttribute("href", "/units/PY-1.2");
    expect(within(link).getByText("Strengthen")).toBeInTheDocument();
    expect(within(link).getByText("VE-6 Apply")).toBeInTheDocument();
  });

  it("shows a build locked with what is pending, and an open one", async () => {
    stubApi(routes());
    renderAt("/courses/python");

    expect(await screen.findByText(/Locked until PY-0\.1 passes its Cold Check/)).toBeInTheDocument();
    expect(screen.getByText("Not written yet")).toBeInTheDocument();
  });

  it("shows no build tile for a stage that has no build by design", async () => {
    const [first] = courseMap.stages;
    stubApi({
      "GET /api/v1/courses/python": { ...courseMap, stages: [{ ...first!, stage: 700, label: "TW 0", title: "Writing basics", build: null }] },
      "GET /api/v1/learners/me/proficiency": proficiency,
    });
    renderAt("/courses/python");

    expect(await screen.findByRole("heading", { name: "Writing basics" })).toBeInTheDocument();
    expect(screen.queryByText(/Locked until/)).not.toBeInTheDocument();
    expect(screen.queryByText("Not written yet")).not.toBeInTheDocument();
    expect(screen.queryByText(/Script|Mini-project/)).not.toBeInTheDocument();
  });

  it("goes back to the courses page", async () => {
    stubApi(routes());
    renderAt("/courses/python");

    expect(await screen.findByRole("link", { name: "Back to Courses" })).toHaveAttribute("href", "/courses");
  });

  it("shows a clear message when the course does not exist", async () => {
    stubApi({});
    renderAt("/courses/cooking");

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});

describe("unit map", () => {
  it("shows the concept, the path and the skills", async () => {
    stubApi(unitRoutes());
    renderAt("/units/PY-0.1");

    expect(await screen.findByRole("heading", { level: 1, name: unit.title })).toBeInTheDocument();
    expect(screen.getByText(unit.concept_line)).toBeInTheDocument();
    const path = screen.getByRole("list", { name: "Lesson path" });
    for (const step of ["Video", "Explain", "Predict", "Trace", "Playground", "Cold Check"]) {
      expect(within(path).getByText(step)).toBeInTheDocument();
    }
    expect(screen.getByText("Predict before running")).toBeInTheDocument();
  });

  it("marks finished steps and the current step", async () => {
    stubApi(unitRoutes());
    renderAt("/units/PY-0.1");

    const path = await screen.findByRole("list", { name: "Lesson path" });
    expect(within(path).getAllByText("Done")).toHaveLength(2);
    expect(within(path).getByText("In progress")).toBeInTheDocument();
  });

  it("goes back to its course map", async () => {
    stubApi(unitRoutes());
    renderAt("/units/PY-0.1");

    expect(await screen.findByRole("link", { name: "Back to Python course map" })).toHaveAttribute("href", "/courses/python");
  });

  it("returns to the build that sent the learner here (SPEC-15 section 9.5)", async () => {
    stubApi(unitRoutes());
    renderAt("/units/PY-0.1?back=%2Fcourses%2Fpython%2Fstages%2F0%2Fbuild");

    const link = await screen.findByRole("link", { name: "Back to your build" });
    expect(link).toHaveAttribute("href", "/courses/python/stages/0/build");
  });

  it.each([
    ["another page of this app", "%2Fprogress"],
    ["a build path with extra text", "%2Fcourses%2Fpython%2Fstages%2F0%2Fbuild%2Fx"],
    ["a build path with a bad stage", "%2Fcourses%2Fpython%2Fstages%2Fx%2Fbuild"],
    ["another site", "https%3A%2F%2Fevil.example%2Fcourses%2Fpython%2Fstages%2F0%2Fbuild"],
    ["a protocol-relative address", "%2F%2Fevil.example%2Fcourses%2Fpython%2Fstages%2F0%2Fbuild"],
  ])("ignores a back value that is %s", async (_label, back) => {
    stubApi(unitRoutes());
    renderAt(`/units/PY-0.1?back=${back}`);

    expect(await screen.findByRole("link", { name: "Back to Python course map" })).toHaveAttribute("href", "/courses/python");
    expect(screen.queryByRole("link", { name: "Back to your build" })).not.toBeInTheDocument();
  });

  it("shows a Cold Check countdown", async () => {
    const soon = new Date(Date.now() + 3 * 3600_000).toISOString();
    stubApi(unitRoutes({ state: "waiting", available_at: soon, last_attempt_at: null }));
    renderAt("/units/PY-0.1");

    expect(await screen.findByText(/Opens in 2 h 59 min|Opens in 3 h/)).toBeInTheDocument();
  });

  it("asks before resetting and says the ledger is kept", async () => {
    const calls = stubApi({ ...unitRoutes(), "POST /api/v1/learners/me/units/PY-0.1/reset": null });
    const user = userEvent.setup();
    renderAt("/units/PY-0.1");

    await user.click(await screen.findByRole("button", { name: "Reset unit" }));

    expect(screen.getByRole("group", { name: "Confirm reset" })).toHaveTextContent(/evidence ledger is kept/i);
    expect(calls.some((c) => c.method === "POST")).toBe(false);

    await user.click(screen.getByRole("button", { name: "Yes, reset" }));

    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    await waitFor(() => expect(screen.getByRole("button", { name: "Reset unit" })).toBeInTheDocument());
  });

  it("can cancel a reset", async () => {
    const calls = stubApi({ ...unitRoutes(), "POST /api/v1/learners/me/units/PY-0.1/reset": null });
    const user = userEvent.setup();
    renderAt("/units/PY-0.1");

    await user.click(await screen.findByRole("button", { name: "Reset unit" }));
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(calls.some((c) => c.method === "POST")).toBe(false);
    expect(screen.getByRole("button", { name: "Reset unit" })).toBeInTheDocument();
  });
});

describe("my progress", () => {
  it("opens on the current stage and shows the next action", async () => {
    const calls = stubApi(progressRoutes());
    renderAt("/progress");

    const next = await screen.findByRole("region", { name: /next learning action/i });
    expect(within(next).getByText(proficiency.next_action!.message)).toBeInTheDocument();
    expect(within(next).getByRole("link", { name: /PY-0\.1/ })).toHaveAttribute("href", "/units/PY-0.1/debug-validate");
    expect(await screen.findByRole("heading", { name: /Skills · Module 0/ })).toBeInTheDocument();
    expect(calls.find((c) => c.url.includes("/proficiency"))!.url).not.toContain("stage=");
  });

  it("draws each skill's ladder with target, current and confidence", async () => {
    stubApi(progressRoutes());
    renderAt("/progress");

    expect(await screen.findByRole("img", { name: "CO-1: target Apply, current Understand, provisional" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "CO-2: target Understand, current Understand, supported" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "DE-2: target Understand, not yet established" })).toBeInTheDocument();
  });

  it("lists unit decisions", async () => {
    stubApi(progressRoutes());
    renderAt("/progress");

    const units = await screen.findByRole("region", { name: /Units · Module 0/ });
    expect(within(units).getByRole("link", { name: /PY-0\.4/ })).toHaveTextContent("Progress");
  });

  it("shows the ledger and filters it by skill on the server", async () => {
    const calls = stubApi(progressRoutes());
    const user = userEvent.setup();
    renderAt("/progress");

    const table = await screen.findByRole("table", { name: "Evidence ledger" });
    expect(within(table).getAllByRole("row")).toHaveLength(3);
    expect(within(table).getByText("Cold Check")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Filter by skill"), "CO-1");

    await waitFor(() => expect(calls.some((c) => c.url.includes("skill_id=CO-1"))).toBe(true));
  });

  it("explains how this is decided", async () => {
    stubApi(progressRoutes());
    renderAt("/progress");

    const how = await screen.findByRole("region", { name: "How this is decided" });
    expect(how).toHaveTextContent(/Cold Check/);
  });

  it("can move to another stage", async () => {
    const calls = stubApi(progressRoutes());
    const user = userEvent.setup();
    renderAt("/progress");

    await screen.findByRole("heading", { name: /Skills · Module 0/ });
    await user.selectOptions(await screen.findByLabelText("Module"), "1");

    await waitFor(() => expect(calls.some((c) => c.url.includes("stage=1"))).toBe(true));
  });

  it("says so when a stage has nothing to show", async () => {
    stubApi({ ...progressRoutes(), "GET /api/v1/learners/me/ledger": [] });
    renderAt("/progress");

    expect(await screen.findByText(/no evidence yet/i)).toBeInTheDocument();
  });
});

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { courseMap, proficiency } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";

vi.mock("../lesson/CodeEditor", () => ({ CodeEditor: () => <textarea aria-label="code" /> }));
vi.mock("../lesson/RunTerminal", () => ({ RunTerminal: () => <div>Terminal</div> }));

const ME = "/api/v1/learners/me";
const REVIEW = `${ME}/courses/python/stages/0/review`;
const PAGE = "/courses/python/stages/0/review";

const base = { available_at: null, last_attempt_at: null, pending_units: [], failed_units: [], items_total: 2, items_done: 0 };

const item = (n = 1) => ({
  exercise_id: `PY-0.1/cold-predict-${n}/v1`,
  unit_id: "PY-0.1",
  activity: "predict",
  origin: "authored",
  variant_no: 1,
  item_type: "predict",
  prompt_markdown: `Question ${n}`,
  predict: { code: ["print(1)"], options: [{ key: "A", text: "First" }, { key: "B", text: "Second" }] },
});

const answered = { outcome: "passed", feedback: "Correct.", evidence_entry_id: "e1", unit_decision: "Progress" };

const routes = (status: object, extra: Record<string, unknown> = {}) => ({
  [`GET ${REVIEW}`]: { ...base, ...status },
  [`GET ${REVIEW}/exercise`]: item(),
  "GET /api/v1/courses/python": courseMap,
  ...extra,
});

function withReview(build: object) {
  const [first, ...others] = courseMap.stages;
  return { ...courseMap, stages: [{ ...first, build: { ...first!.build, ...build } }, ...others] };
}

describe("stage review page", () => {
  it("shows one item, a count, and no AXIS", async () => {
    stubApi(routes({ state: "available" }));
    renderAt(PAGE);

    expect(await screen.findByText("Question 1")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Stage 0 review" })).toBeInTheDocument();
    expect(screen.getByText("Item 1 of 2")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(/AXIS is off/);
    expect(screen.queryByRole("complementary", { name: /AXIS/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Regenerate" })).not.toBeInTheDocument();
  });

  it("sends the answer as a stage review and moves on, showing no answer", async () => {
    let done = 0;
    const calls = stubApi(
      routes({}, {
        [`GET ${REVIEW}`]: () => ({ ...base, state: "available", items_done: done }),
        [`GET ${REVIEW}/exercise`]: () => item(done + 1),
        [`POST ${ME}/attempts`]: () => {
          done += 1;
          return { ...answered, reveal: { correct: "A", why: ["Secret reason"] } };
        },
      }),
    );
    renderAt(PAGE);

    await userEvent.click(await screen.findByRole("radio", { name: /First/ }));
    await userEvent.click(screen.getByRole("button", { name: "Submit, one try" }));

    expect(await screen.findByText("Question 2")).toBeInTheDocument();
    expect(await screen.findByText("Item 2 of 2")).toBeInTheDocument();
    expect(screen.queryByText("Secret reason")).not.toBeInTheDocument();
    const posted = calls.find((c) => c.method === "POST");
    expect(JSON.parse(posted?.body ?? "{}")).toEqual({ exercise_id: "PY-0.1/cold-predict-1/v1", activity: "stage_review", choice: "A", interaction_id: expect.stringMatching(/^[0-9A-HJKMNP-TV-Z]{26}$/) });
  });

  it("names the units on a fail, with the wait and no item", async () => {
    const later = new Date(Date.now() + 3 * 3_600_000).toISOString();
    const calls = stubApi(routes({ state: "failed_waiting", available_at: later, failed_units: ["PY-0.1", "PY-0.4"], items_done: 2 }));
    renderAt(PAGE);

    expect(await screen.findByText(/Try again in 2 h|Try again in 3 h/)).toBeInTheDocument();
    const list = screen.getByRole("list", { name: "Units to strengthen" });
    expect(within(list).getByRole("link", { name: "PY-0.1" })).toHaveAttribute("href", "/units/PY-0.1");
    expect(within(list).getByRole("link", { name: "PY-0.4" })).toBeInTheDocument();
    expect(calls.some((c) => c.url.endsWith("/review/exercise"))).toBe(false);
  });

  it("lists what is left before the review opens", async () => {
    stubApi(routes({ state: "not_ready", pending_units: ["PY-0.3"] }));
    renderAt(PAGE);

    expect(await screen.findByText(/Pass every unit's Cold Check first/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "PY-0.3" })).toBeInTheDocument();
  });

  it("says when a stage has no review", async () => {
    stubApi(routes({ state: "unavailable" }));
    renderAt(PAGE);

    expect(await screen.findByText(/no review yet/i)).toBeInTheDocument();
  });

  it("links to an authored build once passed", async () => {
    stubApi(routes({ state: "passed" }, { "GET /api/v1/courses/python": withReview({ authored: true }) }));
    renderAt(PAGE);

    expect(await screen.findByRole("link", { name: "Go to the build" })).toHaveAttribute("href", "/courses/python/stages/0/build");
  });

  it("uses the slotted stage's own name", async () => {
    const map = { ...courseMap, stages: [{ ...courseMap.stages[0]!, stage: 100, label: "DSA 0" }] };
    stubApi({
      [`GET ${ME}/courses/python/stages/100/review`]: { ...base, state: "not_ready" },
      "GET /api/v1/courses/python": map,
    });
    renderAt("/courses/python/stages/100/review");

    expect(await screen.findByRole("heading", { level: 1, name: "DSA 0 review" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Python course map" })).toHaveAttribute("href", "/courses/python");
  });
});

describe("course map tile", () => {
  const tile = () => screen.findByText("Stage review");
  const render = (build: object) => {
    stubApi({
      "GET /api/v1/courses/python": withReview(build),
      [`GET ${ME}/proficiency`]: proficiency,
    });
    renderAt("/courses/python");
  };

  it("links to the review when it is ready, before the build", async () => {
    render({ review_state: "available", review_planned: true, locked: true, pending_units: [] });

    const link = (await tile()).closest("a");
    expect(link).toHaveAttribute("href", PAGE);
    expect(link).toHaveTextContent("Ready");
    const stage = link?.closest(".unit-grid");
    const tiles = [...(stage?.querySelectorAll(".build-tile") ?? [])];
    expect(tiles[0]).toHaveTextContent("Stage review");
    expect(tiles[1]).toHaveTextContent("Stage 0 build");
  });

  it("is plain text before the units pass", async () => {
    render({ review_state: "not_ready", review_planned: true });

    expect((await tile()).closest("a")).toBeNull();
  });

  it("is hidden when no review is planned", async () => {
    render({ review_state: "not_ready", review_planned: false });

    await screen.findByText("Stage 0 build");
    expect(screen.queryByText("Stage review")).not.toBeInTheDocument();
  });

  it("is hidden when the stage has no items", async () => {
    render({ review_state: "unavailable", review_planned: false });

    await screen.findByText("Stage 0 build");
    expect(screen.queryByText("Stage review")).not.toBeInTheDocument();
  });

  it("shows a slotted stage by its name, never its id", async () => {
    const [first] = courseMap.stages;
    stubApi({
      "GET /api/v1/courses/python": { ...courseMap, stages: [{ ...first!, stage: 100, label: "DSA 0" }] },
      [`GET ${ME}/proficiency`]: proficiency,
    });
    renderAt("/courses/python");

    expect(await screen.findByText("DSA 0")).toBeInTheDocument();
    expect(screen.queryByText("Stage 100")).not.toBeInTheDocument();
  });

  it("stays a link after a fail and after a pass", async () => {
    render({ review_state: "failed_waiting", review_planned: true });
    expect((await tile()).closest("a")).toHaveTextContent("Not yet");
  });
});

describe("rechecks", () => {
  const due = [{ skill_id: "CO-1", skill_name: "Predict before running", days: 7, due_at: "2026-06-08T09:00:00Z", items: 2 }];
  const progress = (reviews: unknown) => ({
    [`GET ${ME}/proficiency`]: proficiency,
    "GET /api/v1/courses/python": courseMap,
    [`GET ${ME}/ledger`]: [],
    [`GET ${ME}/reviews/due`]: reviews,
  });

  it("lists what is due on My progress", async () => {
    stubApi(progress(due));
    renderAt("/progress");

    const panel = await screen.findByRole("region", { name: "Due for review" });
    expect(within(panel).getByRole("link", { name: /CO-1 Predict before running/ })).toHaveAttribute("href", "/reviews/CO-1/7");
    expect(panel).toHaveTextContent("7-day recheck");
  });

  it("hides the queue when nothing is due", async () => {
    stubApi(progress([]));
    renderAt("/progress");

    await screen.findByRole("heading", { level: 1, name: "My progress" });
    expect(screen.queryByRole("region", { name: "Due for review" })).not.toBeInTheDocument();
  });

  it("takes a recheck, one item at a time, and says when it is finished", async () => {
    let left = 2;
    const calls = stubApi({
      [`GET ${ME}/reviews/due`]: () => (left ? due : []),
      [`GET ${ME}/reviews/CO-1/7/exercise`]: () =>
        left ? item(3 - left) : new Response(JSON.stringify({ detail: "Not due." }), { status: 404 }),
      [`POST ${ME}/attempts`]: () => {
        left -= 1;
        return answered;
      },
    });
    renderAt("/reviews/CO-1/7");

    expect(await screen.findByRole("heading", { level: 1, name: "7-day recheck" })).toBeInTheDocument();
    expect(await screen.findByText(/CO-1 Predict before running/)).toBeInTheDocument();
    await userEvent.click(await screen.findByRole("radio", { name: /First/ }));
    await userEvent.click(screen.getByRole("button", { name: "Submit, one try" }));
    await screen.findByText("Question 2");
    await userEvent.click(screen.getByRole("radio", { name: /First/ }));
    await userEvent.click(screen.getByRole("button", { name: "Submit, one try" }));

    expect(await screen.findByText(/Recheck finished/)).toBeInTheDocument();
    await waitFor(() => expect(calls.filter((c) => c.method === "POST")).toHaveLength(2));
    expect(JSON.parse(calls.find((c) => c.method === "POST")?.body ?? "{}").activity).toBe("recheck");
    expect(screen.queryByRole("complementary", { name: /AXIS/i })).not.toBeInTheDocument();
  });

  it("says so when nothing is due", async () => {
    stubApi({
      [`GET ${ME}/reviews/due`]: [],
      [`GET ${ME}/reviews/CO-1/7/exercise`]: new Response(JSON.stringify({ detail: "Not due." }), { status: 404 }),
    });
    renderAt("/reviews/CO-1/7");

    expect(await screen.findByText(/Nothing is due/)).toBeInTheDocument();
  });
});

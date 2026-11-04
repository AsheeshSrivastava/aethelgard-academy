import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { courseMap, unit } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";
import {
  clampAxisWidth,
  DEFAULT_AXIS_WIDTH,
  loadAxisWidth,
  MIN_AXIS_WIDTH,
  MIN_CONTENT_WIDTH,
  saveAxisWidth,
} from "./axisWidth";
import { parseSse } from "./axisStream";
import { activityFor, nextStep, revealText, splitLessonForExplain } from "./steps";

// CodeMirror and xterm need a real browser; the Playwright walk covers them.
vi.mock("./CodeEditor", () => ({
  CodeEditor: ({ value, onChange, label }: { value: string; onChange: (v: string) => void; label: string }) => (
    <textarea aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));
vi.mock("./RunTerminal", () => ({ RunTerminal: () => <div>Terminal</div> }));

const BASE = "/api/v1/learners/me";
const fullUnit = {
  ...unit,
  lesson_markdown: "# Unit\n\n## The idea\n\nPython runs in order.\n\n## Video Walkthrough\n\nHidden section.\n",
  concept_check_config: { prompt: "Explain it." },
  media: [
    {
      media_id: "v1",
      kind: "video",
      title: "How Python runs",
      url: "https://cdn.example.org/v.mp4",
      duration_seconds: 330,
      timestamps: [{ time: "00:00", topic: "Top to bottom" }],
    },
  ],
};
const notReady = { state: "not_ready", available_at: null, last_attempt_at: null };
const available = { ...notReady, state: "available" };

function exercise(activity: string, item_type: string, block: object) {
  return {
    exercise_id: `PY-0.1/${activity}-1/v1`,
    unit_id: "PY-0.1",
    activity,
    origin: "authored",
    variant_no: 1,
    item_type,
    prompt_markdown: "What happens?",
    [item_type]: block,
  };
}

const options = [
  { key: "A", text: "First" },
  { key: "B", text: "Second" },
];

const passed = {
  outcome: "passed",
  feedback: "Correct.",
  evidence_entry_id: "e1",
  unit_decision: "Strengthen",
  reveal: { correct: "A", why: ["Lines run in order."] },
};

function routes(activity: string, ex: object, attempt: unknown = passed, cold: object = notReady) {
  const state = { step: null as string | null, done_steps: [] as string[] };
  const known = (fullUnit.activities ?? []) as string[];
  return {
    "GET /api/v1/units/PY-0.1": {
      ...fullUnit,
      activities: known.includes(activity) ? known : [...known.slice(0, -1), activity, "cold_check"],
    },
    [`GET ${BASE}/units/PY-0.1/cold-check`]: cold,
    [`GET ${BASE}/units/PY-0.1/state`]: () => state,
    [`PUT ${BASE}/units/PY-0.1/state`]: (_url: URL, init?: RequestInit) => Object.assign(state, JSON.parse(String(init?.body))),
    [`GET ${BASE}/units/PY-0.1/activities/${activity}/exercise`]: ex,
    [`POST ${BASE}/attempts`]: attempt,
    [`GET ${BASE}/ledger`]: [],
    [`GET ${BASE}/drafts/${(ex as { exercise_id?: string }).exercise_id}`]: { files: {} },
    [`PUT ${BASE}/drafts/${(ex as { exercise_id?: string }).exercise_id}`]: null,
  };
}

/** The answer a submit sent, without its interaction id (tested on its own below). */
function postedAttempt(fetchCalls: { method: string; url: string; body?: string }[]) {
  const call = fetchCalls.find((c) => c.method === "POST" && c.url.endsWith("/attempts"));
  const { interaction_id: _id, ...answer } = JSON.parse(call?.body ?? "{}");
  return answer;
}

const postedIds = (fetchCalls: { method: string; url: string; body?: string }[]) =>
  fetchCalls.filter((c) => c.method === "POST" && c.url.endsWith("/attempts")).map((c) => JSON.parse(c.body ?? "{}").interaction_id);

// --- Pure helpers ---

describe("lesson helpers", () => {
  it("finds the next step", () => {
    expect(nextStep(["video", "explain", "predict"], "video")).toBe("explain");
    expect(nextStep(["video", "explain"], "explain")).toBeNull();
  });

  it("maps every step to an activity AXIS accepts", () => {
    expect(activityFor("debug-validate")).toBe("Debug & Validate");
    expect(activityFor("video")).toBe("Explain");
    expect(activityFor("playground")).toBe("Modify");
  });

  it("shows revealed answers in plain words", () => {
    expect(revealText("A")).toBe("A");
    expect(revealText(["waiting", "done"])).toBe("waiting / done");
    expect(revealText({ line: 3, error_type: "name" })).toBe("Line 3, name");
  });

  it("keeps the lesson text but drops sections that belong elsewhere", () => {
    const text = splitLessonForExplain(fullUnit.lesson_markdown);

    expect(text).toContain("Python runs in order.");
    expect(text).not.toContain("Hidden section");
  });

  it("drops command-line workflow sections from the in-app lesson", () => {
    const text = splitLessonForExplain("## 3. Ideas\n\nKeep.\n\n## 4. Local Workflow Instructions\n\nuv run lms pull\n");

    expect(text).toContain("Keep.");
    expect(text).not.toContain("uv run");
  });

  it("parses streamed events, even split across reads", () => {
    const first = parseSse('event: token\ndata: {"text":"Hi"}\n\nevent: do');
    expect(first.events).toEqual([{ event: "token", data: { text: "Hi" } }]);

    const second = parseSse(`${first.rest}ne\ndata: {"assistance_level":"none","cited_concepts":[]}\n\n`);
    expect(second.events[0]?.event).toBe("done");
    expect(second.rest).toBe("");
  });
});

// --- Rail, video, explain ---

describe("step rail", () => {
  it("lists every step and goes back to the unit map", async () => {
    stubApi(routes("predict", {}));
    renderAt("/units/PY-0.1/video");

    const rail = await screen.findByRole("navigation", { name: "Lesson steps" });
    for (const name of ["Video", "Explain", "Predict", "Trace", "Playground", "Cold Check"]) {
      expect(within(rail).getByRole("link", { name: new RegExp(name) })).toBeInTheDocument();
    }
    expect(screen.getByRole("link", { name: /^Back to PY-0\.1/ })).toHaveAttribute("href", "/units/PY-0.1");
  });

  it("marks the current step and a locked Cold Check", async () => {
    stubApi(routes("predict", {}));
    renderAt("/units/PY-0.1/video");

    const rail = await screen.findByRole("navigation", { name: "Lesson steps" });
    expect(within(rail).getByRole("link", { name: /Video/ })).toHaveAttribute("aria-current", "page");
    expect(await within(rail).findByRole("link", { name: /Cold Check.*locked/i })).toBeInTheDocument();
  });

  it("marks finished steps", async () => {
    stubApi({ ...routes("predict", {}), [`GET ${BASE}/units/PY-0.1/state`]: { step: "explain", done_steps: ["video"] } });
    renderAt("/units/PY-0.1/explain");

    const rail = await screen.findByRole("navigation", { name: "Lesson steps" });
    expect(within(rail).getByRole("link", { name: /Video.*done/i })).toBeInTheDocument();
  });

  it("explains an unknown step", async () => {
    stubApi(routes("predict", {}));
    renderAt("/units/PY-0.1/nonsense");

    expect(await screen.findByRole("alert")).toHaveTextContent(/no step/i);
  });

  it("can reset from the lesson, and says the ledger is kept", async () => {
    stubApi(routes("predict", {}));
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/video");

    await user.click(await screen.findByRole("button", { name: "Reset unit" }));

    expect(screen.getByRole("group", { name: "Confirm reset" })).toHaveTextContent(/evidence ledger is kept/i);
  });
});

describe("video step", () => {
  it("shows the video and its chapters", async () => {
    stubApi(routes("predict", {}));
    renderAt("/units/PY-0.1/video");

    expect(await screen.findByRole("heading", { name: "How Python runs" })).toBeInTheDocument();
    expect(screen.getByText("Top to bottom")).toBeInTheDocument();
  });

  it("shows a clear placeholder when a unit has no video yet", async () => {
    stubApi({ ...routes("predict", {}), "GET /api/v1/units/PY-0.1": { ...fullUnit, media: [] } });
    renderAt("/units/PY-0.1/video");

    expect(await screen.findByText(/video for this unit is not ready/i)).toBeInTheDocument();
  });

  it("falls back to a clear message when the video cannot play", async () => {
    stubApi(routes("predict", {}));
    renderAt("/units/PY-0.1/video");

    const video = await screen.findByLabelText("How Python runs");
    fireEvent.error(video);

    expect(await screen.findByText(/video for this unit is not ready/i)).toBeInTheDocument();
    expect(screen.getByText("Top to bottom")).toBeInTheDocument();
  });

  it("can be marked as watched", async () => {
    stubApi(routes("predict", {}));
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/video");

    await user.click(await screen.findByRole("button", { name: "Mark as watched" }));

    expect(await screen.findByRole("link", { name: /Video.*done/i })).toBeInTheDocument();
  });
});

describe("explain step", () => {
  function explainRoutes(status: string) {
    return {
      ...routes("predict", {}),
      "POST /api/v1/explain": { unit_id: "PY-0.1", status, feedback: "Noted.", evidence_logged: true },
    };
  }

  it("shows the lesson and the concept check", async () => {
    stubApi(explainRoutes("Solid"));
    renderAt("/units/PY-0.1/explain");

    expect(await screen.findByText("Python runs in order.")).toBeInTheDocument();
    expect(screen.getByText("Explain it.")).toBeInTheDocument();
  });

  it("reports Solid", async () => {
    stubApi(explainRoutes("Solid"));
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/explain");

    await user.type(await screen.findByLabelText("Your explanation"), "It runs in order.");
    await user.click(screen.getByRole("button", { name: "Check my explanation" }));

    expect(await screen.findByText("Solid")).toBeInTheDocument();
    expect(screen.getByText("Noted.")).toBeInTheDocument();
  });

  it("never blocks on Shaky", async () => {
    stubApi(explainRoutes("Shaky"));
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/explain");

    await user.type(await screen.findByLabelText("Your explanation"), "Because.");
    await user.click(screen.getByRole("button", { name: "Check my explanation" }));

    expect(await screen.findByText("Shaky")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Next: Predict/ })).toBeInTheDocument();
  });
});

// --- Every item type ---

async function answerAndSubmit(activity: string, ex: object, act: (user: ReturnType<typeof userEvent.setup>) => Promise<void>, attempt: unknown = passed) {
  const calls = stubApi(routes(activity, ex, attempt));
  const user = userEvent.setup();
  renderAt(`/units/PY-0.1/${activity}`);
  await screen.findByText("What happens?");
  await act(user);
  await user.click(screen.getByRole("button", { name: /^Submit/ }));
  await screen.findByRole("status", { name: "Result" });
  return postedAttempt(calls);
}

describe("Make step (Amendment A1.3)", () => {
  const block = (make: boolean) => ({
    starter: ["# Donation calculator: write it from a blank file."],
    tasks: [{ id: "ask", label: "Ask for the price per kilogram" }],
    make,
  });

  it("names the Make step, says it starts from a blank file, and offers Run and Submit", async () => {
    stubApi(routes("build", exercise("build", "playground", block(true))));
    renderAt("/units/PY-0.1/build");

    expect(await screen.findByText(/Make · from a blank file/)).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(/hidden tests/i);
    expect(screen.getByText("Ask for the price per kilogram")).toBeInTheDocument();
    expect(screen.getByText("Terminal")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Submit/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Regenerate" })).not.toBeInTheDocument();
  });

  it("leaves an ordinary Build item as it was", async () => {
    stubApi(routes("build", exercise("build", "playground", block(false))));
    renderAt("/units/PY-0.1/build");

    await screen.findByText("What happens?");
    expect(screen.queryByText(/Make · from a blank file/)).not.toBeInTheDocument();
    expect(screen.queryByText("Terminal")).not.toBeInTheDocument();
  });
});

describe("interaction log (ADR-0022)", () => {
  it("records opening a step, and closing it when the learner moves on", async () => {
    const ex = exercise("predict", "predict", { code: ["print(1)"], stdin: "", options });
    const calls = stubApi({ ...routes("predict", ex), [`POST ${BASE}/interactions`]: null });
    const router = renderAt("/units/PY-0.1/predict");
    await screen.findByText("What happens?");

    await router.navigate({ to: "/units/$unitId/$step", params: { unitId: "PY-0.1", step: "trace" } });

    await waitFor(() => {
      const events = calls.filter((c) => c.url.endsWith("/interactions")).map((c) => JSON.parse(c.body ?? "{}"));
      expect(events[0]).toMatchObject({ event_type: "opened", unit_id: "PY-0.1", activity: "predict" });
      expect(events).toContainEqual(expect.objectContaining({ event_type: "closed", activity: "predict" }));
      expect(events).toContainEqual(expect.objectContaining({ event_type: "opened", activity: "trace" }));
    });
  });
});

describe("one record per answer (SPEC-12 section 5)", () => {
  const ex = exercise("predict", "predict", { code: ["print(1)"], stdin: "", options });

  it("sends the same interaction id when one answer is submitted twice", async () => {
    let release: (value: unknown) => void = () => undefined;
    const slow = new Promise((resolve) => (release = resolve));
    const calls = stubApi({ ...routes("predict", ex), [`POST ${BASE}/attempts`]: () => slow.then(() => passed) });
    renderAt("/units/PY-0.1/predict");
    await userEvent.click(await screen.findByRole("radio", { name: /First/ }));
    const form = screen.getByRole("button", { name: /^Submit/ }).closest("form")!;

    fireEvent.submit(form);
    fireEvent.submit(form);
    release(undefined);
    await screen.findByRole("status", { name: "Result" });

    const ids = postedIds(calls);
    expect(ids).toHaveLength(2);
    expect(ids[0]).toMatch(/^[0-9A-HJKMNP-TV-Z]{26}$/);
    expect(ids[1]).toBe(ids[0]);
  });

  it("uses a new id for the next answer", async () => {
    const calls = stubApi(routes("predict", ex));
    renderAt("/units/PY-0.1/predict");
    await userEvent.click(await screen.findByRole("radio", { name: /First/ }));
    await userEvent.click(screen.getByRole("button", { name: /^Submit/ }));
    await screen.findByRole("status", { name: "Result" });
    await userEvent.click(screen.getByRole("radio", { name: /Second/ }));
    await userEvent.click(screen.getByRole("button", { name: /^Submit/ }));

    await waitFor(() => expect(postedIds(calls)).toHaveLength(2));
    const [first, second] = postedIds(calls);
    expect(second).not.toBe(first);
  });
});

describe("item types", () => {
  it("predict sends the chosen option", async () => {
    const ex = exercise("predict", "predict", { code: ["print(1)"], stdin: "", options });

    const body = await answerAndSubmit("predict", ex, (u) => u.click(screen.getByRole("radio", { name: /First/ })));

    expect(body).toEqual({ exercise_id: "PY-0.1/predict-1/v1", activity: "predict", choice: "A" });
  });

  it("predict needs a choice before it can be submitted", async () => {
    stubApi(routes("predict", exercise("predict", "predict", { code: ["x"], stdin: "", options })));
    renderAt("/units/PY-0.1/predict");

    expect(await screen.findByRole("button", { name: /^Submit/ })).toBeDisabled();
  });

  it("trace sends one answer per line", async () => {
    const ex = exercise("trace", "trace", { code: ["print(1)"], input: "" });

    const body = await answerAndSubmit("trace", ex, (u) => u.type(screen.getByLabelText(/terminal shows/i), "1{enter}2"));

    expect(body.trace_answers).toEqual(["1", "2"]);
  });

  it("debug sends the fixed code", async () => {
    const ex = exercise("debug-validate", "debug", { broken_code: ["print(x)"], stdin: "" });

    const body = await answerAndSubmit("debug-validate", ex, (u) => u.type(screen.getByLabelText("Your code"), "!"));

    expect(body.files["solution.py"]).toContain("print(x)");
  });

  it("debug_locate sends the line and the error type", async () => {
    const ex = exercise("debug-validate", "debug_locate", {
      broken_code: ["a", "b"],
      stdin: "",
      error_types: [{ key: "name", text: "NameError" }],
    });

    const body = await answerAndSubmit("debug-validate", ex, async (u) => {
      await u.selectOptions(screen.getByLabelText("Which line fails?"), "2");
      await u.click(screen.getByRole("radio", { name: "NameError" }));
    });

    expect(body.locate).toEqual({ line: 2, error_type: "name" });
  });

  it.each(["evaluate", "direct"])("%s sends the chosen option", async (activity) => {
    const ex = exercise(activity, "choice", { material: ["some output"], options });

    const body = await answerAndSubmit(activity, ex, (u) => u.click(screen.getByRole("radio", { name: /Second/ })));

    expect(body.choice).toBe("B");
    expect(screen.getByText("some output")).toBeInTheDocument();
  });

  it("explain_spot_flaw sends the flawed sentence", async () => {
    const ex = exercise("cold_check", "explain_spot_flaw", { sentences: options });
    ex.activity = "explain";
    const calls = stubApi(routes("cold_check", ex, passed, available));
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/cold_check");

    await user.click(await screen.findByRole("radio", { name: /Second/ }));
    await user.click(screen.getByRole("button", { name: /^Submit/ }));

    await waitFor(() => expect(postedAttempt(calls).choice).toBe("B"));
  });

  it("explain_model_choice sends the chosen model", async () => {
    const ex = exercise("cold_check", "explain_model_choice", { material: [], options });
    const calls = stubApi(routes("cold_check", ex, passed, available));
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/cold_check");

    await user.click(await screen.findByRole("radio", { name: /First/ }));
    await user.click(screen.getByRole("button", { name: /^Submit/ }));

    await waitFor(() => expect(postedAttempt(calls).choice).toBe("A"));
  });

  it("specify_by_tests sends the tests and shows the mutant score", async () => {
    const ex = exercise("specify", "specify_by_tests", {
      function_name: "desk_for",
      signature: "desk_for(age: int) -> str",
      starter_tests: ["from solution import desk_for"],
    });
    const attempt = { outcome: "failed", feedback: "Your tests caught 2 of 4 faulty programs.", score: { passed: 2, total: 4 }, unit_decision: "Strengthen", evidence_entry_id: "e" };

    const body = await answerAndSubmit("specify", ex, (u) => u.type(screen.getByLabelText("Your tests"), "!"), attempt);

    expect(body.tests).toContain("from solution import desk_for");
    expect(screen.getByText("2 of 4")).toBeInTheDocument();
    expect(screen.getByText("desk_for(age: int) -> str")).toBeInTheDocument();
  });

  it("specify_contract sends single and multiple picks", async () => {
    const ex = exercise("specify", "specify_contract", {
      material: ["The form gives us text."],
      fields: [
        { id: "input", label: "Input type", kind: "single", options: [{ key: "str", text: "str" }] },
        { id: "edges", label: "Edge cases", kind: "multi", options: [{ key: "empty", text: "Empty" }, { key: "spaces", text: "Spaces" }] },
      ],
    });

    const body = await answerAndSubmit("specify", ex, async (u) => {
      await u.click(screen.getByRole("radio", { name: "str" }));
      await u.click(screen.getByRole("checkbox", { name: "Empty" }));
      await u.click(screen.getByRole("checkbox", { name: "Spaces" }));
    });

    expect(body.fields).toEqual({ input: "str", edges: ["empty", "spaces"] });
  });

  it("decompose_plan sends the chosen steps in the chosen order", async () => {
    const ex = exercise("decompose", "decompose_plan", {
      material: [],
      steps: [
        { id: "b", text: "Second step" },
        { id: "a", text: "First step" },
        { id: "x", text: "Not needed" },
      ],
    });

    const body = await answerAndSubmit("decompose", ex, async (u) => {
      await u.click(screen.getByRole("checkbox", { name: "Second step" }));
      await u.click(screen.getByRole("checkbox", { name: "First step" }));
      await u.click(screen.getByRole("button", { name: "Move First step up" }));
    });

    expect(body.plan).toEqual(["a", "b"]);
  });

  it("decompose_plan keeps the order the learner chose", async () => {
    const ex = exercise("decompose", "decompose_plan", {
      material: [],
      steps: [
        { id: "a", text: "Step A" },
        { id: "b", text: "Step B" },
      ],
    });

    const body = await answerAndSubmit("decompose", ex, async (u) => {
      await u.click(screen.getByRole("checkbox", { name: "Step B" }));
      await u.click(screen.getByRole("checkbox", { name: "Step A" }));
    });

    expect(body.plan).toEqual(["b", "a"]);
  });

  it("decompose_code sends code and shows structure checks", async () => {
    const ex = exercise("decompose", "decompose_code", {
      entry_function: "intake_report",
      starter: ["def intake_report(r):", "    pass"],
      structure: { min_helpers: 2, max_lines_per_function: 8 },
    });
    const attempt = {
      outcome: "failed",
      feedback: "Not this time.",
      checks: [
        { label: "Behaviour tests", passed: true },
        { label: "Structure", passed: false, detail: "too few helpers" },
      ],
      unit_decision: "Strengthen",
      evidence_entry_id: "e",
    };

    const body = await answerAndSubmit("decompose", ex, (u) => u.type(screen.getByLabelText("Your code"), "!"), attempt);

    expect(body.files["solution.py"]).toContain("intake_report");
    expect(screen.getByText(/too few helpers/)).toBeInTheDocument();
    expect(screen.getByText(/at least 2 helper functions/)).toBeInTheDocument();
  });

  it("a modify exercise uses the playground form and is graded", async () => {
    const ex = exercise("modify", "playground", { starter: ["x = 1"], tasks: [{ id: "t1", label: "Change x" }] });

    const body = await answerAndSubmit("modify", ex, (u) => u.type(screen.getByLabelText("Your code"), "!"));

    expect(body.activity).toBe("modify");
    expect(screen.getByText("Change x")).toBeInTheDocument();
  });
});

describe("results", () => {
  it("shows no answer before the attempt, and the reveal after it", async () => {
    const ex = exercise("predict", "predict", { code: ["x"], stdin: "", options });
    stubApi(routes("predict", ex));
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/predict");

    await screen.findByText("What happens?");
    expect(screen.queryByText("Lines run in order.")).not.toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: /First/ }));
    await user.click(screen.getByRole("button", { name: /^Submit/ }));

    expect(await screen.findByText("Lines run in order.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Next: Trace/ })).toHaveAttribute("href", "/units/PY-0.1/trace");
  });

  it("formats the explanation instead of showing raw markdown", async () => {
    const ex = exercise("predict", "predict", { code: ["x"], stdin: "", options });
    const attempt = { ...passed, reveal: { correct: "A", why: ["`print()` writes a line."] } };
    stubApi(routes("predict", ex, attempt));
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/predict");

    await user.click(await screen.findByRole("radio", { name: /First/ }));
    await user.click(screen.getByRole("button", { name: /^Submit/ }));

    const code = await screen.findByText("print()");
    expect(code.tagName).toBe("CODE");
  });

  it("shows lesson tables as tables", async () => {
    stubApi({
      ...routes("predict", {}),
      "GET /api/v1/units/PY-0.1": { ...fullUnit, lesson_markdown: "## Terms\n\n| Term | Role |\n| --- | --- |\n| `input()` | Reads text |\n" },
    });
    renderAt("/units/PY-0.1/explain");

    expect(await screen.findByRole("table")).toBeInTheDocument();
  });

  it("explains a server refusal", async () => {
    const ex = exercise("predict", "predict", { code: ["x"], stdin: "", options });
    stubApi({
      ...routes("predict", ex),
      [`POST ${BASE}/attempts`]: () => new Response(JSON.stringify({ detail: "Fetch the current exercise." }), { status: 409 }),
    });
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/predict");

    await user.click(await screen.findByRole("radio", { name: /First/ }));
    await user.click(screen.getByRole("button", { name: /^Submit/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Fetch the current exercise.");
  });
});

describe("regenerate", () => {
  const ex = exercise("predict", "predict", { code: ["x"], stdin: "", options });

  it("asks for a new exercise and clears the old result", async () => {
    const next = { ...ex, exercise_id: "PY-0.1/predict-1/v2", prompt_markdown: "A new question?" };
    let served = ex;
    const calls = stubApi({
      ...routes("predict", ex),
      [`GET ${BASE}/units/PY-0.1/activities/predict/exercise`]: () => served,
      [`POST ${BASE}/units/PY-0.1/activities/predict/exercises:regenerate`]: () => {
        served = next;
        return next;
      },
    });
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/predict");

    await user.click(await screen.findByRole("radio", { name: /First/ }));
    await user.click(screen.getByRole("button", { name: /^Submit/ }));
    await screen.findByRole("status", { name: "Result" });
    await user.click(screen.getByRole("button", { name: "Regenerate" }));

    expect(await screen.findByText("A new question?")).toBeInTheDocument();
    expect(screen.queryByRole("status", { name: "Result" })).not.toBeInTheDocument();
    expect(calls.some((c) => c.url.endsWith("exercises:regenerate"))).toBe(true);
  });

  it("is not offered on Explain or the Cold Check", async () => {
    stubApi({ ...routes("cold_check", ex, passed, available), "POST /api/v1/explain": {} });
    renderAt("/units/PY-0.1/explain");

    await screen.findByLabelText("Your explanation");
    expect(screen.queryByRole("button", { name: "Regenerate" })).not.toBeInTheDocument();
  });
});

describe("no seeds yet", () => {
  it("says the activity is not ready", async () => {
    stubApi({
      ...routes("predict", {}),
      [`GET ${BASE}/units/PY-0.1/activities/predict/exercise`]: () =>
        new Response(JSON.stringify({ detail: "PY-0.1 has no 'predict' exercise yet." }), { status: 404 }),
    });
    renderAt("/units/PY-0.1/predict");

    expect(await screen.findByText(/not written yet/i)).toBeInTheDocument();
  });
});

// --- Cold Check ---

describe("cold check", () => {
  const item = exercise("cold_check", "predict", { code: ["x"], stdin: "", options });

  it("counts down while waiting, with no exercise and no AXIS", async () => {
    const soon = new Date(Date.now() + 2 * 3600_000).toISOString();
    const cold = { state: "waiting", available_at: soon, last_attempt_at: null };
    const calls = stubApi(routes("cold_check", item, passed, cold));
    renderAt("/units/PY-0.1/cold_check");

    expect(await screen.findByText(/Opens in (2 h|1 h 59 min)/)).toBeInTheDocument();
    expect(screen.queryByRole("complementary", { name: "AXIS facilitator" })).not.toBeInTheDocument();
    expect(calls.some((c) => c.url.includes("/activities/cold_check/exercise"))).toBe(false);
  });

  it("says there is one try and that AXIS is off", async () => {
    stubApi(routes("cold_check", item, passed, available));
    renderAt("/units/PY-0.1/cold_check");

    const notice = await screen.findByRole("note");
    expect(notice).toHaveTextContent(/one try/i);
    expect(notice).toHaveTextContent(/AXIS is off/i);
    expect(screen.queryByText(/^Ready now/)).not.toBeInTheDocument();
    expect(screen.queryByRole("complementary", { name: "AXIS facilitator" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Regenerate" })).not.toBeInTheDocument();
  });

  it("serves the next item after an attempt", async () => {
    const second = { ...item, exercise_id: "PY-0.1/cold-trace-1/v1", prompt_markdown: "Second item?" };
    let served = item;
    stubApi({
      ...routes("cold_check", item, passed, available),
      [`GET ${BASE}/units/PY-0.1/activities/cold_check/exercise`]: () => served,
      [`POST ${BASE}/attempts`]: () => {
        served = second;
        return { outcome: "passed", feedback: "Correct.", unit_decision: "Strengthen", evidence_entry_id: "e" };
      },
    });
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/cold_check");

    await user.click(await screen.findByRole("radio", { name: /First/ }));
    await user.click(screen.getByRole("button", { name: /^Submit/ }));

    expect(await screen.findByText("Second item?")).toBeInTheDocument();
  });

  const feedback = {
    unit_id: "PY-0.1",
    items: [
      { skill_id: "CO-1", skill_name: "Predict before running", passed: true, your_answer: "C. Queue open", hint: null, practice_activity: "predict", worked: { correct: "C", why: ["The comment is skipped."] } },
      { skill_id: "CO-2", skill_name: "Trace state", passed: false, your_answer: "B A / A", hint: "Follow each name after every line.", practice_activity: "trace", worked: null },
      { skill_id: "CO-6", skill_name: "Explain the concept", passed: null, your_answer: null, hint: null, practice_activity: "predict", worked: null },
    ],
  };

  function coldRoutes(state: object) {
    return {
      ...routes("cold_check", item, passed, state),
      [`GET ${BASE}/units/PY-0.1/cold-check/feedback`]: feedback,
      [`POST ${BASE}/interactions`]: null,
    };
  }

  it("after a fail, shows each item, your answer, a hint and where to practise, never the answer of a failed item", async () => {
    const soon = new Date(Date.now() + 3600_000).toISOString();
    const calls = stubApi(coldRoutes({ state: "failed_waiting", available_at: soon, last_attempt_at: "2026-06-01T09:00:00Z" }));
    renderAt("/units/PY-0.1/cold_check");

    expect(await screen.findByText(/Try again in/)).toBeInTheDocument();
    const summary = await screen.findByRole("region", { name: "Your result" });
    const rows = within(summary).getAllByRole("row").slice(1);
    expect(rows).toHaveLength(3);
    expect(rows[1]).toHaveTextContent("Not yet");
    expect(rows[1]).toHaveTextContent("B A / A");
    expect(rows[1]).toHaveTextContent("Follow each name after every line.");
    expect(within(rows[1]!).getByRole("link", { name: /Practise Trace/ })).toHaveAttribute("href", "/units/PY-0.1/trace");
    expect(rows[2]).toHaveTextContent("Not answered yet");
    expect(within(rows[1]!).queryByText(/Worked answer/)).not.toBeInTheDocument();
    await waitFor(() =>
      expect(calls.some((c) => c.url.endsWith("/interactions") && JSON.parse(c.body ?? "{}").event_type === "feedback_viewed")).toBe(true),
    );
  });

  it("shows the worked answer of a passed item, which will not come back", async () => {
    stubApi(coldRoutes({ state: "passed", available_at: null, last_attempt_at: "2026-06-01T09:00:00Z" }));
    renderAt("/units/PY-0.1/cold_check");

    const summary = await screen.findByRole("region", { name: "Your result" });
    const [passedRow] = within(summary).getAllByRole("row").slice(1);
    expect(passedRow).toHaveTextContent("Passed");
    expect(within(passedRow!).getByText("Worked answer")).toBeInTheDocument();
    expect(passedRow).toHaveTextContent("The comment is skipped.");
  });

  it("says when the Cold Check is not written yet", async () => {
    stubApi({
      ...routes("cold_check", item, passed, available),
      [`GET ${BASE}/units/PY-0.1/activities/cold_check/exercise`]: () =>
        new Response(JSON.stringify({ detail: "none" }), { status: 404 }),
    });
    renderAt("/units/PY-0.1/cold_check");

    expect(await screen.findByText(/not written yet/i)).toBeInTheDocument();
  });
});

// --- AXIS panel ---

describe("AXIS panel", () => {
  const ex = exercise("predict", "predict", { code: ["x"], stdin: "", options });

  function sse(events: [string, object][]) {
    const text = events.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join("");
    return new Response(text, { status: 200, headers: { "content-type": "text/event-stream" } });
  }

  async function ask(reply: () => Response) {
    const calls = stubApi({ ...routes("predict", ex), "POST /api/v1/axis/stream": reply });
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/predict");
    const panel = await screen.findByRole("complementary", { name: "AXIS facilitator" });
    await within(panel).findByRole("group", { name: "Facilitation mode" });
    await screen.findByText("What happens?");
    await user.type(within(panel).getByLabelText("Message AXIS"), "Why?");
    await user.click(within(panel).getByRole("button", { name: "Send" }));
    return { panel, calls, user };
  }

  it("streams the reply and shows citation chips", async () => {
    const { panel } = await ask(() =>
      sse([
        ["token", { text: "What " }],
        ["token", { text: "type?" }],
        ["citation", { concept_id: "c", title: "Standard streams", doc_url: "https://docs.python.org/3/" }],
        ["done", { assistance_level: "small_hint", cited_concepts: ["c"] }],
      ]),
    );

    expect(await within(panel).findByText("What type?")).toBeInTheDocument();
    expect(within(panel).getByRole("link", { name: "Standard streams" })).toHaveAttribute("href", "https://docs.python.org/3/");
  });

  it("renders code in replies as code, not as raw markdown", async () => {
    const { panel } = await ask(() =>
      sse([
        ["token", { text: "Use `input()` here:\n\n```py" }],
        ["token", { text: 'thon\nname = input("Name")\n```\n' }],
        ["done", { assistance_level: "none", cited_concepts: [] }],
      ]),
    );

    const inline = await within(panel).findByText("input()");
    expect(inline.tagName).toBe("CODE");
    await waitFor(() => expect(panel.querySelector("pre code")).toHaveTextContent(/name = input/));
    expect(panel).not.toHaveTextContent("```");
  });

  it("shows HTML from a model as text, never as markup", async () => {
    const { panel } = await ask(() =>
      sse([
        ["token", { text: "Try <img src=x onerror=alert(1)> now." }],
        ["done", { assistance_level: "none", cited_concepts: [] }],
      ]),
    );

    await within(panel).findByText(/Try/);
    expect(panel.querySelector("img")).toBeNull();
  });

  it("sends the exercise, the mode and the page", async () => {
    const { calls, panel } = await ask(() => sse([["done", { assistance_level: "none", cited_concepts: [] }]]));

    await within(panel).findByText("Why?");
    const body = JSON.parse(calls.find((c) => c.url.endsWith("/axis/stream"))?.body ?? "{}");
    expect(body).toMatchObject({
      unit_id: "PY-0.1",
      mode: "Socratic",
      current_activity: "Predict",
      exercise_id: "PY-0.1/predict-1/v1",
      page: "predict",
    });
  });

  it("offers the three modes", async () => {
    const { panel, calls, user } = await ask(() => sse([["done", { assistance_level: "none", cited_concepts: [] }]]));

    await user.click(within(panel).getByRole("radio", { name: "Coach" }));
    await user.type(within(panel).getByLabelText("Message AXIS"), "Again");
    await user.click(within(panel).getByRole("button", { name: "Send" }));

    await waitFor(() => {
      const bodies = calls.filter((c) => c.url.endsWith("/axis/stream")).map((c) => JSON.parse(c.body ?? "{}"));
      expect(bodies.at(-1)?.mode).toBe("Coach");
    });
  });

  it("says how help is logged", async () => {
    stubApi(routes("predict", ex));
    renderAt("/units/PY-0.1/predict");

    const panel = await screen.findByRole("complementary", { name: "AXIS facilitator" });
    expect(panel).toHaveTextContent(/logged/i);
  });

  it("explains when AXIS cannot answer", async () => {
    const { panel } = await ask(() => sse([["error", { message: "AXIS is unavailable right now." }]]));

    expect(await within(panel).findByRole("alert")).toHaveTextContent("AXIS is unavailable");
  });
});

describe("AXIS panel width", () => {
  const ex = exercise("predict", "predict", { code: ["x"], stdin: "", options });

  it("stays between the limits", () => {
    expect(clampAxisWidth(100, 1300)).toBe(MIN_AXIS_WIDTH);
    expect(clampAxisWidth(500, 1300)).toBe(500);
    expect(clampAxisWidth(5000, 1300)).toBe(780);
  });

  it("always leaves the lesson usable on a narrow layout", () => {
    expect(clampAxisWidth(600, 800)).toBe(800 - MIN_CONTENT_WIDTH);
    expect(clampAxisWidth(600, 650)).toBe(MIN_AXIS_WIDTH);
  });

  it("remembers the width, and ignores a damaged saved value", () => {
    saveAxisWidth(512);
    expect(loadAxisWidth()).toBe(512);

    localStorage.setItem("axis-width", "nonsense");
    expect(loadAxisWidth()).toBe(DEFAULT_AXIS_WIDTH);
  });

  it("can be resized from the keyboard", async () => {
    localStorage.removeItem("axis-width");
    stubApi(routes("predict", ex));
    const user = userEvent.setup();
    renderAt("/units/PY-0.1/predict");

    const handle = await screen.findByRole("separator", { name: "Resize AXIS panel" });
    expect(handle).toHaveAttribute("aria-valuenow", String(DEFAULT_AXIS_WIDTH));

    handle.focus();
    await user.keyboard("{ArrowLeft}");

    expect(handle).toHaveAttribute("aria-valuenow", String(DEFAULT_AXIS_WIDTH + 24));
    expect(loadAxisWidth()).toBe(DEFAULT_AXIS_WIDTH + 24);
  });

  it("double-click resets the width", async () => {
    saveAxisWidth(600);
    stubApi(routes("predict", ex));
    renderAt("/units/PY-0.1/predict");

    const handle = await screen.findByRole("separator", { name: "Resize AXIS panel" });
    expect(handle).toHaveAttribute("aria-valuenow", "600");

    fireEvent.doubleClick(handle);

    expect(handle).toHaveAttribute("aria-valuenow", String(DEFAULT_AXIS_WIDTH));
    expect(loadAxisWidth()).toBe(DEFAULT_AXIS_WIDTH);
  });

  it("is not offered on the Cold Check", async () => {
    stubApi(routes("cold_check", ex, passed, available));
    renderAt("/units/PY-0.1/cold_check");

    await screen.findByRole("note");
    expect(screen.queryByRole("separator")).not.toBeInTheDocument();
  });
});

// --- Links from the other pages ---

describe("links into the lesson", () => {
  it("the unit map opens a step", async () => {
    stubApi(routes("predict", {}));
    renderAt("/units/PY-0.1");

    const path = await screen.findByRole("list", { name: "Lesson path" });
    expect(within(path).getByRole("link", { name: /Trace/ })).toHaveAttribute("href", "/units/PY-0.1/trace");
    expect(screen.getByRole("link", { name: "Start lesson" })).toHaveAttribute("href", "/units/PY-0.1/video");
  });

  it("the course map still links to unit maps", () => {
    expect(courseMap.stages[0]?.units[0]?.unit_id).toBe("PY-0.4");
  });
});

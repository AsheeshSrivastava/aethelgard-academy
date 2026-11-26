import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { unit } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";

// ADR-0041 / SPEC-33 section 4 (E1, E5), stage 1, and the stage 1 chaos cases of section 9.
//
// Contract these tests fix (the spec leaves it open):
//   - No component prop name is fixed: the real pages, panel and run terminal are rendered, and only xterm, the
//     run socket and the code editor are faked.
//   - The request carries execution_result = { success: false, stdout: "", stderr, exit_code, duration_ms }
//     (stdout is sent empty), and only when the latest run on this step ended with a non-zero exit code or a
//     timeout AND left error output. Otherwise it carries none.
//   - While an error is held, and only then, the panel says: "Your last run error is sent with your question."
// All text is made up. No server, no model.

vi.mock("./CodeEditor", () => ({
  CodeEditor: ({ value, onChange, label }: { value: string; onChange: (v: string) => void; label: string }) => (
    <textarea aria-label={label} defaultValue={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));
vi.mock("@xterm/xterm", () => ({
  Terminal: class {
    options = {};
    loadAddon() {}
    open() {}
    onData() {}
    write() {}
    writeln() {}
    clear() {}
    reset() {}
    focus() {}
    dispose() {}
  },
}));
vi.mock("@xterm/addon-fit", () => ({
  FitAddon: class {
    fit() {}
  },
}));

const NOTE = "Your last run error is sent with your question.";
const STREAM = "/api/v1/axis/stream";
const BASE = "/api/v1/learners/me";

class FakeSocket {
  static all: FakeSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((message: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  constructor(readonly url: string) {
    FakeSocket.all.push(this);
  }
  send() {}
  close() {
    this.onclose?.();
  }
}

beforeEach(() => {
  FakeSocket.all = [];
  vi.stubGlobal("WebSocket", FakeSocket);
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  );
});

// --- the pages ---

const ITEMS = {
  playground: { item_type: "playground", playground: { starter: ["print('made up')"] } },
  "debug-validate": { item_type: "debug", debug: { broken_code: ["print(missing)"] } },
  predict: { item_type: "predict", predict: { code: ["x"], stdin: "", options: [{ key: "A", text: "First" }] } },
} as const;

const done = () =>
  new Response(`event: done\ndata: ${JSON.stringify({ assistance_level: "none", cited_concepts: [] })}\n\n`, {
    status: 200,
    headers: { "content-type": "text/event-stream" },
  });

function unitRoutes(unitId: string): Record<string, unknown> {
  const routes: Record<string, unknown> = {
    [`GET /api/v1/units/${unitId}`]: { ...unit, unit_id: unitId, activities: [...Object.keys(ITEMS), "cold_check"] },
    [`GET ${BASE}/units/${unitId}/cold-check`]: { state: "not_ready", available_at: null, last_attempt_at: null },
    [`GET ${BASE}/units/${unitId}/state`]: { step: null, done_steps: [] },
    [`PUT ${BASE}/units/${unitId}/state`]: null,
  };
  for (const [step, item] of Object.entries(ITEMS)) {
    const id = `${unitId}/${step}-1/v1`;
    routes[`GET ${BASE}/units/${unitId}/activities/${step}/exercise`] = {
      exercise_id: id,
      unit_id: unitId,
      activity: step,
      origin: "authored",
      variant_no: 1,
      prompt_markdown: `Made-up task ${step}`,
      ...item,
    };
    routes[`GET ${BASE}/drafts/${id}`] = { files: {} };
    routes[`PUT ${BASE}/drafts/${id}`] = null;
  }
  return routes;
}

const BUILD_ME = `${BASE}/courses/python/stages/0`;
const build = {
  exercise_id: "python/stage-0/build",
  course_id: "python",
  stage: 0,
  stage_label: "Module 0",
  title: "Made-up build",
  kind: "script",
  maturity: "P1",
  status: "draft",
  brief_markdown: "Write one made-up script.",
  sample_run: ["made up"],
  entry: "made.py",
  files: [{ path: "made.py", starter: ["# Starter"] }],
  requirements: [{ id: "plan", label: "Plan written", unit_id: "PY-0.1" }],
  proves: [{ skill_id: "CO-1", unit_id: "PY-0.4", label: "Run a script" }],
  submitted: false,
};

function open(path: string, extra: Record<string, unknown> = {}) {
  const calls = stubApi({
    ...unitRoutes("PY-0.1"),
    ...unitRoutes("PY-0.2"),
    "GET /api/v1/courses/python/stages/0/build": build,
    "GET /api/v1/learners/me/drafts/python/stage-0/build": { files: {} },
    "PUT /api/v1/learners/me/drafts/python/stage-0/build": null,
    [`POST ${BUILD_ME}/build:check`]: { requirements: [] },
    "GET /api/v1/axis/status": { course_reference: "ready" },
    [`POST ${STREAM}`]: done,
    ...extra,
  });
  const user = userEvent.setup();
  const router = renderAt(path);
  const panel = () => screen.findByRole("complementary", { name: "AXIS facilitator" });
  const sent = () => calls.filter((c) => c.url === STREAM).map((c) => JSON.parse(c.body ?? "{}") as Record<string, unknown>);

  async function ask() {
    const aside = await panel();
    const before = sent().length;
    await user.type(within(aside).getByLabelText("Message AXIS"), "Why?");
    await waitFor(() => expect(within(aside).getByRole("button", { name: "Send" })).toBeEnabled());
    await user.click(within(aside).getByRole("button", { name: "Send" }));
    await waitFor(() => expect(sent()).toHaveLength(before + 1));
    return sent().at(-1)!;
  }

  async function run(events: object[]) {
    await user.click(await screen.findByRole("button", { name: "Run" }));
    const socket = FakeSocket.all.at(-1)!;
    act(() => {
      socket.onopen?.();
      for (const event of events) socket.onmessage?.({ data: JSON.stringify(event) });
    });
  }

  async function go(unitId: string, step: string) {
    await act(() => router.navigate({ to: "/units/$unitId/$step", params: { unitId, step } }));
    await screen.findByText(step === "playground" ? "Made-up task playground" : `Made-up task ${step}`);
  }

  const note = async () => within(await panel()).queryByText(NOTE);
  return { user, ask, run, go, note, panel };
}

async function onStep(step: keyof typeof ITEMS, extra: Record<string, unknown> = {}) {
  const page = open(`/units/PY-0.1/${step}`, extra);
  await screen.findByText(`Made-up task ${step}`);
  await page.panel();
  return page;
}

const err = (data: string) => ({ type: "stderr", data });
const out = (data: string) => ({ type: "stdout", data });
const exit = (code: number, timed_out = false) => ({ type: "exit", code, duration_ms: 12.5, timed_out });
const failed = (text: string) => [err(text), exit(1)];
const result = (stderr: string, exit_code = 1) => ({ success: false, stdout: "", stderr, exit_code });
const none = (body: Record<string, unknown>) => expect(body.execution_result ?? null).toBeNull();

// =====================================================================================================
// E1: the panel sends the latest run's error output
// =====================================================================================================

describe("SPEC-33 E1: the run's error output goes with the question", () => {
  it("test_panel_sends_the_latest_run_error", async () => {
    const page = await onStep("playground");

    await page.run([out("made-up output\n"), err("Traceback (most recent call last):\n"), err("NameError: made up\n"), exit(1)]);

    const body = await page.ask();
    expect(body.execution_result).toMatchObject(result("Traceback (most recent call last):\nNameError: made up\n"));
    expect((body.execution_result as { duration_ms: unknown }).duration_ms).toEqual(expect.any(Number));
    expect(body.learner_code).toBe("print('made up')");
    // It stays held until another run: a second question carries it too.
    expect((await page.ask()).execution_result).toMatchObject({ stderr: expect.stringContaining("NameError") });
  });

  it("works on an exercise item with a run terminal", async () => {
    const page = await onStep("debug-validate");

    await page.run(failed("NameError: made up\n"));

    expect((await page.ask()).execution_result).toMatchObject(result("NameError: made up\n"));
    expect(await page.note()).toBeInTheDocument();
  });

  it("works on the stage build", async () => {
    const page = open("/courses/python/stages/0/build");
    await page.panel();

    await page.run([err("ValueError: made up\n"), exit(2)]);

    expect(await page.note()).toBeInTheDocument();
    expect((await page.ask()).execution_result).toMatchObject(result("ValueError: made up\n", 2));
  });

  it("sends only the newest failed run", async () => {
    const page = await onStep("playground");

    await page.run(failed("KeyError: older\n"));
    await page.run(failed("IndexError: newer\n"));

    expect((await page.ask()).execution_result).toMatchObject(result("IndexError: newer\n"));
  });

  it("sends a run that timed out and left error output", async () => {
    const page = await onStep("playground");

    await page.run([err("Stopped: the made-up time limit was reached.\n"), exit(0, true)]);

    expect((await page.ask()).execution_result).toMatchObject({
      success: false,
      stderr: "Stopped: the made-up time limit was reached.\n",
    });
  });

  it.each([
    ["no run yet", null],
    ["a successful run that wrote to the error stream", [err("DeprecationWarning: made up\n"), exit(0)]],
    ["a failed run with no error output", [out("made-up output\n"), exit(3)]],
  ])("sends nothing and says nothing after %s", async (_name, events) => {
    const page = await onStep("playground");

    if (events) await page.run(events);

    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());
  });
});

describe("SPEC-33 E1: when the held error is cleared", () => {
  it("test_a_successful_run_clears_it", async () => {
    const page = await onStep("playground");
    await page.run(failed("NameError: made up\n"));
    expect(await page.note()).toBeInTheDocument();

    await page.run([out("fine\n"), exit(0)]);

    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());
  });

  it("a later failed run with no error output clears it too", async () => {
    const page = await onStep("playground");
    await page.run(failed("NameError: made up\n"));
    expect(await page.note()).toBeInTheDocument();

    await page.run([exit(1)]);

    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());
  });

  it("changing the step clears it, and returning does not bring it back", async () => {
    const page = await onStep("playground");
    await page.run(failed("NameError: made up\n"));
    expect(await page.note()).toBeInTheDocument();

    await page.go("PY-0.1", "debug-validate");
    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());

    await page.go("PY-0.1", "playground");
    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());
  });

  it("changing the unit clears it, even on the same step name", async () => {
    const page = await onStep("playground");
    await page.go("PY-0.2", "playground"); // both units are loaded once, so the later moves reuse the page
    await page.go("PY-0.1", "playground");
    await page.run(failed("NameError: made up\n"));
    expect(await page.note()).toBeInTheDocument();

    await page.go("PY-0.2", "playground");
    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());

    await page.go("PY-0.1", "playground");
    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());
  });
});

// =====================================================================================================
// Section 9: chaos check (stage 1 cases)
// =====================================================================================================

describe("SPEC-33 section 9: chaos", () => {
  it("a very long, binary error output still ends with its cause line", async () => {
    const page = await onStep("playground");
    const cause = "ValueError: the made-up cause line\n";

    await page.run([err("\u0000\u0001�".repeat(20_000)), err("frame\n".repeat(5_000)), err(cause), exit(1)]);

    const sentError = (await page.ask()).execution_result as { stderr: string };
    expect(sentError.stderr.endsWith(cause)).toBe(true);
  });

  it("an error from before a code change is still the latest run, so it is sent with the new code", async () => {
    const page = await onStep("playground");
    await page.run(failed("NameError: made up\n"));

    const editor = screen.getByLabelText("Your code");
    await page.user.clear(editor);
    await page.user.type(editor, "total = 1");

    const body = await page.ask();
    expect(body.learner_code).toBe("total = 1");
    expect(body.execution_result).toMatchObject(result("NameError: made up\n"));
    expect(await page.note()).toBeInTheDocument();
  });
});

// =====================================================================================================
// Section 12 reading 2: Regenerate and Reset clear it; a run that finishes late attaches to nothing
// =====================================================================================================

const deliver = (socket: FakeSocket, events: object[]) =>
  act(() => {
    for (const event of events) socket.onmessage?.({ data: JSON.stringify(event) });
  });

describe("SPEC-33 section 12 reading 2: reset actions clear the held error", () => {
  it("Regenerate clears it", async () => {
    const id = "PY-0.1/debug-validate-2/v1";
    const page = open("/units/PY-0.1/debug-validate", {
      [`POST ${BASE}/units/PY-0.1/activities/debug-validate/exercises:regenerate`]: {
        exercise_id: id,
        unit_id: "PY-0.1",
        activity: "debug-validate",
        origin: "generated",
        variant_no: 2,
        prompt_markdown: "Made-up second variant",
        ...ITEMS["debug-validate"],
      },
      [`GET ${BASE}/drafts/${id}`]: { files: {} },
      [`PUT ${BASE}/drafts/${id}`]: null,
    });
    await screen.findByText("Made-up task debug-validate");
    await page.run(failed("NameError: made up\n"));
    expect(await page.note()).toBeInTheDocument();

    await page.user.click(screen.getByRole("button", { name: "Regenerate" }));
    await screen.findByText("Made-up second variant");

    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());
  });

  it("Reset code clears it", async () => {
    const page = await onStep("playground");
    await page.run(failed("NameError: made up\n"));
    expect(await page.note()).toBeInTheDocument();

    await page.user.click(screen.getByRole("button", { name: "Reset code" }));

    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());
  });

  it("Reset unit clears it", async () => {
    const page = await onStep("playground", { [`POST ${BASE}/units/PY-0.1/reset`]: null });
    await page.run(failed("NameError: made up\n"));
    expect(await page.note()).toBeInTheDocument();

    await page.user.click(screen.getByRole("button", { name: "Reset unit" }));
    await page.user.click(screen.getByRole("button", { name: "Yes, reset" }));

    await waitFor(async () => expect(await page.note()).not.toBeInTheDocument());
  });

  it("Reset build clears it", async () => {
    const page = open("/courses/python/stages/0/build", { [`POST ${BUILD_ME}/build:reset`]: null });
    await page.panel();
    await page.run(failed("ValueError: made up\n"));
    expect(await page.note()).toBeInTheDocument();

    await page.user.click(screen.getByRole("button", { name: "Reset build" }));
    const dialog = screen.getByRole("alertdialog", { name: "Reset this build" });
    await page.user.click(within(dialog).getByRole("button", { name: "Reset build" }));
    await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());

    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());
  });

  it("a run still going when the code is reset attaches nothing", async () => {
    const page = await onStep("playground");
    await page.run([]);
    const socket = FakeSocket.all.at(-1)!;
    await page.user.click(screen.getByRole("button", { name: "Reset code" }));

    deliver(socket, failed("NameError: late\n"));

    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());
  });
});

describe("SPEC-33 section 12 reading 2: a late run", () => {
  it("does not attach to the new unit, even on the same step", async () => {
    const page = await onStep("playground");
    await page.go("PY-0.2", "playground");
    await page.go("PY-0.1", "playground");
    await page.run([]);
    const socket = FakeSocket.all.at(-1)!;

    await page.go("PY-0.2", "playground");
    deliver(socket, failed("NameError: late\n"));

    expect(await page.note()).not.toBeInTheDocument();
    none(await page.ask());
  });

  it("does not attach to a new step, nor replace that step's own error", async () => {
    const page = await onStep("playground");
    await page.run([]);
    const socket = FakeSocket.all.at(-1)!;

    await page.go("PY-0.1", "debug-validate");
    await page.run(failed("KeyError: current\n"));
    deliver(socket, failed("NameError: late\n"));

    expect((await page.ask()).execution_result).toMatchObject(result("KeyError: current\n"));
  });
});

describe("SPEC-33 section 4: the client holds a bounded error", () => {
  it("keeps the end, at most 20000 characters, starting on a whole line", async () => {
    const page = await onStep("playground");

    await page.run([err("made-up frame\n".repeat(10_000)), err("ValueError: last\n"), exit(1)]);

    const { stderr } = (await page.ask()).execution_result as { stderr: string };
    expect(stderr.length).toBeLessThanOrEqual(20_000);
    expect(stderr.startsWith("made-up frame\n")).toBe(true);
    expect(stderr.endsWith("ValueError: last\n")).toBe(true);
  });
});

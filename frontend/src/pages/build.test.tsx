import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { courseMap } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";

// CodeMirror and xterm need a real browser; the Playwright walk covers them.
vi.mock("../lesson/CodeEditor", () => ({
  CodeEditor: ({ value, onChange, label }: { value: string; onChange: (v: string) => void; label: string }) => (
    <textarea aria-label={label} defaultValue={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));
vi.mock("../lesson/RunTerminal", () => ({
  RunTerminal: ({ entry, getCode }: { entry?: string; getCode: () => string }) => (
    <button type="button" onClick={() => document.body.setAttribute("data-ran", `${entry}:${getCode()}`)}>
      Terminal
    </button>
  ),
}));

const PATH = "/courses/python/stages/0/build";
const API = "/api/v1/courses/python/stages/0/build";
const ME = "/api/v1/learners/me/courses/python/stages/0";
const DRAFT = "/api/v1/learners/me/drafts/python/stage-0/build";

const build = {
  exercise_id: "python/stage-0/build",
  course_id: "python",
  stage: 0,
  stage_label: "Stage 0",
  title: "Pantry intake check-in script",
  kind: "script",
  status: "draft",
  brief_markdown: "Write one script for **the desk**.",
  sample_run: ["Name: meera", "", "--- CHECK-IN SLIP ---"],
  entry: "checkin.py",
  files: [
    { path: "checkin.py", starter: ["# Starter"] },
    { path: "README.md", starter: ["# Readme"] },
  ],
  requirements: [
    { id: "plan", label: "Plan written as comments", unit_id: "PY-0.1" },
    { id: "sample", label: "Output matches the sample run (Verify)", unit_id: "PY-0.4" },
    { id: "note", label: "Ownership note written", unit_id: "PY-0.3" },
  ],
  proves: [
    { skill_id: "CO-1", unit_id: "PY-0.4", label: "Run a script" },
    { skill_id: "DE-3", unit_id: "PY-0.3", label: "Own the reasoning" },
  ],
  submitted: false,
};

type Status = Record<string, boolean | null>;

function results(status: Status, details: Record<string, string> = {}) {
  return { requirements: Object.entries(status).map(([id, met]) => ({ id, met, detail: details[id] })) };
}

const passing = { outcome: "passed", feedback: "This build is in your ledger.", evidence_entry_id: "e1", unit_decision: "Progress", checks: [] };

function routes(extra: Record<string, unknown> = {}) {
  return {
    [`GET ${API}`]: build,
    [`GET ${DRAFT}`]: { files: {} },
    [`PUT ${DRAFT}`]: null,
    [`POST ${ME}/build:check`]: (_url: URL, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body)) as { run_checks: boolean };
      return results({ plan: true, sample: body.run_checks ? true : null, note: true });
    },
    [`POST ${ME}/build:reset`]: null,
    "POST /api/v1/learners/me/attempts": passing,
    ...extra,
  };
}

function bodies(calls: { method: string; url: string; body?: string }[], url: string) {
  return calls.filter((c) => c.url === url).map((c) => JSON.parse(c.body ?? "{}") as Record<string, unknown>);
}

const checkUrl = `${ME}/build:check`;
const requirements = () => screen.findByRole("region", { name: /Requirements/ });

describe("locked", () => {
  it("names what is left, and keeps the way back", async () => {
    stubApi({ [`GET ${API}`]: new Response(JSON.stringify({ detail: "Pass the Cold Check in: PY-0.3." }), { status: 423 }) });
    renderAt(PATH);

    expect(await screen.findByText("Pass the Cold Check in: PY-0.3.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Python course map" })).toHaveAttribute("href", "/courses/python");
    expect(screen.queryByRole("button", { name: "Submit build" })).not.toBeInTheDocument();
  });

  it("says plainly when a build is not written yet", async () => {
    stubApi({ [`GET ${API}`]: new Response(JSON.stringify({ detail: "The build for stage 0 is not written yet." }), { status: 404 }) });
    renderAt(PATH);

    expect(await screen.findByText(/not written yet/)).toBeInTheDocument();
  });
});

describe("a slotted stage", () => {
  it("uses its own name and links back to its own course", async () => {
    const api = "/api/v1/courses/backend/stages/600/build";
    stubApi({ ...routes(), [`GET ${api}`]: { ...build, course_id: "backend", stage: 600, stage_label: "DB 0" } });
    renderAt("/courses/backend/stages/600/build");

    expect(await screen.findByText("DB 0 build")).toBeInTheDocument();
    expect(screen.queryByText(/Stage 600/)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Python for Backend/AI course map" })).toHaveAttribute("href", "/courses/backend");
  });
});

describe("the page", () => {
  it("shows the brief, sample run, requirements, files, note and what the build proves", async () => {
    stubApi(routes());
    renderAt(PATH);

    expect(await screen.findByRole("heading", { level: 1, name: "Pantry intake check-in script" })).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Script")).toBeInTheDocument();
    expect((await screen.findByText("the desk")).tagName).toBe("STRONG");
    expect(screen.getByText(/--- CHECK-IN SLIP ---/)).toBeInTheDocument();
    expect(within(await requirements()).getAllByRole("listitem")).toHaveLength(3);
    expect(screen.getByRole("button", { name: "checkin.py" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "README.md" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByLabelText("Ownership note")).toBeInTheDocument();
    const proves = screen.getByRole("region", { name: "What this build proves" });
    expect(within(proves).getByText("Run a script")).toBeInTheDocument();
  });

  it("shows AXIS in Socratic only", async () => {
    stubApi(routes());
    renderAt(PATH);

    const axis = await screen.findByRole("complementary", { name: "AXIS facilitator" });
    expect(within(axis).getByText("Socratic during builds")).toBeInTheDocument();
    expect(within(axis).queryByRole("radio")).not.toBeInTheDocument();
  });

  it("does not show a Draft label on an approved build", async () => {
    stubApi(routes({ [`GET ${API}`]: { ...build, status: "approved" } }));
    renderAt(PATH);

    await screen.findByRole("heading", { level: 1 });
    expect(screen.queryByText("Draft")).not.toBeInTheDocument();
  });

  it("runs the entry file with the current code", async () => {
    stubApi(routes());
    renderAt(PATH);

    await userEvent.click(await screen.findByRole("button", { name: "Terminal" }));

    expect(document.body.getAttribute("data-ran")).toBe("checkin.py:# Starter");
  });

  it("restores saved work and the saved note", async () => {
    stubApi(routes({ [`GET ${DRAFT}`]: { files: { "checkin.py": "# saved", "ownership-note.txt": "My saved note" } } }));
    renderAt(PATH);

    expect(await screen.findByLabelText("checkin.py code")).toHaveValue("# saved");
    expect(screen.getByLabelText("Ownership note")).toHaveValue("My saved note");
  });

  it("saves work and the note together", async () => {
    const calls = stubApi(routes());
    renderAt(PATH);

    fireEvent.change(await screen.findByLabelText("Ownership note"), { target: { value: "My note" } });

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true), { timeout: 2000 });
    const saved = JSON.parse(calls.find((c) => c.method === "PUT")!.body!) as { files: Record<string, string> };
    expect(saved.files).toEqual({ "checkin.py": "# Starter", "README.md": "# Readme", "ownership-note.txt": "My note" });
  });

  it("keeps each file's text when switching tabs", async () => {
    stubApi(routes());
    renderAt(PATH);

    fireEvent.change(await screen.findByLabelText("checkin.py code"), { target: { value: "# changed" } });
    await userEvent.click(screen.getByRole("button", { name: "README.md" }));
    expect(screen.getByLabelText("README.md code")).toHaveValue("# Readme");
    await userEvent.click(screen.getByRole("button", { name: "checkin.py" }));

    expect(screen.getByLabelText("checkin.py code")).toHaveValue("# changed");
  });
});

describe("requirements", () => {
  it("are checked by the server as you work, without running code", async () => {
    const calls = stubApi(routes());
    renderAt(PATH);

    const list = await requirements();
    await waitFor(() => expect(within(list).getByText("2 of 3 met")).toBeInTheDocument());
    expect(bodies(calls, checkUrl).every((b) => b.run_checks === false)).toBe(true);
  });

  it("shows the reason for an unmet one", async () => {
    stubApi(routes({ [`POST ${ME}/build:check`]: results({ plan: false, sample: null, note: false }, { plan: "The file has a syntax error on line 3." }) }));
    renderAt(PATH);

    expect(await screen.findByText("The file has a syntax error on line 3.")).toBeInTheDocument();
  });

  it("Verify runs the hidden checks and meets the behaviour requirement", async () => {
    const calls = stubApi(routes());
    renderAt(PATH);

    await waitFor(async () => expect(within(await requirements()).getByText("2 of 3 met")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: "Verify" }));

    await waitFor(async () => expect(within(await requirements()).getByText("3 of 3 met")).toBeInTheDocument());
    expect(bodies(calls, checkUrl).some((b) => b.run_checks === true)).toBe(true);
  });

  it("Verify shows why a check failed", async () => {
    stubApi(routes({
      [`POST ${ME}/build:check`]: (_u: URL, init?: RequestInit) =>
        (JSON.parse(String(init?.body)) as { run_checks: boolean }).run_checks
          ? results({ plan: true, sample: false, note: true }, { sample: "Output line 2 should be 'x'." })
          : results({ plan: true, sample: null, note: true }),
    }));
    renderAt(PATH);

    await userEvent.click(await screen.findByRole("button", { name: "Verify" }));

    expect(await screen.findByText("Output line 2 should be 'x'.")).toBeInTheDocument();
  });

  it("Verify passes even while the note is unfinished, because it does not check the note", async () => {
    stubApi(routes({
      [`POST ${ME}/build:check`]: (_u: URL, init?: RequestInit) =>
        results({ plan: true, sample: (JSON.parse(String(init?.body)) as { run_checks: boolean }).run_checks ? true : null, note: false }),
    }));
    renderAt(PATH);

    await waitFor(async () => expect(within(await requirements()).getByText("1 of 3 met")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: "Verify" }));

    expect(await screen.findByText("Verify passed.")).toBeInTheDocument();
  });

  it("editing the entry file clears Verify, so an old pass cannot unlock Submit", async () => {
    stubApi(routes());
    renderAt(PATH);

    await userEvent.click(await screen.findByRole("button", { name: "Verify" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Submit build" })).toBeEnabled());

    fireEvent.change(screen.getByLabelText("checkin.py code"), { target: { value: "# edited" } });

    await waitFor(() => expect(screen.getByRole("button", { name: "Submit build" })).toBeDisabled());
  });

  it("editing the README keeps Verify", async () => {
    stubApi(routes());
    renderAt(PATH);

    await userEvent.click(await screen.findByRole("button", { name: "Verify" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Submit build" })).toBeEnabled());
    await userEvent.click(screen.getByRole("button", { name: "README.md" }));

    fireEvent.change(screen.getByLabelText("README.md code"), { target: { value: "# edited" } });

    await new Promise((resolve) => setTimeout(resolve, 600));
    expect(screen.getByRole("button", { name: "Submit build" })).toBeEnabled();
  });
});

describe("submitting", () => {
  async function verified() {
    await userEvent.click(await screen.findByRole("button", { name: "Verify" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Submit build" })).toBeEnabled());
  }

  it("is off until every requirement is met", async () => {
    stubApi(routes());
    renderAt(PATH);

    expect(await screen.findByRole("button", { name: "Submit build" })).toBeDisabled();
    expect(screen.getByText("Meet every requirement to submit.")).toBeInTheDocument();
  });

  it("sends the files and the note, and no evidence fields", async () => {
    const calls = stubApi(routes());
    renderAt(PATH);
    fireEvent.change(await screen.findByLabelText("Ownership note"), { target: { value: "I wrote it myself." } });
    await verified();

    await userEvent.click(screen.getByRole("button", { name: "Submit build" }));

    expect(await screen.findByText("This build is in your ledger.")).toBeInTheDocument();
    const [attempt] = bodies(calls, "/api/v1/learners/me/attempts");
    expect(attempt).toEqual({
      exercise_id: "python/stage-0/build",
      activity: "build",
      files: { "checkin.py": "# Starter", "README.md": "# Readme" },
      ownership_note: "I wrote it myself.",
      interaction_id: expect.stringMatching(/^[0-9A-HJKMNP-TV-Z]{26}$/),
    });
  });

  it("shows which requirements the server refused", async () => {
    stubApi(routes({
      "POST /api/v1/learners/me/attempts": {
        outcome: "failed",
        feedback: "Some requirements are not met yet.",
        unit_decision: "Undecided",
        checks: [{ label: "Output matches the sample run (Verify)", passed: false, detail: "Line 2 differs." }],
      },
    }));
    renderAt(PATH);
    await verified();

    await userEvent.click(screen.getByRole("button", { name: "Submit build" }));

    expect(await screen.findByText(/Line 2 differs/)).toBeInTheDocument();
    expect(screen.getByText("Not yet")).toBeInTheDocument();
  });

  it("says so when a build was submitted before", async () => {
    stubApi(routes({ [`GET ${API}`]: { ...build, submitted: true } }));
    renderAt(PATH);

    expect(await screen.findByText(/already submitted/i)).toBeInTheDocument();
  });

  it("shows an error if the server cannot take it", async () => {
    stubApi(routes({ "POST /api/v1/learners/me/attempts": new Response(JSON.stringify({ detail: "Too large." }), { status: 413 }) }));
    renderAt(PATH);
    await verified();

    await userEvent.click(screen.getByRole("button", { name: "Submit build" }));

    expect(await screen.findByText("Too large.")).toBeInTheDocument();
  });
});

describe("reset", () => {
  it("asks first, and says evidence stays", async () => {
    const calls = stubApi(routes());
    renderAt(PATH);

    await userEvent.click(await screen.findByRole("button", { name: "Reset build" }));

    expect(within(screen.getByRole("alertdialog")).getByText(/stays in your ledger/)).toBeInTheDocument();
    await userEvent.click(within(screen.getByRole("alertdialog")).getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(calls.some((c) => c.url.endsWith("build:reset"))).toBe(false);
  });

  it("puts the starter back", async () => {
    const calls = stubApi(routes({ [`GET ${DRAFT}`]: { files: { "checkin.py": "# saved", "ownership-note.txt": "Note" } } }));
    renderAt(PATH);
    await screen.findByLabelText("checkin.py code");

    await userEvent.click(screen.getByRole("button", { name: "Reset build" }));
    await userEvent.click(within(screen.getByRole("alertdialog")).getByRole("button", { name: "Reset build" }));

    await waitFor(() => expect(screen.getByLabelText("checkin.py code")).toHaveValue("# Starter"));
    expect(screen.getByLabelText("Ownership note")).toHaveValue("");
    expect(calls.some((c) => c.method === "POST" && c.url.endsWith("build:reset"))).toBe(true);
  });
});

describe("course map", () => {
  function mapWith(buildSummary: object) {
    return {
      "GET /api/v1/courses/python": { ...courseMap, stages: [{ ...courseMap.stages[0], build: buildSummary }] },
      "GET /api/v1/learners/me/proficiency": new Response("{}", { status: 500 }),
    };
  }

  it("links an unlocked, written build", async () => {
    stubApi(mapWith({ title: "Check-in", kind: "script", locked: false, pending_units: [], authored: true, status: "draft" }));
    renderAt("/courses/python");

    expect(await screen.findByRole("link", { name: /Check-in/ })).toHaveAttribute("href", "/courses/python/stages/0/build");
  });

  it("does not link a locked build", async () => {
    stubApi(mapWith({ title: "Check-in", kind: "script", locked: true, pending_units: ["PY-0.1"], authored: true, status: "draft" }));
    renderAt("/courses/python");

    await screen.findByText(/Locked until PY-0\.1/);
    expect(screen.queryByRole("link", { name: /Check-in/ })).not.toBeInTheDocument();
  });

  it("says when an unlocked build is not written yet", async () => {
    stubApi(mapWith({ title: "Stage 0 build", kind: "script", locked: false, pending_units: [], authored: false, status: null }));
    renderAt("/courses/python");

    expect(await screen.findByText("Not written yet")).toBeInTheDocument();
  });
});

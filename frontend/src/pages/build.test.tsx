import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { courseMap } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";

// CodeMirror and xterm need a real browser; the Playwright walk covers them.
vi.mock("../lesson/CodeEditor", () => ({
  CodeEditor: ({ value, onChange, label, language = "python" }: { value: string; onChange: (v: string) => void; label: string; language?: string }) => (
    <textarea aria-label={label} data-language={language} defaultValue={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));
vi.mock("../lesson/RunTerminal", () => ({
  RunTerminal: ({ entry, getFiles }: { entry?: string; getFiles: () => Record<string, string> }) => (
    <button type="button" onClick={() => document.body.setAttribute("data-ran", `${entry}:${JSON.stringify(getFiles())}`)}>
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
  stage_label: "Module 0",
  title: "Pantry intake check-in script",
  kind: "script",
  maturity: "P1",
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
    stubApi({ [`GET ${API}`]: new Response(JSON.stringify({ detail: "The build for Module 0 is not written yet." }), { status: 404 }) });
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
    expect(screen.queryByText(/Module 600/)).not.toBeInTheDocument();
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
    expect(screen.getByText("P1 · Module build")).toBeInTheDocument();
    expect((await screen.findByText("the desk")).tagName).toBe("STRONG");
    expect(screen.getByText(/--- CHECK-IN SLIP ---/)).toBeInTheDocument();
    expect(within(await requirements()).getAllByRole("listitem")).toHaveLength(3);
    expect(screen.getByRole("button", { name: "checkin.py" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "README.md" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByLabelText("Code ownership note")).toBeInTheDocument();
    const proves = screen.getByRole("region", { name: "What this build proves" });
    expect(within(proves).getByText("Run a script")).toBeInTheDocument();
  });

  it("colours only Python files; the README is plain text", async () => {
    stubApi(routes());
    renderAt(PATH);

    expect(await screen.findByLabelText("checkin.py code")).toHaveAttribute("data-language", "python");
    await userEvent.click(screen.getByRole("button", { name: "README.md" }));
    expect(screen.getByLabelText("README.md code")).toHaveAttribute("data-language", "text");
  });

  it("has no Socratic README button any more (owner 2B, ADR-0028)", async () => {
    stubApi(routes());
    renderAt(PATH);

    const axis = await screen.findByRole("complementary", { name: "AXIS facilitator" });
    expect(within(axis).queryByRole("button", { name: /about my README/i })).not.toBeInTheDocument();
  });

  it("asks for one real run in the README checklist (owner 1A)", async () => {
    stubApi(routes());
    renderAt(PATH);

    expect(await screen.findByText(/Paste one real run/)).toBeInTheDocument();
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

    expect(document.body.getAttribute("data-ran")).toBe(`checkin.py:${JSON.stringify({ "checkin.py": "# Starter" })}`);
  });

  it("runs every Python file of a multi-file build, from its entry", async () => {
    const files = [...build.files, { path: "slip.py", starter: ["# Slip"] }];
    stubApi(routes({ [`GET ${API}`]: { ...build, files } }));
    renderAt(PATH);

    await userEvent.click(await screen.findByRole("button", { name: "slip.py" }));
    fireEvent.change(screen.getByLabelText("slip.py code"), { target: { value: "# edited slip" } });
    await userEvent.click(screen.getByRole("button", { name: "Terminal" }));

    expect(document.body.getAttribute("data-ran")).toBe(
      `checkin.py:${JSON.stringify({ "checkin.py": "# Starter", "slip.py": "# edited slip" })}`,
    );
  });

  it("restores saved work and the saved note", async () => {
    stubApi(routes({ [`GET ${DRAFT}`]: { files: { "checkin.py": "# saved", "ownership-note.txt": "My saved note" } } }));
    renderAt(PATH);

    expect(await screen.findByLabelText("checkin.py code")).toHaveValue("# saved");
    expect(screen.getByLabelText("Code ownership note")).toHaveValue("My saved note");
  });

  it("saves work and the note together", async () => {
    const calls = stubApi(routes());
    renderAt(PATH);

    fireEvent.change(await screen.findByLabelText("Code ownership note"), { target: { value: "My note" } });

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    const saved = JSON.parse(calls.find((c) => c.method === "PUT")!.body!) as { files: Record<string, string> };
    expect(saved.files).toEqual({
      "checkin.py": "# Starter",
      "README.md": "# Readme",
      "ownership-note.txt": "My note",
      "review-note.txt": "",
    });
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

  it("editing another Python file clears Verify too, since the checks run it", async () => {
    const files = [...build.files, { path: "slip.py", starter: ["# Slip"] }];
    stubApi(routes({ [`GET ${API}`]: { ...build, files } }));
    renderAt(PATH);

    await userEvent.click(await screen.findByRole("button", { name: "Verify" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Submit build" })).toBeEnabled());
    await userEvent.click(screen.getByRole("button", { name: "slip.py" }));

    fireEvent.change(screen.getByLabelText("slip.py code"), { target: { value: "# edited" } });

    await waitFor(() => expect(screen.getByRole("button", { name: "Submit build" })).toBeDisabled());
  });

  it("editing the README keeps Verify", async () => {
    const calls = stubApi(routes());
    renderAt(PATH);

    await userEvent.click(await screen.findByRole("button", { name: "Verify" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Submit build" })).toBeEnabled());
    await userEvent.click(screen.getByRole("button", { name: "README.md" }));
    const checksBefore = bodies(calls, checkUrl).length;

    fireEvent.change(screen.getByLabelText("README.md code"), { target: { value: "# edited" } });

    // Wait for the page to re-check the edited work, not for a fixed time.
    await waitFor(() => expect(bodies(calls, checkUrl).length).toBeGreaterThan(checksBefore));
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
    fireEvent.change(await screen.findByLabelText("Code ownership note"), { target: { value: "I wrote it myself." } });
    await verified();

    await userEvent.click(screen.getByRole("button", { name: "Submit build" }));

    expect(await screen.findByText("This build is in your ledger.")).toBeInTheDocument();
    const [attempt] = bodies(calls, "/api/v1/learners/me/attempts");
    expect(attempt).toEqual({
      exercise_id: "python/stage-0/build",
      activity: "build",
      files: { "checkin.py": "# Starter", "README.md": "# Readme" },
      ownership_note: "I wrote it myself.",
      review_note: "",
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
    expect(screen.getByLabelText("Code ownership note")).toHaveValue("");
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
    stubApi(mapWith({ title: "Check-in", kind: "script", maturity: "P1", locked: false, pending_units: [], authored: true, status: "draft" }));
    renderAt("/courses/python");

    expect(await screen.findByRole("link", { name: /Check-in/ })).toHaveAttribute("href", "/courses/python/stages/0/build");
  });

  it("shows the build's maturity beside its kind", async () => {
    stubApi(mapWith({ title: "Check-in", kind: "script", maturity: "P1", locked: true, pending_units: ["PY-0.1"], authored: true, status: "draft" }));
    renderAt("/courses/python");

    expect(await screen.findByText("P1 · Module build")).toBeInTheDocument();
    expect(screen.getByText("Script")).toBeInTheDocument();
  });

  it("does not link a locked build", async () => {
    stubApi(mapWith({ title: "Check-in", kind: "script", locked: true, pending_units: ["PY-0.1"], authored: true, status: "draft" }));
    renderAt("/courses/python");

    await screen.findByText(/Locked until PY-0\.1/);
    expect(screen.queryByRole("link", { name: /Check-in/ })).not.toBeInTheDocument();
  });

  it("says when an unlocked build is not written yet", async () => {
    stubApi(mapWith({ title: "Module 0 build", kind: "script", locked: false, pending_units: [], authored: false, status: null }));
    renderAt("/courses/python");

    expect(await screen.findByText("Not written yet")).toBeInTheDocument();
  });
});

describe("README work (SPEC-15 section 9)", () => {
  const SAMPLE = "readme-sample";
  const readmeBuild = {
    ...build,
    requirements: [
      ...build.requirements,
      { id: "readme-sections", label: "README answers the five checklist points", unit_id: "PY-0.4" },
      { id: "readme-run", label: "README gives the exact command for checkin.py", unit_id: "PY-0.4" },
      { id: SAMPLE, label: "README's sample run is real (Verify)", unit_id: "PY-0.4" },
      { id: "review", label: "Review note written", unit_id: "PY-0.4" },
    ],
  };
  const DRAFT_README = `${ME}/build:draft-readme`;
  const drafted = { markdown: "# Check-in\n\n## What it does\n\nAXIS wrote this.", status: "drafted", model: "offline-mock" };

  /** The server's answers: sections, run and review follow what the learner typed; the sample needs Verify. */
  function readmeRoutes(extra: Record<string, unknown> = {}) {
    return routes({
      [`GET ${API}`]: readmeBuild,
      [`POST ${ME}/build:check`]: (_url: URL, init?: RequestInit) => {
        const body = JSON.parse(String(init?.body)) as { run_checks: boolean; review_note?: string };
        return results({
          plan: true,
          sample: body.run_checks ? true : null,
          note: true,
          "readme-sections": true,
          "readme-run": true,
          [SAMPLE]: body.run_checks ? true : null,
          review: (body.review_note ?? "").length >= 20,
        });
      },
      [`POST ${DRAFT_README}`]: drafted,
      ...extra,
    });
  }

  const openReadme = async () => userEvent.click(await screen.findByRole("button", { name: "README.md" }));
  const readmeText = () => screen.getByLabelText("README.md code");
  const points = async () => within(await screen.findByRole("region", { name: "README checklist" })).getAllByRole("listitem");

  it("links to TW Module 0 from the README tab and asks to come back to this build", async () => {
    stubApi(readmeRoutes());
    renderAt(PATH);

    await screen.findByLabelText("checkin.py code");
    expect(screen.queryByRole("link", { name: /Learn it in TW Module 0/ })).not.toBeInTheDocument();
    await openReadme();

    const link = screen.getByRole("link", { name: "Stuck on the README? Learn it in TW Module 0" });
    const url = new URL(link.getAttribute("href") ?? "", "http://test");
    expect(url.pathname).toBe("/units/TW-0.1");
    expect(url.searchParams.get("back")).toBe(PATH);
  });

  it("drafts into the README tab straight away when the README is still the starter", async () => {
    const calls = stubApi(readmeRoutes());
    renderAt(PATH);
    await openReadme();

    await userEvent.click(screen.getByRole("button", { name: "Draft my README" }));

    await waitFor(() => expect(readmeText()).toHaveValue(drafted.markdown));
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(bodies(calls, DRAFT_README)).toEqual([{ files: { "checkin.py": "# Starter", "README.md": "# Readme" } }]);
    expect(bodies(calls, "/api/v1/learners/me/attempts")).toEqual([]);
  });

  it("asks before replacing a README the learner has changed, and Cancel keeps it", async () => {
    const calls = stubApi(readmeRoutes());
    renderAt(PATH);
    await openReadme();
    fireEvent.change(readmeText(), { target: { value: "# My own words" } });

    await userEvent.click(screen.getByRole("button", { name: "Draft my README" }));

    const dialog = screen.getByRole("alertdialog", { name: "Replace your README" });
    expect(within(dialog).getByText("Replace your README with an AXIS draft?")).toBeInTheDocument();
    expect(bodies(calls, DRAFT_README)).toEqual([]);
    await userEvent.click(within(dialog).getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(readmeText()).toHaveValue("# My own words");
  });

  it("replaces the README once confirmed, sending the current files", async () => {
    const calls = stubApi(readmeRoutes());
    renderAt(PATH);
    await openReadme();
    fireEvent.change(readmeText(), { target: { value: "# My own words" } });
    await userEvent.click(screen.getByRole("button", { name: "Draft my README" }));

    await userEvent.click(within(screen.getByRole("alertdialog")).getByRole("button", { name: "Replace README" }));

    await waitFor(() => expect(readmeText()).toHaveValue(drafted.markdown));
    expect(bodies(calls, DRAFT_README)).toEqual([{ files: { "checkin.py": "# Starter", "README.md": "# My own words" } }]);
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });

  it("shows a plain error when the draft fails and leaves the README alone", async () => {
    stubApi(readmeRoutes({ [`POST ${DRAFT_README}`]: new Response(JSON.stringify({ detail: "AXIS could not draft the README right now." }), { status: 502 }) }));
    renderAt(PATH);
    await openReadme();

    await userEvent.click(screen.getByRole("button", { name: "Draft my README" }));

    expect(await screen.findByText("AXIS could not draft the README right now.")).toBeInTheDocument();
    expect(readmeText()).toHaveValue("# Readme");
  });

  it("lists the five README points with met, missing and not checked yet", async () => {
    stubApi(
      readmeRoutes({
        [`POST ${ME}/build:check`]: results(
          { plan: true, sample: null, note: true, "readme-sections": false, "readme-run": true, [SAMPLE]: null, review: false },
          { "readme-sections": "Write at least 4 words under 'What you need first'." },
        ),
      }),
    );
    renderAt(PATH);

    await waitFor(async () => expect((await points())[1]?.textContent).toMatch(/Missing/));
    const text = (await points()).map((row) => row.textContent ?? "");
    expect(text).toHaveLength(5);
    expect(text[0]).toMatch(/What it does.*Met/);
    expect(text[1]).toMatch(/What you need first.*Write at least 4 words.*Missing/);
    expect(text[2]).toMatch(/How to run it.*Not checked yet/);
    expect(text[3]).toMatch(/A sample run.*Not checked yet/);
    expect(text[4]).toMatch(/Limits.*Not checked yet/);
  });

  it("shows every point met once the server says so, and the sample run only after Verify", async () => {
    stubApi(readmeRoutes());
    renderAt(PATH);

    await waitFor(async () => expect((await points())[0]?.textContent).toMatch(/Met/));
    expect((await points())[3]?.textContent).toMatch(/A sample run.*Not checked yet/);
    await userEvent.click(screen.getByRole("button", { name: "Verify" }));

    await waitFor(async () => expect((await points())[3]?.textContent).toMatch(/A sample run.*Met/));
    for (const row of await points()) expect(row.textContent).toMatch(/Met/);
  });

  it("shows why the sample run was not met after Verify", async () => {
    stubApi(
      readmeRoutes({
        [`POST ${ME}/build:check`]: (_url: URL, init?: RequestInit) =>
          (JSON.parse(String(init?.body)) as { run_checks: boolean }).run_checks
            ? results({ plan: true, sample: true, note: true, "readme-sections": true, "readme-run": true, [SAMPLE]: false, review: false }, { [SAMPLE]: "Your script did not print: `Name: ADA`" })
            : results({ plan: true, sample: null, note: true, "readme-sections": true, "readme-run": true, [SAMPLE]: null, review: false }),
      }),
    );
    renderAt(PATH);

    await userEvent.click(await screen.findByRole("button", { name: "Verify" }));

    expect((await screen.findAllByText("Your script did not print: `Name: ADA`")).length).toBeGreaterThan(0);
    await waitFor(async () => expect((await points())[3]?.textContent).toMatch(/A sample run.*Missing/));
  });

  it("editing the README makes an old sample run result stale", async () => {
    stubApi(readmeRoutes());
    renderAt(PATH);
    fireEvent.change(await screen.findByLabelText("README review note"), { target: { value: "I fixed the command after running it." } });
    fireEvent.change(screen.getByLabelText("Code ownership note"), { target: { value: "I wrote it myself." } });
    await userEvent.click(screen.getByRole("button", { name: "Verify" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Submit build" })).toBeEnabled());

    await openReadme();
    fireEvent.change(readmeText(), { target: { value: "# A different README" } });

    await waitFor(() => expect(screen.getByRole("button", { name: "Submit build" })).toBeDisabled());
    await waitFor(async () => expect((await points())[3]?.textContent).toMatch(/Not checked yet/));
  });

  it("keeps the review note with the README checklist, apart from the code ownership note, with its prompt, and sends it on check and submit", async () => {
    const calls = stubApi(readmeRoutes());
    renderAt(PATH);
    const ownership = await screen.findByLabelText("Code ownership note");
    const review = screen.getByLabelText("README review note");
    expect(within(screen.getByRole("region", { name: "README checklist" })).getByLabelText("README review note")).toBe(review);
    expect(ownership).not.toBe(review);
    expect(
      screen.getByText("What did you change in the README, and why? If AXIS drafted it, say what you fixed after running your script."),
    ).toBeInTheDocument();

    fireEvent.change(ownership, { target: { value: "I wrote it myself." } });
    fireEvent.change(review, { target: { value: "I fixed the command after running it." } });
    await userEvent.click(screen.getByRole("button", { name: "Verify" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Submit build" })).toBeEnabled());
    await userEvent.click(screen.getByRole("button", { name: "Submit build" }));

    await screen.findByText("This build is in your ledger.");
    expect(bodies(calls, checkUrl).some((b) => b.review_note === "I fixed the command after running it.")).toBe(true);
    const [attempt] = bodies(calls, "/api/v1/learners/me/attempts");
    expect(attempt?.review_note).toBe("I fixed the command after running it.");
    expect(attempt?.ownership_note).toBe("I wrote it myself.");
  });

  it("saves the review note in the draft", async () => {
    const calls = stubApi(readmeRoutes());
    renderAt(PATH);
    fireEvent.change(await screen.findByLabelText("README review note"), { target: { value: "I added the command." } });

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    const saved = JSON.parse(calls.find((c) => c.method === "PUT")!.body!) as { files: Record<string, string> };
    expect(saved.files["review-note.txt"]).toBe("I added the command.");
  });

  it("restores a saved review note without turning it into a file tab", async () => {
    stubApi(readmeRoutes({ [`GET ${DRAFT}`]: { files: { "checkin.py": "# saved", "review-note.txt": "Saved review" } } }));
    renderAt(PATH);

    expect(await screen.findByLabelText("README review note")).toHaveValue("Saved review");
    expect(screen.queryByRole("button", { name: "review-note.txt" })).not.toBeInTheDocument();
  });

  it("clears the review note on reset", async () => {
    stubApi(readmeRoutes({ [`GET ${DRAFT}`]: { files: { "review-note.txt": "Saved review" } } }));
    renderAt(PATH);
    await screen.findByLabelText("README review note");

    await userEvent.click(screen.getByRole("button", { name: "Reset build" }));
    await userEvent.click(within(screen.getByRole("alertdialog")).getByRole("button", { name: "Reset build" }));

    await waitFor(() => expect(screen.getByLabelText("README review note")).toHaveValue(""));
  });

  it("never says the word stage to the learner", async () => {
    stubApi(readmeRoutes());
    renderAt(PATH);
    await openReadme();

    expect(document.body.textContent).not.toMatch(/\bstages?\b/i);
  });
});

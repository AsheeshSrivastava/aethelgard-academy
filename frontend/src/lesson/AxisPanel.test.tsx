import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { stubApi } from "../test/harness";
import { AxisPanel } from "./AxisPanel";

// ADR-0039 / SPEC-31 R6 to R9: the starting mode is suggested by the step's activity, the learner can
// change it, builds stay Socratic, and the request carries the mode the learner sees.
const STREAM = "POST /api/v1/axis/stream";

function done() {
  const text = `event: done\ndata: ${JSON.stringify({ assistance_level: "none", cited_concepts: [] })}\n\n`;
  return new Response(text, { status: 200, headers: { "content-type": "text/event-stream" } });
}

function setup(step: string, props: { socraticOnly?: boolean } = {}, reply: () => unknown = done) {
  const calls = stubApi({ [STREAM]: reply, "GET /api/v1/axis/status": { course_reference: "ready" } });
  const panel = (at: string) => <AxisPanel unitId="PY-0.1" step={at} getCode={() => undefined} {...props} />;
  const view = render(panel(step));
  return {
    user: userEvent.setup(),
    moveTo: (at: string) => view.rerender(panel(at)),
    sent: () => calls.filter((c) => c.url === "/api/v1/axis/stream").map((c) => JSON.parse(c.body ?? "{}")),
  };
}

const radio = (name: string) => screen.getByRole("radio", { name });
const chosen = () => screen.getAllByRole("radio").filter((r) => (r as HTMLInputElement).checked).map((r) => r.parentElement?.textContent);

async function ask(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Message AXIS"), "Why?");
  await waitFor(() => expect(screen.getByRole("button", { name: "Send" })).toBeEnabled());
  await user.click(screen.getByRole("button", { name: "Send" }));
}

describe("SPEC-31 R6: the suggested starting mode", () => {
  it.each([
    ["explain", "Explain", "Coach"],
    ["video", "Explain", "Coach"],
    ["specify", "Specify", "Hybrid"],
    ["decompose", "Decompose", "Hybrid"],
    ["modify", "Modify", "Hybrid"],
    ["playground", "Modify", "Hybrid"],
    ["evaluate", "Evaluate", "Hybrid"],
    ["direct", "Direct", "Hybrid"],
    ["predict", "Predict", "Socratic"],
    ["trace", "Trace", "Socratic"],
    ["debug-validate", "Debug & Validate", "Socratic"],
    // An activity name outside the list falls back to Socratic.
    ["build", "Build", "Socratic"],
    // An unknown step is already mapped to Explain by activityFor.
    ["something-new", "Explain", "Coach"],
  ])("step %s (%s) starts in %s and sends it", async (step, activity, mode) => {
    const { user, sent } = setup(step);

    expect(chosen()).toEqual([mode]);
    await ask(user);

    await waitFor(() => expect(sent()).toHaveLength(1));
    expect(sent()[0]).toMatchObject({ mode, current_activity: activity, page: step });
  });
});

describe("SPEC-31 R7: the learner's choice", () => {
  it("holds while they stay on the step", async () => {
    const { user, sent, moveTo } = setup("explain");

    await user.click(radio("Socratic"));
    await ask(user);
    moveTo("explain"); // the page renders again on the same step
    await ask(user);

    expect(chosen()).toEqual(["Socratic"]);
    await waitFor(() => expect(sent().map((b) => b.mode)).toEqual(["Socratic", "Socratic"]));
  });

  it("gives way to the suggestion of a new step, and is not brought back on return", async () => {
    const { user, sent, moveTo } = setup("explain");

    await user.click(radio("Socratic"));
    moveTo("specify");
    expect(chosen()).toEqual(["Hybrid"]);
    await ask(user);
    moveTo("explain");
    expect(chosen()).toEqual(["Coach"]);
    await ask(user);

    await waitFor(() => expect(sent().map((b) => b.mode)).toEqual(["Hybrid", "Coach"]));
  });

  it("re-suggests when two steps share a suggestion but the learner had chosen another mode", async () => {
    const { user, moveTo } = setup("predict");

    await user.click(radio("Coach"));
    moveTo("trace");

    expect(chosen()).toEqual(["Socratic"]);
  });
});

describe("SPEC-31 section 6: changes while a reply is streaming", () => {
  function held() {
    const releases: (() => void)[] = [];
    const reply = () => new Promise<Response>((resolve) => releases.push(() => resolve(done())));
    return { reply, release: () => releases.shift()?.() };
  }

  it("a step change mid-reply leaves the sent request alone and the next one uses the new suggestion", async () => {
    const { reply, release } = held();
    const { user, sent, moveTo } = setup("explain", {}, reply);

    await ask(user);
    await waitFor(() => expect(sent()).toHaveLength(1));
    moveTo("trace");
    expect(chosen()).toEqual(["Socratic"]);
    release();
    await ask(user);

    await waitFor(() => expect(sent().map((b) => [b.mode, b.current_activity])).toEqual([
      ["Coach", "Explain"],
      ["Socratic", "Trace"],
    ]));
    release();
  });

  it("a mode change mid-reply applies from the next question", async () => {
    const { reply, release } = held();
    const { user, sent } = setup("explain", {}, reply);

    await ask(user);
    await waitFor(() => expect(sent()).toHaveLength(1));
    await user.click(radio("Hybrid"));
    release();
    await ask(user);

    await waitFor(() => expect(sent().map((b) => b.mode)).toEqual(["Coach", "Hybrid"]));
    release();
  });
});

describe("SPEC-31 R8: builds stay Socratic", () => {
  it.each(["build", "explain", "specify"])("on step %s there is no picker and the request is Socratic", async (step) => {
    const { user, sent } = setup(step, { socraticOnly: true });

    expect(screen.queryByRole("radio")).not.toBeInTheDocument();
    expect(screen.getByText("Socratic during builds")).toBeInTheDocument();
    await ask(user);

    await waitFor(() => expect(sent()[0]?.mode).toBe("Socratic"));
  });
});

describe("SPEC-31 R9: the request carries the mode the learner chose", () => {
  it.each(["Socratic", "Hybrid", "Coach"])("sends %s when chosen, whatever the activity suggests", async (mode) => {
    const { user, sent } = setup("specify");

    await user.click(radio(mode));
    await ask(user);

    await waitFor(() => expect(sent()[0]).toMatchObject({ mode, current_activity: "Specify" }));
  });
});

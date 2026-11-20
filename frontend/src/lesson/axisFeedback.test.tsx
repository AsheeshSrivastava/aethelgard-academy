import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { stubApi } from "../test/harness";
import { AxisPanel } from "./AxisPanel";

// SPEC-29 R27, R28: the thumbs control under each finished AXIS answer.
const VOTES = "POST /api/v1/learners/me/interactions";

function sse(events: [string, object][]) {
  const text = events.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join("");
  return new Response(text, { status: 200, headers: { "content-type": "text/event-stream" } });
}

function answer(id: string, text = "What type?") {
  return () =>
    sse([
      ["token", { text }],
      ["citation", { concept_id: "c", title: "Standard streams", doc_url: "https://docs.python.org/3/" }],
      ["done", { assistance_level: "small_hint", cited_concepts: ["c"], source_state: "course", interaction_id: id }],
    ]);
}

function setup(routes: Record<string, unknown>) {
  const calls = stubApi({ "POST /api/v1/axis/stream": answer("T1"), [VOTES]: null, ...routes });
  render(<AxisPanel unitId="PY-0.1" step="predict" getCode={() => undefined} />);
  return { calls, user: userEvent.setup() };
}

async function askQuestion(user: ReturnType<typeof userEvent.setup>, question = "Why?") {
  await user.type(screen.getByLabelText("Message AXIS"), question);
  await user.click(screen.getByRole("button", { name: "Send" }));
}

function votes(calls: { method: string; url: string; body?: string }[]) {
  return calls
    .filter((c) => c.method === "POST" && c.url === "/api/v1/learners/me/interactions")
    .map((c) => JSON.parse(c.body ?? "{}"));
}

const helpful = () => screen.getByRole("button", { name: /Helpful/ });
const notHelpful = () => screen.getByRole("button", { name: /Not helpful/ });

describe("AXIS rating (thumbs)", () => {
  it("shows_no_rating_while_streaming", async () => {
    const { user } = setup({ "POST /api/v1/axis/stream": () => new Promise<Response>(() => {}) });
    await askQuestion(user);
    expect(await screen.findByText("Thinking…")).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Rate this answer" })).not.toBeInTheDocument();
  });

  it("shows_no_rating_on_error_or_blocked_turn", async () => {
    const { user } = setup({
      "POST /api/v1/axis/stream": () =>
        sse([
          ["token", { text: "Partial" }],
          ["error", { message: "Blocked." }],
        ]),
    });
    await askQuestion(user);
    expect(await screen.findByRole("alert")).toHaveTextContent("Blocked.");
    expect(screen.queryByRole("group", { name: "Rate this answer" })).not.toBeInTheDocument();
  });

  it("shows_no_rating_when_done_has_no_interaction_id", async () => {
    const { user } = setup({ "POST /api/v1/axis/stream": () => sse([["token", { text: "Hi" }], ["done", { assistance_level: "none", cited_concepts: [] }]]) });
    await askQuestion(user);
    expect(await screen.findByText("Hi")).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Rate this answer" })).not.toBeInTheDocument();
  });

  it("shows_two_buttons_in_a_labelled_group_after_done", async () => {
    const { user } = setup({});
    await askQuestion(user);
    const group = await screen.findByRole("group", { name: "Rate this answer" });
    expect(within(group).getAllByRole("button").map((b) => b.textContent)).toEqual(["Helpful", "Not helpful"]);
    expect(helpful()).toHaveAttribute("aria-pressed", "false");
    expect(notHelpful()).toHaveAttribute("aria-pressed", "false");
  });

  it("buttons_are_native_and_keyboard_operable", async () => {
    const { calls, user } = setup({});
    await askQuestion(user);
    await screen.findByRole("group", { name: "Rate this answer" });
    expect(helpful().tagName).toBe("BUTTON");
    expect(helpful()).toHaveAttribute("type", "button");
    expect(notHelpful().tagName).toBe("BUTTON");
    helpful().focus();
    await user.keyboard("{Enter}");
    await waitFor(() => expect(votes(calls)).toHaveLength(1));
    await user.tab();
    expect(notHelpful()).toHaveFocus();
    await user.keyboard(" ");
    await waitFor(() => expect(votes(calls)).toHaveLength(2));
    expect(votes(calls)[1]?.payload.vote).toBe("down");
  });

  it("pressing_helpful_posts_axis_feedback_with_the_done_interaction_id", async () => {
    const { calls, user } = setup({});
    await askQuestion(user);
    await screen.findByRole("group", { name: "Rate this answer" });
    await user.click(helpful());
    await waitFor(() => expect(votes(calls)).toEqual([{ event_type: "axis_feedback", payload: { turn_id: "T1", vote: "up" } }]));
  });

  it("pressed_state_is_shown_by_aria_pressed_and_a_tick_not_colour", async () => {
    const { user } = setup({});
    await askQuestion(user);
    await screen.findByRole("group", { name: "Rate this answer" });
    await user.click(helpful());
    await waitFor(() => expect(helpful()).toHaveAttribute("aria-pressed", "true"));
    expect(helpful()).toHaveTextContent("✓ Helpful");
    expect(helpful().className).toContain("axis-rate-chosen");
    expect(notHelpful()).toHaveAttribute("aria-pressed", "false");
    expect(notHelpful().textContent).toBe("Not helpful");
  });

  it("pressing_the_chosen_button_again_sends_clear", async () => {
    const { calls, user } = setup({});
    await askQuestion(user);
    await screen.findByRole("group", { name: "Rate this answer" });
    await user.click(helpful());
    await waitFor(() => expect(votes(calls)).toHaveLength(1));
    await user.click(helpful());
    await waitFor(() => expect(votes(calls)).toHaveLength(2));
    expect(votes(calls)[1]).toEqual({ event_type: "axis_feedback", payload: { turn_id: "T1", vote: "clear" } });
    expect(helpful()).toHaveAttribute("aria-pressed", "false");
    expect(helpful().textContent).toBe("Helpful");
  });

  it("switching_vote_sends_a_new_event", async () => {
    const { calls, user } = setup({});
    await askQuestion(user);
    await screen.findByRole("group", { name: "Rate this answer" });
    await user.click(helpful());
    await user.click(notHelpful());
    await waitFor(() => expect(votes(calls).map((v) => v.payload.vote)).toEqual(["up", "down"]));
    expect(notHelpful()).toHaveAttribute("aria-pressed", "true");
    expect(helpful()).toHaveAttribute("aria-pressed", "false");
  });

  it("status_says_thanks_after_save_and_error_after_failure", async () => {
    let fail = false;
    const { user } = setup({ [VOTES]: () => (fail ? new Response("{}", { status: 500 }) : null) });
    await askQuestion(user);
    const group = await screen.findByRole("group", { name: "Rate this answer" });
    const status = () => within(group.parentElement as HTMLElement).getByRole("status");
    await user.click(helpful());
    await waitFor(() => expect(status()).toHaveTextContent("Thanks, noted."));
    expect(status()).toHaveAttribute("aria-live", "polite");
    fail = true;
    await user.click(notHelpful());
    await waitFor(() => expect(status()).toHaveTextContent("Could not save your vote. Try again."));
  });

  it("a_failed_save_restores_the_previous_state_and_does_not_retry", async () => {
    let fail = false;
    const { calls, user } = setup({ [VOTES]: () => (fail ? new Response("{}", { status: 500 }) : null) });
    await askQuestion(user);
    await screen.findByRole("group", { name: "Rate this answer" });
    await user.click(helpful());
    await waitFor(() => expect(helpful()).toHaveAttribute("aria-pressed", "true"));
    fail = true;
    await user.click(notHelpful());
    await screen.findByText("Could not save your vote. Try again.");
    expect(helpful()).toHaveAttribute("aria-pressed", "true");
    expect(notHelpful()).toHaveAttribute("aria-pressed", "false");
    await new Promise((r) => setTimeout(r, 50));
    expect(votes(calls)).toHaveLength(2);
  });

  it("a_failed_vote_restores_the_last_confirmed_vote_and_never_says_thanks", async () => {
    let fail = false;
    const { user } = setup({ [VOTES]: () => (fail ? new Response("{}", { status: 503 }) : null) });
    await askQuestion(user);
    const group = await screen.findByRole("group", { name: "Rate this answer" });
    const status = () => within(group.parentElement as HTMLElement).getByRole("status");
    await user.click(helpful());
    await waitFor(() => expect(status()).toHaveTextContent("Thanks, noted."));
    fail = true;
    await user.click(helpful()); // would clear the confirmed vote, but the save fails
    await waitFor(() => expect(status()).toHaveTextContent("Could not save your vote. Try again."));
    expect(status()).not.toHaveTextContent("Thanks");
    expect(helpful()).toHaveAttribute("aria-pressed", "true"); // back to the last confirmed vote
    expect(helpful().textContent).toBe("✓ Helpful");
    expect(status()).toHaveAttribute("aria-live", "polite"); // the error is words in a polite status line, not colour
  });

  it("a_network_error_also_restores_the_previous_state", async () => {
    const { user } = setup({
      [VOTES]: () => {
        throw new Error("offline");
      },
    });
    await askQuestion(user);
    await screen.findByRole("group", { name: "Rate this answer" });
    await user.click(helpful());
    await screen.findByText("Could not save your vote. Try again.");
    expect(helpful()).toHaveAttribute("aria-pressed", "false");
  });

  it("a_pending_vote_does_not_disable_the_question_box", async () => {
    const { calls, user } = setup({ [VOTES]: () => new Promise<Response>(() => {}) });
    await askQuestion(user);
    await screen.findByRole("group", { name: "Rate this answer" });
    await user.click(helpful());
    await waitFor(() => expect(votes(calls)).toHaveLength(1));
    const box = screen.getByLabelText("Message AXIS");
    expect(box).toBeEnabled();
    await user.type(box, "Next");
    expect(box).toHaveValue("Next");
    expect(screen.getByRole("button", { name: "Send" })).toBeEnabled();
  });

  it("each_answer_has_its_own_rating", async () => {
    let n = 0;
    const { calls, user } = setup({ "POST /api/v1/axis/stream": () => answer(`T${++n}`)() });
    await askQuestion(user, "One");
    await screen.findByRole("group", { name: "Rate this answer" });
    await askQuestion(user, "Two");
    await waitFor(() => expect(screen.getAllByRole("group", { name: "Rate this answer" })).toHaveLength(2));
    const groups = screen.getAllByRole("group", { name: "Rate this answer" });
    const first = groups[0] as HTMLElement;
    const second = groups[1] as HTMLElement;
    await user.click(within(first).getByRole("button", { name: "Helpful" }));
    await waitFor(() => expect(within(first).getByRole("button", { name: /Helpful/ })).toHaveAttribute("aria-pressed", "true"));
    expect(within(second).getByRole("button", { name: "Helpful" })).toHaveAttribute("aria-pressed", "false");
    await user.click(within(second).getByRole("button", { name: "Not helpful" }));
    await waitFor(() => expect(votes(calls)).toHaveLength(2));
    expect(votes(calls).map((v) => [v.payload.turn_id, v.payload.vote])).toEqual([
      ["T1", "up"],
      ["T2", "down"],
    ]);
    expect(within(first).getByRole("button", { name: /Helpful/ })).toHaveAttribute("aria-pressed", "true");
  });

  it("rapid_presses_last_press_wins_on_screen", async () => {
    const resolvers: (() => void)[] = [];
    const { calls, user } = setup({
      [VOTES]: () =>
        new Promise<Response>((resolve) => {
          resolvers.push(() => resolve(new Response(null, { status: 204 })));
        }),
    });
    await askQuestion(user);
    await screen.findByRole("group", { name: "Rate this answer" });
    await user.click(helpful());
    await user.click(notHelpful());
    await waitFor(() => expect(votes(calls)).toHaveLength(2));
    resolvers[1]?.();
    resolvers[0]?.();
    await screen.findByText("Thanks, noted.");
    expect(notHelpful()).toHaveAttribute("aria-pressed", "true");
    expect(helpful()).toHaveAttribute("aria-pressed", "false");
  });

  it("answer_text_and_citations_are_unchanged_by_rating", async () => {
    const { calls, user } = setup({});
    await askQuestion(user);
    await screen.findByRole("group", { name: "Rate this answer" });
    const before = document.querySelector(".axis-messages")?.querySelector(".message-axis");
    const textBefore = before?.querySelector("p")?.textContent;
    await user.click(helpful());
    await waitFor(() => expect(votes(calls)).toHaveLength(1));
    expect(screen.getByText("What type?")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Standard streams" })).toHaveAttribute("href", "https://docs.python.org/3/");
    expect(document.querySelector(".message-axis p")?.textContent).toBe(textBefore);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});

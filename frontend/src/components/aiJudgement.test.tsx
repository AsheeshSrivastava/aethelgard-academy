import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AiJudgement, type AiJudgementData } from "./AiJudgement";

const judged: AiJudgementData = {
  status: "judged",
  verdict: "Shaky",
  ideas: [
    { id: "returns-text", text: "input() gives back text.", met: true },
    { id: "math-needs-conversion", text: "Math on text needs a number first.", met: false },
  ],
  feedback: "Add what happens when you do math on the text.",
  model: "gemini-3.8-flash",
  reason: null,
  message: "",
  interaction_id: "01J9ZK3Y4D8Q2W6X0ANSWER001",
};

const notJudged: AiJudgementData = {
  status: "not_judged",
  verdict: null,
  ideas: [],
  feedback: null,
  model: null,
  reason: "provider_refused",
  message: "The AI provider refused the request (quota, rate limit or key). This was not judged.",
  interaction_id: "01J9ZK3Y4D8Q2W6X0ANSWER002",
};

describe("AI judgement (SPEC-18 section 7)", () => {
  it("shows the verdict, each idea as met or missed, the feedback and the annotation", () => {
    render(<AiJudgement judgement={judged} onDispute={() => undefined} />);

    expect(screen.getByText("Shaky")).toBeInTheDocument();
    const items = screen.getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("Met input() gives back text.");
    expect(items[1]).toHaveTextContent("Missed Math on text needs a number first.");
    expect(screen.getByText("Add what happens when you do math on the text.")).toBeInTheDocument();
    expect(screen.getByText("Judged by AXIS (gemini-3.8-flash). AI can be wrong.")).toBeInTheDocument();
  });

  it("lets the learner dispute once", async () => {
    const dispute = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<AiJudgement judgement={judged} onDispute={dispute} />);

    await user.click(screen.getByRole("button", { name: "This seems wrong" }));

    expect(await screen.findByText("Thanks. Noted for review.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "This seems wrong" })).not.toBeInTheDocument();
    expect(dispute).toHaveBeenCalledTimes(1);
  });

  it("keeps the button when the dispute did not send", async () => {
    const user = userEvent.setup();
    render(<AiJudgement judgement={judged} onDispute={() => Promise.reject(new Error("offline"))} />);

    await user.click(screen.getByRole("button", { name: "This seems wrong" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("did not send");
    expect(screen.getByRole("button", { name: "This seems wrong" })).toBeEnabled();
  });

  it("has no button when no handler is given", () => {
    render(<AiJudgement judgement={judged} />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows the plain message for a not-judged answer, with no verdict and no button", () => {
    render(<AiJudgement judgement={notJudged} onDispute={() => undefined} />);

    expect(screen.getByText(notJudged.message)).toBeInTheDocument();
    expect(screen.queryByText("Solid")).not.toBeInTheDocument();
    expect(screen.queryByText("Shaky")).not.toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.queryByText(/AI can be wrong/)).not.toBeInTheDocument();
  });
});

import { fireEvent, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { renderAt, stubApi } from "../test/harness";

const BASE = "/api/v1/settings/models";

function overview(over: Partial<Record<string, unknown>> = {}) {
  return {
    active: "local",
    judge_profile_id: null,
    mock: false,
    cap_usd: 5,
    month_spend_usd: 0.0123,
    profiles: [
      { id: "local", label: "Local model", kind: "openai_compatible", base_url: "http://127.0.0.1:8888/v1",
        model: "auto", paid: false, price_per_million: null, estimate_per_question_usd: 0,
        key_env: "UNSLOTH_STUDIO_AUTH_TOKEN", key_set: true },
      { id: "openai", label: "OpenAI", kind: "openai_compatible", base_url: "https://api.openai.com/v1",
        model: "gpt-6-luna", paid: true, price_per_million: { input: 0.1, output: 0.5 },
        estimate_per_question_usd: 0.00035, key_env: "OPENAI_API_KEY", key_set: false },
      { id: "gemini", label: "Gemini", kind: "gemini", base_url: null, model: "gemini-3.8-flash", paid: true,
        price_per_million: { input: 0.75, output: 3.75 }, estimate_per_question_usd: 0.002625,
        key_env: "GEMINI_API_KEY", key_set: true },
    ],
    ...over,
  };
}

const usage = {
  session_id: "run-1",
  session: [
    { profile_id: "local", model: "qwen3.5-9b", calls: 3, input_tokens: null, output_tokens: null, cost_usd: 0, estimated: false },
    { profile_id: "gemini", model: "gemini-3.8-flash-001", calls: 2, input_tokens: 800, output_tokens: 40, cost_usd: 0.00075, estimated: false },
  ],
  month: [
    { profile_id: "gemini", model: "gemini-3.8-flash-001", calls: 9, input_tokens: 4000, output_tokens: 200, cost_usd: 0.0123, estimated: false },
  ],
  month_spend_usd: 0.0123,
  cap_usd: 5,
};

function routes(extra: Record<string, unknown> = {}) {
  return {
    "GET /api/v1/features": { test_mode: false },
    [`GET ${BASE}`]: overview(),
    [`GET ${BASE}/usage`]: usage,
    ...extra,
  };
}

describe("Model settings page (SPEC-17 section 7)", () => {
  it("shows a card per profile with price and key status, and marks the active one", async () => {
    stubApi(routes());
    renderAt("/settings/models");

    const local = await screen.findByRole("region", { name: "Local model" });
    expect(within(local).getByText("Free")).toBeInTheDocument();
    expect(within(local).getByText("In use")).toBeInTheDocument();

    const openai = screen.getByRole("region", { name: "OpenAI" });
    expect(within(openai).getByText(/\$0\.10 in · \$0\.50 out per 1M tokens/)).toBeInTheDocument();
    expect(within(openai).getByText("Key set: no")).toBeInTheDocument();
    expect(within(openai).getByRole("button", { name: "Use OpenAI" })).toBeDisabled();

    const gemini = screen.getByRole("region", { name: "Gemini" });
    expect(within(gemini).getByText("Key set: yes")).toBeInTheDocument();
  });

  it("asks for confirmation with cost and privacy note before a paid switch", async () => {
    const calls = stubApi(routes({ [`PUT ${BASE}/active`]: overview({ active: "gemini" }) }));
    renderAt("/settings/models");

    fireEvent.click(await screen.findByRole("button", { name: "Use Gemini" }));
    const panel = screen.getByRole("dialog", { name: "Switch to Gemini" });
    expect(within(panel).getByText(/about \$0\.0026 per question/)).toBeInTheDocument();
    expect(within(panel).getByText(/Your code and questions are sent to Gemini\./)).toBeInTheDocument();

    const confirm = within(panel).getByRole("button", { name: "Switch" });
    expect(confirm).toBeDisabled();
    fireEvent.click(within(panel).getByRole("checkbox"));
    fireEvent.click(confirm);

    await screen.findByText("Now using Gemini.");
    const put = calls.find((c) => c.method === "PUT");
    expect(JSON.parse(put!.body!)).toEqual({ profile_id: "gemini", confirm_paid: true });
  });

  it("tests the connection and names the model that answered", async () => {
    stubApi(routes({
      [`POST ${BASE}/test`]: { ok: true, model_answered: "gemini-3.6-flash-002", latency_ms: 412, input_tokens: 12, output_tokens: 2 },
    }));
    renderAt("/settings/models");

    fireEvent.click(await screen.findByRole("button", { name: "Test connection" }));
    expect(await screen.findByText("Answered by gemini-3.6-flash-002 in 412 ms (12 in, 2 out tokens).")).toBeInTheDocument();
  });

  it("shows a failed test's reason", async () => {
    stubApi(routes({ [`POST ${BASE}/test`]: { ok: false, reason: "Connection test failed: AuthenticationError" } }));
    renderAt("/settings/models");

    fireEvent.click(await screen.findByRole("button", { name: "Test connection" }));
    expect(await screen.findByText(/Connection test failed: AuthenticationError/)).toBeInTheDocument();
  });

  it("lists token use for this session and month, and the spend against the cap", async () => {
    stubApi(routes());
    renderAt("/settings/models");

    const session = await screen.findByRole("table", { name: "This session" });
    expect(within(session).getByText("qwen3.5-9b")).toBeInTheDocument();
    expect(within(session).getAllByText("not reported")).toHaveLength(2);
    expect(within(session).getByText("800")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "This month" })).toBeInTheDocument();
    expect(screen.getByText("Spent this month: $0.0123 of $5.00")).toBeInTheDocument();
  });

  it("disables switching in mock mode", async () => {
    stubApi(routes({ [`GET ${BASE}`]: overview({ mock: true }) }));
    renderAt("/settings/models");

    expect(await screen.findByText("Mock mode is on (MOCK_AI=true). No model is called.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Use Gemini" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Test connection" })).not.toBeInTheDocument();
  });

  it("chooses a judging model apart from the chat model (SPEC-18 section 8)", async () => {
    const calls = stubApi(routes({ [`PUT ${BASE}/judge`]: overview({ judge_profile_id: null }) }));
    renderAt("/settings/models");

    const select = await screen.findByRole("combobox", { name: "Judging model" });
    expect(select).toHaveValue("");
    expect(within(select).getByRole("option", { name: "Same as AXIS chat" })).toBeInTheDocument();
    expect(within(select).queryByRole("option", { name: "OpenAI" })).not.toBeInTheDocument(); // no key set
    expect(within(select).getByRole("option", { name: "Gemini" })).toBeInTheDocument();
    expect(calls.some((c) => c.method === "PUT")).toBe(false);
  });

  it("asks for the same paid confirmation before a paid judging model", async () => {
    const calls = stubApi(routes({ [`PUT ${BASE}/judge`]: overview({ judge_profile_id: "gemini" }) }));
    renderAt("/settings/models");

    fireEvent.change(await screen.findByRole("combobox", { name: "Judging model" }), { target: { value: "gemini" } });
    const panel = screen.getByRole("dialog", { name: "Use Gemini for judging" });
    const confirm = within(panel).getByRole("button", { name: "Use for judging" });
    expect(confirm).toBeDisabled();
    expect(calls.some((c) => c.method === "PUT")).toBe(false);
    fireEvent.click(within(panel).getByRole("checkbox"));
    fireEvent.click(confirm);

    await screen.findByText("Judging model saved.");
    const put = calls.find((c) => c.method === "PUT");
    expect(JSON.parse(put!.body!)).toEqual({ profile_id: "gemini", confirm_paid: true });
  });

  it("goes back to the chat model without a prompt", async () => {
    const calls = stubApi(
      routes({
        [`GET ${BASE}`]: overview({ judge_profile_id: "gemini" }),
        [`PUT ${BASE}/judge`]: overview({ judge_profile_id: null }),
      }),
    );
    renderAt("/settings/models");

    fireEvent.change(await screen.findByRole("combobox", { name: "Judging model" }), { target: { value: "" } });

    await screen.findByText("Judging model saved.");
    expect(JSON.parse(calls.find((c) => c.method === "PUT")!.body!)).toEqual({ profile_id: null, confirm_paid: false });
  });

  it("never shows a key, only whether one is set", async () => {
    stubApi(routes());
    renderAt("/settings/models");
    await screen.findByRole("region", { name: "Gemini" });
    expect(document.body.textContent).not.toMatch(/sk-|AIza/);
  });
});

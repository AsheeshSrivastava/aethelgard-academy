import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { courseMap, ledger, proficiency } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";

const ME = "/api/v1/learners/me";

function routes(nextAction: object) {
  return {
    [`GET ${ME}/proficiency`]: { ...proficiency, next_action: { ...proficiency.next_action!, ...nextAction } },
    "GET /api/v1/courses/python": courseMap,
    [`GET ${ME}/ledger`]: ledger,
    [`GET ${ME}/reviews/due`]: [],
  };
}

describe("My progress, 2026-11-04 fixes", () => {
  it("names when a locked Cold Check retry opens, and points to a fresh item", async () => {
    stubApi(routes({ activity: "debug-validate", retry_at: "2026-11-04T10:00:00Z" }));
    renderAt("/progress");

    const next = await screen.findByRole("region", { name: "Next learning action" });
    expect(within(next).getByText(/Cold Check retry opens at \d{1,2} Nov 2026, \d{1,2}:\d{2} (am|pm)\./)).toBeInTheDocument();
    expect(within(next).getByText(/Meanwhile, try a new Debug & Validate item\./)).toBeInTheDocument();
  });

  it("says only when the retry opens if nothing new is left", async () => {
    stubApi(routes({ activity: "cold_check", retry_at: "2026-11-04T10:00:00Z" }));
    renderAt("/progress");

    const next = await screen.findByRole("region", { name: "Next learning action" });
    expect(within(next).getByText(/Cold Check retry opens at/)).toBeInTheDocument();
    expect(within(next).queryByText(/Meanwhile/)).not.toBeInTheDocument();
  });

  it("shows no retry line when nothing is locked", async () => {
    stubApi(routes({ retry_at: null }));
    renderAt("/progress");

    const next = await screen.findByRole("region", { name: "Next learning action" });
    expect(within(next).queryByText(/retry opens/)).not.toBeInTheDocument();
  });

  it("dates the ledger like 4 Nov 2026", async () => {
    stubApi(routes({}));
    renderAt("/progress");

    const table = await screen.findByRole("table", { name: "Evidence ledger" });
    const cells = within(table).getAllByRole("cell").map((c) => c.textContent ?? "");
    expect(cells.some((text) => /^\d{1,2} [A-Z][a-z]{2} \d{4}$/.test(text))).toBe(true);
    expect(cells.some((text) => /\d+\/\d+\/\d{4}/.test(text))).toBe(false);
  });
});

describe("My progress redesign, 2026-11-14", () => {
  it("says where you are in plain words, with one tile per unit", async () => {
    stubApi(routes({}));
    renderAt("/progress");

    const here = await screen.findByRole("region", { name: "Where you are" });
    expect(within(here).getByText(/1 of 2 units done for now/)).toBeInTheDocument();
    expect(within(here).getByText("Done for now")).toBeInTheDocument();
    expect(within(here).getByText("Needs work")).toBeInTheDocument();
  });

  it("groups each unit's skills under its card", async () => {
    stubApi(routes({}));
    renderAt("/progress");

    const card = await screen.findByRole("article", { name: /PY-0\.4/ });
    expect(within(card).getByText("Run a first program")).toBeInTheDocument();
    expect(within(card).getByRole("img", { name: /^CO-1:/ })).toBeInTheDocument();
    expect(within(card).getByRole("img", { name: /^CO-2:/ })).toBeInTheDocument();
    expect(within(card).queryByRole("img", { name: /^DE-2:/ })).not.toBeInTheDocument();
  });

  it("says when a unit was reset and how much is redone", async () => {
    stubApi(routes({}));
    renderAt("/progress");

    const card = await screen.findByRole("article", { name: /PY-0\.1/ });
    expect(within(card).getByText(/You reset this unit on 9 Nov 2026\. 1 of 3 activities redone/)).toBeInTheDocument();
  });

  it("names the other module that a skill's proof came from", async () => {
    stubApi(routes({}));
    renderAt("/progress");

    const card = await screen.findByRole("article", { name: /PY-0\.4/ });
    expect(within(card).getByText("Includes proof from Module 1.")).toBeInTheDocument();
  });

  it("explains the ladder colours in plain words", async () => {
    stubApi(routes({}));
    renderAt("/progress");

    const legend = await screen.findByRole("region", { name: "How to read the ladders" });
    expect(within(legend).getByText(/Proven: 2 results, including a Cold Check/)).toBeInTheDocument();
    expect(within(legend).getByText(/Seen once, not yet proven/)).toBeInTheDocument();
  });

  it("keeps the full evidence log in a collapsible section", async () => {
    stubApi(routes({}));
    renderAt("/progress");

    const log = (await screen.findByText("Full evidence log")).closest("details");
    expect(log).not.toBeNull();
    expect(await within(log as HTMLElement).findByRole("table", { name: "Evidence ledger" })).toBeInTheDocument();
  });
});

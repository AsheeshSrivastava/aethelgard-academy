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

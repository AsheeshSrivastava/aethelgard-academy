import { afterEach, describe, expect, it, vi } from "vitest";

import { api, SESSION_ID } from "./client";

afterEach(() => vi.unstubAllGlobals());

function captureFetch() {
  const seen: { url: string; init?: RequestInit }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      seen.push({ url: String(input), init });
      return new Response(null, { status: 204 });
    }),
  );
  return seen;
}

describe("session id (ADR-0022)", () => {
  it("is one ULID for the whole visit", () => {
    expect(SESSION_ID).toMatch(/^[0-9A-HJKMNP-TV-Z]{26}$/);
  });

  it("goes with every request", async () => {
    const seen = captureFetch();
    await api.resetUnit("PY-0.1");
    await api.logEvent({ event_type: "opened", unit_id: "PY-0.1", activity: "predict" });

    for (const call of seen) {
      expect(new Headers(call.init?.headers).get("X-Session-Id")).toBe(SESSION_ID);
    }
    expect(JSON.parse(String(seen[1]!.init?.body))).toEqual({ event_type: "opened", unit_id: "PY-0.1", activity: "predict" });
  });

  it("never lets a failed log write reach the page", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new Error("offline"))));

    await expect(api.logEvent({ event_type: "opened" })).resolves.toBeUndefined();
  });
});

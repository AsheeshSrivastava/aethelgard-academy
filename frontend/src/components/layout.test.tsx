import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { courses } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";

const features = (testMode: boolean) => ({ live_sessions: false, forums: false, gamification: false, test_mode: testMode });

describe("test mode banner", () => {
  it("shows on every page while test mode is on", async () => {
    stubApi({ "GET /api/v1/features": features(true), "GET /api/v1/courses": courses });
    renderAt("/courses");

    expect(await screen.findByRole("status", { name: "Test mode" })).toHaveTextContent("Test mode: timers off");
  });

  it("is absent when test mode is off", async () => {
    stubApi({ "GET /api/v1/features": features(false), "GET /api/v1/courses": courses });
    renderAt("/courses");

    await screen.findByRole("heading", { level: 1, name: "Courses" });
    expect(screen.queryByRole("status", { name: "Test mode" })).not.toBeInTheDocument();
  });

  it("is absent when the flag cannot be read", async () => {
    stubApi({ "GET /api/v1/courses": courses });
    renderAt("/courses");

    await screen.findByRole("heading", { level: 1, name: "Courses" });
    expect(screen.queryByRole("status", { name: "Test mode" })).not.toBeInTheDocument();
  });
});

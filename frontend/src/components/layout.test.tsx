import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { courses } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";

const features = (testMode: boolean) => ({ live_sessions: false, forums: false, gamification: false, test_mode: testMode });

describe("page shell", () => {
  it("has no back arrow on the front page", async () => {
    stubApi({ "GET /api/v1/courses": courses });
    renderAt("/");

    await screen.findByRole("heading", { level: 1 });
    expect(screen.queryByRole("link", { name: "Go back" })).not.toBeInTheDocument();
  });

  it("returns to the page the learner was on", async () => {
    stubApi({ "GET /api/v1/courses": courses });
    const router = renderAt("/courses");
    await screen.findByRole("heading", { level: 1, name: "Courses" });

    await userEvent.click(screen.getByRole("link", { name: "Concept library" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/concepts"));
    await userEvent.click(screen.getByRole("link", { name: "Go back" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/courses"));
  });

  it("goes up to the page above when the tab has no earlier page", async () => {
    stubApi({ "GET /api/v1/courses": courses });
    const router = renderAt("/courses");
    const back = await screen.findByRole("link", { name: "Go back" });

    expect(back).toHaveAttribute("href", "/");
    await userEvent.click(back);
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });

  it("credits Quest & Crossfire in the footer", async () => {
    stubApi({ "GET /api/v1/courses": courses });
    renderAt("/courses");

    expect(await screen.findByRole("contentinfo")).toHaveTextContent("by Quest & Crossfire");
  });
});

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

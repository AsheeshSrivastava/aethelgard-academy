import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SHOTS = process.env.SCREENSHOT_DIR;

async function shot(page: Page, name: string) {
  if (SHOTS) await page.screenshot({ path: join(SHOTS, `${name}.png`), fullPage: true });
}

async function expectNoSideScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

test("a learner walks from the front page to a unit and back", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: /learn to build/i })).toBeVisible();
  await expect(page.getByText("18 stages · 81 units")).toBeVisible();
  await shot(page, "front-page");

  await page.getByRole("navigation", { name: "Primary" }).getByRole("link", { name: "Courses" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Courses" })).toBeVisible();
  await shot(page, "courses");

  await page.getByRole("link", { name: /^Python 14|^Python Read/ }).first().click();
  await expect(page.getByRole("heading", { name: "Running your first program" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Owning a Python subsystem" })).toBeVisible();
  await shot(page, "course-map");

  await page.getByRole("link", { name: /PY-0\.1/ }).first().click();
  await expect(page.getByRole("heading", { level: 1, name: "Python as an executing program" })).toBeVisible();
  await expect(page.getByRole("list", { name: "Lesson path" }).getByText("Cold Check")).toBeVisible();
  await shot(page, "unit-map");

  await page.getByRole("link", { name: "Back to Python course map" }).click();
  await expect(page).toHaveURL(/\/courses\/python$/);
});

test("deep links survive a reload", async ({ page }) => {
  await page.goto("/units/PY-0.4");
  await expect(page.getByRole("heading", { level: 1, name: "Run a first program" })).toBeVisible();

  await page.reload();

  await expect(page.getByRole("heading", { level: 1, name: "Run a first program" })).toBeVisible();
});

test("the other two courses are not empty", async ({ page }) => {
  await page.goto("/courses/backend");
  await expect(page.getByRole("heading", { name: "Backend service mental model" })).toBeVisible();

  await page.goto("/courses/ai-engineering");
  await expect(page.getByRole("heading", { name: "AI-system mental model" })).toBeVisible();
});

test("a real answer shows up in My progress", async ({ page, request }) => {
  const exercise = await (await request.get("/api/v1/learners/me/units/PY-0.1/activities/predict/exercise")).json();
  const attempt = await request.post("/api/v1/learners/me/attempts", {
    data: { exercise_id: exercise.exercise_id, activity: "predict", choice: "A" },
  });
  expect(attempt.ok()).toBe(true);

  await page.goto("/progress");

  await expect(page.getByRole("heading", { name: /Skills · Stage 0/ })).toBeVisible();
  await expect(page.getByRole("img", { name: /^CO-1: target/ })).toBeVisible();
  await expect(page.getByRole("table", { name: "Evidence ledger" }).getByText("PY-0.1")).toBeVisible();
  await shot(page, "my-progress");

  await page.getByLabel("Filter by skill").selectOption("VE-4");
  await expect(page.getByText(/no evidence yet/i)).toBeVisible();
});

test("reset asks first, and keeps the ledger", async ({ page, request }) => {
  const before = await (await request.get("/api/v1/learners/me/ledger")).json();

  await page.goto("/units/PY-0.1");
  await page.getByRole("button", { name: "Reset unit" }).click();
  await expect(page.getByRole("group", { name: "Confirm reset" })).toContainText("evidence ledger is kept");
  await shot(page, "reset-confirm");
  await page.getByRole("button", { name: "Yes, reset" }).click();
  await expect(page.getByRole("button", { name: "Reset unit" })).toBeVisible();

  const after = await (await request.get("/api/v1/learners/me/ledger")).json();
  expect(after).toHaveLength(before.length);
});

test("every page fits a phone with no sideways scrolling", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });

  for (const [path, name] of [
    ["/", "phone-front-page"],
    ["/courses", "phone-courses"],
    ["/courses/python", "phone-course-map"],
    ["/units/PY-0.1", "phone-unit-map"],
    ["/progress", "phone-my-progress"],
  ] as const) {
    await page.goto(path);
    await page.getByRole("heading", { level: 1 }).first().waitFor();
    await page.waitForLoadState("networkidle");
    await expectNoSideScroll(page);
    await shot(page, name);
  }
});

test("the dark theme applies and is remembered", async ({ page }) => {
  await page.goto("/progress");
  await page.getByRole("heading", { level: 1 }).waitFor();

  const toggle = page.getByRole("button", { name: /switch to dark theme/i });
  await toggle.click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.waitForLoadState("networkidle");
  await shot(page, "dark-my-progress");

  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("heading", { level: 1 }).waitFor();
  await shot(page, "dark-front-page");
});

test("the old shell stays reachable until parity", async ({ page }) => {
  await page.goto("/legacy");

  await expect(page).toHaveTitle(/Aethelgard/);
});

test("the page loads no scripts or styles from other sites", async ({ page }) => {
  const outside: string[] = [];
  page.on("request", (request) => {
    if (!request.url().startsWith("http://127.0.0.1")) outside.push(request.url());
  });

  await page.goto("/");
  await page.getByRole("heading", { level: 1 }).waitFor();
  await page.waitForLoadState("networkidle");

  expect(outside).toEqual([]);
});

import { execFileSync } from "node:child_process";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SHOTS = process.env.SCREENSHOT_DIR;
const MAP = "/courses/python";
const REVIEW = "/courses/python/stages/0/review";

// Option positions in real Cold Check seeds, so every answer goes through the real grader.
const QUEUE = { right: 1, wrong: 3 };
const ZONE = { right: 2, wrong: 3 };

async function shot(page: Page, name: string) {
  if (SHOTS) await page.screenshot({ path: join(SHOTS, `${name}.png`), fullPage: true });
}

async function expectNoSideScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

/** Stands in for earlier days of work: only the throwaway test database changes. */
function database(action: string, ...args: string[]) {
  const script = `
import sqlite3, sys
from datetime import datetime, timedelta, timezone
db = sqlite3.connect(sys.argv[1])
now = datetime.now(timezone.utc)
ago = lambda **kw: (now - timedelta(**kw)).isoformat()
L = "default_learner"
action = sys.argv[2]
with db:
    if action == "start-round":
        for unit in ("PY-0.1", "PY-0.3", "PY-0.4"):
            db.execute("INSERT OR REPLACE INTO unit_cold_check VALUES (?, ?, ?, ?, 1)", (L, unit, ago(hours=50), ago(hours=25)))
        db.execute("DELETE FROM review_item WHERE learner_id = ?", (L,))
        db.execute("DELETE FROM review_result WHERE learner_id = ?", (L,))
        db.execute("INSERT INTO review_item VALUES (?, 'stage_review', 'python/0', 0, 'PY-0.1/cold-predict-1/v1', 'PY-0.1', 'CO-1', NULL)", (L,))
        db.execute("INSERT INTO review_item VALUES (?, 'stage_review', 'python/0', 1, 'PY-0.4/cold-predict-1/v1', 'PY-0.4', 'CO-1', NULL)", (L,))
    if action == "a-day-later":
        db.execute("UPDATE review_result SET last_attempt_at = ?", (ago(hours=25),))
    if action == "recheck-due":
        db.execute(
            "INSERT INTO evidence_ledger (entry_id, learner_id, unit_id, skill_id, evidence_category, evidence_strength,"
            " assistance_level, demonstration_context, recorded_at, cold_check, review_kind)"
            " VALUES ('e2e-review', ?, 'PY-0.1', 'CO-1', 'Explain / Reason', 'Strong', 'none', 'seeded', ?, 1, 'stage_review')",
            (L, ago(days=8)),
        )
        db.execute("INSERT INTO review_item VALUES (?, 'recheck', 'CO-1/7', 0, 'PY-0.1/cold-predict-1/v1', 'PY-0.1', 'CO-1', NULL)", (L,))
`;
  execFileSync("uv", ["run", "--no-sync", "python", "-c", script, process.env.LMS_E2E_DB!, action, ...args], { cwd: ".." });
}

// Stage 0 only: other stages (Stage 5 with PY-0.2) can have a review tile too.
const reviewTile = (page: Page) =>
  page.locator(".stage", { hasText: "Running your first program" }).locator(".build-tile", { hasText: /^Module review/ });

async function answer(page: Page, option: number) {
  await page.getByRole("radio").nth(option).check();
  await page.getByRole("button", { name: "Submit, one try" }).click();
}

// These run in order: they share one learner, and this file runs after the Stage 0 build.
test.describe.serial("stage review and rechecks", () => {
  test("a learner fails a stage review, then passes it a day later, and the build opens", async ({ page }) => {
    database("start-round");

    await page.goto(MAP);
    await expect(reviewTile(page)).toContainText("Ready");
    await expect(page.locator(".build-tile", { hasText: "Pantry intake" })).toContainText("Locked until you pass the module review");
    await shot(page, "review-course-map");

    await reviewTile(page).click();
    await expect(page.getByRole("heading", { level: 1, name: "Module 0 review" })).toBeVisible();
    await expect(page.getByText("Item 1 of 2")).toBeVisible();
    await expect(page.getByRole("note")).toContainText("AXIS is off");
    await expect(page.locator(".axis-panel")).toHaveCount(0);
    await shot(page, "review-item");

    await answer(page, QUEUE.wrong);
    await expect(page.getByText("Item 2 of 2")).toBeVisible();
    await answer(page, ZONE.right);

    await expect(page.getByText(/Not yet\. Try again in/)).toBeVisible();
    const strengthen = page.getByRole("list", { name: "Units to strengthen" });
    await expect(strengthen).toContainText("PY-0.1");
    await expect(strengthen).not.toContainText("PY-0.4");
    await shot(page, "review-failed");

    await page.goto(MAP);
    await expect(reviewTile(page)).toContainText("Not yet");
    await page.goto("/courses/python/stages/0/build");
    await expect(page.getByText("Pass the module review first.")).toBeVisible();

    database("a-day-later");
    await page.goto(REVIEW);
    await expect(page.getByText("Item 2 of 2")).toBeVisible();
    await answer(page, QUEUE.right);

    await expect(page.getByText("Passed.")).toBeVisible();
    await page.getByRole("link", { name: "Go to the build" }).click();
    await expect(page.getByText("Module 0 build", { exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Back to Python course map" })).toBeVisible();
  });

  test("the review fits a phone, and works in dark mode", async ({ page }) => {
    database("start-round");

    await page.setViewportSize({ width: 375, height: 800 });
    await page.goto(REVIEW);
    await page.getByText("Item 1 of 2").waitFor();
    await page.getByRole("heading", { level: 1, name: "Module 0 review" }).waitFor();
    await expectNoSideScroll(page);
    await shot(page, "phone-review-item");
    await page.goto(MAP);
    await reviewTile(page).waitFor();
    await expectNoSideScroll(page);

    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(REVIEW);
    await page.getByRole("button", { name: /switch to dark theme/i }).click();
    await page.getByText("Item 1 of 2").waitFor();
    await page.getByRole("heading", { level: 1, name: "Module 0 review" }).waitFor();
    await shot(page, "dark-review-item");
  });

  test("a due recheck is in My progress and can be taken", async ({ page }) => {
    database("recheck-due");

    await page.goto("/progress?course=python");
    const panel = page.getByRole("region", { name: "Due for review" });
    await expect(panel).toContainText("7-day recheck");
    await shot(page, "due-for-review");

    await page.setViewportSize({ width: 375, height: 800 });
    await expectNoSideScroll(page);
    await shot(page, "phone-due-for-review");
    await page.setViewportSize({ width: 1280, height: 900 });

    await panel.getByRole("link", { name: /CO-1/ }).click();
    await expect(page.getByRole("heading", { level: 1, name: "7-day recheck" })).toBeVisible();
    await expect(page.locator(".axis-panel")).toHaveCount(0);
    await shot(page, "recheck-item");
    await answer(page, QUEUE.wrong);

    await expect(page.getByText(/Recheck finished/)).toBeVisible();

    await page.goto("/progress?course=python");
    await page.getByRole("heading", { level: 1, name: "My progress" }).waitFor();
    await expect(page.getByRole("table", { name: "Evidence ledger" })).toContainText("Recheck");
    await expect(page.getByRole("region", { name: "Due for review" })).toHaveCount(0);
  });
});

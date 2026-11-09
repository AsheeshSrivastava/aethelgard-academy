import { execFileSync } from "node:child_process";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SHOTS = process.env.SCREENSHOT_DIR;
const UNIT = "/units/PY-0.1";

async function shot(page: Page, name: string) {
  if (SHOTS) await page.screenshot({ path: join(SHOTS, `${name}.png`), fullPage: true });
}

/** Stands in for the 24-hour wait: only the throwaway test database changes, never the app. */
function moveClockForward(unitId: string) {
  const script = `
import sqlite3, sys
from datetime import datetime, timedelta, timezone
db = sqlite3.connect(sys.argv[1])
past = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
with db:
    db.execute("UPDATE unit_cold_check SET completed_at = ?, last_attempt_at = CASE WHEN last_attempt_at IS NULL THEN NULL ELSE ? END WHERE unit_id = ?", (past, past, sys.argv[2]))
`;
  execFileSync("uv", ["run", "--no-sync", "python", "-c", script, process.env.LMS_E2E_DB!, unitId], { cwd: ".." });
}

async function replaceCode(page: Page, code: string) {
  await page.locator(".cm-content").click();
  await page.keyboard.press("Control+A");
  await page.keyboard.press("Delete");
  await page.keyboard.insertText(code);
}

async function expectNoSideScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

const rail = (page: Page) => page.getByRole("navigation", { name: "Lesson steps" });
const axis = (page: Page) => page.getByRole("complementary", { name: "AXIS facilitator" });

test("a learner walks all of PY-0.1, through the Cold Check", async ({ page }) => {
  test.setTimeout(120_000);
  await page.request.post("/api/v1/learners/me/units/PY-0.1/reset");

  // Unit map into the lesson
  await page.goto(UNIT);
  await page.getByRole("link", { name: /Start lesson|Continue lesson/ }).click();
  await expect(page).toHaveURL(/\/units\/PY-0\.1\/\w+/);
  await page.goto(`${UNIT}/video`);

  // Video
  await expect(page.getByRole("heading", { name: /How Python Executes/i })).toBeVisible();
  await expect(page.getByText(/video for this unit is not ready/i)).toBeVisible();
  await shot(page, "lesson-video");
  await page.getByRole("button", { name: "Mark as watched" }).click();
  await page.getByRole("link", { name: "Next: Explain" }).click();

  // Explain is in parts (SPEC-19); the concept check is the last one, "Say it back".
  const parts = page.getByRole("navigation", { name: "Explain parts" });
  await expect(parts).toBeVisible();
  await parts.getByRole("button", { name: "Say it back" }).click();

  // Explain: a Shaky answer never blocks
  await expect(page.getByLabel("Your explanation")).toBeVisible();
  await page.getByLabel("Your explanation").fill("Because it is code.");
  await page.getByRole("button", { name: "Check my explanation" }).click();
  await expect(page.getByText("Shaky", { exact: true })).toBeVisible();
  await shot(page, "lesson-explain");
  await page.getByRole("link", { name: "Next: Predict" }).click();

  // Predict: nothing revealed before the attempt
  await expect(page.getByRole("button", { name: "Submit answer" })).toBeDisabled();
  await expect(page.getByText("Statements run from top to bottom")).toHaveCount(0);
  await shot(page, "lesson-predict");
  await page.getByRole("radio").first().check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByRole("status", { name: "Result" })).toContainText("Passed");
  await expect(page.getByText("Statements run from top to bottom")).toBeVisible();
  await shot(page, "lesson-predict-result");

  // Regenerate gives a new variant and clears the result
  await page.getByRole("button", { name: "Regenerate" }).click();
  await expect(page.getByText(/variant 2/)).toBeVisible();
  await expect(page.getByRole("status", { name: "Result" })).toHaveCount(0);

  // AXIS answers, streaming, in the mock
  await axis(page).getByLabel("Message AXIS").fill("Why does this happen?");
  await axis(page).getByRole("button", { name: "Send" }).click();
  await expect(axis(page).getByText(/expected type of your variable/)).toBeVisible();
  await expect(axis(page).locator(".citation").first()).toBeVisible();
  await shot(page, "lesson-axis");

  // Trace
  await page.goto(`${UNIT}/trace`);
  await page.getByLabel(/terminal shows/i).fill("waiting\nchecked in");
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByRole("status", { name: "Result" })).toContainText("Passed");
  await shot(page, "lesson-trace");

  // Playground: a real program pauses at input() and resumes
  await page.goto(`${UNIT}/playground`);
  await expect(page.locator(".cm-content")).toBeVisible();
  await replaceCode(page, 'name = input("Name: ")\nprint("Hello", name.strip().title())\n');
  await page.getByRole("button", { name: "Run" }).click();
  await expect(page.getByText("Waiting for your input")).toBeVisible();
  await page.locator(".terminal-host .xterm-helper-textarea").focus();
  await page.keyboard.type("  amara okafor ");
  await page.keyboard.press("Enter");
  await expect(page.locator(".terminal-host")).toContainText("Hello Amara Okafor");
  await expect(page.locator(".terminal-host")).toContainText("exit code 0");
  await shot(page, "lesson-playground");

  // Drafts are saved
  await page.waitForTimeout(1200);
  await page.reload();
  await expect(page.locator(".cm-content")).toContainText("Hello");

  // The clock has started
  await page.goto(`${UNIT}/cold_check`);
  await expect(page.getByText(/Opens in/)).toBeVisible();
  await expect(rail(page).getByRole("link", { name: /Cold Check.*locked/ })).toBeVisible();
  await expect(axis(page)).toHaveCount(0);
  await shot(page, "lesson-cold-waiting");

  // A day later
  moveClockForward("PY-0.1");
  await page.reload();
  await expect(page.getByRole("note")).toContainText("AXIS is off");
  await expect(axis(page)).toHaveCount(0);
  await shot(page, "lesson-cold-item");

  // CO-1: fail this one on purpose
  await page.getByRole("radio").first().check();
  await page.getByRole("button", { name: "Submit, one try" }).click();

  // CO-2
  await expect(page.getByLabel(/terminal shows/i)).toBeVisible();
  await page.getByLabel(/terminal shows/i).fill("B A");
  await page.getByRole("button", { name: "Submit, one try" }).click();

  // CO-6, then the round ends with a fail and no answers shown
  await page.getByRole("radio", { name: /stores the code/ }).check();
  await page.getByRole("button", { name: "Submit, one try" }).click();
  await expect(page.getByText(/Try again in/)).toBeVisible();
  await expect(page.getByRole("region", { name: "Your result" })).toContainText("Not yet");
  await shot(page, "lesson-cold-failed");

  // The retry covers only the failed skill
  moveClockForward("PY-0.1");
  await page.reload();
  await expect(page.getByText("Kofi Mensah").first()).toBeVisible();
  await page.getByRole("radio").nth(1).check();
  await page.getByRole("button", { name: "Submit, one try" }).click();
  await expect(page.getByText("Passed.", { exact: true })).toBeVisible();
  await shot(page, "lesson-cold-passed");

  // My progress shows it, and the stage build lock moved
  await page.getByRole("link", { name: "See My progress" }).click();
  await expect(page.getByRole("table", { name: "Evidence ledger" }).getByText("Cold Check").first()).toBeVisible();
  await shot(page, "progress-after-cold-check");
});

test("AXIS shows code as code, and its panel can be dragged wider", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/units/PY-0.4/predict");

  await axis(page).getByRole("radio", { name: "Hybrid" }).check({ force: true });
  await axis(page).getByLabel("Message AXIS").fill("Show me the whole solution");
  await axis(page).getByRole("button", { name: "Send" }).click();
  await expect(axis(page).locator("pre code")).toContainText("run_intake");
  await expect(axis(page)).not.toContainText("```");
  await shot(page, "axis-code");

  const before = (await axis(page).boundingBox())!;
  const handle = (await page.getByRole("separator", { name: "Resize AXIS panel" }).boundingBox())!;
  await page.mouse.move(handle.x + handle.width / 2, handle.y + 100);
  await page.mouse.down();
  await page.mouse.move(handle.x - 200, handle.y + 100, { steps: 5 });
  await page.mouse.up();

  const after = (await axis(page).boundingBox())!;
  expect(after.width).toBeGreaterThan(before.width + 150);
  await shot(page, "axis-wide");

  await page.getByRole("button", { name: /switch to dark theme/i }).click();
  await shot(page, "dark-axis-code");
  await page.getByRole("button", { name: /switch to light theme/i }).click();

  await page.setViewportSize({ width: 375, height: 800 });
  await expectNoSideScroll(page);
  await expect(page.getByRole("separator", { name: "Resize AXIS panel" })).toBeHidden();
  await shot(page, "phone-axis-code");
  await page.setViewportSize({ width: 1280, height: 900 });

  await page.reload();
  await expect(axis(page)).toBeVisible();
  expect((await axis(page).boundingBox())!.width).toBeCloseTo(after.width, -1);
});

test("a learner finds a concept by search, and by a wiki link in a lesson", async ({ page, request }) => {
  const ledgerBefore = (await (await request.get("/api/v1/learners/me/ledger")).json()).length;
  await page.setViewportSize({ width: 1280, height: 900 });

  // From the top bar, by search
  await page.goto("/");
  await page.getByRole("navigation", { name: "Primary" }).getByRole("link", { name: "Concept library" }).click();
  await expect(page).toHaveURL(/\/concepts$/);
  await shot(page, "concepts-empty");
  const box = page.getByRole("searchbox", { name: "Search concepts" });
  await box.fill("print");
  await expect(page).toHaveURL(/q=print/);
  await expect(page.getByRole("status")).toContainText("concept");
  await shot(page, "concepts-results");
  await page.getByRole("link", { name: /print\(\) function/ }).click();

  // The note
  await expect(page.getByRole("heading", { level: 1, name: "print() function" })).toBeVisible();
  await expect(page.getByText("Draft")).toHaveCount(0);
  await expect(page.locator(".prose pre code").first()).toBeVisible();
  await expect(page.locator(".prose")).not.toContainText("[[");
  await shot(page, "concept-note");

  // A wiki link inside a note goes to the next note
  await page.locator(".prose").getByRole("link", { name: "variable" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Variables" })).toBeVisible();

  // The back arrow returns to the page before, one step at a time: the first note, then the library.
  await page.getByRole("link", { name: "Go back" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "print() function" })).toBeVisible();
  await page.getByRole("link", { name: "Go back" }).click();
  await expect(page).toHaveURL(/\/concepts\?q=print/);
  await expect(page.getByRole("searchbox", { name: "Search concepts" })).toHaveValue("print");

  // The recent list. Only what was opened from search is listed.
  await page.getByRole("navigation", { name: "Primary" }).getByRole("link", { name: "Concept library" }).click();
  await expect(page).toHaveURL(/\/concepts$/);
  const recent = page.getByRole("region", { name: "Recently opened" });
  await expect(recent.getByRole("link", { name: /print\(\) function/ })).toBeVisible();
  await expect(recent.getByRole("link", { name: /Variables/ })).toHaveCount(0);
  await shot(page, "concepts-recent");

  // By keyboard
  await box.fill("variables");
  await box.press("Enter");
  await expect(page.getByRole("heading", { level: 1, name: "Variables" })).toBeVisible();

  // From a lesson's Explain text
  // The link sits in the lesson's second part (SPEC-19 parts).
  await page.goto("/units/PY-0.1/explain");
  await page.getByRole("navigation", { name: "Explain parts" }).getByRole("button", { name: /Reference Desk/ }).click();
  await expect(page.locator(".prose")).not.toContainText("[[");
  await page.locator(".prose").getByRole("link", { name: "Comments in Python" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Comments in Python" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Used in units" }).getByRole("link", { name: /PY-0\.1/ })).toBeVisible();

  // Dark, then phone
  await page.getByRole("button", { name: /switch to dark theme/i }).click();
  await page.goto("/concepts/expressions");
  await expect(page.getByRole("heading", { level: 1, name: "Expressions" })).toBeVisible();
  await expect(page.locator(".prose table")).toBeVisible();
  await shot(page, "dark-concept-note");
  await page.goto("/concepts");
  await expect(page.getByRole("region", { name: "Recently opened" })).toBeVisible();
  await shot(page, "dark-concepts");
  await page.getByRole("button", { name: /switch to light theme/i }).click();

  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto("/concepts");
  await expect(page.getByRole("region", { name: "Recently opened" })).toBeVisible();
  await expectNoSideScroll(page);
  await shot(page, "phone-concepts");
  await page.goto("/concepts/expressions");
  await expect(page.getByRole("heading", { level: 1, name: "Expressions" })).toBeVisible();
  await expectNoSideScroll(page);
  await shot(page, "phone-concept-note");
  await page.setViewportSize({ width: 1280, height: 900 });

  const ledgerAfter = (await (await request.get("/api/v1/learners/me/ledger")).json()).length;
  expect(ledgerAfter).toBe(ledgerBefore);
});

test("a verified playground writes no evidence", async ({ page, request }) => {
  const before = (await (await request.get("/api/v1/learners/me/ledger")).json()).length;

  await page.goto("/units/PY-0.4/playground");
  await expect(page.locator(".cm-content")).toBeVisible();
  await replaceCode(
    page,
    [
      'raw_name = input("Applicant Name: ")',
      'raw_zone = input("Pickup Zone: ")',
      "clean_name = raw_name.strip().title()",
      "clean_zone = raw_zone.strip().upper()",
      "queue_number = 7",
      'ticket = "TICKET-" + str(queue_number)',
      'print(f"REGISTRATION CONFIRMED: {clean_name} [ZONE-{clean_zone}] {ticket}")',
      "",
    ].join("\n"),
  );
  await page.getByRole("button", { name: "Verify" }).click();

  await expect(page.getByRole("status", { name: "Result" })).toContainText("Passed");
  const after = (await (await request.get("/api/v1/learners/me/ledger")).json()).length;
  expect(after).toBe(before);
});

test("a program that never ends is stopped", async ({ page }) => {
  await page.goto("/units/PY-0.4/playground");
  await expect(page.locator(".cm-content")).toBeVisible();
  await replaceCode(page, "while True:\n    pass\n");
  await page.getByRole("button", { name: "Run" }).click();

  await expect(page.locator(".terminal-host")).toContainText("Stopped", { timeout: 20_000 });
});

test("lessons fit a phone, and work in dark mode", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  for (const [path, name] of [
    [`${UNIT}/video`, "phone-lesson-video"],
    [`${UNIT}/explain`, "phone-lesson-explain"],
    [`${UNIT}/predict`, "phone-lesson-predict"],
    ["/units/PY-0.4/playground", "phone-lesson-playground"],
    ["/units/PY-0.3/direct", "phone-lesson-direct"],
  ] as const) {
    await page.goto(path);
    await rail(page).waitFor();
    await page.waitForLoadState("networkidle");
    await expectNoSideScroll(page);
    await shot(page, name);
  }

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/units/PY-0.4/predict");
  await page.getByRole("button", { name: /switch to dark theme/i }).click();
  await page.waitForLoadState("networkidle");
  await shot(page, "dark-lesson-predict");
  await page.goto("/units/PY-0.4/playground");
  await expect(page.locator(".cm-content")).toBeVisible();
  await shot(page, "dark-lesson-playground");
});

test("a unit with no seeds says so, and still shows its steps", async ({ page }) => {
  await page.goto("/units/PY-1.2/predict");

  await expect(page.getByText(/not written yet/i)).toBeVisible();
  await expect(rail(page)).toBeVisible();
});

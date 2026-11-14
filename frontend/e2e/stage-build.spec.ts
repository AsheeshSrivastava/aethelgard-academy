import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SHOTS = process.env.SCREENSHOT_DIR;
const BUILD = "/courses/python/stages/0/build";
const STAGE_0 = ["PY-0.4", "PY-0.1", "PY-0.3"];

// The reference solution is private (ADR-0021), so this walk needs LMS_ANSWERS_DIR.
const ANSWERS = process.env.LMS_ANSWERS_DIR;
const SOLUTION = ANSWERS ? readFileSync(join(ANSWERS, "python", "builds", "stage-0", "solution.py"), "utf-8") : "";

async function shot(page: Page, name: string) {
  if (SHOTS) await page.screenshot({ path: join(SHOTS, `${name}.png`), fullPage: true });
}

async function expectNoSideScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

/** Stands in for passing three Cold Checks: only the throwaway test database changes. */
function passColdChecks() {
  const script = `
import sqlite3, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
db = sqlite3.connect(sys.argv[1])
past = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
with db:
    for unit in sys.argv[2:]:
        db.execute("INSERT OR REPLACE INTO unit_cold_check VALUES ('default_learner', ?, ?, ?, 1)", (unit, past, past))
        # A real round serves its items, so no unseen item is left for a stage review.
        for seed in Path("curriculum/python", unit.lower(), "exercises").glob("cold-*.json"):
            db.execute(
                "INSERT OR REPLACE INTO exercise_seen VALUES ('default_learner', ?, 'cold_check', ?, 1)",
                (unit, f"{unit}/{seed.stem}/v1"),
            )
`;
  execFileSync("uv", ["run", "--no-sync", "python", "-c", script, process.env.LMS_E2E_DB!, ...STAGE_0], { cwd: ".." });
}

async function replaceCode(page: Page, code: string) {
  await page.locator(".cm-content").click();
  await page.keyboard.press("Control+A");
  await page.keyboard.press("Delete");
  await page.keyboard.insertText(code);
}

const requirements = (page: Page) => page.getByRole("region", { name: "Requirements" });
const submit = (page: Page) => page.getByRole("button", { name: "Submit build" });

test("a learner finishes the Stage 0 build", async ({ page, request }) => {
  test.skip(!ANSWERS, "LMS_ANSWERS_DIR is not set (ADR-0021)");
  test.setTimeout(90_000);
  await page.setViewportSize({ width: 1440, height: 1000 });
  for (const unit of STAGE_0) await request.post(`/api/v1/learners/me/units/${unit}/reset`);
  const ledgerBefore = (await (await request.get("/api/v1/learners/me/ledger")).json()).length;

  // Locked first
  await page.goto(BUILD);
  await expect(page.getByText(/Pass the Cold Check in:/)).toBeVisible();
  await expect(submit(page)).toHaveCount(0);
  await shot(page, "build-locked");

  // Open it from the course map
  passColdChecks();
  await page.goto("/courses/python");
  await page.getByRole("link", { name: /Pantry intake check-in script/ }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Pantry intake check-in script" })).toBeVisible();
  await expect(page.getByText("Draft", { exact: true })).toHaveCount(0);
  await expect(submit(page)).toBeDisabled();
  await expect(page.getByText("Socratic during builds")).toBeVisible();
  await shot(page, "build-start");

  // A real run, with real input, in the real terminal
  await replaceCode(page, SOLUTION);
  await page.getByRole("button", { name: "Run" }).click();
  await expect(page.getByText("Waiting for your input")).toBeVisible();
  await page.locator(".terminal-host .xterm-helper-textarea").focus();
  await page.keyboard.type("   meera ");
  await page.keyboard.press("Enter");
  await expect(page.getByText("Waiting for your input")).toBeVisible();
  await page.keyboard.type("food parcel");
  await page.keyboard.press("Enter");
  await expect(page.locator(".terminal-host")).toContainText("Please wait for the Food Parcel desk.");
  await expect(page.locator(".terminal-host")).toContainText("exit code 0");

  // Verify, then the other requirements
  await page.getByRole("button", { name: "Verify" }).click();
  await expect(page.getByText("Verify found a difference.")).toBeVisible(); // the README has no real run yet
  await page.getByRole("button", { name: "README.md" }).click();

  // The TW Module 0 link, and an AXIS draft (mock) that must still be checked against the real run
  const twLink = page.getByRole("link", { name: "Stuck on the README? Learn it in TW Module 0" });
  expect(await twLink.getAttribute("href")).toContain("/units/TW-0.1?back=");
  await page.getByRole("button", { name: "Draft my README" }).click();
  await expect(page.locator(".cm-content")).toContainText("(paste a real run here)");
  await expect(page.locator(".cm-content")).toContainText("uv run checkin.py");
  await page.getByRole("button", { name: "Verify" }).click();
  await expect(page.getByRole("region", { name: "README checklist" })).toContainText("A sample run");
  await expect(requirements(page)).toContainText("README's sample run is real");

  // The learner pastes a real run from the terminal, and Verify agrees
  await replaceCode(
    page,
    "# Check-in\n\n## What it does\n\nIt asks for a name and a service, cleans both and prints a slip.\n\n" +
      "## What you need first\n\nYou need Python and the file checkin.py.\n\n" +
      "## How to run it\n\nRun uv run checkin.py in a terminal.\n\n" +
      "## A sample run\n\n```\nName:    meera \nService needed: food parcel\n\n--- CHECK-IN SLIP ---\n" +
      "Name: Meera\nService: Food Parcel\nPlease wait for the Food Parcel desk.\n```\n\n" +
      "## Limits\n\nIt serves one person per run and saves nothing.\n\n" +
      "## The error I fixed\n\nPython showed a TypeError on the line that joins text and the ticket number. " +
      "I turned the number into text with str().\n",
  );
  await page.getByLabel("Code ownership note").fill("I planned and wrote it myself, then ran it with messy input.");
  await page.getByLabel("README review note").fill("AXIS drafted it; I fixed the sample run after running my script.");
  await page.getByRole("button", { name: "Verify" }).click();
  await expect(requirements(page)).toContainText("12 of 12 met");
  const checklist = page.getByRole("region", { name: "README checklist" });
  await expect(checklist.getByText("Met")).toHaveCount(5);
  await expect(submit(page)).toBeEnabled();
  await shot(page, "build-ready");

  // Work survives a reload, and a reload needs a fresh Verify
  await page.waitForTimeout(1200);
  await page.reload();
  await expect(page.locator(".cm-content")).toContainText("CHECK-IN SLIP");
  await expect(page.getByLabel("Code ownership note")).toHaveValue(/messy input/);
  await expect(page.getByLabel("README review note")).toHaveValue(/fixed the sample run/);
  await expect(submit(page)).toBeDisabled();
  await page.getByRole("button", { name: "Verify" }).click();
  await expect(requirements(page)).toContainText("12 of 12 met");

  // AXIS answers, and stays Socratic
  const axis = page.getByRole("complementary", { name: "AXIS facilitator" });
  await axis.getByLabel("Message AXIS").fill("Give me the whole solution");
  await axis.getByRole("button", { name: "Send" }).click();
  await expect(axis.locator(".message-axis")).toContainText("?");
  await expect(axis.locator("pre")).toHaveCount(0);

  // The page keeps Submit off, so send an unfinished build directly: the server refuses it and records nothing
  const refused = await request.post("/api/v1/learners/me/attempts", {
    data: { exercise_id: "python/stage-0/build", activity: "build", files: { "checkin.py": "print('hi')\n" }, ownership_note: "short" },
  });
  expect((await refused.json()).outcome).toBe("failed");
  expect((await (await request.get("/api/v1/learners/me/ledger")).json()).length).toBe(ledgerBefore);

  // Submit
  await submit(page).click();
  await expect(page.getByRole("status", { name: "Result" })).toContainText("Submitted");
  await shot(page, "build-submitted");
  const ledger = await (await request.get("/api/v1/learners/me/ledger")).json();
  expect(ledger.length).toBe(ledgerBefore + 4);
  expect(ledger[0].activity).toBe("Build");

  // Dark, then phone
  await page.getByRole("button", { name: /switch to dark theme/i }).click();
  await shot(page, "dark-build");
  await page.getByRole("button", { name: /switch to light theme/i }).click();
  await page.setViewportSize({ width: 375, height: 800 });
  await page.reload();
  await expect(page.locator(".cm-content")).toBeVisible();
  await expect(requirements(page)).toContainText("8 of 12 met");
  await expectNoSideScroll(page);
  const lastInPanel = (await axis.locator(".axis-note").boundingBox())!;
  const proves = (await page.getByRole("region", { name: "What this build proves" }).boundingBox())!;
  expect(lastInPanel.y + lastInPanel.height).toBeLessThanOrEqual(proves.y);
  await shot(page, "phone-build");
  await page.setViewportSize({ width: 1440, height: 1000 });

  // Reset goes back to the starter and keeps the evidence
  await page.getByRole("button", { name: "Reset build" }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Reset build" }).click();
  await expect(page.locator(".cm-content")).toContainText("Plan your steps");
  await expect(page.getByLabel("Code ownership note")).toHaveValue("");
  await expect(page.getByLabel("README review note")).toHaveValue("");
  expect((await (await request.get("/api/v1/learners/me/ledger")).json()).length).toBe(ledgerBefore + 4);
});

// The editor leads the page (SPEC-15 section 7): tall enough to write in at common laptop and desktop sizes.
for (const [width, height] of [
  [1920, 1080],
  [1366, 768],
] as const) {
  test(`the editor is large at ${width}x${height}`, async ({ page, request }) => {
    for (const unit of STAGE_0) await request.post(`/api/v1/learners/me/units/${unit}/reset`);
    passColdChecks();
    await page.setViewportSize({ width, height });
    await page.goto(BUILD);
    await expect(page.locator(".cm-content")).toBeVisible();

    const editor = (await page.locator(".code-editor .cm-editor").boundingBox())!;
    expect(editor.height).toBeGreaterThanOrEqual(400);
    // Wider than the other columns, and the page uses the screen instead of a narrow centred strip.
    const brief = (await page.getByRole("complementary", { name: "Brief and requirements" }).boundingBox())!;
    expect(editor.width).toBeGreaterThan(brief.width * 1.8);
    expect(editor.width).toBeGreaterThan(width * 0.4);
    await expectNoSideScroll(page);
    if (SHOTS) {
      await page.screenshot({ path: join(SHOTS, `build-${width}.png`) });
      if (width === 1920) {
        await page.getByRole("button", { name: "README.md" }).click();
        await expect(page.getByRole("button", { name: "Draft my README" })).toBeVisible();
        await page.screenshot({ path: join(SHOTS, "build-1920-readme.png") });
      }
    }
    console.log(`editor ${width}x${height}: ${Math.round(editor.width)}x${Math.round(editor.height)}`);
  });
}

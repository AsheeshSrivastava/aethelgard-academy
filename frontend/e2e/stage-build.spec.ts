import { execFileSync } from "node:child_process";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SHOTS = process.env.SCREENSHOT_DIR;
const BUILD = "/courses/python/stages/0/build";
const STAGE_0 = ["PY-0.4", "PY-0.1", "PY-0.3"];

const SOLUTION = [
  "# Ask for the name and the service.",
  'raw_name = input("Name: ")',
  'raw_service = input("Service needed: ")',
  "# Clean both answers.",
  "name = raw_name.strip().title()",
  "service = raw_service.strip().title()",
  "# Print the slip.",
  "print()",
  'print("--- CHECK-IN SLIP ---")',
  'print(f"Name: {name}")',
  'print(f"Service: {service}")',
  'print(f"Please wait for the {service} desk.")',
  "",
].join("\n");

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
  await page.getByRole("link", { name: /Relief centre check-in script/ }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Relief centre check-in script" })).toBeVisible();
  await expect(page.getByText("Draft")).toHaveCount(0);
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
  await page.keyboard.type("housing");
  await page.keyboard.press("Enter");
  await expect(page.locator(".terminal-host")).toContainText("Please wait for the Housing desk.");
  await expect(page.locator(".terminal-host")).toContainText("exit code 0");

  // Verify, then the other requirements
  await page.getByRole("button", { name: "Verify" }).click();
  await expect(page.getByText("Verify passed.")).toBeVisible();
  await page.getByRole("button", { name: "README.md" }).click();
  await replaceCode(page, "# Check-in\n\nRun it with python checkin.py\n");
  await page.getByLabel("Ownership note").fill("I planned and wrote it myself, then ran it with messy input.");
  await expect(requirements(page)).toContainText("7 of 7 met");
  await expect(submit(page)).toBeEnabled();
  await shot(page, "build-ready");

  // Work survives a reload, and a reload needs a fresh Verify
  await page.waitForTimeout(1200);
  await page.reload();
  await expect(page.locator(".cm-content")).toContainText("CHECK-IN SLIP");
  await expect(page.getByLabel("Ownership note")).toHaveValue(/messy input/);
  await expect(submit(page)).toBeDisabled();
  await page.getByRole("button", { name: "Verify" }).click();
  await expect(requirements(page)).toContainText("7 of 7 met");

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
  await expect(requirements(page)).toContainText("5 of 7 met");
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
  await expect(page.getByLabel("Ownership note")).toHaveValue("");
  expect((await (await request.get("/api/v1/learners/me/ledger")).json()).length).toBe(ledgerBefore + 4);
});

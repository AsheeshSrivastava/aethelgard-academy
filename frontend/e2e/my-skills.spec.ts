import { join } from "node:path";

import { expect, test } from "@playwright/test";

const SHOTS = process.env.SCREENSHOT_DIR;

// SPEC-12 section 6.1: every framework skill once, by area, from all evidence.
test("My skills lists all 27 skills by area and fits a phone", async ({ page }) => {
  await page.goto("/skills");

  await expect(page.getByRole("heading", { level: 1, name: "My skills" })).toBeVisible();
  await expect(page.getByRole("region", { name: "What the levels mean" })).toContainText("Understand");
  for (const area of ["Comprehend", "Specify", "Build & Adapt", "Verify", "Decide & Direct"]) {
    await expect(page.getByRole("region", { name: area })).toBeVisible();
  }
  await expect(page.locator(".skill-entry")).toHaveCount(27);
  if (SHOTS) await page.screenshot({ path: join(SHOTS, "my-skills.png"), fullPage: true });

  await page.setViewportSize({ width: 375, height: 800 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
  if (SHOTS) await page.screenshot({ path: join(SHOTS, "phone-my-skills.png"), fullPage: true });
});

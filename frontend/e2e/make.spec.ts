import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SHOTS = process.env.SCREENSHOT_DIR;
const MAKE = "/units/PY-1.2/build";

// The PY-1.2 Make item's own reference program and a plausible wrong one (curriculum/python/py-1.2).
const RIGHT = 'price = float(input("Price per kg: "))\nkilograms = float(input("Kilograms: "))\ntotal = round(price * kilograms, 2)\nprint("Total value:", total)\n';
const NOT_ROUNDED = 'price = float(input("Price per kg: "))\nkilograms = float(input("Kilograms: "))\nprint("Total value:", price * kilograms)\n';

async function shot(page: Page, name: string) {
  if (SHOTS) await page.screenshot({ path: join(SHOTS, `${name}.png`), fullPage: true });
}

async function expectNoSideScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

async function replaceCode(page: Page, code: string) {
  await page.locator(".cm-content").click();
  await page.keyboard.press("Control+A");
  await page.keyboard.press("Delete");
  await page.keyboard.insertText(code);
}

const result = (page: Page) => page.getByRole("status", { name: "Result" });

test.describe.serial("Make step (Amendment A1.3)", () => {
  test("a learner writes the donation calculator from a blank file, fails, then passes", async ({ page }) => {
    await page.goto(MAKE);
    await expect(page.getByText("Make · from a blank file")).toBeVisible();
    await expect(page.getByRole("note")).toContainText("hidden tests");
    await expect(page.getByText("Round the total to 2 decimal places", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Run" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Regenerate" })).toHaveCount(0);
    const starter = await page.locator(".cm-content").innerText();
    expect(starter.split("\n").every((line) => line.trim() === "" || line.trim().startsWith("#"))).toBe(true);
    await shot(page, "make-start");

    await replaceCode(page, NOT_ROUNDED);
    await page.getByRole("button", { name: /^Submit/ }).click();
    await expect(result(page)).toContainText("Not yet");

    await replaceCode(page, RIGHT);
    await page.getByRole("button", { name: /^Submit/ }).click();
    await expect(result(page)).toContainText("Passed");
    await shot(page, "make-passed");

    await page.goto("/progress?course=python&stage=1");
    await page.getByText("Full evidence log").click();
    await expect(page.getByRole("table", { name: "Evidence ledger" })).toContainText("Build");
  });

  test("the Make step fits a phone, and works in dark mode", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await page.goto(MAKE);
    await page.getByText("Make · from a blank file").waitFor();
    await expectNoSideScroll(page);
    await shot(page, "phone-make");

    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(MAKE);
    await page.getByRole("button", { name: /switch to dark theme/i }).click();
    await page.getByText("Make · from a blank file").waitFor();
    await shot(page, "dark-make");
  });
});

import { expect, test } from "@playwright/test";

test("the old shell opens the moved concept notes", async ({ page }) => {
  await page.goto("/legacy");

  const links = await page.evaluate(() => (window as unknown as { processWikiLinks: (text: string) => string }).processWikiLinks("[[variables]] `print()` `input()`"));
  expect(links).toContain("openConceptDrawer('variables')");
  expect(links).toContain("openConceptDrawer('print-function')");
  expect(links).toContain("openConceptDrawer('built-in-input')");

  const notes: [string, string][] = [
    ["variables", "Variables"],
    ["print-function", "print() function"],
    ["built-in-input", "input() function"],
  ];
  for (const [slug, title] of notes) {
    await page.evaluate((id) => (window as unknown as { openConceptDrawer: (id: string) => Promise<void> }).openConceptDrawer(id), slug);
    await expect(page.locator("#drawer-title")).toHaveText(title);
  }
});

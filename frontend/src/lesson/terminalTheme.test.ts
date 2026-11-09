import { afterEach, describe, expect, it } from "vitest";

import { terminalTheme } from "./RunTerminal";

describe("terminal colours (step 6)", () => {
  afterEach(() => {
    document.documentElement.style.removeProperty("--code-bg");
  });

  it("reads the theme tokens, because xterm cannot use CSS variables", () => {
    document.documentElement.style.setProperty("--code-bg", "#123456");
    expect(terminalTheme().background).toBe("#123456");
  });

  it("stays dark when a token is missing", () => {
    expect(terminalTheme()).toMatchObject({ background: "#0e141b", foreground: "#e6edf3", cursor: "#4ff5f5" });
  });
});

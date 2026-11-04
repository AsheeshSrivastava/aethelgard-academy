import "@testing-library/jest-dom/vitest";
import { cleanup, configure } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// Tests wait for a condition, never a fixed time. On a busy machine a page can take
// longer than the 1 s default to appear, so allow 5 s; a passing wait still returns at once.
configure({ asyncUtilTimeout: 5000 });

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

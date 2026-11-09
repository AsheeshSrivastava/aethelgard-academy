import { describe, expect, it } from "vitest";

import { parentPath } from "./backPath";

describe("parentPath: where Go back leads with no earlier page in the tab", () => {
  it.each([
    ["/", null],
    ["/courses", "/"],
    ["/courses/python", "/courses"],
    ["/courses/python/stages/0/build", "/courses/python"],
    ["/courses/backend/stages/2/review", "/courses/backend"],
    ["/units/PY-0.4", "/courses/python"],
    ["/units/NET-0.1", "/courses/backend"],
    ["/units/PY-0.4/explain", "/units/PY-0.4"],
    ["/concepts", "/"],
    ["/concepts/print-function", "/concepts"],
    ["/reviews/CO-1/7", "/progress"],
    ["/progress", "/"],
    ["/skills", "/"],
    ["/settings/models", "/"],
    ["/no-such-page", "/"],
  ])("%s -> %s", (path, parent) => {
    expect(parentPath(path)).toBe(parent);
  });

  it("returns to the build a unit was opened from", () => {
    expect(parentPath("/units/TW-0.1", { back: "/courses/python/stages/0/build" })).toBe("/courses/python/stages/0/build");
  });

  it("ignores a back target that is not this app's build path", () => {
    expect(parentPath("/units/TW-0.1", { back: "https://example.com/" })).toBe("/courses/python");
  });
});

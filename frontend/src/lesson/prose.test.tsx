import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { streamSafe } from "./axisStream";
import { Prose } from "./Prose";

const FENCED = "Look:\n\n```python\nname = input('Name')\nprint(name)\n```\n";

describe("rendering", () => {
  it("shows a fenced block as code and inline code as a code span", () => {
    const { container } = render(<Prose>{"Use `input()` here.\n\n```python\nprint(1)\n```\n"}</Prose>);

    expect(screen.getByText("input()").tagName).toBe("CODE");
    expect(container.querySelector("pre code")).toHaveTextContent("print(1)");
    expect(container).not.toHaveTextContent("```");
  });

  it("colours Python", () => {
    const { container } = render(<Prose>{"```python\ndef f():\n    return 'x'\n```\n"}</Prose>);

    expect(container.querySelector("pre .tok-keyword")).toHaveTextContent("def");
    expect(container.querySelector("pre .tok-string")).toHaveTextContent("'x'");
  });

  it("keeps the code exact when colouring it", () => {
    const code = "def f(a):\n    return a  # keep\n\n\nprint(f(1))";
    const { container } = render(<Prose>{`\`\`\`py\n${code}\n\`\`\`\n`}</Prose>);

    expect(container.querySelector("pre code")?.textContent).toBe(code);
  });

  it("leaves other languages plain", () => {
    const { container } = render(<Prose>{"```bash\nuv run lms\n```\n"}</Prose>);

    expect(container.querySelector("pre .tok-keyword")).toBeNull();
    expect(container.querySelector("pre code")).toHaveTextContent("uv run lms");
  });

  it("renders paragraphs, lists and bold", () => {
    const { container } = render(<Prose>{"First **bold**.\n\n- one\n- two\n"}</Prose>);

    expect(container.querySelector("strong")).toHaveTextContent("bold");
    expect(container.querySelectorAll("li")).toHaveLength(2);
  });
});

describe("safety", () => {
  it("never creates elements from model HTML", () => {
    const { container } = render(<Prose>{'Hello <img src=x onerror="alert(1)"> and <script>alert(2)</script> <b>bold</b>'}</Prose>);

    expect(container.querySelector("img, script, b")).toBeNull();
  });

  it.each([
    "javascript:alert(1)",
    "data:text/html,x",
    "vbscript:x",
    "file:///etc/passwd",
    "mailto:someone@example.org",
    "/api/v1/learners/me/ledger",
    "irc://example.org",
  ])("drops a %s link", (url) => {
    const { container } = render(<Prose>{`[click](${url})`}</Prose>);

    expect(container.querySelector("a")?.getAttribute("href") ?? "").toBe("");
  });

  it("keeps http and https links, opening safely in a new tab", () => {
    render(<Prose>{"[docs](https://docs.python.org/3/)"}</Prose>);

    const link = screen.getByRole("link", { name: "docs" });
    expect(link).toHaveAttribute("href", "https://docs.python.org/3/");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noreferrer");
  });

  it("drops images, so a reply cannot load anything from outside", () => {
    const { container } = render(<Prose>{"![x](https://evil.example/track.png)"}</Prose>);

    expect(container.querySelector("img")).toBeNull();
  });
});

describe("copy button", () => {
  it("copies the code exactly", async () => {
    const writeText = vi.fn(async () => undefined);
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
    render(<Prose>{FENCED}</Prose>);

    fireEvent.click(screen.getByRole("button", { name: "Copy code" }));

    expect(writeText).toHaveBeenCalledWith("name = input('Name')\nprint(name)");
    await waitFor(() => expect(screen.getByRole("button", { name: "Copied" })).toBeInTheDocument());
  });

  it("stays quiet if the browser refuses", async () => {
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText: vi.fn(async () => Promise.reject(new Error("no"))) } });
    render(<Prose>{FENCED}</Prose>);

    fireEvent.click(screen.getByRole("button", { name: "Copy code" }));

    await waitFor(() => expect(screen.getByRole("button", { name: "Copy code" })).toBeInTheDocument());
  });
});

describe("while streaming", () => {
  it.each([
    ["half an opening fence", "Look:\n\n``", "Look:"],
    ["one backtick of a fence", "Look:\n\n`", "Look:"],
    ["an unfinished inline span", "Use `inp", "Use inp"],
  ])("hides %s", (_name, partial, expected) => {
    expect(streamSafe(partial).trim()).toBe(expected);
  });

  it("leaves finished text alone", () => {
    expect(streamSafe("Use `input()` now.")).toBe("Use `input()` now.");
    expect(streamSafe(FENCED)).toBe(FENCED);
  });

  it("does not touch backticks inside an open code block", () => {
    const open = "```python\nx = '`'\n``";

    expect(streamSafe(open)).toBe(open);
  });

  it("shows an unclosed fence as an open code block at every point in the stream", () => {
    const whole = "Try:\n\n```python\nprint('hi')\nprint('bye')\n```\nDone `now`.";
    for (let end = 1; end <= whole.length; end++) {
      const { container, unmount } = render(<Prose>{streamSafe(whole.slice(0, end))}</Prose>);
      const outside = [...container.querySelectorAll(".prose > p")].map((p) => p.textContent).join(" ");
      expect(outside).not.toContain("`");
      unmount();
    }
  });
});

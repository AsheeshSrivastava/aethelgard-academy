import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryHistory, createRootRoute, createRouter, RouterProvider } from "@tanstack/react-router";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { stubApi } from "../test/harness";
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

describe("wiki links", () => {
  const notes = [
    { concept_id: "variables", name: "Variables", category: "c", summary: "s", status: "draft" },
    { concept_id: "print-function", name: "print() function", category: "c", summary: "s", status: "draft" },
  ];

  function renderLinks(text: string, on = true) {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const page = createRootRoute({
      component: () => (
        <QueryClientProvider client={client}>
          <Prose wikiLinks={on}>{text}</Prose>
        </QueryClientProvider>
      ),
    });
    const router = createRouter({ routeTree: page, history: createMemoryHistory() });
    return render(<RouterProvider router={router as never} />);
  }

  beforeEach(() => {
    stubApi({ "GET /api/v1/concepts": notes });
  });

  it("links a slug and shows the concept's title", async () => {
    renderLinks("See [[print-function]].");

    expect(await screen.findByRole("link", { name: "print() function" })).toHaveAttribute("href", "/concepts/print-function");
  });

  it("shows the label when there is one", async () => {
    renderLinks("Store it in a [[variables|variable]] first.");

    expect(await screen.findByRole("link", { name: "variable" })).toHaveAttribute("href", "/concepts/variables");
    expect(screen.getByText(/Store it in a/)).toHaveTextContent("Store it in a variable first.");
  });

  it("works inside a table, where the pipe is escaped", async () => {
    renderLinks("| Term |\n| --- |\n| [[variables\\|a name]] |\n");

    expect(await screen.findByRole("link", { name: "a name" })).toHaveAttribute("href", "/concepts/variables");
  });

  it("works in lists and bold", async () => {
    renderLinks("- **[[variables]]**\n");

    expect(await screen.findByRole("link", { name: "Variables" })).toBeInTheDocument();
  });

  it("finds several links in one line", async () => {
    renderLinks("[[variables]] and [[print-function]]");

    expect(await screen.findAllByRole("link")).toHaveLength(2);
  });

  it("leaves code alone", async () => {
    const { container } = renderLinks("`[[variables]]`\n\n```python\nx = [[variables]]\n```\n\n[[variables]]");

    await screen.findByRole("link", { name: "Variables" });
    expect(container.querySelectorAll("a")).toHaveLength(1);
    expect(container.querySelector("p code")).toHaveTextContent("[[variables]]");
    expect(container.querySelector("pre code")).toHaveTextContent("x = [[variables]]");
  });

  it("shows an unknown slug as plain text and warns in development", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const { container } = renderLinks("See [[nothing-here]] and [[gone|the gone note]].");

    await waitFor(() => expect(warn).toHaveBeenCalledWith(expect.stringContaining("nothing-here")));
    expect(container).toHaveTextContent("See nothing-here and the gone note.");
    expect(container.querySelector("a")).toBeNull();
    warn.mockRestore();
  });

  it("leaves a badly written slug as it is", async () => {
    const { container } = renderLinks("[[Not A Slug]] [[../../etc]] [[x|]]");

    await waitFor(() => expect(container).toHaveTextContent("[[Not A Slug]]"));
    expect(container).toHaveTextContent("[[../../etc]]");
    expect(container.querySelector("a")).toBeNull();
  });

  it("shows plain text if the list of concepts cannot load", async () => {
    stubApi({});
    const { container } = renderLinks("See [[variables|a variable]].");

    await waitFor(() => expect(container).toHaveTextContent("See a variable."));
    expect(container.querySelector("a")).toBeNull();
  });

  it("never puts a link inside a link", async () => {
    const { container } = renderLinks("[see [[variables]] here](https://docs.python.org/3/)");

    await waitFor(() => expect(container.querySelector("a")).toHaveAttribute("href", "https://docs.python.org/3/"));
    expect(container.querySelector("a a")).toBeNull();
    expect(container.querySelector("a")).toHaveTextContent("see [[variables]] here");
  });

  it("stays off by default, so AXIS replies keep the brackets", async () => {
    const calls = stubApi({ "GET /api/v1/concepts": notes });
    const { container } = renderLinks("[[variables]]", false);

    expect(await within(container).findByText("[[variables]]")).toBeInTheDocument();
    expect(calls).toEqual([]);
  });

  it("cannot be used to smuggle a link to another site", async () => {
    const { container } = renderLinks("[[variables|[x](javascript:alert(1))]] [[https://evil.example]]");

    await waitFor(() => expect(container.querySelectorAll("a[href^='javascript'], a[href*='evil']")).toHaveLength(0));
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

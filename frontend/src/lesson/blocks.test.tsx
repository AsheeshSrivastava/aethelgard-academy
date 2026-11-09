import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { stubApi } from "../test/harness";
import { parseQuickCheck, parseSteps } from "./LessonBlocks";
import { Prose } from "./Prose";

const STEPS = `caption: A desk.

title: Take in
code: input("Name: ")
result: "  meera "
note: Always text.

title: Send out
code: print(name)`;

const QUICK = `id: py-0.4-strip-upper
question: Someone types \`  north-01 \`. Which line gives \`NORTH-01\`?
A: \`code.upper()\`
B: \`code.strip().upper()\`
C: \`code.title()\``;

const URL = "POST /api/v1/units/PY-0.4/quick-checks/py-0.4-strip-upper";

function show(markdown: string, unitId?: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <Prose unitId={unitId}>{markdown}</Prose>
    </QueryClientProvider>,
  );
}

const fence = (lang: string, body: string) => `\`\`\`${lang}\n${body}\n\`\`\`\n`;

describe("steps block (SPEC-19 section 2)", () => {
  it("parses a valid block", () => {
    expect(parseSteps(STEPS)).toEqual({
      caption: "A desk.",
      steps: [
        { title: "Take in", code: 'input("Name: ")', result: '"  meera "', note: "Always text." },
        { title: "Send out", code: "print(name)" },
      ],
    });
  });

  it.each([
    ["one step", "title: Only"],
    ["six steps", Array.from({ length: 6 }, (_, n) => `title: S${n}`).join("\n")],
    ["a field before any title", "code: x\ntitle: A\ntitle: B"],
    ["an unknown key", "title: A\ntitle: B\ncolour: red"],
    ["two captions", "caption: a\ncaption: b\ntitle: A\ntitle: B"],
  ])("refuses %s", (_, text) => {
    expect(parseSteps(text)).toBeNull();
  });

  it("draws numbered boxes in a figure, read as an ordered list", () => {
    show(fence("steps", STEPS), "PY-0.4");

    const figure = screen.getByRole("figure");
    const items = within(figure).getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent("Take in");
    expect(items[0]).toHaveTextContent(/Result:/);
    expect(items[0]!.querySelector(".steps-result code")?.textContent).toBe('"  meera "');
    expect(figure).toHaveTextContent("A desk.");
  });

  it("shows an invalid block as plain code", () => {
    show(fence("steps", "title: Only"), "PY-0.4");

    expect(screen.queryByRole("figure")).not.toBeInTheDocument();
    expect(screen.getByText("title: Only")).toBeInTheDocument();
  });
});

describe("quick check (SPEC-19 section 3)", () => {
  it("parses the public half and ignores a key that should not be there", () => {
    expect(parseQuickCheck(QUICK)?.options.map(([letter]) => letter)).toEqual(["A", "B", "C"]);
    expect(parseQuickCheck(`${QUICK}\nanswer: B`)?.id).toBe("py-0.4-strip-upper");
    expect(parseQuickCheck("id: q\nquestion: Q?\nA: a")).toBeNull();
  });

  it("says Right with the why for a right choice", async () => {
    const calls = stubApi({ [URL]: { correct: true, why: "Fixture reason." } }); // not the real key (ADR-0021)
    show(fence("quickcheck", QUICK), "PY-0.4");

    expect(screen.getByText("Not graded. Just for you.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "C: code.title()" }));

    expect(await screen.findByText("Right. Fixture reason.")).toBeInTheDocument();
    expect(calls.at(-1)?.body).toBe(JSON.stringify({ choice: "C" }));
    expect(screen.getByRole("button", { name: "A: code.upper()" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "C: code.title()" })).toHaveClass("quick-option-right");
  });

  it("lets the learner try again after a wrong choice, without the answer", async () => {
    stubApi({ [URL]: { correct: false, why: null } });
    show(fence("quickcheck", QUICK), "PY-0.4");

    await userEvent.click(screen.getByRole("button", { name: "A: code.upper()" }));

    expect(await screen.findByText("Not quite. Try another.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "A: code.upper()" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "B: code.strip().upper()" })).toBeEnabled();
  });

  it("says when it cannot be marked", async () => {
    stubApi({ [URL]: new Response(JSON.stringify({ title: "Quick check not available", status: 503 }), { status: 503 }) });
    show(fence("quickcheck", QUICK), "PY-0.4");

    await userEvent.click(screen.getByRole("button", { name: "B: code.strip().upper()" }));

    expect(await screen.findByText("This check can't be marked here.")).toBeInTheDocument();
  });
});

describe("keyboard access (step 7 audit, WCAG 2.1.1)", () => {
  it("lets a keyboard reach wide code blocks and tables, which scroll on a phone", () => {
    show("```\nlong line\n```\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n");

    expect(screen.getByText("long line").closest("pre")).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("table")).toHaveAttribute("tabindex", "0");
  });
});

describe("outside a lesson", () => {
  it("never turns an AXIS reply's code into blocks", () => {
    show(fence("quickcheck", QUICK) + fence("steps", STEPS));

    expect(screen.queryByRole("figure")).not.toBeInTheDocument();
    expect(screen.queryByText("Not graded. Just for you.")).not.toBeInTheDocument();
  });

  it("draws a Key idea blockquote as a box only in a lesson", () => {
    show("> **Key idea:** text is not a number.", "PY-0.4");
    expect(screen.getByText(/text is not a number/).closest("blockquote")).toHaveClass("key-idea");
  });
});

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { concepts, conceptNote } from "../test/fixtures";
import { renderAt, stubApi } from "../test/harness";

function routes(extra: Record<string, unknown> = {}) {
  return {
    "GET /api/v1/concepts": (url: URL) => {
      const q = url.searchParams.get("q");
      return q ? concepts.filter((c) => c.name.toLowerCase().includes(q.toLowerCase())) : concepts;
    },
    "GET /api/v1/learners/me/concepts/recent": [],
    "GET /api/v1/concepts/variables": conceptNote,
    "PUT /api/v1/learners/me/concepts/recent/variables": null,
    ...extra,
  };
}

const searchBox = () => screen.findByRole("searchbox", { name: "Search concepts" });

describe("top bar", () => {
  it("links to the Concept library", async () => {
    stubApi(routes());
    renderAt("/concepts");

    const nav = await screen.findByRole("navigation", { name: "Primary" });
    expect(within(nav).getByRole("link", { name: "Concept library" })).toHaveAttribute("href", "/concepts");
  });
});

describe("the library page", () => {
  it("shows the latest notes under the search bar, in the order given", async () => {
    stubApi(routes({ "GET /api/v1/learners/me/concepts/recent": [concepts[1], concepts[0]] }));
    renderAt("/concepts");

    const recent = await screen.findByRole("region", { name: "Recently opened" });
    const names = (await within(recent).findAllByRole("link")).map((link) => link.textContent);
    expect(names[0]).toContain("Variables");
    expect(names[1]).toContain("print() function");
  });

  it("says how to start when nothing has been opened", async () => {
    stubApi(routes());
    renderAt("/concepts");

    expect(await screen.findByText(/met in a lesson/i)).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Recently opened" })).not.toBeInTheDocument();
  });

  it("waits for typing to stop, then searches once", async () => {
    const calls = stubApi(routes());
    renderAt("/concepts");

    await userEvent.type(await searchBox(), "vari");

    expect(await screen.findByRole("link", { name: /Variables/ })).toBeInTheDocument();
    expect(calls.filter((c) => c.url.startsWith("/api/v1/concepts?q="))).toEqual([expect.objectContaining({ url: "/api/v1/concepts?q=vari" })]);
  });

  it("keeps the search in the address and starts from it", async () => {
    stubApi(routes());
    const router = renderAt("/concepts?q=vari");

    expect(await screen.findByRole("link", { name: /Variables/ })).toBeInTheDocument();
    expect(await searchBox()).toHaveValue("vari");
    expect(router.state.location.search).toEqual({ q: "vari" });
  });

  it("hides the recent list while searching", async () => {
    stubApi(routes({ "GET /api/v1/learners/me/concepts/recent": [concepts[0]] }));
    renderAt("/concepts?q=vari");

    await screen.findByRole("link", { name: /Variables/ });
    expect(screen.queryByRole("region", { name: "Recently opened" })).not.toBeInTheDocument();
  });

  it("counts results for screen readers and marks a draft", async () => {
    stubApi(routes());
    renderAt("/concepts?q=vari");

    const card = await screen.findByRole("link", { name: /Variables/ });
    expect(screen.getByRole("status")).toHaveTextContent("1 concept");
    expect(within(card).getByText("Draft")).toBeInTheDocument();
  });

  it("says so when nothing matches", async () => {
    stubApi(routes());
    renderAt("/concepts?q=zzz");

    expect(await screen.findByText(/no concept matches/i)).toBeInTheDocument();
  });

  it("shows an error if search fails", async () => {
    stubApi({ "GET /api/v1/learners/me/concepts/recent": [] });
    renderAt("/concepts?q=vari");

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });

  it("does not record a note until it is opened", async () => {
    const calls = stubApi(routes());
    renderAt("/concepts?q=vari");

    await screen.findByRole("link", { name: /Variables/ });
    expect(calls.some((c) => c.method === "PUT")).toBe(false);
  });

  it("records a note opened from the results", async () => {
    const calls = stubApi(routes());
    const router = renderAt("/concepts?q=vari");

    await userEvent.click(await screen.findByRole("link", { name: /Variables/ }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/concepts/variables"));
    expect(calls).toContainEqual(expect.objectContaining({ method: "PUT", url: "/api/v1/learners/me/concepts/recent/variables" }));
  });

  it("still opens the note if recording fails", async () => {
    stubApi({ ...routes(), "PUT /api/v1/learners/me/concepts/recent/variables": new Response("{}", { status: 500 }) });
    const router = renderAt("/concepts?q=vari");

    await userEvent.click(await screen.findByRole("link", { name: /Variables/ }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/concepts/variables"));
  });
});

describe("keyboard", () => {
  it("Enter opens the top result straight after typing", async () => {
    const calls = stubApi(routes());
    const router = renderAt("/concepts");

    await userEvent.type(await searchBox(), "vari{Enter}");

    await waitFor(() => expect(router.state.location.pathname).toBe("/concepts/variables"));
    expect(calls).toContainEqual(expect.objectContaining({ method: "PUT" }));
  });

  it("Enter with nothing to open stays put", async () => {
    stubApi(routes());
    const router = renderAt("/concepts");

    await userEvent.type(await searchBox(), "zzz{Enter}");

    await screen.findByText(/no concept matches/i);
    expect(router.state.location.pathname).toBe("/concepts");
  });

  it("arrow keys move through the results and back to the box", async () => {
    stubApi(routes());
    renderAt("/concepts?q=i");

    const box = await searchBox();
    const links = await screen.findAllByRole("link", { name: /function|Variables/ });
    box.focus();

    await userEvent.keyboard("{ArrowDown}");
    expect(links[0]).toHaveFocus();
    await userEvent.keyboard("{ArrowDown}");
    expect(links[1]).toHaveFocus();
    await userEvent.keyboard("{ArrowDown}");
    expect(links[1]).toHaveFocus();
    await userEvent.keyboard("{ArrowUp}{ArrowUp}");
    expect(box).toHaveFocus();
  });
});

describe("a note", () => {
  it("shows the title, draft label, body, related notes and units", async () => {
    stubApi(routes());
    renderAt("/concepts/variables");

    expect(await screen.findByRole("heading", { level: 1, name: "Variables" })).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("State", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("input()").tagName).toBe("CODE");

    const related = screen.getByRole("region", { name: "Related concepts" });
    expect(within(related).getByRole("link", { name: "print() function" })).toHaveAttribute("href", "/concepts/print-function");
    const units = screen.getByRole("region", { name: "Used in units" });
    expect(within(units).getByRole("link", { name: /PY-0\.1/ })).toHaveAttribute("href", "/units/PY-0.1");
    expect(screen.getByRole("link", { name: /official documentation/i })).toHaveAttribute("href", "https://docs.python.org/3/");
    expect(screen.getByRole("link", { name: "Go back" })).toHaveAttribute("href", "/concepts");
  });

  it("turns wiki links in the body into links", async () => {
    stubApi(routes());
    renderAt("/concepts/variables");

    expect(await screen.findByRole("link", { name: "the print() function" })).toHaveAttribute("href", "/concepts/print-function");
  });

  it("is not recorded by opening it directly", async () => {
    const calls = stubApi(routes());
    renderAt("/concepts/variables");

    await screen.findByRole("heading", { level: 1, name: "Variables" });
    expect(calls.some((c) => c.method === "PUT")).toBe(false);
  });

  it("leaves out empty sections", async () => {
    stubApi(routes({ "GET /api/v1/concepts/variables": { ...conceptNote, related: [], used_in: [], doc_url: "", status: "approved" } }));
    renderAt("/concepts/variables");

    await screen.findByRole("heading", { level: 1, name: "Variables" });
    expect(screen.queryByRole("region", { name: "Related concepts" })).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Used in units" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /official documentation/i })).not.toBeInTheDocument();
    expect(screen.queryByText("Draft")).not.toBeInTheDocument();
  });

  it("says plainly when a note does not exist, and keeps the way back", async () => {
    stubApi({ ...routes(), "GET /api/v1/concepts/gone": new Response(JSON.stringify({ detail: "x" }), { status: 404 }) });
    renderAt("/concepts/gone");

    expect(await screen.findByText(/no concept note here/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go back" })).toBeInTheDocument();
  });

  it("keeps a note's HTML as text", async () => {
    stubApi(routes({ "GET /api/v1/concepts/variables": { ...conceptNote, content_markdown: "<img src=x onerror=alert(1)> [x](javascript:alert(1))" } }));
    const { container } = { container: document.body };
    renderAt("/concepts/variables");

    await screen.findByRole("heading", { level: 1, name: "Variables" });
    await waitFor(() => expect(container.querySelector(".prose")).not.toBeNull());
    expect(container.querySelector(".prose img")).toBeNull();
    expect(container.querySelector(".prose a[href]")).toBeNull();
  });
});

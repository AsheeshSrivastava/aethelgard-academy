import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryHistory, RouterProvider } from "@tanstack/react-router";
import { render } from "@testing-library/react";
import { vi } from "vitest";

import { makeRouter } from "../router";

type Reply = unknown | ((url: URL, init?: RequestInit) => unknown);

/** Answer API calls from a route table; anything unlisted fails loudly. */
export function stubApi(routes: Record<string, Reply>) {
  const calls: { method: string; url: string }[] = [];
  const stub = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), "http://test");
    const method = init?.method ?? "GET";
    calls.push({ method, url: url.pathname + url.search });
    const key = `${method} ${url.pathname}`;
    if (!(key in routes)) {
      return new Response(JSON.stringify({ title: "Not stubbed", status: 500, detail: key }), {
        status: 500,
      });
    }
    const reply = routes[key];
    const body = typeof reply === "function" ? (reply as (u: URL, i?: RequestInit) => unknown)(url, init) : reply;
    if (body === null) return new Response(null, { status: 204 });
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", stub);
  return calls;
}

export function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = makeRouter(createMemoryHistory({ initialEntries: [path] }));
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return router;
}

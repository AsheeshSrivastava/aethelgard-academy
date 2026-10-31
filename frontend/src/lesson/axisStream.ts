export interface SseEvent {
  event: string;
  data: Record<string, unknown>;
}

/** Split buffered text into complete events; `rest` is the unfinished tail. */
export function parseSse(buffer: string): { events: SseEvent[]; rest: string } {
  const blocks = buffer.replaceAll("\r\n", "\n").split("\n\n");
  const rest = blocks.pop() ?? "";
  const events: SseEvent[] = [];
  for (const block of blocks) {
    const event = block.match(/^event: (.*)$/m)?.[1];
    const data = block.match(/^data: (.*)$/m)?.[1];
    if (event && data) events.push({ event, data: JSON.parse(data) as Record<string, unknown> });
  }
  return { events, rest };
}

/** Hide half-typed markdown, so raw backticks never flash while a reply streams. */
export function streamSafe(text: string): string {
  const lines = text.split("\n");
  const fences = lines.slice(0, -1).filter((line) => /^\s*(```|~~~)/.test(line)).length;
  if (fences % 2 === 1) return text; // Inside an open code block: everything is code.

  const last = lines.at(-1) ?? "";
  if (/^\s*`{1,2}$/.test(last)) return lines.slice(0, -1).join("\n");

  const singles = (last.replace(/```/g, "").match(/`/g) ?? []).length;
  if (singles % 2 === 0) return text;
  const cut = last.lastIndexOf("`");
  return [...lines.slice(0, -1), last.slice(0, cut) + last.slice(cut + 1)].join("\n");
}

export async function streamAxis(body: object, onEvent: (event: SseEvent) => void): Promise<void> {
  const response = await fetch("/api/v1/axis/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok || !response.body) {
    onEvent({ event: "error", data: { message: "AXIS is unavailable right now." } });
    return;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const { events, rest } = parseSse(buffer);
    buffer = rest;
    events.forEach(onEvent);
  }
}

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

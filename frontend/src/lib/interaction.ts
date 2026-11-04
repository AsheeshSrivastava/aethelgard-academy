import { useCallback, useRef } from "react";

const CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";

/** A ULID: 10 time characters then 16 random ones, so ids are unique and sort by time. */
export function newInteractionId(time: number = Date.now()): string {
  let stamp = "";
  let rest = time;
  for (let i = 0; i < 10; i += 1) {
    stamp = CROCKFORD[rest % 32] + stamp;
    rest = Math.floor(rest / 32);
  }
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return stamp + Array.from(bytes, (b) => CROCKFORD[b % 32]).join("");
}

/**
 * One id per answer (SPEC-12 section 5): sending the same answer again, such as a double
 * click, reuses it so the server records it once. Call `next` after the answer is recorded.
 */
export function useInteractionId() {
  const id = useRef(newInteractionId());
  const current = useCallback(() => id.current, []);
  const next = useCallback(() => {
    id.current = newInteractionId();
  }, []);
  return { current, next };
}

/** Model provider Settings API (SPEC-17 section 6). Keys never come here: only `key_set`. */
import { request } from "./client";

export interface ModelProfile {
  id: string;
  label: string;
  kind: "openai_compatible" | "gemini";
  base_url: string | null;
  model: string;
  paid: boolean;
  price_per_million: { input: number; output: number } | null;
  estimate_per_question_usd: number;
  key_env: string | null;
  key_set: boolean;
}

export interface ModelOverview {
  profiles: ModelProfile[];
  active: string;
  mock: boolean;
  cap_usd: number;
  month_spend_usd: number;
}

export type ConnectionTest =
  | { ok: true; model_answered: string; latency_ms: number; input_tokens: number | null; output_tokens: number | null }
  | { ok: false; reason: string };

export interface UsageRow {
  profile_id: string;
  model: string;
  calls: number;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_usd: number;
  estimated: boolean;
}

export interface ModelUsage {
  session_id: string;
  session: UsageRow[];
  month: UsageRow[];
  month_spend_usd: number;
  cap_usd: number;
}

const BASE = "/settings/models";

export const modelSettingsApi = {
  overview: () => request<ModelOverview>(BASE),
  usage: () => request<ModelUsage>(`${BASE}/usage`),
  switchTo: (profileId: string, confirmPaid: boolean) =>
    request<ModelOverview>(`${BASE}/active`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile_id: profileId, confirm_paid: confirmPaid }),
    }),
  test: () => request<ConnectionTest>(`${BASE}/test`, { method: "POST" }),
};

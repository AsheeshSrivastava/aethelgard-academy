import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  modelSettingsApi,
  type ConnectionTest,
  type ModelOverview,
  type ModelProfile,
  type UsageRow,
} from "../api/modelSettings";
import { BackLink, ErrorNote, Loading } from "../components/common";

function money(value: number, digits = 4): string {
  return `$${value.toFixed(digits)}`;
}

function priceLine(profile: ModelProfile): string {
  if (!profile.paid || !profile.price_per_million) return "Free";
  const { input, output } = profile.price_per_million;
  return `${money(input, 2)} in · ${money(output, 2)} out per 1M tokens`;
}

function tokens(value: number | null): string {
  return value === null ? "not reported" : value.toLocaleString("en-GB");
}

function ConfirmPaid({ profile, onCancel, onConfirm, busy, title, action = "Switch" }: {
  profile: ModelProfile;
  onCancel: () => void;
  onConfirm: () => void;
  busy: boolean;
  title?: string;
  action?: string;
}) {
  const [ticked, setTicked] = useState(false);
  const titleId = `confirm-${profile.id}`;
  return (
    <div role="dialog" aria-labelledby={titleId} className="card panel model-confirm">
      <h3 id={titleId}>{title ?? `Switch to ${profile.label}`}</h3>
      <p>
        {profile.label} is paid: {priceLine(profile)}, about {money(profile.estimate_per_question_usd)} per question.
        Calls stop when this month's spend reaches the cap.
      </p>
      <p>Your code and questions are sent to {profile.label}.</p>
      <label className="model-confirm-tick">
        <input type="checkbox" checked={ticked} onChange={(e) => setTicked(e.target.checked)} /> I understand the cost and
        that my work leaves this computer.
      </label>
      <div className="model-actions">
        <button type="button" className="button button-primary" disabled={!ticked || busy} onClick={onConfirm}>
          {action}
        </button>
        <button type="button" className="button" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  );
}

function ProfileCard({ profile, data, onUse }: { profile: ModelProfile; data: ModelOverview; onUse: (p: ModelProfile) => void }) {
  const active = data.active === profile.id;
  const titleId = `profile-${profile.id}`;
  return (
    <section className="card panel model-card" aria-labelledby={titleId}>
      <div className="model-card-head">
        <h2 id={titleId}>{profile.label}</h2>
        {active && <span className="chip chip-progress">In use</span>}
      </div>
      <p className="small">
        Model: <code>{profile.model}</code>
      </p>
      {profile.kind === "openai_compatible" && profile.base_url && !profile.paid && (
        <p className="small muted">Address: {profile.base_url}</p>
      )}
      <p className="small">{priceLine(profile)}</p>
      {profile.key_env && <p className="small muted">Key set: {profile.key_set ? "yes" : "no"}</p>}
      {!active && (
        <button
          type="button"
          className="button button-small"
          aria-label={`Use ${profile.label}`}
          disabled={data.mock || !profile.key_set}
          onClick={() => onUse(profile)}
        >
          Use this
        </button>
      )}
    </section>
  );
}

function UsageTable({ title, rows, labels }: { title: string; rows: UsageRow[]; labels: Record<string, string> }) {
  return (
    <div className="table-scroll">
      <table aria-label={title}>
        <caption className="eyebrow">{title}</caption>
        <thead>
          <tr>
            <th>Provider</th>
            <th>Model</th>
            <th>Calls</th>
            <th>Input tokens</th>
            <th>Output tokens</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={6} className="muted">
                No calls yet.
              </td>
            </tr>
          )}
          {rows.map((row) => (
            <tr key={`${row.profile_id}/${row.model}`}>
              <td>{labels[row.profile_id] ?? row.profile_id}</td>
              <td>{row.model}</td>
              <td>{row.calls}</td>
              <td>{tokens(row.input_tokens)}</td>
              <td>{tokens(row.output_tokens)}</td>
              <td>
                {money(row.cost_usd)}
                {row.estimated ? " (estimated)" : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TestResult({ result }: { result: ConnectionTest }) {
  if (!result.ok) return <p role="status" className="model-test-fail">{result.reason}</p>;
  return (
    <p role="status">
      Answered by {result.model_answered} in {result.latency_ms} ms ({tokens(result.input_tokens)} in,{" "}
      {tokens(result.output_tokens)} out tokens).
    </p>
  );
}

export function ModelSettings() {
  const queryClient = useQueryClient();
  const overview = useQuery({ queryKey: ["model-settings"], queryFn: modelSettingsApi.overview });
  const usage = useQuery({ queryKey: ["model-usage"], queryFn: modelSettingsApi.usage });
  const [pending, setPending] = useState<ModelProfile | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const refreshUsage = () => queryClient.invalidateQueries({ queryKey: ["model-usage"] });

  const switchTo = useMutation({
    mutationFn: ({ profile, confirm }: { profile: ModelProfile; confirm: boolean }) =>
      modelSettingsApi.switchTo(profile.id, confirm),
    onSuccess: (data, { profile }) => {
      queryClient.setQueryData(["model-settings"], data);
      setPending(null);
      setNotice(`Now using ${profile.label}.`);
    },
  });

  const [pendingJudge, setPendingJudge] = useState<ModelProfile | null>(null);
  const setJudge = useMutation({
    mutationFn: ({ profileId, confirm }: { profileId: string | null; confirm: boolean }) =>
      modelSettingsApi.setJudge(profileId, confirm),
    onSuccess: (data) => {
      queryClient.setQueryData(["model-settings"], data);
      setPendingJudge(null);
      setNotice("Judging model saved.");
    },
  });

  const test = useMutation({ mutationFn: modelSettingsApi.test, onSettled: refreshUsage });

  if (overview.isPending) return <Loading what="model settings" />;
  if (overview.isError) return <ErrorNote error={overview.error} />;

  const data = overview.data;
  const labels = Object.fromEntries(data.profiles.map((p) => [p.id, p.label]));
  const active = data.profiles.find((p) => p.id === data.active);

  function use(profile: ModelProfile) {
    setNotice(null);
    test.reset();
    if (profile.paid) setPending(profile);
    else switchTo.mutate({ profile, confirm: false });
  }

  function chooseJudge(value: string) {
    setNotice(null);
    const profile = data.profiles.find((p) => p.id === value);
    if (!profile) setJudge.mutate({ profileId: null, confirm: false });
    else if (profile.paid) setPendingJudge(profile);
    else setJudge.mutate({ profileId: profile.id, confirm: false });
  }

  return (
    <main className="container page">
      <BackLink to="/" label="Home" />
      <h1 className="page-title">AI model</h1>
      <p className="lead">
        Choose which model answers AXIS. AXIS keeps the same rules whichever you pick: it answers only from the
        curriculum, and Socratic mode never gives code.
      </p>

      {data.mock && <p className="test-mode-banner" role="status">Mock mode is on (MOCK_AI=true). No model is called.</p>}
      {notice && <p role="status">{notice}</p>}
      {switchTo.isError && <ErrorNote error={switchTo.error} />}

      <div className="grid grid-three">
        {data.profiles.map((profile) => (
          <ProfileCard key={profile.id} profile={profile} data={data} onUse={use} />
        ))}
      </div>

      {pending && (
        <ConfirmPaid
          profile={pending}
          busy={switchTo.isPending}
          onCancel={() => setPending(null)}
          onConfirm={() => switchTo.mutate({ profile: pending, confirm: true })}
        />
      )}

      <section className="card panel" aria-label="Judging model">
        <label className="field">
          <span>Judging model</span>
          <select
            value={data.judge_profile_id ?? ""}
            disabled={data.mock || setJudge.isPending}
            onChange={(event) => chooseJudge(event.target.value)}
          >
            <option value="">Same as AXIS chat</option>
            {data.profiles
              .filter((p) => p.key_set)
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
          </select>
        </label>
        <p className="small muted">
          Judges written explanations, such as the concept check, so every learner is judged the same way.
        </p>
        {setJudge.isError && <ErrorNote error={setJudge.error} />}
      </section>

      {pendingJudge && (
        <ConfirmPaid
          profile={pendingJudge}
          busy={setJudge.isPending}
          title={`Use ${pendingJudge.label} for judging`}
          action="Use for judging"
          onCancel={() => setPendingJudge(null)}
          onConfirm={() => setJudge.mutate({ profileId: pendingJudge.id, confirm: true })}
        />
      )}

      {!data.mock && active && (
        <section className="card panel" aria-label="Connection">
          <div className="model-actions">
            <button type="button" className="button" disabled={test.isPending} onClick={() => test.mutate()}>
              Test connection
            </button>
            <span className="muted small">One short call to {active.label}{active.paid ? ", which counts toward the cap" : ""}.</span>
          </div>
          {test.data && <TestResult result={test.data} />}
          {test.isError && <ErrorNote error={test.error} />}
        </section>
      )}

      <section className="card panel" aria-label="Token use">
        <p>
          Spent this month: {money(usage.data?.month_spend_usd ?? data.month_spend_usd)} of {money(data.cap_usd, 2)}
        </p>
        {usage.isPending && <Loading what="token use" />}
        {usage.isError && <ErrorNote error={usage.error} />}
        {usage.data && (
          <>
            <UsageTable title="This session" rows={usage.data.session} labels={labels} />
            <UsageTable title="This month" rows={usage.data.month} labels={labels} />
          </>
        )}
      </section>
    </main>
  );
}

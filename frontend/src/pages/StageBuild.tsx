import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";

import { api, ApiError, type AttemptResult, type StageBuild as Build } from "../api/client";
import { BackLink, ErrorNote, Loading } from "../components/common";
import { AxisPanel } from "../lesson/AxisPanel";
import { CodeEditor } from "../lesson/CodeEditor";
import { Prose } from "../lesson/Prose";
import { RunTerminal } from "../lesson/RunTerminal";
import { courseName, maturityLabel } from "../lib/format";
import { useInteractionId } from "../lib/interaction";

const NOTE_FILE = "ownership-note.txt";
const CHECK_WAIT_MS = 400;
const SAVE_WAIT_MS = 800;

type Files = Record<string, string>;
type Checked = Record<string, { met: boolean | null; detail?: string | null }>;

const starters = (build: Build): Files => Object.fromEntries(build.files.map((file) => [file.path, file.starter.join("\n")]));

function byId(requirements: { id: string; met: boolean | null; detail?: string | null }[]): Checked {
  return Object.fromEntries(requirements.map(({ id, met, detail }) => [id, { met, detail }]));
}

function BuildResult({ result }: { result: AttemptResult }) {
  const passed = result.outcome === "passed";
  return (
    <div className={`result ${passed ? "result-passed" : "result-failed"}`} role="status" aria-label="Result">
      <p className="result-title">{passed ? "Submitted" : "Not yet"}</p>
      <p className="small">{result.feedback}</p>
      {!passed && (
        <ul className="plain-list check-list">
          {result.checks
            ?.filter((check) => !check.passed)
            .map((check) => (
              <li key={check.label} className="small">
                {check.label}
                {check.detail ? ` (${check.detail})` : ""}
              </li>
            ))}
        </ul>
      )}
    </div>
  );
}

function Requirements({ build, checked }: { build: Build; checked: Checked }) {
  const met = build.requirements.filter((r) => checked[r.id]?.met === true).length;
  return (
    <section className="card panel" aria-labelledby="build-requirements">
      <h2 id="build-requirements" className="eyebrow">
        Requirements
      </h2>
      <p className="small muted">{`${met} of ${build.requirements.length} met`}</p>
      <ul className="plain-list requirement-list">
        {build.requirements.map((requirement) => {
          const result = checked[requirement.id];
          const isMet = result?.met === true;
          return (
            <li key={requirement.id} className="requirement">
              <span className={`requirement-box${isMet ? " requirement-met" : ""}`} aria-hidden="true">
                {isMet ? "✓" : ""}
              </span>
              <span className="requirement-text">
                <span className="small">
                  {requirement.label}
                  <span className="sr-only">{isMet ? " (met)" : " (not met)"}</span>
                </span>
                {result?.detail && !isMet && <span className="small requirement-detail">{result.detail}</span>}
              </span>
              <span className="mono muted small">{requirement.unit_id}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function Workspace({ build, courseId, stage, initial, initialNote }: { build: Build; courseId: string; stage: number; initial: Files; initialNote: string }) {
  const client = useQueryClient();
  const [files, setFiles] = useState(initial);
  const [note, setNote] = useState(initialNote);
  const [open, setOpen] = useState(build.entry);
  const [version, setVersion] = useState(0);
  const [live, setLive] = useState<Checked>({});
  const [verified, setVerified] = useState<Checked>({});
  const [confirming, setConfirming] = useState(false);
  const [submitted, setSubmitted] = useState<AttemptResult | null>(null);
  const started = useRef(false);
  const liveRound = useRef(0);
  const entryEdits = useRef(0);

  const stageArgs = { courseId, stage };

  // The server holds every rule, so the page asks it instead of judging the work here.
  useEffect(() => {
    const round = ++liveRound.current;
    const timer = setTimeout(() => {
      void api
        .checkBuild(stageArgs, { files, ownership_note: note, run_checks: false })
        .then((result) => {
          if (round === liveRound.current) setLive(byId(result.requirements));
        })
        .catch(() => undefined);
    }, CHECK_WAIT_MS);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [files, note]);

  useEffect(() => {
    if (!started.current) {
      started.current = true;
      return;
    }
    const timer = setTimeout(() => {
      const saved = { ...files, [NOTE_FILE]: note };
      void api.saveDraft(build.exercise_id, saved).catch(() => undefined);
      client.setQueryData(["draft", build.exercise_id], { files: saved });
    }, SAVE_WAIT_MS);
    return () => clearTimeout(timer);
  }, [files, note, build.exercise_id, client]);

  function edit(value: string) {
    setFiles((current) => ({ ...current, [open]: value }));
    if (open === build.entry) {
      entryEdits.current += 1;
      setVerified({});
    }
  }

  const verify = useMutation({
    mutationFn: () => {
      const editsAtStart = entryEdits.current;
      return api.checkBuild(stageArgs, { files, ownership_note: note, run_checks: true }).then((result) => ({ result, editsAtStart }));
    },
    onSuccess: ({ result, editsAtStart }) => {
      if (editsAtStart === entryEdits.current) setVerified(byId(result.requirements));
    },
  });

  const interaction = useInteractionId();
  const submit = useMutation({
    mutationFn: () =>
      api.attempt({ exercise_id: build.exercise_id, activity: "build", files, ownership_note: note, interaction_id: interaction.current() }),
    onSuccess: (result) => {
      interaction.next();
      setSubmitted(result);
      void client.invalidateQueries({ queryKey: ["ledger"] });
      void client.invalidateQueries({ queryKey: ["proficiency"] });
      void client.invalidateQueries({ queryKey: ["courseMap"] });
    },
  });

  const reset = useMutation({
    mutationFn: () => api.resetBuild(stageArgs),
    onSuccess: () => {
      client.setQueryData(["draft", build.exercise_id], { files: {} });
      started.current = false;
      entryEdits.current += 1;
      setFiles(starters(build));
      setNote("");
      setVerified({});
      setSubmitted(null);
      setConfirming(false);
      setVersion(version + 1);
    },
  });

  const checked: Checked = Object.fromEntries(
    build.requirements.map((r) => {
      const seen = live[r.id];
      return [r.id, seen?.met === null ? (verified[r.id] ?? seen) : (seen ?? { met: null })];
    }),
  );
  const ready = build.requirements.every((r) => checked[r.id]?.met === true);
  const getCode = useCallback(() => files[build.entry] ?? "", [files, build.entry]);
  // Verify speaks only for the checks it runs; live results cover the rest.
  const firstFailure = build.requirements
    .filter((r) => live[r.id]?.met === null)
    .some((r) => verified[r.id]?.met === false);
  const done = submitted?.outcome === "passed" || build.submitted;

  return (
    <>
      <div className="build-actions">
        <button type="button" className="button button-small" onClick={() => setConfirming(true)}>
          Reset build
        </button>
      </div>
      {confirming && (
        <div className="card reset-confirm" role="alertdialog" aria-label="Reset this build">
          <p className="small">Your files and note go back to the starter. Evidence already recorded stays in your ledger.</p>
          <div className="actions">
            <button type="button" className="button button-small" onClick={() => setConfirming(false)}>
              Cancel
            </button>
            <button type="button" className="button button-small button-primary" disabled={reset.isPending} onClick={() => reset.mutate()}>
              Reset build
            </button>
          </div>
        </div>
      )}
      <div className="build-layout">
        <aside className="build-side" aria-label="Brief and requirements">
          <section className="card panel" aria-labelledby="build-brief">
            <h2 id="build-brief" className="eyebrow">
              Brief
            </h2>
            <Prose>{build.brief_markdown}</Prose>
            <h3 className="eyebrow">A correct run looks like this</h3>
            <pre className="material">{build.sample_run.join("\n")}</pre>
          </section>
          <Requirements build={build} checked={checked} />
        </aside>

        <section className="build-work" aria-label="Build workspace">
          <div className="workspace">
            <div className="workspace-head">
              <div className="file-tabs">
                {build.files.map((file) => (
                  <button
                    key={file.path}
                    type="button"
                    className={`file-tab${file.path === open ? " file-tab-open" : ""}`}
                    aria-pressed={file.path === open}
                    onClick={() => setOpen(file.path)}
                  >
                    {file.path}
                  </button>
                ))}
              </div>
              <button type="button" className="button button-small" disabled={verify.isPending} onClick={() => verify.mutate()}>
                {verify.isPending ? "Checking…" : "Verify"}
              </button>
            </div>
            <CodeEditor key={`${open}-${version}`} value={files[open] ?? ""} onChange={edit} label={`${open} code`} />
            <RunTerminal getCode={getCode} exerciseId={build.exercise_id} entry={build.entry} />
          </div>
          {verify.isError && <ErrorNote error={verify.error} />}
          {verify.isSuccess && !verify.isPending && Object.keys(verified).length > 0 && (
            <p className="small" role="status">
              {firstFailure ? "Verify found a difference. Check the requirements list." : "Verify passed."}
            </p>
          )}
          <form
            className="card panel"
            onSubmit={(event) => {
              event.preventDefault();
              submit.mutate();
            }}
          >
            <div className="field">
              <label htmlFor="ownership-note">Ownership note</label>
              <span id="ownership-hint" className="small muted">
                What did you write yourself, what did a tool or AXIS help with, and how did you check the result?
              </span>
              <textarea id="ownership-note" aria-describedby="ownership-hint" rows={4} value={note} onChange={(event) => setNote(event.target.value)} />
            </div>
            <div className="actions">
              <button type="submit" className="button button-primary" disabled={!ready || submit.isPending}>
                {submit.isPending ? "Checking…" : "Submit build"}
              </button>
              <span className="small muted">{ready ? "Ready to submit." : "Meet every requirement to submit."}</span>
            </div>
            {done && !submitted && <p className="small">You already submitted this build. You can improve it and submit again.</p>}
          </form>
          {submit.isError && <ErrorNote error={submit.error} />}
          {submitted && <BuildResult result={submitted} />}
        </section>

        <div className="build-axis">
          <AxisPanel unitId={build.proves[0]?.unit_id ?? ""} step="build" exerciseId={build.exercise_id} getCode={getCode} socraticOnly />
          <section className="card panel" aria-labelledby="build-proves">
            <h2 id="build-proves" className="eyebrow">
              What this build proves
            </h2>
            <ul className="plain-list">
              {build.proves.map((proof) => (
                <li key={proof.skill_id} className="small">
                  {proof.label} <span className="mono muted">{proof.unit_id}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </>
  );
}

export function StageBuild() {
  const { courseId, stage } = useParams({ from: "/courses/$courseId/stages/$stage/build" });
  const number = Number(stage);
  const build = useQuery({ queryKey: ["stageBuild", courseId, number], queryFn: () => api.stageBuild({ courseId, stage: number }), retry: false });
  const exerciseId = build.data?.exercise_id;
  const draft = useQuery({
    queryKey: ["draft", exerciseId],
    queryFn: () => api.getDraft(exerciseId ?? ""),
    enabled: exerciseId !== undefined,
    staleTime: Infinity,
  });
  const closed = build.error instanceof ApiError && (build.error.status === 423 || build.error.status === 404);

  const data = build.data;
  const { [NOTE_FILE]: savedNote, ...savedFiles } = draft.data?.files ?? {};

  return (
    <main className="lesson-page">
      <BackLink to="/courses/$courseId" params={{ courseId }} label={`${courseName(courseId)} course map`} />
      {build.isPending && <Loading what="the build" />}
      {closed && <p>{(build.error as ApiError).message}</p>}
      {build.isError && !closed && <ErrorNote error={build.error} />}
      {data && (
        <>
          <div className="concept-head">
            <span className="mono muted">{data.stage_label} build</span>
            <span className="chip chip-build">{data.kind === "script" ? "Script" : "Mini-project"}</span>
            <span className="chip chip-maturity">{maturityLabel(data.maturity)}</span>
            {data.status === "draft" && <span className="chip">Draft</span>}
          </div>
          <h1 className="page-title build-title">{data.title}</h1>
          {draft.isPending ? (
            <Loading what="your work" />
          ) : (
            <Workspace build={data} courseId={courseId} stage={number} initial={{ ...starters(data), ...savedFiles }} initialNote={savedNote ?? ""} />
          )}
        </>
      )}
    </main>
  );
}

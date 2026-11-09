import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";

import { api, ApiError, type ColdCheckStatus, type Exercise, type Unit } from "../api/client";
import { ErrorNote, Loading } from "../components/common";
import { ResetUnit } from "../components/ResetUnit";
import { AxisPanel } from "../lesson/AxisPanel";
import { AxisResizer } from "../lesson/AxisResizer";
import { loadAxisWidth } from "../lesson/axisWidth";
import { CodeWorkspace, ItemForm, type Answer } from "../lesson/items";
import { Prose } from "../lesson/Prose";
import { NextLink, Result } from "../lesson/Result";
import { explainParts, nextStep } from "../lesson/steps";
import { AiJudgement } from "../components/AiJudgement";
import { coldCheckMessage, stepName } from "../lib/format";
import { useInteractionId } from "../lib/interaction";
import { useNow } from "../lib/useNow";

function useLessonState(unitId: string) {
  const client = useQueryClient();
  const key = ["unitState", unitId];
  const state = useQuery({ queryKey: key, queryFn: () => api.unitState(unitId) });

  const save = useCallback(
    (step: string | null, done: string[]) => {
      client.setQueryData(key, { step, done_steps: done });
      void api.saveUnitState(unitId, { step, done_steps: done }).catch(() => undefined);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [client, unitId],
  );

  const markDone = useCallback(
    (step: string) => {
      const current = client.getQueryData<{ step?: string | null; done_steps?: string[] }>(key);
      const done = current?.done_steps ?? [];
      if (!done.includes(step)) save(current?.step ?? step, [...done, step]);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [client, save],
  );

  return { state, save, markDone };
}

function StepRail({ unit, step, done, cold }: { unit: Unit; step: string; done: string[]; cold?: ColdCheckStatus }) {
  return (
    <nav className="step-rail" aria-label="Lesson steps">
      {(unit.activities ?? []).map((name) => {
        const isDone = done.includes(name) || (name === "cold_check" && cold?.state === "passed");
        const locked = name === "cold_check" && cold !== undefined && cold.state !== "available" && cold.state !== "passed";
        const note = isDone ? " (done)" : locked ? " (locked)" : "";
        return (
          <Link
            key={name}
            to="/units/$unitId/$step"
            params={{ unitId: unit.unit_id, step: name }}
            className={`rail-step${name === step ? " rail-current" : ""}${isDone ? " rail-done" : ""}${locked ? " rail-locked" : ""}`}
            aria-label={`${stepName(name)}${note}`}
          >
            <span aria-hidden="true">{isDone ? "✓ " : ""}</span>
            {stepName(name)}
          </Link>
        );
      })}
    </nav>
  );
}

function VideoStep({ unit, next, onDone, done }: { unit: Unit; next: string | null; onDone: () => void; done: boolean }) {
  const media = unit.media?.find((item) => item.kind === "video");
  const [failed, setFailed] = useState(false);
  return (
    <div className="card lesson-card">
      {media && !failed ? (
        <video className="video" controls preload="metadata" src={media.url} aria-label={media.title} onError={() => setFailed(true)}>
          Your browser cannot play this video.
        </video>
      ) : (
        <p className="video-placeholder">The video for this unit is not ready yet. You can go straight to Explain.</p>
      )}
      <h1 className="step-title">{media?.title ?? unit.title}</h1>
      {!!media?.timestamps?.length && (
        <div>
          <h2 className="eyebrow">Chapters</h2>
          <ul className="plain-list chapters">
            {media.timestamps.map((chapter) => (
              <li key={chapter.time}>
                <span className="mono muted">{chapter.time}</span> {chapter.topic}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="actions">
        {!done && (
          <button type="button" className="button" onClick={onDone}>
            Mark as watched
          </button>
        )}
        <NextLink unitId={unit.unit_id} step={next} />
      </div>
    </div>
  );
}

function ExplainStep({ unit, next, onDone }: { unit: Unit; next: string | null; onDone: () => void }) {
  const [text, setText] = useState("");
  const client = useQueryClient();
  const check = useMutation({
    mutationFn: () => api.explain(unit.unit_id, text),
    onSuccess: (result) => {
      // The step stays open until a judgement exists (ADR-0026): an unjudged answer writes nothing.
      if (result.status === "judged") onDone();
      return client.invalidateQueries({ queryKey: ["coldCheck", unit.unit_id] });
    },
  });
  const prompt = unit.concept_check_config?.prompt as string | undefined;
  // Parts come from the lesson's "##" headings; "Say it back" is always last (SPEC-19 section 1).
  const parts = [...explainParts(unit.lesson_markdown ?? ""), { title: SAY_IT_BACK, body: "" }];
  const [index, setIndex] = useState(0);
  const [seen, setSeen] = useState(0);
  const part = parts[index]!;
  const sayItBack = index === parts.length - 1;
  // Parts change without touching the URL or history: the Back arrow still leaves the lesson.
  const heading = useRef<HTMLHeadingElement>(null);
  const moved = useRef(false);
  const go = (to: number) => {
    moved.current = true;
    setIndex(to);
    setSeen((most) => Math.max(most, to));
  };
  // After a move, put focus (and the view) on the new part's heading, not on the first load.
  useEffect(() => {
    if (!moved.current) return;
    heading.current?.focus();
    heading.current?.scrollIntoView?.({ block: "nearest" });
  }, [index]);

  return (
    <div className="explain">
      <nav className="explain-parts" aria-label="Explain parts">
        <span className="eyebrow explain-eyebrow">Explain · {parts.length} short parts</span>
        <ol>
          {parts.map((item, at) => {
            const state = at === index ? "current" : at <= seen ? "done" : "todo";
            return (
              <li key={item.title + at}>
                <button type="button" className={`explain-part explain-part-${state}`} aria-current={at === index ? "step" : undefined} onClick={() => go(at)}>
                  <span className="explain-dot" aria-hidden="true">
                    {state === "done" ? "✓" : at + 1}
                  </span>
                  <span>{item.title}</span>
                </button>
              </li>
            );
          })}
        </ol>
        {(unit.wiki_links ?? []).length > 0 && (
          <div className="explain-notes">
            <span className="small muted">Concept notes</span>
            <span className="explain-note-links">
              {(unit.wiki_links ?? []).map((link) => (
                <Link key={link.wiki_slug} to="/concepts/$slug" params={{ slug: link.wiki_slug }} className="explain-note">
                  {link.concept_name}
                </Link>
              ))}
            </span>
          </div>
        )}
        {next && (
          <div className="explain-skip">
            <span className="explain-skip-title">Already know this?</span>
            <span className="small muted">Skip ahead and try {stepName(next)}. You can come back any time.</span>
            <Link to="/units/$unitId/$step" params={{ unitId: unit.unit_id, step: next }} className="button button-small">
              Try {stepName(next)} now
            </Link>
          </div>
        )}
      </nav>

      <div className="explain-main">
        <article className="card lesson-card explain-card" aria-labelledby="explain-part-title">
          <span className="mono muted small">
            Part {index + 1} of {parts.length}
          </span>
          {index === 0 && <h1 className="step-title">{unit.concept_line}</h1>}
          <h2 id="explain-part-title" className="explain-part-title" ref={heading} tabIndex={-1}>
            {part.title}
          </h2>
          {!sayItBack && (
            <Prose wikiLinks unitId={unit.unit_id}>
              {part.body}
            </Prose>
          )}
          {sayItBack && (
            <>
      <form
        className="concept-check"
        onSubmit={(event) => {
          event.preventDefault();
          check.mutate();
        }}
      >
        <h2 className="panel-title">Concept check</h2>
        <p className="small">{prompt ?? `Explain in your own words: ${unit.concept_line}`}</p>
        <label className="field">
          <span>Your explanation</span>
          <textarea rows={5} value={text} onChange={(event) => setText(event.target.value)} />
        </label>
        <div className="actions">
          <button type="submit" className="button button-primary" disabled={!text.trim() || check.isPending}>
            {check.isPending ? "Checking…" : "Check my explanation"}
          </button>
        </div>
        <p className="small muted">A shaky answer never blocks you. It tells AXIS what to revisit with you.</p>
      </form>
      {check.isError && <ErrorNote error={check.error} />}
      {check.data && (
        <>
          <AiJudgement
            judgement={check.data}
            onDispute={check.data.interaction_id ? () => api.disputeJudgement(check.data.interaction_id as string) : undefined}
          />
          <NextLink unitId={unit.unit_id} step={next} />
        </>
      )}
            </>
          )}
        </article>
        <div className="explain-nav">
          {index > 0 && (
            <button type="button" className="button" onClick={() => go(index - 1)}>
              <span aria-hidden="true">←</span>Part {index}: {parts[index - 1]!.title}
            </button>
          )}
          {!sayItBack && (
            <button type="button" className="button button-primary explain-next" onClick={() => go(index + 1)}>
              Part {index + 2}: {parts[index + 1]!.title}
              <span aria-hidden="true">→</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

const SAY_IT_BACK = "Say it back";

function useAttempt(exercise: Exercise | undefined, activity: string, onDone: () => void) {
  const client = useQueryClient();
  const interaction = useInteractionId();
  return useMutation({
    mutationFn: (answer: Answer) =>
      api.attempt({ exercise_id: exercise?.exercise_id ?? "", activity, ...answer, interaction_id: interaction.current() }),
    onSuccess: () => {
      interaction.next();
      onDone();
      void client.invalidateQueries({ queryKey: ["ledger"] });
      void client.invalidateQueries({ queryKey: ["proficiency"] });
      void client.invalidateQueries({ queryKey: ["coldCheck"] });
      void client.invalidateQueries({ queryKey: ["coldFeedback"] });
    },
  });
}

function ExerciseStep({ unit, step, next, onDone, onExercise }: { unit: Unit; step: string; next: string | null; onDone: () => void; onExercise: (id?: string) => void }) {
  const client = useQueryClient();
  const key = ["exercise", unit.unit_id, step];
  const exercise = useQuery({ queryKey: key, queryFn: () => api.exercise(unit.unit_id, step), retry: false });
  const attempt = useAttempt(exercise.data, step, onDone);
  const regenerate = useMutation({
    mutationFn: () => api.regenerate(unit.unit_id, step),
    onSuccess: (fresh) => {
      attempt.reset();
      client.setQueryData(key, fresh);
    },
  });

  useEffect(() => {
    onExercise(exercise.data?.exercise_id);
    return () => onExercise(undefined);
  }, [exercise.data?.exercise_id, onExercise]);

  if (exercise.isPending) return <Loading what="the exercise" />;
  if (exercise.isError) {
    const missing = exercise.error instanceof ApiError && exercise.error.status === 404;
    return (
      <div className="card lesson-card">
        <h1 className="step-title">{stepName(step)}</h1>
        {missing ? (
          <>
            <p>This activity is not written yet.</p>
            <NextLink unitId={unit.unit_id} step={next} />
          </>
        ) : (
          <ErrorNote error={exercise.error} />
        )}
      </div>
    );
  }

  const data = exercise.data;
  // A Make step (Amendment A1.3): one program written from a blank file, so there is nothing to regenerate.
  const make = data.item_type === "playground" && !!data.playground?.make;
  return (
    <div className="card lesson-card">
      <div className="exercise-head">
        <span className="eyebrow">
          {make ? "Make · from a blank file" : `${stepName(step)} · ${data.origin === "authored" ? "Authored" : "Generated"} variant ${data.variant_no}`}
        </span>
        {!make && (
          <button type="button" className="button button-small" disabled={regenerate.isPending} onClick={() => regenerate.mutate()}>
            Regenerate
          </button>
        )}
      </div>
      <Prose>{data.prompt_markdown}</Prose>
      {make && (
        <p className="cold-notice" role="note">
          Write the whole program yourself. Run it as often as you like; when you submit, hidden tests check it. You can submit again, and your newest result counts.
        </p>
      )}
      <ItemForm key={data.exercise_id} exercise={data} busy={attempt.isPending} submitLabel="Submit answer" onSubmit={(answer) => attempt.mutate(answer)} />
      {regenerate.isError && <ErrorNote error={regenerate.error} />}
      {attempt.isError && <ErrorNote error={attempt.error} />}
      {attempt.data && <Result result={attempt.data} unitId={unit.unit_id} next={next} />}
    </div>
  );
}

function PlaygroundStep({ unit, next, onDone, onCode }: { unit: Unit; next: string | null; onDone: () => void; onCode: (get: (() => string) | undefined) => void }) {
  const exercise = useQuery({ queryKey: ["exercise", unit.unit_id, "playground"], queryFn: () => api.exercise(unit.unit_id, "playground"), retry: false });
  const attempt = useAttempt(exercise.data, "playground", onDone);

  if (exercise.isPending) return <Loading what="the playground" />;
  if (exercise.isError) {
    return (
      <div className="card lesson-card">
        <h1 className="step-title">Playground</h1>
        <p>The playground for this unit is not written yet.</p>
        <NextLink unitId={unit.unit_id} step={next} />
      </div>
    );
  }

  const data = exercise.data;
  return (
    <div className="card lesson-card">
      <div className="exercise-head">
        <span className="eyebrow">Playground · Practice, not graded</span>
      </div>
      <h1 className="step-title">{data.prompt_markdown}</h1>
      <CodeWorkspace exerciseId={data.exercise_id} starter={data.playground?.starter ?? []} label="Your code">
        {(getCode) => {
          onCode(getCode);
          return (
            <div className="actions">
              <button type="button" className="button button-primary" disabled={attempt.isPending} onClick={() => attempt.mutate({ files: { "solution.py": getCode() } })}>
                {attempt.isPending ? "Checking…" : "Verify"}
              </button>
            </div>
          );
        }}
      </CodeWorkspace>
      {attempt.isError && <ErrorNote error={attempt.error} />}
      {attempt.data && <Result result={attempt.data} unitId={unit.unit_id} next={next} />}
    </div>
  );
}

/** Option A feedback (ADR-0022 section 2.5): your answer, a hint, where to practise; worked answers only once passed. */
function ColdSummary({ unitId }: { unitId: string }) {
  const feedback = useQuery({ queryKey: ["coldFeedback", unitId], queryFn: () => api.coldCheckFeedback(unitId) });
  const answered = !!feedback.data?.items.some((item) => item.passed !== null);

  useEffect(() => {
    if (answered) void api.logEvent({ event_type: "feedback_viewed", unit_id: unitId, activity: "cold_check" });
  }, [answered, unitId]);

  if (!answered) return null;
  return (
    <section className="cold-summary" aria-labelledby="cold-result">
      <h2 id="cold-result" className="panel-title">
        Your result
      </h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Skill</th>
              <th scope="col">Result</th>
              <th scope="col">Your answer</th>
              <th scope="col">Next</th>
            </tr>
          </thead>
          <tbody>
            {feedback.data!.items.map((item, index) => (
              <tr key={`${item.skill_id}-${index}`}>
                <td>
                  <span className="mono">{item.skill_id}</span> {item.skill_name}
                </td>
                <td>{item.passed === null ? "Not answered yet" : item.passed ? "Passed" : "Not yet"}</td>
                <td>{item.your_answer ?? ""}</td>
                <td>
                  {item.passed === false && (
                    <>
                      {item.hint && <p className="small">{item.hint}</p>}
                      <Link to="/units/$unitId/$step" params={{ unitId, step: item.practice_activity }}>
                        Practise {stepName(item.practice_activity)}
                      </Link>
                    </>
                  )}
                  {item.passed && item.worked && (
                    <details>
                      <summary>Worked answer</summary>
                      <p className="small mono">{Array.isArray(item.worked.correct) ? item.worked.correct.join(" / ") : JSON.stringify(item.worked.correct).replace(/^"|"$/g, "")}</p>
                      {(item.worked.why ?? []).map((line) => (
                        <p key={line} className="small">
                          {line}
                        </p>
                      ))}
                    </details>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ColdCheckItem({ unit }: { unit: Unit }) {
  const client = useQueryClient();
  const key = ["exercise", unit.unit_id, "cold_check"];
  const exercise = useQuery({ queryKey: key, queryFn: () => api.exercise(unit.unit_id, "cold_check"), retry: false });
  const attempt = useAttempt(exercise.data, "cold_check", () => undefined);

  if (exercise.isPending) return <Loading what="the Cold Check" />;
  if (exercise.isError) {
    const missing = exercise.error instanceof ApiError && exercise.error.status === 404;
    return missing ? <p>This unit's Cold Check is not written yet.</p> : <ErrorNote error={exercise.error} />;
  }

  const data = exercise.data;
  return (
    <>
      <Prose>{data.prompt_markdown}</Prose>
      <ItemForm
        key={data.exercise_id}
        exercise={data}
        busy={attempt.isPending}
        submitLabel="Submit, one try"
        onSubmit={(answer) =>
          attempt.mutate(answer, {
            onSuccess: () => {
              attempt.reset();
              void client.invalidateQueries({ queryKey: key });
            },
          })
        }
      />
      {attempt.isError && <ErrorNote error={attempt.error} />}
    </>
  );
}

function ColdCheckStep({ unit, cold }: { unit: Unit; cold?: ColdCheckStatus }) {
  const now = useNow(30_000);
  const client = useQueryClient();
  const opensAt = cold?.available_at ? new Date(cold.available_at).getTime() : 0;
  const waiting = cold?.state === "waiting" || cold?.state === "failed_waiting";
  const shouldRefresh = waiting && opensAt > 0 && now.getTime() >= opensAt;

  useEffect(() => {
    if (shouldRefresh) void client.invalidateQueries({ queryKey: ["coldCheck", unit.unit_id] });
  }, [shouldRefresh, client, unit.unit_id]);

  return (
    <div className="card lesson-card">
      <h1 className="step-title">Cold Check</h1>
      {!cold && <Loading what="the Cold Check" />}
      {cold && cold.state !== "available" && <p className="cold-message">{coldCheckMessage(cold, now)}</p>}
      {cold?.state === "available" && (
        <>
          <p className="cold-notice" role="note">
            One try for each skill. AXIS is off, so this shows what you can do on your own.
          </p>
          <ColdCheckItem unit={unit} />
        </>
      )}
      {cold && cold.state !== "not_ready" && cold.state !== "waiting" && <ColdSummary unitId={unit.unit_id} />}
      {cold?.state === "passed" && (
        <Link to="/progress" className="button button-primary">
          See My progress
        </Link>
      )}
    </div>
  );
}

export function Lesson() {
  const { unitId, step } = useParams({ from: "/units/$unitId/$step" });
  const unit = useQuery({ queryKey: ["unit", unitId], queryFn: () => api.unit(unitId) });
  const cold = useQuery({ queryKey: ["coldCheck", unitId], queryFn: () => api.coldCheck(unitId) });
  const { state, save, markDone } = useLessonState(unitId);
  const [exerciseId, setExerciseId] = useState<string | undefined>();
  const codeGetter = useRef<(() => string) | undefined>(undefined);
  const layout = useRef<HTMLDivElement>(null);
  const [axisWidth, setAxisWidth] = useState(loadAxisWidth);

  const stepKnown = unit.data?.activities?.includes(step);
  const stateReady = state.isSuccess;
  const doneSteps = state.data?.done_steps ?? [];

  useEffect(() => {
    if (stepKnown && stateReady && state.data?.step !== step) save(step, doneSteps);
    // Only entering a step should record it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, stepKnown, stateReady]);

  const finish = useCallback(() => markDone(step), [markDone, step]);
  const onCode = useCallback((get: (() => string) | undefined) => {
    codeGetter.current = get;
  }, []);

  useEffect(() => () => {
    codeGetter.current = undefined;
  }, [step]);

  // Opening and leaving a step go to the interaction log (ADR-0022); nothing waits for it.
  useEffect(() => {
    if (!stepKnown) return;
    const openedAt = Date.now();
    void api.logEvent({ event_type: "opened", unit_id: unitId, activity: step });
    return () => {
      void api.logEvent({
        event_type: "closed",
        unit_id: unitId,
        activity: step,
        payload: { seconds_open: Math.round((Date.now() - openedAt) / 1000) },
      });
    };
  }, [unitId, step, stepKnown]);

  if (unit.isPending) {
    return (
      <main className="lesson-page">
        <Loading what="the lesson" />
      </main>
    );
  }
  if (unit.isError) {
    return (
      <main className="lesson-page">
        <ErrorNote error={unit.error} />
      </main>
    );
  }

  const data = unit.data;
  const steps = data.activities ?? [];
  const next = nextStep(steps, step);
  const onColdCheck = step === "cold_check";

  return (
    <main className="lesson-page">
      <div className="lesson-top">
        <div className="lesson-head">
          <span className="mono muted small">
            {data.unit_id} · {data.stage_label}
          </span>
          <span className="lesson-unit-title">{data.title}</span>
        </div>
        <StepRail unit={data} step={step} done={doneSteps} cold={cold.data} />
        <span className="lesson-progress">
          <span className="cm-bar" aria-hidden="true">
            <span style={{ width: `${(steps.filter((name) => doneSteps.includes(name)).length / Math.max(steps.length, 1)) * 100}%` }} />
          </span>
          <span className="muted small">
            {steps.filter((name) => doneSteps.includes(name)).length} of {steps.length} steps done
          </span>
        </span>
        <ResetUnit unitId={unitId} />
      </div>

      {!stepKnown ? (
        <ErrorNote error={new Error(`This unit has no step called "${step}".`)} />
      ) : (
        <div ref={layout} className="lesson-layout" style={{ "--axis-width": `${axisWidth}px` } as CSSProperties}>
          <section className="lesson-content" aria-label="Lesson content">
            {step === "video" && <VideoStep unit={data} next={next} onDone={finish} done={doneSteps.includes("video")} />}
            {step === "explain" && <ExplainStep unit={data} next={next} onDone={finish} />}
            {step === "playground" && <PlaygroundStep unit={data} next={next} onDone={finish} onCode={onCode} />}
            {onColdCheck && <ColdCheckStep unit={data} cold={cold.data} />}
            {!["video", "explain", "playground", "cold_check"].includes(step) && (
              <ExerciseStep key={step} unit={data} step={step} next={next} onDone={finish} onExercise={setExerciseId} />
            )}
          </section>
          {!onColdCheck && (
            <>
              <AxisResizer layout={layout} width={axisWidth} onChange={setAxisWidth} />
              <AxisPanel unitId={unitId} step={step} exerciseId={exerciseId} getCode={() => codeGetter.current?.()} />
            </>
          )}
        </div>
      )}
    </main>
  );
}

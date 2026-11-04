import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import { api, ApiError, type Exercise } from "../api/client";
import { BackLink, ErrorNote, Loading } from "../components/common";
import { ItemForm } from "../lesson/items";
import { Prose } from "../lesson/Prose";
import { courseName, reviewMessage } from "../lib/format";
import { useInteractionId } from "../lib/interaction";
import { useNow } from "../lib/useNow";

/** One item, one try, no answer shown. A failed item can come back (SPEC-16 section 3.3). */
function RoundItem({ exercise, activity, onAnswered }: { exercise: Exercise; activity: string; onAnswered: () => void }) {
  const client = useQueryClient();
  const interaction = useInteractionId();
  const attempt = useMutation({
    mutationFn: (answer: object) =>
      api.attempt({ exercise_id: exercise.exercise_id, activity, ...answer, interaction_id: interaction.current() }),
    onSuccess: () => {
      interaction.next();
      onAnswered();
      void client.invalidateQueries({ queryKey: ["ledger"] });
      void client.invalidateQueries({ queryKey: ["proficiency"] });
      void client.invalidateQueries({ queryKey: ["courseMap"] });
    },
  });
  return (
    <>
      <Prose>{exercise.prompt_markdown}</Prose>
      <ItemForm key={exercise.exercise_id} exercise={exercise} busy={attempt.isPending} submitLabel="Submit, one try" onSubmit={(answer) => attempt.mutate(answer)} />
      {attempt.isError && <ErrorNote error={attempt.error} />}
    </>
  );
}

function UnitLinks({ units, label }: { units: string[]; label: string }) {
  return (
    <ul className="plain-list review-units" aria-label={label}>
      {units.map((unitId) => (
        <li key={unitId}>
          <Link to="/units/$unitId" params={{ unitId }} className="mono">
            {unitId}
          </Link>
        </li>
      ))}
    </ul>
  );
}

function StageItems({ courseId, stage, total, done }: { courseId: string; stage: number; total: number; done: number }) {
  const client = useQueryClient();
  const key = ["stageReviewItem", courseId, stage];
  const exercise = useQuery({ queryKey: key, queryFn: () => api.stageReviewExercise({ courseId, stage }), retry: false, gcTime: 0 });
  const exerciseId = exercise.data?.exercise_id;

  // The round is made when the first item is served, so the count arrives after it.
  useEffect(() => {
    if (exerciseId) void client.invalidateQueries({ queryKey: ["stageReview", courseId, stage] });
  }, [exerciseId, client, courseId, stage]);

  if (exercise.isPending) return <Loading what="the review" />;
  if (exercise.isError) return <ErrorNote error={exercise.error} />;
  return (
    <>
      {total > 0 && <p className="eyebrow">{`Item ${Math.min(done + 1, total)} of ${total}`}</p>}
      <RoundItem
        exercise={exercise.data}
        activity="stage_review"
        onAnswered={() => {
          void client.invalidateQueries({ queryKey: key });
          void client.invalidateQueries({ queryKey: ["stageReview", courseId, stage] });
        }}
      />
    </>
  );
}

export function StageReview() {
  const { courseId, stage } = useParams({ from: "/courses/$courseId/stages/$stage/review" });
  const number = Number(stage);
  const client = useQueryClient();
  const now = useNow(30_000);
  const status = useQuery({ queryKey: ["stageReview", courseId, number], queryFn: () => api.stageReview({ courseId, stage: number }), retry: false });
  const map = useQuery({ queryKey: ["courseMap", courseId], queryFn: () => api.courseMap(courseId) });
  const view = map.data?.stages.find((s) => s.stage === number);
  const data = status.data;

  const opensAt = data?.available_at ? new Date(data.available_at).getTime() : 0;
  const shouldRefresh = data?.state === "failed_waiting" && opensAt > 0 && now.getTime() >= opensAt;
  useEffect(() => {
    if (shouldRefresh) void client.invalidateQueries({ queryKey: ["stageReview", courseId, number] });
  }, [shouldRefresh, client, courseId, number]);

  return (
    <main className="container page review-page">
      <BackLink to="/courses/$courseId" params={{ courseId }} label={`${courseName(courseId)} course map`} />
      <div className="card lesson-card">
        <h1 className="step-title">{view ? `${view.label} review` : "Stage review"}</h1>
        {status.isPending && <Loading what="the review" />}
        {status.isError && <ErrorNote error={status.error} />}
        {data && data.state !== "available" && <p className="cold-message">{reviewMessage(data, now)}</p>}
        {data?.state === "available" && (
          <>
            <p className="cold-notice" role="note">
              A mix from every unit of this stage. One try for each item. AXIS is off, so this shows what you can do on your own.
            </p>
            <StageItems courseId={courseId} stage={number} total={data.items_total ?? 0} done={data.items_done ?? 0} />
          </>
        )}
        {data?.state === "not_ready" && <UnitLinks units={data.pending_units ?? []} label="Units left" />}
        {data?.state === "failed_waiting" && (
          <>
            <h2 className="panel-title">Strengthen these units first</h2>
            <UnitLinks units={data.failed_units ?? []} label="Units to strengthen" />
          </>
        )}
        {data?.state === "passed" && (
          <div className="actions">
            {view?.build?.authored && (
              <Link to="/courses/$courseId/stages/$stage/build" params={{ courseId, stage }} className="button button-primary">
                Go to the build
              </Link>
            )}
            <Link to="/progress" className="button">
              See My progress
            </Link>
          </div>
        )}
      </div>
    </main>
  );
}

export function Recheck() {
  const { skillId, days } = useParams({ from: "/reviews/$skillId/$days" });
  const number = Number(days);
  const client = useQueryClient();
  const [answered, setAnswered] = useState(0);
  const due = useQuery({ queryKey: ["reviewsDue"], queryFn: () => api.dueReviews() });
  const key = ["recheckItem", skillId, number];
  const exercise = useQuery({ queryKey: key, queryFn: () => api.recheckExercise(skillId, number), retry: false, gcTime: 0 });
  const review = due.data?.find((d) => d.skill_id === skillId && d.days === number);
  const none = exercise.error instanceof ApiError && exercise.error.status === 404;

  return (
    <main className="container page review-page">
      <BackLink to="/progress" label="My progress" />
      <div className="card lesson-card">
        <h1 className="step-title">{`${number}-day recheck`}</h1>
        {review && (
          <p className="eyebrow">
            {review.skill_id} {review.skill_name}
          </p>
        )}
        {exercise.isPending && <Loading what="the recheck" />}
        {exercise.isError && !none && <ErrorNote error={exercise.error} />}
        {none && (
          <>
            <p className="cold-message">{answered ? "Recheck finished. It now counts in My progress." : "Nothing is due for this skill right now."}</p>
            <Link to="/progress" className="button button-primary">
              See My progress
            </Link>
          </>
        )}
        {exercise.data && (
          <>
            <p className="cold-notice" role="note">
              One try for each item. AXIS is off, and a miss resets nothing.
            </p>
            <RoundItem
              exercise={exercise.data}
              activity="recheck"
              onAnswered={() => {
                setAnswered((n) => n + 1);
                void client.invalidateQueries({ queryKey: key });
                void client.invalidateQueries({ queryKey: ["reviewsDue"] });
              }}
            />
          </>
        )}
      </div>
    </main>
  );
}

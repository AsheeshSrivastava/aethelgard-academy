import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { ErrorNote } from "./common";

/** Restart a stage review: its rounds and result go, the evidence ledger stays (ADR-0016 amendment). */
export function RestartStageReview({ courseId, stage }: { courseId: string; stage: number }) {
  const [confirming, setConfirming] = useState(false);
  const client = useQueryClient();
  const restart = useMutation({
    mutationFn: () => api.resetStageReview({ courseId, stage }),
    onSuccess: () => {
      setConfirming(false);
      return client.invalidateQueries();
    },
  });

  if (!confirming) {
    return (
      <button type="button" className="button" onClick={() => setConfirming(true)}>
        Restart stage review
      </button>
    );
  }
  return (
    <div className="reset-confirm" role="group" aria-label="Confirm restart">
      <p className="small">
        This clears this stage review and its result, so the build closes until you pass it again. Your evidence ledger is kept.
      </p>
      {restart.isError && <ErrorNote error={restart.error} />}
      <div className="actions">
        <button type="button" className="button button-danger" disabled={restart.isPending} onClick={() => restart.mutate()}>
          Yes, restart
        </button>
        <button type="button" className="button" onClick={() => setConfirming(false)}>
          Cancel
        </button>
      </div>
    </div>
  );
}

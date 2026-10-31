import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { ErrorNote } from "./common";

export function ResetUnit({ unitId }: { unitId: string }) {
  const [confirming, setConfirming] = useState(false);
  const client = useQueryClient();
  const reset = useMutation({
    mutationFn: () => api.resetUnit(unitId),
    onSuccess: () => {
      setConfirming(false);
      return client.invalidateQueries();
    },
  });

  if (!confirming) {
    return (
      <button type="button" className="button" onClick={() => setConfirming(true)}>
        Reset unit
      </button>
    );
  }
  return (
    <div className="reset-confirm" role="group" aria-label="Confirm reset">
      <p className="small">This clears your place, your drafts and this unit's Cold Check. Your evidence ledger is kept.</p>
      {reset.isError && <ErrorNote error={reset.error} />}
      <div className="actions">
        <button type="button" className="button button-danger" disabled={reset.isPending} onClick={() => reset.mutate()}>
          Yes, reset
        </button>
        <button type="button" className="button" onClick={() => setConfirming(false)}>
          Cancel
        </button>
      </div>
    </div>
  );
}

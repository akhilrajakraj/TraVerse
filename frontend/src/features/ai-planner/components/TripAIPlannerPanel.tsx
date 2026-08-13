import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ApiRequestError } from "../../../lib/apiClient";
import { agentRunStatusColors } from "../../../lib/statusColors";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Spinner } from "../../../components/ui/Spinner";
import { StatusBadge } from "../../../components/ui/StatusBadge";
import { useTriggerTripPlan } from "../hooks/useTriggerTripPlan";
import { useTripPlanStatus } from "../hooks/useTripPlanStatus";

interface TripAIPlannerPanelProps { tripId: string; }
const POLL_BRIDGE_MS = 30_000;

export function TripAIPlannerPanel({ tripId }: TripAIPlannerPanelProps) {
  const queryClient = useQueryClient();
  const trigger = useTriggerTripPlan();
  const [pollUntil, setPollUntil] = useState<number | null>(null);
  const invalidatedRunId = useRef<string | null>(null);
  const statusQuery = useTripPlanStatus(tripId, { pollUntil });
  const status = statusQuery.data;
  const statusError = statusQuery.error;
  const notStarted = statusError instanceof ApiRequestError && statusError.status === 404;
  const isActive = status?.status === "pending" || status?.status === "running";
  const isTerminal = status?.status === "succeeded" || status?.status === "failed" || status?.status === "needs_review";

  useEffect(() => {
    if (pollUntil === null) return;
    const timeout = window.setTimeout(() => setPollUntil(null), Math.max(0, pollUntil - Date.now()));
    return () => window.clearTimeout(timeout);
  }, [pollUntil]);

  useEffect(() => {
    if (!status || !isTerminal) return;
    setPollUntil(null);
    if (status.status !== "succeeded" || invalidatedRunId.current === status.id) return;
    invalidatedRunId.current = status.id;
    void Promise.all([
      queryClient.invalidateQueries({ queryKey: ["trips", tripId] }),
      queryClient.invalidateQueries({ queryKey: ["itinerary", "trip", tripId] }),
      queryClient.invalidateQueries({ queryKey: ["budget", "trip", tripId] }),
      queryClient.invalidateQueries({ queryKey: ["recommendations", "trip", tripId] }),
    ]);
  }, [isTerminal, queryClient, status, tripId]);

  function handleTrigger() {
    setPollUntil(Date.now() + POLL_BRIDGE_MS);
    trigger.mutate(tripId, { onError: () => setPollUntil(null) });
  }

  const showInitialStatusError = statusQuery.isError && !notStarted && pollUntil === null;
  const showQueuedStatus = trigger.isSuccess && !status && (notStarted || statusQuery.isError);

  const statusCopy = {
    succeeded: { title: "Your AI trip plan is ready", description: "The planning workflow completed successfully." },
    failed: { title: "The AI planner could not complete the run", description: "The server rejected the planning attempt. You can safely retry it." },
    needs_review: { title: "The AI planner needs another attempt", description: "The AI provider returned invalid structured data. This run was not treated as a completed plan." },
    pending: { title: "Planning request accepted", description: "The asynchronous planner is waiting to start." },
    running: { title: "AI planner is working", description: "The planning workflow is running asynchronously." },
  } as const;

  return (
    <section className="mt-8 border-t border-[var(--line)] pt-6" aria-labelledby="ai-planner-heading">
      <div className="mb-5">
        <span className="section-kicker">AI Planner</span>
        <h2 id="ai-planner-heading" className="mt-1 text-xl font-semibold">Generate a trip plan</h2>
        <p className="mt-2 text-sm text-neutral">Ask the existing TraVerse planning workflow to generate an itinerary and its connected trip data.</p>
      </div>

      {showInitialStatusError ? (
        <ErrorState
          title="Planner status unavailable"
          message={statusError instanceof Error ? statusError.message : "We couldn't retrieve the AI planner status."}
          onRetry={() => void statusQuery.refetch()}
        />
      ) : null}

      {statusQuery.isLoading && !status ? <Spinner label="Checking planner status..." /> : null}

      {status ? (
        <Card>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-sm font-semibold">Travel planner run</p>
              <p className="mt-1 text-base font-medium">{statusCopy[status.status].title}</p>
              <p className="mt-1 text-sm text-neutral">{statusCopy[status.status].description}</p>
            </div>
            <StatusBadge status={status.status} colorMap={agentRunStatusColors} />
          </div>

          {status.status === "needs_review" ? (
            <div className="mt-4 rounded-lg border border-warning bg-warning-bg p-4">
              <p className="text-sm font-medium text-warning">No new AI-generated plan is considered complete from this run.</p>
              <p className="mt-1 text-sm text-neutral">The parser failure happened inside the AI workflow before the result could be accepted. The retry button below starts a new server-side planning run.</p>
              {status.error_message ? (
                <details className="mt-3 text-sm text-neutral">
                  <summary className="cursor-pointer font-medium">Show technical diagnostic</summary>
                  <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-md bg-[var(--surface-solid)] p-3 text-xs">{status.error_message}</pre>
                </details>
              ) : null}
            </div>
          ) : null}

          {status.status === "failed" && status.error_message ? (
            <p className="mt-4 text-sm text-danger" role="alert">{status.error_message}</p>
          ) : null}

          {status.status === "succeeded" ? (
            <p className="mt-4 text-sm text-neutral">Itinerary, budget, and recommendation panels will refresh from the authoritative server state.</p>
          ) : null}
        </Card>
      ) : null}

      {showQueuedStatus ? (
        <Card className="mt-4">
          <p className="font-semibold">Planning request queued</p>
          <p className="mt-1 text-sm text-neutral">The planner has accepted the request. Waiting for the asynchronous Agent Run to appear.</p>
        </Card>
      ) : null}

      {pollUntil !== null && !isActive && !isTerminal && !statusQuery.isLoading ? (
        <p className="mt-3 text-sm text-neutral" role="status">Waiting for the planner worker to start...</p>
      ) : null}

      {trigger.isError ? (
        <div className="mt-4" role="alert">
          <ErrorState
            title="Unable to start AI planning"
            message={trigger.error instanceof Error ? trigger.error.message : "We couldn't queue the planning request."}
          />
        </div>
      ) : null}

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <Button type="button" onClick={handleTrigger} isLoading={trigger.isPending} disabled={trigger.isPending || Boolean(isActive) || Boolean(pollUntil)}>
          {isTerminal ? "Retry AI planner" : "Generate AI trip plan"}
        </Button>
        {pollUntil !== null ? <span className="text-sm text-neutral">Checking planner status automatically.</span> : null}
      </div>
    </section>
  );
}

import { useQuery } from "@tanstack/react-query";

import { fetchTripPlanStatus, type AgentRunStatusResponse } from "../api/aiPlannerApi";

export const tripPlanStatusQueryKey = (tripId: string) =>
  ["ai-planner", "trip", tripId, "status"] as const;

const terminalStatuses = new Set<AgentRunStatusResponse["status"]>([
  "succeeded",
  "failed",
  "needs_review",
]);

export function useTripPlanStatus(
  tripId: string,
  options: { pollAfterTrigger?: boolean } = {},
) {
  const { pollAfterTrigger = false } = options;

  return useQuery({
    queryKey: tripPlanStatusQueryKey(tripId),
    queryFn: () => fetchTripPlanStatus(tripId),
    enabled: Boolean(tripId),
    retry: (failureCount, error) => {
      if (error instanceof Error && "status" in error && error.status === 404) {
        return false;
      }
      return failureCount < 2;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status;

      if (status && terminalStatuses.has(status)) {
        return false;
      }

      if (status === "pending" || status === "running") {
        return 2000;
      }

      // A 202 trigger queues Celery work before the AgentRun is created.
      // While the trigger is active, give that asynchronous boundary a short
      // polling window without creating a separate client-side run state.
      if (pollAfterTrigger && !query.state.error) {
        return 2000;
      }

      return false;
    },
  });
}

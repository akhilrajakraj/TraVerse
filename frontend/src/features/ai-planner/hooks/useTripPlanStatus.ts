import { useQuery } from "@tanstack/react-query";

import { ApiRequestError } from "../../../lib/apiClient";
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
  options: { pollUntil?: number | null } = {},
) {
  const { pollUntil = null } = options;

  return useQuery({
    queryKey: tripPlanStatusQueryKey(tripId),
    queryFn: () => fetchTripPlanStatus(tripId),
    enabled: Boolean(tripId),
    retry: (failureCount, error) => {
      if (error instanceof ApiRequestError && error.status === 404) {
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

      if (pollUntil !== null && Date.now() < pollUntil) {
        return 2000;
      }

      return false;
    },
  });
}

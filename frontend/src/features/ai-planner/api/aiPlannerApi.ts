import { apiRequest } from "../../../lib/apiClient";

export type AgentRunStatus =
  | "pending"
  | "running"
  | "succeeded"
  | "failed"
  | "needs_review";

export interface TripPlanTriggerResponse {
  message: string;
  task_id: string;
  trip_id: string;
}

export interface AgentRunStatusResponse {
  id: string;
  agent_type: string;
  status: AgentRunStatus;
  error_message: string;
  started_at: string | null;
  completed_at: string | null;
}

export function triggerTripPlan(tripId: string): Promise<TripPlanTriggerResponse> {
  return apiRequest<TripPlanTriggerResponse>(
    `/api/ai_agents/trips/${tripId}/plan/`,
    { method: "POST" },
  );
}

export function fetchTripPlanStatus(
  tripId: string,
): Promise<AgentRunStatusResponse> {
  return apiRequest<AgentRunStatusResponse>(
    `/api/ai_agents/trips/${tripId}/plan/status/`,
  );
}

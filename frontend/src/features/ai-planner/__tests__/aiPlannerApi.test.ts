import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../../../lib/apiClient";
import { fetchTripPlanStatus, triggerTripPlan } from "../api/aiPlannerApi";

vi.mock("../../../lib/apiClient", () => ({
  apiRequest: vi.fn(),
}));

const mockedApiRequest = vi.mocked(apiRequest);

describe("aiPlannerApi", () => {
  beforeEach(() => {
    mockedApiRequest.mockReset();
  });

  it("queues a trip plan through the verified AI planner endpoint", async () => {
    mockedApiRequest.mockResolvedValue({
      message: "Travel planning has been queued.",
      task_id: "task-123",
      trip_id: "trip-1",
    });

    await triggerTripPlan("trip-1");

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "/api/ai_agents/trips/trip-1/plan/",
      { method: "POST" },
    );
  });

  it("reads the latest planner status through the verified status endpoint", async () => {
    mockedApiRequest.mockResolvedValue({
      id: "run-1",
      agent_type: "travel_planner",
      status: "running",
      error_message: "",
      started_at: "2026-09-01T10:00:00Z",
      completed_at: null,
    });

    const result = await fetchTripPlanStatus("trip-1");

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "/api/ai_agents/trips/trip-1/plan/status/",
    );
    expect(result.status).toBe("running");
  });
});

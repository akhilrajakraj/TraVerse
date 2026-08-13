import { StatusBadge } from "../../../components/ui/StatusBadge";
import { agentRunStatusColors } from "../../../lib/statusColors";
import type { AgentRunStatus } from "../api/aiPlannerApi";

interface AgentRunStatusIndicatorProps {
  status: AgentRunStatus;
  errorMessage?: string;
}

const statusCopy: Record<AgentRunStatus, { title: string; description: string }> = {
  pending: {
    title: "Planning request accepted",
    description: "The planning run is queued and waiting for the worker to begin.",
  },
  running: {
    title: "AI planner is working",
    description: "The server reports that the planning workflow is currently running.",
  },
  succeeded: {
    title: "Your AI trip plan is ready",
    description: "The planning workflow completed successfully.",
  },
  failed: {
    title: "The AI planner could not complete the run",
    description: "The server marked this planning attempt as failed. You can start another run.",
  },
  needs_review: {
    title: "The AI planner needs another attempt",
    description: "The server did not accept the generated result as a completed plan.",
  },
};

const progressStatuses: AgentRunStatus[] = ["pending", "running", "succeeded"];

function progressState(status: AgentRunStatus, step: AgentRunStatus) {
  if (status === "failed" || status === "needs_review") {
    if (step === "pending") return "complete";
    if (step === "running") return "complete";
    return "stopped";
  }

  if (status === "succeeded") return "complete";

  const current = progressStatuses.indexOf(status);
  const target = progressStatuses.indexOf(step);

  if (target < current) return "complete";
  if (target === current) return "active";
  return "upcoming";
}

export function AgentRunStatusIndicator({ status, errorMessage }: AgentRunStatusIndicatorProps) {
  const copy = statusCopy[status];
  const isRunning = status === "pending" || status === "running";
  const isException = status === "failed" || status === "needs_review";

  return (
    <div aria-live="polite" aria-label={`AI planner status: ${status}`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold">Travel planner run</p>
          <p className="mt-1 text-base font-medium">{copy.title}</p>
          <p className="mt-1 text-sm text-neutral">{copy.description}</p>
        </div>
        <StatusBadge status={status} colorMap={agentRunStatusColors} />
      </div>

      <ol className="mt-6 grid gap-3 sm:grid-cols-3" aria-label="AI planner progress">
        {progressStatuses.map((step, index) => {
          const state = progressState(status, step);
          return (
            <li
              key={step}
              className={`rounded-lg border p-3 ${
                state === "active"
                  ? "border-info bg-info/5"
                  : state === "complete"
                    ? "border-success bg-success-bg"
                    : state === "stopped"
                      ? "border-warning bg-warning-bg"
                      : "border-[var(--line)] bg-[var(--surface)]"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-bold"
                  aria-hidden="true"
                >
                  {state === "complete" ? "✓" : state === "active" ? "•" : index + 1}
                </span>
                <span className="text-sm font-semibold">
                  {step === "pending" ? "Queued" : step === "running" ? "Processing" : "Complete"}
                </span>
              </div>
              <p className="mt-2 text-xs text-neutral">
                {step === "pending"
                  ? "Agent Run created and waiting for execution."
                  : step === "running"
                    ? "Backend workflow is executing."
                    : "Backend marked the run successful."}
              </p>
            </li>
          );
        })}
      </ol>

      {isRunning ? (
        <p className="mt-4 text-sm text-neutral" role="status">
          Status is refreshed automatically while the Agent Run remains active.
        </p>
      ) : null}

      {isException ? (
        <div className="mt-4 rounded-lg border border-warning bg-warning-bg p-4">
          <p className="text-sm font-medium">
            {status === "needs_review"
              ? "This run is not treated as a completed AI plan."
              : "This run did not complete successfully."}
          </p>
          {errorMessage ? (
            <details className="mt-2 text-sm text-neutral">
              <summary className="cursor-pointer font-medium">Show technical diagnostic</summary>
              <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-md bg-[var(--surface-solid)] p-3 text-xs">
                {errorMessage}
              </pre>
            </details>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

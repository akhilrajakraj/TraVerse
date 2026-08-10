export type StatusColor = "success" | "warning" | "danger" | "info" | "neutral";
export type StatusColorMap = Record<string, StatusColor>;

export const tripStatusColors: StatusColorMap = {
  draft: "neutral",
  planning: "info",
  planned: "success",
  completed: "success",
  cancelled: "danger",
};

export const agentRunStatusColors: StatusColorMap = {
  pending: "neutral",
  running: "info",
  succeeded: "success",
  failed: "danger",
  needs_review: "warning",
};

export const recommendationStatusColors: StatusColorMap = {
  pending: "neutral",
  accepted: "success",
  rejected: "danger",
};

export const bookingStatusColors: StatusColorMap = {
  intent_only: "neutral",
  confirmed: "success",
  cancelled: "danger",
};

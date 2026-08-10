import type { StatusColorMap } from "../../lib/statusColors";

interface StatusBadgeProps {
  status: string;
  colorMap: StatusColorMap;
  label?: string;
}

const colorClasses: Record<string, string> = {
  success: "bg-success-bg text-success",
  warning: "bg-warning-bg text-warning",
  danger: "bg-danger-bg text-danger",
  info: "bg-info-bg text-info",
  neutral: "bg-neutral-bg text-neutral",
};

export function StatusBadge({ status, colorMap, label }: StatusBadgeProps) {
  const color = colorMap[status] ?? "neutral";

  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClasses[color]}`}>
      {label ?? status}
    </span>
  );
}

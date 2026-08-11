import type { ReactNode } from "react";

export function EmptyState({ message, action }: { message: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-gray-300 p-8 text-center text-neutral">
      <p>{message}</p>
      {action}
    </div>
  );
}

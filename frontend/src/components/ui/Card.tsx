import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-[var(--line)] bg-[var(--surface-solid)] p-5 text-[var(--text)] shadow-sm ${className}`}>{children}</div>;
}

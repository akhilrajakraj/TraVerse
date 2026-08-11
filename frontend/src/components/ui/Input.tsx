import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> { label?: string; error?: string; }

export function Input({ label, error, id, className = "", ...rest }: InputProps) {
  const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);
  return <label className="flex flex-col gap-1.5 text-sm font-medium text-[var(--text)]" htmlFor={inputId}>
    {label && <span>{label}</span>}
    <input id={inputId} className={`rounded-xl border border-[var(--line)] bg-[var(--surface-solid)] px-3 py-3 text-[var(--text)] outline-none transition focus:border-orange-500 focus:ring-2 focus:ring-orange-500/20 ${className}`} aria-invalid={Boolean(error)} {...rest} />
    {error && <span className="text-xs text-red-600" role="alert">{error}</span>}
  </label>;
}

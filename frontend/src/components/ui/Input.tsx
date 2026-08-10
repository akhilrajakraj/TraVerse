import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, id, className = "", ...rest }: InputProps) {
  const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <label className="flex flex-col gap-1.5 text-sm font-medium text-neutral" htmlFor={inputId}>
      {label && <span>{label}</span>}
      <input
        id={inputId}
        className={`rounded-md border border-neutral-bg bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-info focus:ring-2 focus:ring-info/20 ${className}`}
        aria-invalid={Boolean(error)}
        {...rest}
      />
      {error && <span className="text-xs text-danger" role="alert">{error}</span>}
    </label>
  );
}

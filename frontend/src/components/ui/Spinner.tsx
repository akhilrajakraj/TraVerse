export function Spinner({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-neutral" role="status">
      <div className="h-4 w-4 animate-spin rounded-full border-2 border-info border-t-transparent" />
      <span>{label}</span>
    </div>
  );
}

type RiskBadgeProps = {
  level: string | null | undefined;
};

const styles: Record<string, string> = {
  low: "bg-emerald-100 text-emerald-800",
  medium: "bg-amber-100 text-amber-800",
  high: "bg-rose-100 text-rose-800",
};

export function RiskBadge({ level }: RiskBadgeProps) {
  if (!level) return null;
  const key = level.toLowerCase();
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize ${styles[key] ?? "bg-slate-100 text-slate-700"}`}
    >
      {level}
    </span>
  );
}

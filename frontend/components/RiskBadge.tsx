"use client";

const BADGE_STYLES: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  green: { bg: "rgba(74,222,128,0.12)", text: "#4ade80", dot: "#4ade80", label: "Low risk" },
  amber: { bg: "rgba(255,180,84,0.12)", text: "var(--accent-amber)", dot: "var(--accent-amber)", label: "Medium risk" },
  red: { bg: "rgba(248,113,113,0.12)", text: "#f87171", dot: "#f87171", label: "High risk" },
};

export default function RiskBadge({
  badge,
  score,
  loading,
  error,
}: {
  badge?: string;
  score?: number;
  loading?: boolean;
  error?: boolean;
}) {
  if (loading) {
    return <span className="text-xs font-mono text-[var(--text-dim)]">checking...</span>;
  }
  if (error) {
    return <span className="text-xs font-mono text-[var(--text-dim)]">n/a</span>;
  }
  if (!badge || !BADGE_STYLES[badge]) {
    return <span className="text-xs font-mono text-[var(--text-dim)]">-</span>;
  }
  const style = BADGE_STYLES[badge];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
      style={{ backgroundColor: style.bg, color: style.text }}
      title={typeof score === "number" ? `Risk score: ${(score * 100).toFixed(1)}%` : undefined}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: style.dot }} />
      {style.label}
    </span>
  );
}
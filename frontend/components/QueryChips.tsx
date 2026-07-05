"use client";

const EXAMPLES = [
  "What are the top 5 product categories by revenue?",
  "Which sellers have the most orders?",
  "What's the average delivery time by state?",
  "Show me the 10 most recent orders",
];

export default function QueryChips({ onSelect }: { onSelect: (q: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {EXAMPLES.map((q) => (
        <button
          key={q}
          type="button"
          onClick={() => onSelect(q)}
          className="text-xs font-mono px-3 py-1.5 rounded-full border border-[var(--border)] text-[var(--text-dim)] hover:border-[var(--accent-violet)] hover:text-[var(--text)] transition-colors"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
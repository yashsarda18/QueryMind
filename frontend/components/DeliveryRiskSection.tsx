"use client";

import { useState } from "react";

interface BatchPredictResult {
  order_id: string;
  risk_score?: number;
  is_late_predicted?: boolean;
  risk_badge?: "green" | "amber" | "red";
  error?: string | null;
}

const EXAMPLE_IDS = [
  "54282e97f61c23b78330c15b154c867d",
  "6ca46f2b9a1592929647682510800e0e",
  "99b3fb1a943fa5d4af2a3386f00fdd19",
];
const MAX_BATCH_SIZE = 25;

function parseOrderIds(input: string) {
  return input
    .split(/[\n,]+/)
    .map((id) => id.trim())
    .filter((id) => id.length > 0);
}

export default function DeliveryRiskSection() {
  const [orderIdsInput, setOrderIdsInput] = useState("");
  const [results, setResults] = useState<BatchPredictResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);

  async function handleCheckRisk(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setWarning(null);
    setResults([]);

    const parsedIds = parseOrderIds(orderIdsInput);
    if (parsedIds.length === 0) {
      setError("Please enter one or more order IDs.");
      return;
    }

    const order_ids = parsedIds.slice(0, MAX_BATCH_SIZE);
    if (parsedIds.length > MAX_BATCH_SIZE) {
      setWarning(`Only the first ${MAX_BATCH_SIZE} order IDs will be checked.`);
    }

    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/predict/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_ids }),
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data: { results: BatchPredictResult[] } = await res.json();
      setResults(data.results || []);
    } catch (err: any) {
      setError(err?.message || "Request failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function useExampleIds() {
    setOrderIdsInput(EXAMPLE_IDS.join("\n"));
    setResults([]);
    setError(null);
    setWarning(null);
  }

  return (
    <section className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl p-6 md:p-8 space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="font-display text-xl font-medium">Delivery Risk Predictor</h2>
          <p className="text-[var(--text-dim)] text-sm mt-1 max-w-2xl">
            Paste order IDs comma-separated or one per line, then check batch delivery risk for up to {MAX_BATCH_SIZE} orders.
          </p>
        </div>
        <button
          type="button"
          onClick={useExampleIds}
          className="inline-flex items-center justify-center rounded-lg border border-[var(--border)] bg-transparent px-4 py-2 text-sm text-[var(--text)] hover:border-[var(--accent-violet)] hover:text-[var(--accent-violet)] transition-colors"
        >
          Try example
        </button>
      </div>

      <form onSubmit={handleCheckRisk} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Order IDs</label>
          <textarea
            value={orderIdsInput}
            onChange={(e) => setOrderIdsInput(e.target.value)}
            rows={5}
            placeholder={EXAMPLE_IDS.join("\n")}
            className="w-full resize-none rounded-2xl border border-[var(--border)] bg-[var(--bg)] px-4 py-3 text-sm outline-none transition-colors focus:border-[var(--accent-violet)]"
          />
          <div className="text-[var(--text-dim)] text-xs">Separate IDs with commas, new lines, or both.</div>
        </div>

        {warning && (
          <div className="rounded-2xl border border-yellow-800 bg-yellow-950/50 p-3 text-sm text-yellow-200">
            {warning}
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-800 bg-red-950/50 p-3 text-sm text-red-200">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center rounded-lg bg-[var(--accent-violet)] px-5 py-3 text-sm font-medium text-[#0b0f1a] transition-opacity disabled:opacity-50 hover:opacity-90"
          >
            {loading ? "Checking..." : "Check Risk"}
          </button>
          <div className="text-[var(--text-dim)] text-xs">
            Max {MAX_BATCH_SIZE} order IDs per request.
          </div>
        </div>
      </form>

      {results.length > 0 && (
        <div className="overflow-x-auto rounded-3xl border border-[var(--border)] bg-[var(--bg)] p-0">
          <table className="min-w-full text-sm border-separate border-spacing-0">
            <thead className="bg-[var(--surface)]">
              <tr>
                <th className="px-4 py-3 text-left font-mono text-xs uppercase tracking-wide text-[var(--text-dim)]">Order ID</th>
                <th className="px-4 py-3 text-left font-mono text-xs uppercase tracking-wide text-[var(--text-dim)]">Risk badge</th>
                <th className="px-4 py-3 text-left font-mono text-xs uppercase tracking-wide text-[var(--text-dim)]">Risk score</th>
              </tr>
            </thead>
            <tbody>
              {results.map((row) => {
                const hasError = Boolean(row.error);
                return (
                  <tr key={row.order_id} className="border-t border-[var(--border)] last:border-b last:border-[var(--border)]">
                    <td className="px-4 py-3 align-top">
                      <div className="font-mono text-sm break-all">{row.order_id}</div>
                    </td>
                    <td className="px-4 py-3 align-top">
                      {hasError ? (
                        <span className="inline-flex items-center rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-300">
                          N/A
                        </span>
                      ) : (
                        <span
                          className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium"
                          style={{
                            backgroundColor:
                              row.risk_badge === "green"
                                ? "rgba(74,222,128,0.12)"
                                : row.risk_badge === "amber"
                                ? "rgba(255,180,84,0.12)"
                                : "rgba(248,113,113,0.12)",
                            color:
                              row.risk_badge === "green"
                                ? "#4ade80"
                                : row.risk_badge === "amber"
                                ? "var(--accent-amber)"
                                : "#f87171",
                          }}
                        >
                          {row.risk_badge === "green"
                            ? "Low risk"
                            : row.risk_badge === "amber"
                            ? "Medium risk"
                            : "High risk"}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 align-top">
                      {hasError ? (
                        <div className="text-sm text-[var(--text-dim)]">{row.error}</div>
                      ) : (
                        <div className="font-mono text-sm text-[var(--text)]">
                          {typeof row.risk_score === "number" ? `${Math.round(row.risk_score * 100)}%` : "-"}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

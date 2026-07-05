"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

// Heuristic: first string column = category axis, first numeric column = value axis.
// Not a general-purpose chart -- good enough for single-dimension aggregation queries
// like "top N categories by X", which is most of what this dataset's questions produce.
function pickChartColumns(rows: Record<string, any>[]) {
  if (!rows.length) return null;
  const keys = Object.keys(rows[0]);
  const categoryKey = keys.find((k) => typeof rows[0][k] === "string");
  const valueKey = keys.find((k) => typeof rows[0][k] === "number" && k !== categoryKey);
  if (!categoryKey || !valueKey) return null;
  return { categoryKey, valueKey };
}

export default function ResultsChart({ rows }: { rows: Record<string, any>[] }) {
  const picked = pickChartColumns(rows);
  if (!picked) return null;

  const data = rows.slice(0, 15).map((r) => ({
    name: String(r[picked.categoryKey]).length > 14
      ? String(r[picked.categoryKey]).slice(0, 14) + "..."
      : String(r[picked.categoryKey]),
    value: r[picked.valueKey],
  }));

  return (
    <div>
      <div className="text-xs text-[var(--text-dim)] mb-2 font-mono">
        {picked.valueKey.toUpperCase()} BY {picked.categoryKey.toUpperCase()}
      </div>
      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fill: "var(--text-dim)", fontSize: 11 }}
              interval={0}
              angle={-30}
              textAnchor="end"
              height={60}
            />
            <YAxis tick={{ fill: "var(--text-dim)", fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: "var(--text)" }}
            />
            <Bar dataKey="value" fill="var(--accent-violet)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
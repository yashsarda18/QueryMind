"use client";

import { useEffect, useState } from "react";
import HeroPipeline from "@/components/HeroPipeline";
import ScrollReveal from "@/components/ScrollReveal";

interface QueryResponse {
  status: "success" | "unanswerable" | "invalid_sql" | "execution_error";
  message?: string;
  sql?: string;
  results?: Record<string, any>[];
}

const GITHUB_URL = "https://github.com/yashsarda18";
const LINKEDIN_URL = "https://linkedin.com/in/yashsarda18";

function LivePill() {
  const [live, setLive] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
      .then((res) => setLive(res.ok))
      .catch(() => setLive(false));
  }, []);

  const color = live === null ? "var(--text-dim)" : live ? "#4ade80" : "#f87171";
  const label = live === null ? "Checking..." : live ? "Live - API connected" : "API offline";

  return (
    <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-dim)]">
      <span className="pulse-dot h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </div>
  );
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setResult(null);
    setFetchError(null);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data: QueryResponse = await res.json();
      setResult(data);
    } catch (err: any) {
      setFetchError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const columns = result?.results?.length ? Object.keys(result.results[0]) : [];

  return (
    <main className="min-h-screen bg-[var(--bg)] text-[var(--text)] overflow-x-hidden">
      <nav className="flex items-center justify-between px-8 py-5 border-b border-[var(--border)] relative z-10">
        <div className="flex items-center gap-4">
          <span className="font-display font-bold tracking-tight">QueryMind</span>
          <LivePill />
        </div>
        <div className="flex items-center gap-5 text-sm">
          <span className="text-[var(--text-dim)] font-mono text-xs hidden sm:inline">by Yash Sarda</span>
          <a href={GITHUB_URL} target="_blank" className="hover:text-[var(--accent-violet)] transition-colors">
            GitHub
          </a>
          <a href={LINKEDIN_URL} target="_blank" className="hover:text-[var(--accent-amber)] transition-colors">
            LinkedIn
          </a>
        </div>
      </nav>

      <section className="relative max-w-6xl mx-auto px-8 pt-16 pb-8 grid md:grid-cols-2 gap-12 items-center">
        <div
          style={{
            position: "absolute", width: 500, height: 500, top: -150, left: -200,
            background: "var(--accent-violet)", opacity: 0.18, borderRadius: "9999px",
            filter: "blur(100px)", pointerEvents: "none", zIndex: 0,
          }}
        />
        <div
          style={{
            position: "absolute", width: 450, height: 450, top: 50, right: -200,
            background: "var(--accent-amber)", opacity: 0.14, borderRadius: "9999px",
            filter: "blur(100px)", pointerEvents: "none", zIndex: 0,
          }}
        />

        <div className="relative z-10">
          <h1 className="font-display text-4xl md:text-5xl font-bold leading-tight">
            Ask your data <br />
            questions in <span className="text-[var(--accent-violet)]">plain English.</span>
          </h1>
          <p className="text-[var(--text-dim)] mt-5 max-w-md">
            QueryMind turns natural language into validated SQL, runs it against 100k+ real
            e-commerce orders, and flags delivery risk with a live ML model - no query language required.
          </p>
          <a
            href="#try-it"
            className="inline-block mt-7 bg-[var(--accent-violet)] text-[#0b0f1a] font-medium px-5 py-2.5 rounded-lg hover:opacity-90 transition-opacity"
          >
            Try it live
          </a>
        </div>
        <div className="relative z-10">
          <HeroPipeline />
        </div>
      </section>

      <ScrollReveal>
        <section id="try-it" className="max-w-4xl mx-auto px-8 py-16 space-y-6">
          <div>
            <h2 className="font-display text-xl font-medium">Ask a question</h2>
            <p className="text-[var(--text-dim)] text-sm mt-1">
              Try: "What are the top 5 product categories by revenue?"
            </p>
          </div>

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              className="flex-1 bg-[var(--surface)] border border-[var(--border)] rounded-lg px-4 py-2.5 outline-none focus:border-[var(--accent-violet)] transition-colors"
              placeholder="Ask anything about the dataset..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-[var(--accent-violet)] text-[#0b0f1a] px-5 py-2.5 rounded-lg font-medium disabled:opacity-50 hover:opacity-90 transition-opacity"
            >
              {loading ? "Running..." : "Ask"}
            </button>
          </form>

          {fetchError && (
            <div className="bg-[var(--surface)] border border-red-800 text-red-300 rounded-lg p-4 text-sm">
              Network error: {fetchError}
            </div>
          )}

          {result && result.status !== "success" && (
            <div className="bg-[var(--surface)] border rounded-lg p-4" style={{ borderColor: "var(--accent-amber)" }}>
              <div className="font-medium mb-1 text-[var(--accent-amber)]">{result.status}</div>
              <div className="text-sm text-[var(--text-dim)]">{result.message}</div>
            </div>
          )}

          {result?.status === "success" && (
            <div className="space-y-4">
              {result.sql && (
                <div>
                  <div className="text-xs text-[var(--text-dim)] mb-1 font-mono">GENERATED SQL</div>
                  <pre className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-4 overflow-x-auto text-sm font-mono text-[var(--accent-violet)]">
                    {result.sql}
                  </pre>
                </div>
              )}

              {result.results && result.results.length > 0 ? (
                <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
                  <table className="w-full text-sm">
                    <thead className="bg-[var(--surface)]">
                      <tr>
                        {columns.map((col) => (
                          <th
                            key={col}
                            className="text-left px-3 py-2.5 border-b border-[var(--border)] font-mono text-xs text-[var(--text-dim)]"
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.results.map((row, i) => (
                        <tr key={i} className="border-b border-[var(--border)] last:border-0">
                          {columns.map((col) => (
                            <td key={col} className="px-3 py-2.5">
                              {String(row[col])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-[var(--text-dim)] text-sm">Query returned no rows.</div>
              )}
            </div>
          )}
        </section>
      </ScrollReveal>

      <footer className="border-t border-[var(--border)] py-6 text-center text-xs text-[var(--text-dim)] font-mono">
        QueryMind - built by Yash Sarda ·{" "}
        <a href={GITHUB_URL} className="hover:text-[var(--text)]">
          GitHub
        </a>{" "}
        ·{" "}
        <a href={LINKEDIN_URL} className="hover:text-[var(--text)]">
          LinkedIn
        </a>
      </footer>
    </main>
  );
}
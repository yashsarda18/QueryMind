"use client";

import { useRef } from "react";

const stages = [
  { label: "Question", sub: "\"Top 5 categories by revenue?\"", depth: 0, accent: "violet" },
  { label: "SQL", sub: "SELECT ... GROUP BY ...", depth: 40, accent: "violet" },
  { label: "Database", sub: "Postgres - 100k+ orders", depth: 80, accent: "amber" },
  { label: "Risk Score", sub: "XGBoost - live /predict", depth: 120, accent: "amber" },
];

export default function HeroPipeline() {
  const wrapperRef = useRef<HTMLDivElement>(null);

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    const el = wrapperRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    el.style.setProperty("--rx", `${y * -10}deg`);
    el.style.setProperty("--ry", `${x * 14}deg`);
  }

  function handleMouseLeave() {
    const el = wrapperRef.current;
    if (!el) return;
    el.style.setProperty("--rx", "0deg");
    el.style.setProperty("--ry", "0deg");
  }

  return (
    <div
      className="relative h-[420px] w-full [perspective:1200px]"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div
        ref={wrapperRef}
        className="relative h-full w-full transition-transform duration-300 ease-out [transform-style:preserve-3d]"
        style={{ transform: "rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg))" }}
      >
        <div className="absolute left-1/2 top-1/2 h-[2px] w-[85%] -translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-[var(--accent-violet)]/0 via-[var(--accent-violet)]/60 to-[var(--accent-amber)]/60 [transform:translateZ(20px)]" />

        {stages.map((s, i) => {
          const color = s.accent === "violet" ? "var(--accent-violet)" : "var(--accent-amber)";
          return (
            <div
              key={s.label}
              className="animate-card absolute left-1/2 top-1/2 w-56 -translate-x-1/2 -translate-y-1/2 rounded-xl border bg-[var(--surface)]/80 backdrop-blur-md p-4 shadow-2xl transition-shadow duration-300"
              style={{
                transform: `translateZ(${s.depth}px) translateX(${(i - 1.5) * 130}px) translateY(${(i % 2 === 0 ? -1 : 1) * 18}px)`,
                animationDelay: `${i * 0.15}s, ${i * 0.4 + 0.6}s`,
                borderColor: color,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.boxShadow = `0 0 24px ${color}55`)}
              onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
            >
              <div className="text-[11px] font-mono tracking-wide" style={{ color }}>
                STAGE {i + 1}
              </div>
              <div className="font-display text-sm font-medium mt-1">{s.label}</div>
              <div className="text-xs text-[var(--text-dim)] mt-1 font-mono truncate">{s.sub}</div>
            </div>
          );
        })}

        <div
          className="animate-card absolute left-1/2 top-1/2 w-64 -translate-x-1/2 -translate-y-1/2 rounded-xl border bg-[var(--surface)]/90 backdrop-blur-md p-4 shadow-2xl transition-shadow duration-300"
          style={{
            transform: "translateZ(170px) translateX(0px) translateY(90px)",
            animationDelay: "0.6s, 2s",
            borderColor: "var(--accent-amber)",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.boxShadow = "0 0 28px #ffb45455")}
          onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
        >
          <div className="flex items-center justify-between text-[11px] font-mono tracking-wide text-[var(--accent-amber)]">
            <span>LIVE RESULT</span>
            <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-[var(--accent-amber)]" />
          </div>
          <div className="mt-2 text-xs font-mono space-y-1">
            <div className="flex justify-between text-[var(--text)]">
              <span>beleza_saude</span>
              <span>$1.26M</span>
            </div>
            <div className="flex justify-between text-[var(--text-dim)]">
              <span>relogios_presentes</span>
              <span>$1.21M</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
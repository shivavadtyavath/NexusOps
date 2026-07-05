"use client";
import { useEffect, useState } from "react";
import { useNexusStore } from "@/store/nexusStore";
import { getHealthReport, getGlobalSummary } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Activity, TrendingUp, AlertTriangle, CheckCircle } from "lucide-react";
import { clsx } from "clsx";

function ScoreRing({ score }: { score: number }) {
  const color = score >= 80 ? "#3fb950" : score >= 60 ? "#e3b341" : "#f85149";
  const r = 36;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  return (
    <div className="relative w-24 h-24 flex items-center justify-center">
      <svg width="96" height="96" className="-rotate-90">
        <circle cx="48" cy="48" r={r} fill="none" stroke="#21262d" strokeWidth="8" />
        <circle
          cx="48" cy="48" r={r} fill="none"
          stroke={color} strokeWidth="8"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold font-mono" style={{ color }}>{score.toFixed(0)}</span>
        <span className="text-[10px] text-[var(--muted)]">/ 100</span>
      </div>
    </div>
  );
}

export default function HealthDashboard() {
  const { selectedRepo, healthReport, setHealthReport, globalSummary, setGlobalSummary } =
    useNexusStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getGlobalSummary().then(setGlobalSummary).catch(() => {});
  }, [setGlobalSummary]);

  useEffect(() => {
    if (!selectedRepo) return;
    const [owner, name] = selectedRepo.split("/");
    setLoading(true);
    setError(null);
    getHealthReport(owner, name)
      .then(setHealthReport)
      .catch(() => setError("No health data yet. Run analysis first."))
      .finally(() => setLoading(false));
  }, [selectedRepo, setHealthReport]);

  const sevData = healthReport
    ? [
        { name: "Critical", value: healthReport.critical, fill: "#f85149" },
        { name: "High", value: healthReport.high, fill: "#e3b341" },
        { name: "Medium", value: healthReport.medium, fill: "#58a6ff" },
        { name: "Low", value: healthReport.low, fill: "#6e7681" },
      ]
    : [];

  const typeData = healthReport
    ? Object.entries(healthReport.by_type).map(([k, v]) => ({ name: k, value: v }))
    : [];

  return (
    <div className="p-4 space-y-5 overflow-y-auto h-full">
      <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-widest block">
        Code Health
      </span>

      {loading && (
        <div className="flex items-center gap-2 text-[var(--muted)] text-sm">
          <div className="w-4 h-4 border-2 border-[var(--blue)] border-t-transparent rounded-full animate-spin" />
          Loading health data...
        </div>
      )}

      {error && !loading && (
        <p className="text-xs text-[var(--muted)] bg-[var(--surface-2)] rounded p-3">{error}</p>
      )}

      {healthReport && !loading && (
        <>
          {/* Score */}
          <div className="bg-[var(--surface-2)] rounded-lg p-4 border border-[var(--border)] flex items-center gap-6">
            <ScoreRing score={healthReport.health_score} />
            <div>
              <p className="text-sm font-semibold text-[var(--white)]">Health Score</p>
              <p className="text-xs text-[var(--muted)] mt-0.5">{healthReport.repo}</p>
              <p className="text-xs text-[var(--muted)] mt-1">
                {healthReport.files_analyzed} files · {healthReport.total_issues} issues
              </p>
            </div>
          </div>

          {/* Severity chart */}
          {sevData.some((d) => d.value > 0) && (
            <div className="bg-[var(--surface-2)] rounded-lg p-3 border border-[var(--border)]">
              <p className="text-xs text-[var(--muted)] mb-3">Issues by Severity</p>
              <ResponsiveContainer width="100%" height={80}>
                <BarChart data={sevData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                  <XAxis dataKey="name" tick={{ fill: "#6e7681", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#6e7681", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: "#161b22", border: "1px solid #21262d", borderRadius: "6px", fontSize: 11 }}
                    labelStyle={{ color: "#e6edf3" }}
                    cursor={{ fill: "rgba(255,255,255,0.04)" }}
                  />
                  <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                    {sevData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Issue type distribution */}
          {typeData.length > 0 && (
            <div className="bg-[var(--surface-2)] rounded-lg p-3 border border-[var(--border)]">
              <p className="text-xs text-[var(--muted)] mb-2">By Issue Type</p>
              <div className="flex flex-wrap gap-2">
                {typeData.map(({ name, value }) => (
                  <div key={name} className="flex items-center gap-1.5 bg-[var(--border)] px-2 py-1 rounded">
                    <span className="text-[10px] text-[var(--white)] capitalize">{name}</span>
                    <span className="text-[10px] text-[var(--blue)] font-bold">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {healthReport.recommendations.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-[var(--muted)] uppercase tracking-widest">Recommendations</p>
              {healthReport.recommendations.map((rec, i) => (
                <div key={i} className="bg-[var(--surface-2)] rounded-lg p-3 border border-[var(--border)]">
                  <p className="text-xs text-[var(--white)] leading-relaxed">{rec}</p>
                </div>
              ))}
            </div>
          )}

          {/* Top files */}
          {healthReport.by_file.length > 0 && (
            <div className="bg-[var(--surface-2)] rounded-lg p-3 border border-[var(--border)]">
              <p className="text-xs text-[var(--muted)] mb-2">Top Problem Files</p>
              {healthReport.by_file.slice(0, 5).map((f, i) => (
                <div key={i} className="flex items-center justify-between py-1 border-b border-[var(--border)] last:border-0">
                  <span className="text-[10px] text-[var(--white)] truncate flex-1 mr-2">{f.file}</span>
                  <span className={clsx(
                    "text-[10px] font-bold shrink-0",
                    f.issues >= 5 ? "text-[var(--red)]" : f.issues >= 3 ? "text-[var(--orange)]" : "text-[var(--muted)]"
                  )}>{f.issues} issues</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Global summary */}
      {globalSummary && (
        <div className="bg-[var(--surface-2)] rounded-lg p-3 border border-[var(--border)] space-y-2">
          <p className="text-xs text-[var(--muted)] uppercase tracking-widest">Global Overview</p>
          <div className="flex gap-4">
            <div>
              <p className="text-lg font-bold text-[var(--red)]">{globalSummary.total_issues}</p>
              <p className="text-[10px] text-[var(--muted)]">Total Issues</p>
            </div>
            <div>
              <p className="text-lg font-bold text-[var(--orange)]">{globalSummary.by_severity?.critical || 0}</p>
              <p className="text-[10px] text-[var(--muted)]">Critical</p>
            </div>
            <div>
              <p className="text-lg font-bold text-[var(--blue)]">{globalSummary.recent_runs?.length || 0}</p>
              <p className="text-[10px] text-[var(--muted)]">Recent Runs</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

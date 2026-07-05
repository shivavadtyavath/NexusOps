"use client";
import { useState } from "react";
import { useNexusStore } from "@/store/nexusStore";
import { resolveIssue, generateFixes } from "@/lib/api";
import { ShieldAlert, Bug, Zap, Code2, CheckCheck, Wrench, ChevronDown, ChevronRight, FileCode } from "lucide-react";
import { clsx } from "clsx";
import type { CodeIssue, Severity } from "@/lib/types";

const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low"];

const SEVERITY_CONFIG: Record<Severity, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
  critical: { label: "Critical", color: "text-[var(--red)]", bg: "bg-red-900/20 border-red-900/40", icon: <ShieldAlert size={12} /> },
  high: { label: "High", color: "text-[var(--orange)]", bg: "bg-orange-900/20 border-orange-900/40", icon: <Bug size={12} /> },
  medium: { label: "Medium", color: "text-[var(--blue)]", bg: "bg-blue-900/20 border-blue-900/40", icon: <Zap size={12} /> },
  low: { label: "Low", color: "text-[var(--muted)]", bg: "bg-[var(--border)] border-[var(--border)]", icon: <Code2 size={12} /> },
};

function IssueCard({ issue, onResolve }: { issue: CodeIssue; onResolve: (id: number) => void }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = SEVERITY_CONFIG[issue.severity] || SEVERITY_CONFIG.low;

  return (
    <div className={clsx("border rounded-lg mb-2 overflow-hidden slide-in", cfg.bg)}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-2.5 flex items-start gap-2 text-left hover:brightness-110 transition-all"
      >
        <span className={clsx("mt-0.5 shrink-0", cfg.color)}>{cfg.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={clsx("text-xs font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded border text-[10px]", cfg.color, cfg.bg)}>
              {cfg.label}
            </span>
            <span className="text-xs text-[var(--muted)] bg-[var(--border)] px-1.5 py-0.5 rounded capitalize">
              {issue.issue_type}
            </span>
            <span className="text-xs font-semibold text-[var(--white)] truncate flex-1">{issue.title}</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <FileCode size={10} className="text-[var(--muted)]" />
            <span className="text-[10px] text-[var(--muted)] truncate">
              {issue.file_path}{issue.line_start ? `:${issue.line_start}` : ""}
            </span>
            <span className="text-[10px] text-[var(--muted)] ml-auto">
              {Math.round(issue.confidence * 100)}% confidence
            </span>
          </div>
        </div>
        {expanded ? <ChevronDown size={12} className="text-[var(--muted)] mt-1 shrink-0" /> : <ChevronRight size={12} className="text-[var(--muted)] mt-1 shrink-0" />}
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-2 border-t border-[var(--border)] pt-2">
          <p className="text-xs text-[var(--muted)] leading-relaxed">{issue.description}</p>

          {issue.suggestion && (
            <div className="bg-[var(--surface)] rounded p-2 border border-[var(--border)]">
              <p className="text-[10px] text-[var(--blue)] mb-1">💡 Suggestion</p>
              <p className="text-xs text-[var(--white)] leading-relaxed">{issue.suggestion}</p>
            </div>
          )}

          {issue.fixed_code && (
            <div className="bg-[var(--bg)] rounded p-2 border border-[var(--border)]">
              <p className="text-[10px] text-[var(--green)] mb-1">✓ AI Fix</p>
              <pre className="text-[10px] text-[var(--white)] overflow-x-auto whitespace-pre-wrap leading-relaxed">
                {issue.fixed_code.slice(0, 400)}{issue.fixed_code.length > 400 ? "\n..." : ""}
              </pre>
            </div>
          )}

          {!issue.is_resolved && issue.id && (
            <button
              onClick={() => onResolve(issue.id!)}
              className="flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium bg-green-900/20 text-[var(--green)] hover:bg-green-900/40 transition-colors border border-green-900/40"
            >
              <CheckCheck size={12} /> Mark Resolved
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function IssuesList() {
  const { issues, selectedRepo, severityFilter, setSeverityFilter, resolveIssueLocally, setIssues } =
    useNexusStore();
  const [fixLoading, setFixLoading] = useState(false);

  const filtered = issues.filter((i) => {
    if (i.is_resolved) return false;
    if (severityFilter && i.severity !== severityFilter) return false;
    return true;
  });

  const counts = SEVERITY_ORDER.reduce((acc, sev) => {
    acc[sev] = issues.filter((i) => i.severity === sev && !i.is_resolved).length;
    return acc;
  }, {} as Record<string, number>);

  async function handleResolve(id: number) {
    try {
      await resolveIssue(id);
      resolveIssueLocally(id);
    } catch { /* ignore */ }
  }

  async function handleAutoFix() {
    if (!selectedRepo) return;
    const fixable = filtered
      .filter((i) => i.severity === "critical" || i.severity === "high")
      .slice(0, 10)
      .map((i) => i.id!)
      .filter(Boolean);

    if (!fixable.length) return;
    setFixLoading(true);
    try {
      await generateFixes(selectedRepo, fixable);
    } finally {
      setFixLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--border)] space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-widest">
            Issues ({filtered.length})
          </span>
          <button
            onClick={handleAutoFix}
            disabled={fixLoading || filtered.length === 0}
            className={clsx(
              "flex items-center gap-1 px-2 py-1 rounded text-[10px] font-semibold transition-colors",
              fixLoading
                ? "bg-[var(--border)] text-[var(--muted)] cursor-not-allowed"
                : "bg-purple-900/30 text-[var(--purple)] hover:bg-purple-900/50 border border-purple-900/40"
            )}
          >
            <Wrench size={10} />
            {fixLoading ? "Generating..." : "AI Fix Critical"}
          </button>
        </div>

        {/* Severity filters */}
        <div className="flex gap-1 flex-wrap">
          <button
            onClick={() => setSeverityFilter(null)}
            className={clsx(
              "px-2 py-0.5 rounded text-[10px] font-medium transition-colors",
              !severityFilter ? "bg-[var(--blue)] text-white" : "bg-[var(--border)] text-[var(--muted)] hover:text-[var(--white)]"
            )}
          >
            All ({issues.filter((i) => !i.is_resolved).length})
          </button>
          {SEVERITY_ORDER.map((sev) => {
            const cfg = SEVERITY_CONFIG[sev];
            return (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev === severityFilter ? null : sev)}
                className={clsx(
                  "px-2 py-0.5 rounded text-[10px] font-medium transition-colors border",
                  severityFilter === sev ? `${cfg.color} ${cfg.bg}` : "bg-[var(--border)] text-[var(--muted)] border-transparent"
                )}
              >
                {cfg.label} ({counts[sev]})
              </button>
            );
          })}
        </div>
      </div>

      {/* Issue list */}
      <div className="flex-1 overflow-y-auto p-3">
        {!selectedRepo ? (
          <div className="text-center py-12 text-[var(--muted)] text-sm">
            Select a repository and run analysis
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12">
            <CheckCheck size={32} className="text-[var(--green)] mx-auto mb-2" />
            <p className="text-sm text-[var(--muted)]">No issues found</p>
          </div>
        ) : (
          filtered.map((issue, idx) => (
            <IssueCard key={issue.id || idx} issue={issue} onResolve={handleResolve} />
          ))
        )}
      </div>
    </div>
  );
}

"use client";
import { useEffect } from "react";
import { useNexusStore } from "@/store/nexusStore";
import { listRuns } from "@/lib/api";
import { Clock, CheckCircle2, XCircle, Loader2, GitBranch } from "lucide-react";
import { clsx } from "clsx";
import { formatDistanceToNow } from "date-fns";

export default function RunHistory() {
  const { runs, setRuns, selectedRepo } = useNexusStore();

  useEffect(() => {
    listRuns(selectedRepo || undefined, 30)
      .then(setRuns)
      .catch(() => {});
  }, [selectedRepo, setRuns]);

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-[var(--border)]">
        <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-widest">
          Analysis History
        </span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {runs.length === 0 ? (
          <div className="p-6 text-center text-[var(--muted)] text-sm">
            No runs yet. Trigger your first analysis.
          </div>
        ) : (
          runs.map((run) => (
            <div key={run.id} className="px-4 py-3 border-b border-[var(--border)] hover:bg-[var(--surface-2)] transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {run.status === "done" ? (
                    <CheckCircle2 size={13} className="text-[var(--green)]" />
                  ) : run.status === "failed" ? (
                    <XCircle size={13} className="text-[var(--red)]" />
                  ) : (
                    <Loader2 size={13} className="text-[var(--blue)] animate-spin" />
                  )}
                  <span className="text-xs font-medium text-[var(--white)] truncate max-w-[140px]">
                    {run.repo}
                  </span>
                </div>
                {run.health_score !== null && (
                  <span className={clsx(
                    "text-xs font-bold font-mono",
                    run.health_score >= 80 ? "text-[var(--green)]" :
                    run.health_score >= 60 ? "text-[var(--orange)]" : "text-[var(--red)]"
                  )}>
                    {run.health_score.toFixed(0)}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3 mt-1">
                <span className="text-[10px] text-[var(--muted)]">{run.files_analyzed} files</span>
                <span className="text-[10px] text-[var(--red)]">{run.issues_found} issues</span>
                {run.duration_ms && (
                  <span className="text-[10px] text-[var(--muted)]">{(run.duration_ms / 1000).toFixed(1)}s</span>
                )}
                <span className="text-[10px] text-[var(--muted)] capitalize ml-auto">{run.trigger}</span>
              </div>

              {run.created_at && (
                <p className="text-[10px] text-[var(--muted)] mt-0.5 flex items-center gap-1">
                  <Clock size={9} />
                  {formatDistanceToNow(new Date(run.created_at), { addSuffix: true })}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

"use client";
import { useState } from "react";
import { useNexusStore } from "@/store/nexusStore";
import { runAnalysis, listIssues } from "@/lib/api";
import { Play, Loader2, GitPullRequest, CheckCircle2, Circle, ArrowRight } from "lucide-react";
import { clsx } from "clsx";

const STAGES = [
  { id: "scan", label: "Scanner Agent", desc: "Fetching & parsing files from GitHub" },
  { id: "review", label: "Reviewer Agent", desc: "AI deep code review via Groq LLM" },
  { id: "report", label: "Reporter Agent", desc: "Computing health score + recommendations" },
];

export default function AnalysisTrigger() {
  const { selectedRepo, setAnalysisResult, setAnalysisRunning, analysisRunning, setIssues } =
    useNexusStore();
  const [branch, setBranch] = useState("");
  const [prNumber, setPrNumber] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState<number>(-1);
  const [doneMs, setDoneMs] = useState<number | null>(null);

  async function handleRun() {
    if (!selectedRepo || analysisRunning) return;
    setAnalysisRunning(true);
    setError(null);
    setStage(0);
    setDoneMs(null);

    try {
      const result = await runAnalysis(
        selectedRepo,
        branch.trim() || undefined,
        prNumber ? parseInt(prNumber) : undefined
      );
      setStage(3); // all done
      setAnalysisResult(result);
      setDoneMs(result.duration_ms);

      // Refresh issues list
      const [owner, name] = selectedRepo.split("/");
      const issues = await listIssues(selectedRepo, undefined, false, 100);
      setIssues(issues);
    } catch (e: unknown) {
      setError("Analysis failed. Check your GitHub token and repo name.");
      setStage(-1);
    } finally {
      setAnalysisRunning(false);
    }
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-widest">
          Run Analysis
        </span>
      </div>

      {/* Options */}
      <div className="space-y-2">
        <input
          value={branch}
          onChange={(e) => setBranch(e.target.value)}
          placeholder="Branch (optional, default: main)"
          className="w-full bg-[var(--surface-2)] border border-[var(--border)] rounded px-3 py-1.5 text-xs text-[var(--white)] placeholder-[var(--muted)] focus:outline-none focus:border-[var(--blue)]"
        />
        <input
          value={prNumber}
          onChange={(e) => setPrNumber(e.target.value)}
          placeholder="PR number (optional, for PR review)"
          className="w-full bg-[var(--surface-2)] border border-[var(--border)] rounded px-3 py-1.5 text-xs text-[var(--white)] placeholder-[var(--muted)] focus:outline-none focus:border-[var(--blue)]"
          type="number"
        />
      </div>

      {/* Run button */}
      <button
        onClick={handleRun}
        disabled={!selectedRepo || analysisRunning}
        className={clsx(
          "w-full flex items-center justify-center gap-2 py-2 rounded-md text-sm font-semibold transition-all",
          !selectedRepo || analysisRunning
            ? "bg-[var(--border)] text-[var(--muted)] cursor-not-allowed"
            : "bg-[var(--blue)] text-white hover:brightness-110"
        )}
      >
        {analysisRunning ? (
          <><Loader2 size={14} className="animate-spin" /> Analyzing...</>
        ) : (
          <><Play size={14} /> Run Full Analysis</>
        )}
      </button>

      {/* Pipeline stages */}
      {(analysisRunning || stage >= 0) && (
        <div className="space-y-2 pt-2">
          {STAGES.map((s, idx) => {
            const isDone = stage > idx || (stage === 3 && idx < 3);
            const isRunning = analysisRunning && stage === idx;
            return (
              <div key={s.id} className="flex items-start gap-2">
                <div className={clsx(
                  "mt-0.5 shrink-0 transition-colors",
                  isDone ? "text-[var(--green)]" : isRunning ? "text-[var(--blue)]" : "text-[var(--border)]"
                )}>
                  {isDone
                    ? <CheckCircle2 size={14} />
                    : isRunning
                    ? <Loader2 size={14} className="animate-spin" />
                    : <Circle size={14} />}
                </div>
                <div>
                  <p className={clsx(
                    "text-xs font-medium",
                    isDone ? "text-[var(--white)]" : isRunning ? "text-[var(--blue)]" : "text-[var(--muted)]"
                  )}>{s.label}</p>
                  <p className="text-[10px] text-[var(--muted)]">{s.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Result */}
      {doneMs !== null && !analysisRunning && (
        <p className="text-xs text-[var(--green)]">
          ✓ Completed in {(doneMs / 1000).toFixed(1)}s
        </p>
      )}

      {error && (
        <p className="text-xs text-[var(--red)] bg-red-900/20 rounded px-2 py-1.5">{error}</p>
      )}
    </div>
  );
}

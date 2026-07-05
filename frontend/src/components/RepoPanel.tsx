"use client";
import { useState } from "react";
import { useNexusStore } from "@/store/nexusStore";
import { registerRepo, listRepos, deleteRepo } from "@/lib/api";
import { GitBranch, Plus, Trash2, RefreshCw, Code2 } from "lucide-react";
import { clsx } from "clsx";

function HealthBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-xs text-[var(--muted)]">—</span>;
  const color = score >= 80 ? "text-[var(--green)]" : score >= 60 ? "text-[var(--orange)]" : "text-[var(--red)]";
  return <span className={clsx("text-xs font-bold font-mono", color)}>{score.toFixed(0)}</span>;
}

export default function RepoPanel() {
  const { repos, setRepos, selectedRepo, selectRepo } = useNexusStore();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAdd() {
    const name = input.trim();
    if (!name || !name.includes("/")) {
      setError("Enter in owner/repo format");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await registerRepo(name);
      const updated = await listRepos();
      setRepos(updated);
      setInput("");
      selectRepo(name);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to register repo";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(fullName: string) {
    const [owner, name] = fullName.split("/");
    try {
      await deleteRepo(owner, name);
      const updated = await listRepos();
      setRepos(updated);
      if (selectedRepo === fullName) selectRepo(updated[0]?.full_name || null);
    } catch { /* ignore */ }
  }

  async function handleRefresh() {
    try {
      const updated = await listRepos();
      setRepos(updated);
    } catch { /* ignore */ }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <Code2 size={14} className="text-[var(--blue)]" />
          <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-widest">Repositories</span>
        </div>
        <button onClick={handleRefresh} className="p-1 rounded hover:bg-[var(--border)] transition-colors">
          <RefreshCw size={12} className="text-[var(--muted)]" />
        </button>
      </div>

      {/* Add repo */}
      <div className="p-3 border-b border-[var(--border)]">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            placeholder="owner/repo"
            className="flex-1 bg-[var(--surface-2)] border border-[var(--border)] rounded px-2 py-1.5 text-xs text-[var(--white)] placeholder-[var(--muted)] focus:outline-none focus:border-[var(--blue)]"
          />
          <button
            onClick={handleAdd}
            disabled={loading}
            className="px-2 py-1.5 bg-[var(--blue)] text-white rounded text-xs font-semibold hover:brightness-110 disabled:opacity-50"
          >
            {loading ? "…" : <Plus size={13} />}
          </button>
        </div>
        {error && <p className="text-[10px] text-[var(--red)] mt-1">{error}</p>}
      </div>

      {/* Repo list */}
      <div className="flex-1 overflow-y-auto">
        {repos.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-xs text-[var(--muted)]">Add a GitHub repo above</p>
          </div>
        ) : (
          repos.map((repo) => (
            <button
              key={repo.full_name}
              onClick={() => selectRepo(repo.full_name)}
              className={clsx(
                "w-full px-3 py-2.5 border-b border-[var(--border)] text-left transition-colors hover:bg-[var(--surface-2)] group",
                selectedRepo === repo.full_name && "bg-[var(--surface-2)] border-l-2 border-l-[var(--blue)]"
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <GitBranch size={11} className="text-[var(--muted)] shrink-0" />
                  <span className="text-xs font-medium text-[var(--white)] truncate">{repo.full_name}</span>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(repo.full_name); }}
                  className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-red-900/30 transition-all"
                >
                  <Trash2 size={11} className="text-[var(--red)]" />
                </button>
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-[10px] text-[var(--muted)]">
                  {repo.language || "Unknown"} · {repo.total_issues_found} issues
                </span>
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-[var(--muted)]">Health</span>
                  <HealthBadge score={repo.health_score} />
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

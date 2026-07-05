"use client";
import { useEffect } from "react";
import { useNexusStore } from "@/store/nexusStore";
import { listRepos, getGlobalSummary } from "@/lib/api";
import RepoPanel from "@/components/RepoPanel";
import AnalysisTrigger from "@/components/AnalysisTrigger";
import IssuesList from "@/components/IssuesList";
import HealthDashboard from "@/components/HealthDashboard";
import RunHistory from "@/components/RunHistory";
import { Shield, Activity, ListChecks, Clock, Zap } from "lucide-react";
import { clsx } from "clsx";

type Tab = "issues" | "health" | "runs";

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: "issues", label: "Issues", icon: <ListChecks size={13} /> },
  { id: "health", label: "Health", icon: <Activity size={13} /> },
  { id: "runs", label: "History", icon: <Clock size={13} /> },
];

export default function Dashboard() {
  const { setRepos, setGlobalSummary, activeTab, setActiveTab } = useNexusStore();

  useEffect(() => {
    listRepos().then(setRepos).catch(() => {});
    getGlobalSummary().then(setGlobalSummary).catch(() => {});
  }, [setRepos, setGlobalSummary]);

  return (
    <div className="flex flex-col h-screen bg-[#0d1117] overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-5 py-2.5 border-b border-[#21262d] bg-[#161b22] shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#58a6ff] to-[#bc8cff] flex items-center justify-center">
            <Shield size={14} className="text-black" />
          </div>
          <span className="text-base font-bold text-white">NexusOps</span>
          <span className="text-xs text-[#6e7681] hidden sm:block">
            Autonomous DevOps Intelligence Platform
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex gap-1.5">
            {["Groq LLM", "LangGraph", "GitHub API", "Bandit", "MCP"].map((t) => (
              <span key={t} className="text-[10px] px-2 py-0.5 rounded bg-[#21262d] text-[#6e7681]">{t}</span>
            ))}
          </div>
          <div className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border border-[#e3b341]/30 bg-orange-900/10 text-[#e3b341]">
            <Zap size={11} />
            <span>100% Free</span>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left: Repos + Trigger */}
        <aside className="w-56 shrink-0 border-r border-[#21262d] bg-[#161b22] flex flex-col overflow-hidden">
          <div className="flex-1 min-h-0 overflow-hidden flex flex-col" style={{ maxHeight: "55%" }}>
            <RepoPanel />
          </div>
          <div className="border-t border-[#21262d] overflow-y-auto" style={{ maxHeight: "45%" }}>
            <AnalysisTrigger />
          </div>
        </aside>

        {/* Center: Tabbed content */}
        <section className="flex-1 min-w-0 flex flex-col overflow-hidden">
          {/* Tab bar */}
          <div className="flex border-b border-[#21262d] bg-[#161b22] shrink-0">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as NexusStore["activeTab"])}
                className={clsx(
                  "flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-all",
                  activeTab === tab.id
                    ? "border-[#58a6ff] text-[#58a6ff]"
                    : "border-transparent text-[#6e7681] hover:text-white"
                )}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 min-h-0 overflow-hidden">
            {activeTab === "issues" && <IssuesList />}
            {activeTab === "health" && <HealthDashboard />}
            {activeTab === "runs" && <RunHistory />}
          </div>
        </section>
      </main>
    </div>
  );
}

// Fix missing type reference
type NexusStore = { activeTab: "dashboard" | "issues" | "runs" | "health" };

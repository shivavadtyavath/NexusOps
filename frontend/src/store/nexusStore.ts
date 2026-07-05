import { create } from "zustand";
import type {
  AnalysisRun,
  AnalyzeResponse,
  CodeIssue,
  GlobalSummary,
  HealthReport,
  Repo,
} from "@/lib/types";

interface NexusStore {
  // Repos
  repos: Repo[];
  selectedRepo: string | null;

  // Analysis
  analysisResult: AnalyzeResponse | null;
  analysisRunning: boolean;
  runs: AnalysisRun[];

  // Issues
  issues: CodeIssue[];
  selectedIssues: Set<number>;
  severityFilter: string | null;

  // Health
  healthReport: HealthReport | null;
  globalSummary: GlobalSummary | null;

  // UI
  activeTab: "dashboard" | "issues" | "runs" | "health";

  // Actions
  setRepos: (repos: Repo[]) => void;
  selectRepo: (repo: string) => void;
  setAnalysisResult: (result: AnalyzeResponse) => void;
  setAnalysisRunning: (running: boolean) => void;
  setRuns: (runs: AnalysisRun[]) => void;
  setIssues: (issues: CodeIssue[]) => void;
  toggleIssueSelection: (id: number) => void;
  clearSelection: () => void;
  setSeverityFilter: (sev: string | null) => void;
  setHealthReport: (report: HealthReport) => void;
  setGlobalSummary: (summary: GlobalSummary) => void;
  setActiveTab: (tab: NexusStore["activeTab"]) => void;
  resolveIssueLocally: (id: number) => void;
}

export const useNexusStore = create<NexusStore>((set) => ({
  repos: [],
  selectedRepo: null,
  analysisResult: null,
  analysisRunning: false,
  runs: [],
  issues: [],
  selectedIssues: new Set(),
  severityFilter: null,
  healthReport: null,
  globalSummary: null,
  activeTab: "dashboard",

  setRepos: (repos) => set({ repos }),
  selectRepo: (repo) => set({ selectedRepo: repo }),
  setAnalysisResult: (result) => set({ analysisResult: result }),
  setAnalysisRunning: (running) => set({ analysisRunning: running }),
  setRuns: (runs) => set({ runs }),
  setIssues: (issues) => set({ issues }),
  toggleIssueSelection: (id) =>
    set((state) => {
      const next = new Set(state.selectedIssues);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { selectedIssues: next };
    }),
  clearSelection: () => set({ selectedIssues: new Set() }),
  setSeverityFilter: (sev) => set({ severityFilter: sev }),
  setHealthReport: (report) => set({ healthReport: report }),
  setGlobalSummary: (summary) => set({ globalSummary: summary }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  resolveIssueLocally: (id) =>
    set((state) => ({
      issues: state.issues.map((i) =>
        (i.id === id ? { ...i, is_resolved: true } : i)
      ),
    })),
}));

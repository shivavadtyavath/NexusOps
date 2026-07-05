import axios from "axios";
import type {
  AnalyzeResponse,
  AnalysisRun,
  CodeIssue,
  GlobalSummary,
  HealthReport,
  Repo,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${BASE}/api/v1`,
  timeout: 180000, // 3 min — analysis takes time
});

// ── Repos ─────────────────────────────────────────────────────────────────────

export async function registerRepo(repoFullName: string): Promise<Repo> {
  const { data } = await api.post("/repos/register", { repo_full_name: repoFullName });
  return data;
}

export async function listRepos(): Promise<Repo[]> {
  const { data } = await api.get("/repos/");
  return data;
}

export async function deleteRepo(owner: string, name: string): Promise<void> {
  await api.delete(`/repos/${owner}/${name}`);
}

// ── Analysis ──────────────────────────────────────────────────────────────────

export async function runAnalysis(
  repoFullName: string,
  branch?: string,
  prNumber?: number
): Promise<AnalyzeResponse> {
  const { data } = await api.post("/analysis/run", {
    repo_full_name: repoFullName,
    branch,
    pr_number: prNumber,
  });
  return data;
}

export async function getAnalysisStatus(): Promise<{
  status: string;
  last_run: string | null;
  duration_ms: number | null;
}> {
  const { data } = await api.get("/analysis/status");
  return data;
}

export async function listRuns(repo?: string, limit = 20): Promise<AnalysisRun[]> {
  const { data } = await api.get("/analysis/runs", { params: { repo, limit } });
  return data;
}

export async function listIssues(
  repo?: string,
  severity?: string,
  resolved = false,
  limit = 50
): Promise<CodeIssue[]> {
  const { data } = await api.get("/analysis/issues", {
    params: { repo, severity, resolved, limit },
  });
  return data;
}

export async function resolveIssue(issueId: number): Promise<void> {
  await api.patch(`/analysis/issues/${issueId}/resolve`);
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function getHealthReport(owner: string, name: string): Promise<HealthReport> {
  const { data } = await api.get(`/health/report/${owner}/${name}`);
  return data;
}

export async function getGlobalSummary(): Promise<GlobalSummary> {
  const { data } = await api.get("/health/summary");
  return data;
}

// ── Fixes ─────────────────────────────────────────────────────────────────────

export async function generateFixes(
  repoFullName: string,
  issueIds: number[],
  createPr = false
): Promise<{ status: string; fixes_applied: number; message: string }> {
  const { data } = await api.post("/fixes/generate", {
    repo_full_name: repoFullName,
    issue_ids: issueIds,
    create_pr: createPr,
  });
  return data;
}

// ── Health check ──────────────────────────────────────────────────────────────

export async function getHealth(): Promise<Record<string, unknown>> {
  const { data } = await axios.get(`${BASE}/health`);
  return data;
}

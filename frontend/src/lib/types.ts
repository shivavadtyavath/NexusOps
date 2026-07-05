export type Severity = "critical" | "high" | "medium" | "low";
export type IssueType = "bug" | "security" | "performance" | "style" | "complexity" | "other";
export type AnalysisStatus = "idle" | "running" | "done" | "partial" | "failed";

export interface Repo {
  full_name: string;
  owner: string;
  name: string;
  default_branch: string;
  language: string | null;
  description: string | null;
  health_score: number | null;
  total_issues_found: number;
  total_fixes_generated: number;
  last_analyzed: string | null;
}

export interface CodeIssue {
  id?: number;
  repo_full_name: string;
  file_path: string;
  line_start: number | null;
  line_end: number | null;
  issue_type: IssueType;
  severity: Severity;
  title: string;
  description: string;
  suggestion: string | null;
  fixed_code: string | null;
  confidence: number;
  is_resolved: boolean;
  created_at: string | null;
}

export interface AnalysisRun {
  id: number;
  repo: string;
  trigger: string;
  status: string;
  files_analyzed: number;
  issues_found: number;
  health_score: number | null;
  duration_ms: number | null;
  created_at: string | null;
}

export interface AnalyzeResponse {
  run_id: number;
  status: string;
  repo: string;
  files_analyzed: number;
  issues_found: number;
  fixes_generated: number;
  health_score: number | null;
  issues: CodeIssue[];
  summary: string;
  duration_ms: number | null;
}

export interface HealthReport {
  repo: string;
  health_score: number;
  total_issues: number;
  files_analyzed: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  by_type: Record<string, number>;
  by_file: Array<{ file: string; issues: number }>;
  recommendations: string[];
  generated_at: string;
}

export interface GlobalSummary {
  total_issues: number;
  by_severity: Record<string, number>;
  top_repos_by_issues: Array<{ repo: string; issues: number }>;
  recent_runs: AnalysisRun[];
}

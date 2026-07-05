"""Pydantic schemas for NexusOps API."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RepoRequest(BaseModel):
    repo_full_name: str  # e.g. "owner/repo"
    branch: Optional[str] = None


class RepoResponse(BaseModel):
    full_name: str
    owner: str
    name: str
    default_branch: str
    language: Optional[str]
    description: Optional[str]
    health_score: Optional[float]
    total_issues_found: int
    total_fixes_generated: int
    last_analyzed: Optional[datetime]
    model_config = {"from_attributes": True}


class IssueSchema(BaseModel):
    id: Optional[int] = None
    repo_full_name: str
    file_path: str
    line_start: Optional[int]
    line_end: Optional[int]
    issue_type: str
    severity: str
    title: str
    description: str
    suggestion: Optional[str]
    fixed_code: Optional[str]
    confidence: float
    is_resolved: bool = False
    created_at: Optional[datetime]
    model_config = {"from_attributes": True}


class AnalyzeRequest(BaseModel):
    repo_full_name: str
    branch: Optional[str] = None
    files: Optional[List[str]] = None  # specific files, or None = full repo
    pr_number: Optional[int] = None


class AnalyzeResponse(BaseModel):
    run_id: int
    status: str
    repo: str
    files_analyzed: int
    issues_found: int
    fixes_generated: int
    health_score: Optional[float]
    issues: List[IssueSchema]
    summary: str
    duration_ms: Optional[int]


class FixRequest(BaseModel):
    repo_full_name: str
    issue_ids: List[int]
    create_pr: bool = False
    branch_name: Optional[str] = None


class FixResponse(BaseModel):
    status: str
    fixes_applied: int
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    message: str


class CodeHealthReport(BaseModel):
    repo: str
    health_score: float
    total_issues: int
    critical: int
    high: int
    medium: int
    low: int
    by_type: Dict[str, int]
    by_file: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime


class WebhookPayload(BaseModel):
    action: Optional[str] = None
    repository: Optional[Dict[str, Any]] = None
    pull_request: Optional[Dict[str, Any]] = None
    commits: Optional[List[Dict[str, Any]]] = None
    ref: Optional[str] = None
    after: Optional[str] = None

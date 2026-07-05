"""Analysis pipeline routes."""
import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc, select

from app.agents.orchestrator import get_status, run_analysis
from app.models.database import AnalysisRun, AsyncSessionLocal, CodeIssue
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, IssueSchema

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run", response_model=AnalyzeResponse)
async def trigger_analysis(request: AnalyzeRequest):
    """
    Trigger full LangGraph pipeline: Scan → Review → Report.
    """
    result = await run_analysis(
        repo_full_name=request.repo_full_name,
        branch=request.branch,
        pr_number=request.pr_number,
        specific_files=request.files,
        trigger="manual",
    )

    if result["status"] == "done" or result["status"] == "partial":
        report = result.get("report") or {}
        issues = [
            IssueSchema(
                repo_full_name=request.repo_full_name,
                file_path=i.get("file_path", ""),
                line_start=i.get("line_start"),
                line_end=i.get("line_end"),
                issue_type=i.get("issue_type", "other"),
                severity=i.get("severity", "low"),
                title=str(i.get("title", ""))[:300],
                description=str(i.get("description", "")),
                suggestion=i.get("suggestion"),
                fixed_code=i.get("fixed_code"),
                confidence=float(i.get("confidence", 0.7)),
            )
            for i in result.get("issues", [])
        ]
        return AnalyzeResponse(
            run_id=result.get("run_id") or 0,
            status=result["status"],
            repo=request.repo_full_name,
            files_analyzed=result.get("files_analyzed", 0),
            issues_found=len(issues),
            fixes_generated=sum(1 for i in issues if i.fixed_code),
            health_score=report.get("health_score"),
            issues=issues,
            summary=json.dumps(report.get("recommendations", [])),
            duration_ms=result.get("duration_ms"),
        )

    raise HTTPException(status_code=500, detail=f"Analysis failed: {result.get('errors')}")


@router.get("/status")
async def get_pipeline_status():
    return get_status()


@router.get("/runs")
async def list_runs(limit: int = Query(20, le=100), repo: Optional[str] = None):
    """List past analysis runs."""
    async with AsyncSessionLocal() as session:
        query = select(AnalysisRun).order_by(desc(AnalysisRun.created_at)).limit(limit)
        if repo:
            query = query.where(AnalysisRun.repo_full_name == repo)
        result = await session.execute(query)
        runs = result.scalars().all()
        return [
            {
                "id": r.id,
                "repo": r.repo_full_name,
                "trigger": r.trigger,
                "status": r.status,
                "files_analyzed": r.files_analyzed,
                "issues_found": r.issues_found,
                "health_score": r.health_score,
                "duration_ms": r.duration_ms,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]


@router.get("/issues")
async def list_issues(
    repo: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: bool = False,
    limit: int = Query(50, le=200),
):
    """List code issues, filterable by repo/severity/resolved."""
    async with AsyncSessionLocal() as session:
        query = (
            select(CodeIssue)
            .where(CodeIssue.is_resolved == resolved)
            .order_by(desc(CodeIssue.created_at))
            .limit(limit)
        )
        if repo:
            query = query.where(CodeIssue.repo_full_name == repo)
        if severity:
            query = query.where(CodeIssue.severity == severity)

        result = await session.execute(query)
        issues = result.scalars().all()
        return [
            {
                "id": i.id,
                "repo": i.repo_full_name,
                "file": i.file_path,
                "line": i.line_start,
                "type": i.issue_type,
                "severity": i.severity,
                "title": i.title,
                "confidence": i.confidence,
                "resolved": i.is_resolved,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in issues
        ]


@router.patch("/issues/{issue_id}/resolve")
async def resolve_issue(issue_id: int):
    """Mark an issue as resolved."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CodeIssue).where(CodeIssue.id == issue_id))
        issue = result.scalar_one_or_none()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        issue.is_resolved = True
        await session.commit()
    return {"message": f"Issue {issue_id} marked as resolved"}

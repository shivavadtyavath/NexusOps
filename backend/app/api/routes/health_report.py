"""Code health report routes."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func, desc

from app.agents.reporter_agent import reporter_agent
from app.models.database import AnalysisRun, AsyncSessionLocal, CodeIssue

router = APIRouter(prefix="/health", tags=["health-report"])


@router.get("/report/{owner}/{name}")
async def get_health_report(owner: str, name: str):
    """Generate a code health report for a repository."""
    full_name = f"{owner}/{name}"

    async with AsyncSessionLocal() as session:
        # Get all unresolved issues
        result = await session.execute(
            select(CodeIssue)
            .where(
                CodeIssue.repo_full_name == full_name,
                CodeIssue.is_resolved == False,
            )
            .order_by(desc(CodeIssue.created_at))
            .limit(200)
        )
        issues = result.scalars().all()

        # Get latest run for stats
        run_result = await session.execute(
            select(AnalysisRun)
            .where(AnalysisRun.repo_full_name == full_name)
            .order_by(desc(AnalysisRun.created_at))
            .limit(1)
        )
        latest_run = run_result.scalar_one_or_none()

    if not issues and not latest_run:
        raise HTTPException(
            status_code=404, detail=f"No analysis data for {full_name}. Run analysis first."
        )

    issues_list = [
        {
            "file_path": i.file_path,
            "issue_type": i.issue_type,
            "severity": i.severity,
            "title": i.title,
            "confidence": i.confidence,
        }
        for i in issues
    ]

    report = reporter_agent.generate_report(
        repo_full_name=full_name,
        issues=issues_list,
        files_analyzed=latest_run.files_analyzed if latest_run else 0,
        total_lines=0,
    )
    return report


@router.get("/summary")
async def get_global_summary():
    """Global summary across all registered repos."""
    async with AsyncSessionLocal() as session:
        # Count by severity
        sev_result = await session.execute(
            select(CodeIssue.severity, func.count(CodeIssue.id))
            .where(CodeIssue.is_resolved == False)
            .group_by(CodeIssue.severity)
        )
        by_severity = dict(sev_result.all())

        # Count by repo
        repo_result = await session.execute(
            select(CodeIssue.repo_full_name, func.count(CodeIssue.id))
            .where(CodeIssue.is_resolved == False)
            .group_by(CodeIssue.repo_full_name)
            .order_by(desc(func.count(CodeIssue.id)))
            .limit(10)
        )
        by_repo = [{"repo": r, "issues": c} for r, c in repo_result.all()]

        # Recent runs
        run_result = await session.execute(
            select(AnalysisRun)
            .order_by(desc(AnalysisRun.created_at))
            .limit(5)
        )
        recent_runs = [
            {
                "id": r.id,
                "repo": r.repo_full_name,
                "status": r.status,
                "health_score": r.health_score,
                "issues": r.issues_found,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in run_result.scalars().all()
        ]

    return {
        "total_issues": sum(by_severity.values()),
        "by_severity": by_severity,
        "top_repos_by_issues": by_repo,
        "recent_runs": recent_runs,
    }

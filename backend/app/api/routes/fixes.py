"""Fix generation routes."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.agents.fixer_agent import fixer_agent
from app.models.database import AsyncSessionLocal, CodeIssue
from app.models.schemas import FixRequest, FixResponse

router = APIRouter(prefix="/fixes", tags=["fixes"])


@router.post("/generate", response_model=FixResponse)
async def generate_fixes(request: FixRequest):
    """
    Generate AI-powered code fixes for selected issues.
    Optionally creates a GitHub PR with the fixes.
    """
    if not request.issue_ids:
        raise HTTPException(status_code=400, detail="No issue IDs provided")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CodeIssue).where(CodeIssue.id.in_(request.issue_ids))
        )
        issues = result.scalars().all()

    if not issues:
        raise HTTPException(status_code=404, detail="No issues found with given IDs")

    # Group issues by file
    by_file: dict = {}
    for issue in issues:
        fp = issue.file_path
        if fp not in by_file:
            by_file[fp] = []
        by_file[fp].append({
            "line_start": issue.line_start,
            "line_end": issue.line_end,
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "title": issue.title,
            "description": issue.description,
            "confidence": issue.confidence,
        })

    fixes_applied = 0
    for file_path, file_issues in by_file.items():
        # Fetch file content from GitHub
        from app.core.github_client import github_client
        code = await github_client.get_file_contents(request.repo_full_name, file_path)
        if not code:
            continue

        from app.core.code_parser import detect_language
        language = detect_language(file_path) or "python"

        file_data = {"code": code, "file_path": file_path, "language": language}
        fixed_code = await fixer_agent.generate_fixes(file_data, file_issues)

        if fixed_code:
            fixes_applied += 1
            # Update DB with fixed code
            async with AsyncSessionLocal() as session:
                for issue_id in request.issue_ids:
                    result = await session.execute(
                        select(CodeIssue).where(CodeIssue.id == issue_id)
                    )
                    issue = result.scalar_one_or_none()
                    if issue and issue.file_path == file_path:
                        issue.fixed_code = fixed_code[:5000]
                await session.commit()

    # Optionally create PR
    pr_url = None
    pr_number = None
    if request.create_pr and fixes_applied > 0:
        return FixResponse(
            status="partial",
            fixes_applied=fixes_applied,
            message=f"Generated fixes for {fixes_applied} file(s). PR creation requires branch push — see README.",
        )

    return FixResponse(
        status="done",
        fixes_applied=fixes_applied,
        pr_url=pr_url,
        pr_number=pr_number,
        message=f"Generated AI fixes for {fixes_applied} file(s). View fixes in /analysis/issues endpoint.",
    )

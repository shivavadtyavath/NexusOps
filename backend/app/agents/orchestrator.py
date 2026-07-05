"""
NexusOps LangGraph Pipeline:
  Scanner → Reviewer → Reporter → (optional) Fixer
"""
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.fixer_agent import fixer_agent
from app.agents.reporter_agent import reporter_agent
from app.agents.reviewer_agent import reviewer_agent
from app.agents.scanner_agent import scanner_agent
from app.models.database import AnalysisRun, AsyncSessionLocal, CodeIssue
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NexusState(TypedDict):
    repo_full_name: str
    branch: Optional[str]
    pr_number: Optional[int]
    specific_files: Optional[List[str]]
    trigger: str
    scanned_files: List[Dict[str, Any]]
    raw_issues: List[Dict[str, Any]]
    report: Optional[Dict[str, Any]]
    fixes: Optional[List[Dict[str, Any]]]
    run_id: Optional[int]
    errors: List[str]
    started_at: float


async def node_scan(state: NexusState) -> NexusState:
    logger.info("nexus.scan", repo=state["repo_full_name"])
    try:
        if state.get("pr_number"):
            result = await scanner_agent.scan_pr_diff(
                state["repo_full_name"], state["pr_number"]
            )
        else:
            result = await scanner_agent.scan_repo(
                state["repo_full_name"],
                branch=state.get("branch"),
                specific_files=state.get("specific_files"),
            )
        state["scanned_files"] = result.get("files", [])
    except Exception as e:
        logger.error("nexus.scan_error", error=str(e))
        state["errors"].append(f"Scan: {str(e)}")
        state["scanned_files"] = []
    return state


async def node_review(state: NexusState) -> NexusState:
    logger.info("nexus.review", files=len(state["scanned_files"]))
    try:
        ai_issues = await reviewer_agent.review_files(state["scanned_files"])

        # Also include static issues from scanner
        static_issues = []
        for f in state["scanned_files"]:
            for si in f.get("static_issues", []):
                si["file_path"] = f["file_path"]
                static_issues.append(si)

        # Merge, deduplicate by title+file
        seen = set()
        all_issues = []
        for issue in (ai_issues + static_issues):
            key = (issue.get("file_path"), issue.get("title", ""), issue.get("line_start"))
            if key not in seen:
                seen.add(key)
                all_issues.append(issue)

        state["raw_issues"] = all_issues
    except Exception as e:
        logger.error("nexus.review_error", error=str(e))
        state["errors"].append(f"Review: {str(e)}")
        state["raw_issues"] = []
    return state


async def node_report(state: NexusState) -> NexusState:
    logger.info("nexus.report", issues=len(state["raw_issues"]))
    try:
        total_lines = sum(f.get("lines", 0) for f in state["scanned_files"])
        report = reporter_agent.generate_report(
            state["repo_full_name"],
            state["raw_issues"],
            len(state["scanned_files"]),
            total_lines,
        )
        state["report"] = report

        # Persist run to DB
        run_id = await _persist_run(state, report)
        state["run_id"] = run_id

        # Post PR comment if triggered by PR
        if state.get("pr_number"):
            comment = await reporter_agent.generate_pr_review_comment(
                state["raw_issues"], state["repo_full_name"], state["pr_number"]
            )
            try:
                from app.core.github_client import github_client
                await github_client.post_pr_comment(
                    state["repo_full_name"], state["pr_number"], comment
                )
            except Exception as e:
                logger.warning("nexus.pr_comment_error", error=str(e))

    except Exception as e:
        logger.error("nexus.report_error", error=str(e))
        state["errors"].append(f"Report: {str(e)}")
    return state


async def _persist_run(state: NexusState, report: Dict[str, Any]) -> Optional[int]:
    try:
        duration = int((time.time() - state["started_at"]) * 1000)
        async with AsyncSessionLocal() as session:
            run = AnalysisRun(
                repo_full_name=state["repo_full_name"],
                trigger=state["trigger"],
                commit_sha=None,
                pr_number=state.get("pr_number"),
                branch=state.get("branch"),
                files_analyzed=report["files_analyzed"],
                issues_found=report["total_issues"],
                fixes_generated=0,
                health_score=report["health_score"],
                duration_ms=duration,
                status="done" if not state["errors"] else "partial",
                summary=json.dumps({
                    "critical": report["critical"],
                    "high": report["high"],
                    "medium": report["medium"],
                    "low": report["low"],
                }),
            )
            session.add(run)
            await session.flush()
            run_id = run.id

            # Persist issues
            for issue in state["raw_issues"][:100]:
                db_issue = CodeIssue(
                    repo_full_name=state["repo_full_name"],
                    file_path=issue.get("file_path", ""),
                    line_start=issue.get("line_start"),
                    line_end=issue.get("line_end"),
                    issue_type=issue.get("issue_type", "other"),
                    severity=issue.get("severity", "low"),
                    title=str(issue.get("title", ""))[:300],
                    description=str(issue.get("description", "")),
                    suggestion=issue.get("suggestion"),
                    fixed_code=issue.get("fixed_code"),
                    confidence=float(issue.get("confidence", 0.7)),
                )
                session.add(db_issue)

            await session.commit()
            return run_id
    except Exception as e:
        logger.error("nexus.persist_error", error=str(e))
        return None


def build_pipeline():
    graph = StateGraph(NexusState)
    graph.add_node("scan", node_scan)
    graph.add_node("review", node_review)
    graph.add_node("report", node_report)
    graph.add_edge(START, "scan")
    graph.add_edge("scan", "review")
    graph.add_edge("review", "report")
    graph.add_edge("report", END)
    return graph.compile()


_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


_status = {"status": "idle", "last_run": None, "duration_ms": None}


async def run_analysis(
    repo_full_name: str,
    branch: Optional[str] = None,
    pr_number: Optional[int] = None,
    specific_files: Optional[List[str]] = None,
    trigger: str = "manual",
) -> Dict[str, Any]:
    global _status
    _status["status"] = "running"
    start = time.time()

    initial: NexusState = {
        "repo_full_name": repo_full_name,
        "branch": branch,
        "pr_number": pr_number,
        "specific_files": specific_files,
        "trigger": trigger,
        "scanned_files": [],
        "raw_issues": [],
        "report": None,
        "fixes": None,
        "run_id": None,
        "errors": [],
        "started_at": start,
    }

    pipeline = get_pipeline()
    final = await pipeline.ainvoke(initial)

    duration_ms = int((time.time() - start) * 1000)
    _status = {
        "status": "done" if not final["errors"] else "partial",
        "last_run": datetime.utcnow().isoformat(),
        "duration_ms": duration_ms,
    }

    return {
        "status": _status["status"],
        "run_id": final.get("run_id"),
        "repo": repo_full_name,
        "files_analyzed": len(final["scanned_files"]),
        "issues": final["raw_issues"],
        "report": final.get("report"),
        "errors": final["errors"],
        "duration_ms": duration_ms,
    }


def get_status() -> Dict[str, Any]:
    return dict(_status)

"""
GitHub Webhook handler — auto-triggers analysis on PR open/push.
"""
import hashlib
import hmac
import json

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from app.agents.orchestrator import run_analysis
from app.config import settings
from app.utils.logger import get_logger

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = get_logger(__name__)


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook HMAC signature."""
    if not settings.github_webhook_secret:
        return True  # Skip verification if no secret set
    expected = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
):
    """
    Receive GitHub webhook events and trigger analysis.
    Events handled: pull_request (opened/synchronized), push
    """
    body = await request.body()

    if not verify_signature(body, x_hub_signature_256 or ""):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    repo = (payload.get("repository") or {}).get("full_name")
    if not repo:
        return {"status": "ignored", "reason": "no repo info"}

    event = x_github_event or ""
    logger.info("webhook.received", event=event, repo=repo)

    if event == "pull_request":
        action = payload.get("action")
        if action in ("opened", "synchronize", "reopened"):
            pr_number = payload["pull_request"]["number"]
            background_tasks.add_task(
                run_analysis,
                repo_full_name=repo,
                pr_number=pr_number,
                trigger="webhook_pr",
            )
            return {"status": "queued", "event": "pr_review", "pr": pr_number}

    elif event == "push":
        ref = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else None
        if branch:
            background_tasks.add_task(
                run_analysis,
                repo_full_name=repo,
                branch=branch,
                trigger="webhook_push",
            )
            return {"status": "queued", "event": "push_scan", "branch": branch}

    return {"status": "ignored", "event": event}

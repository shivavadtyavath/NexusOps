"""Repository management routes."""
from typing import List
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, desc

from app.core.github_client import github_client
from app.models.database import AsyncSessionLocal, Repository
from app.models.schemas import RepoRequest, RepoResponse

router = APIRouter(prefix="/repos", tags=["repositories"])


@router.post("/register", response_model=RepoResponse)
async def register_repo(request: RepoRequest):
    """Register a GitHub repository for analysis."""
    try:
        meta = await github_client.get_repo(request.repo_full_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot access repo: {str(e)}")

    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(Repository).where(Repository.full_name == meta["full_name"])
        )
        repo = existing.scalar_one_or_none()
        if repo is None:
            repo = Repository(
                full_name=meta["full_name"],
                owner=meta["owner"],
                name=meta["name"],
                default_branch=meta["default_branch"],
                language=meta["language"],
                description=meta["description"],
            )
            session.add(repo)
        await session.commit()
        await session.refresh(repo)
        return repo


@router.get("/", response_model=List[RepoResponse])
async def list_repos(limit: int = Query(20, le=100)):
    """List registered repositories."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Repository).order_by(desc(Repository.created_at)).limit(limit)
        )
        return result.scalars().all()


@router.get("/{owner}/{name}", response_model=RepoResponse)
async def get_repo(owner: str, name: str):
    """Get a single repo's details."""
    full_name = f"{owner}/{name}"
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        repo = result.scalar_one_or_none()
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repo {full_name} not registered")
        return repo


@router.delete("/{owner}/{name}")
async def delete_repo(owner: str, name: str):
    """Remove a repo from monitoring."""
    full_name = f"{owner}/{name}"
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        repo = result.scalar_one_or_none()
        if not repo:
            raise HTTPException(status_code=404, detail="Repo not found")
        await session.delete(repo)
        await session.commit()
    return {"message": f"Removed {full_name}"}

"""
GitHub client wrapper — uses PyGithub (free, uses GitHub REST API).
GitHub gives 5,000 free API calls/hour with a token.
"""
import asyncio
import base64
from typing import Any, Dict, List, Optional, Tuple

from github import Github, GithubException, Auth
from github.Repository import Repository

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_github: Optional[Github] = None


def get_github() -> Github:
    global _github
    if _github is None:
        if settings.github_token:
            _github = Github(auth=Auth.Token(settings.github_token))
        else:
            _github = Github()  # unauthenticated (lower rate limit)
    return _github


class GitHubClient:
    """Async-friendly GitHub client using PyGithub in thread pool."""

    async def get_repo(self, full_name: str) -> Dict[str, Any]:
        """Get repository metadata."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_get_repo, full_name)

    def _sync_get_repo(self, full_name: str) -> Dict[str, Any]:
        gh = get_github()
        repo = gh.get_repo(full_name)
        return {
            "full_name": repo.full_name,
            "owner": repo.owner.login,
            "name": repo.name,
            "default_branch": repo.default_branch,
            "language": repo.language,
            "description": repo.description,
        }

    async def get_file_contents(
        self, full_name: str, path: str, ref: Optional[str] = None
    ) -> Optional[str]:
        """Get decoded file content as a string."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._sync_get_file, full_name, path, ref
        )

    def _sync_get_file(
        self, full_name: str, path: str, ref: Optional[str]
    ) -> Optional[str]:
        try:
            gh = get_github()
            repo = gh.get_repo(full_name)
            kwargs = {}
            if ref:
                kwargs["ref"] = ref
            content = repo.get_contents(path, **kwargs)
            if isinstance(content, list):
                return None  # directory
            if content.encoding == "base64":
                return base64.b64decode(content.content).decode("utf-8", errors="replace")
            return content.decoded_content.decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning("github.get_file_error", path=path, error=str(e))
            return None

    async def list_files(
        self,
        full_name: str,
        extensions: Optional[List[str]] = None,
        ref: Optional[str] = None,
        max_files: int = 50,
    ) -> List[Dict[str, Any]]:
        """List all files in repo matching extensions."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._sync_list_files, full_name, extensions, ref, max_files
        )

    def _sync_list_files(
        self,
        full_name: str,
        extensions: Optional[List[str]],
        ref: Optional[str],
        max_files: int,
    ) -> List[Dict[str, Any]]:
        try:
            gh = get_github()
            repo = gh.get_repo(full_name)
            kwargs = {}
            if ref:
                kwargs["ref"] = ref

            files = []
            contents = repo.get_git_tree(ref or repo.default_branch, recursive=True)
            for item in contents.tree:
                if item.type != "blob":
                    continue
                if extensions:
                    if not any(item.path.endswith(ext) for ext in extensions):
                        continue
                if item.size and item.size > settings.max_file_size_kb * 1024:
                    continue
                files.append({
                    "path": item.path,
                    "size": item.size,
                    "sha": item.sha,
                })
                if len(files) >= max_files:
                    break
            return files
        except Exception as e:
            logger.error("github.list_files_error", repo=full_name, error=str(e))
            return []

    async def get_pr_diff(
        self, full_name: str, pr_number: int
    ) -> List[Dict[str, Any]]:
        """Get changed files and their diffs for a PR."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._sync_get_pr_diff, full_name, pr_number
        )

    def _sync_get_pr_diff(
        self, full_name: str, pr_number: int
    ) -> List[Dict[str, Any]]:
        try:
            gh = get_github()
            repo = gh.get_repo(full_name)
            pr = repo.get_pull(pr_number)
            files = []
            for f in pr.get_files():
                files.append({
                    "path": f.filename,
                    "status": f.status,  # added|modified|removed
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "patch": f.patch or "",
                })
            return files
        except Exception as e:
            logger.error("github.pr_diff_error", pr=pr_number, error=str(e))
            return []

    async def create_pr(
        self,
        full_name: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str,
    ) -> Dict[str, Any]:
        """Create a pull request."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._sync_create_pr, full_name, title, body, head_branch, base_branch
        )

    def _sync_create_pr(
        self, full_name: str, title: str, body: str, head: str, base: str
    ) -> Dict[str, Any]:
        gh = get_github()
        repo = gh.get_repo(full_name)
        pr = repo.create_pull(title=title, body=body, head=head, base=base)
        return {"number": pr.number, "url": pr.html_url, "title": pr.title}

    async def post_pr_comment(
        self, full_name: str, pr_number: int, comment: str
    ) -> None:
        """Post a review comment on a PR."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self._sync_post_comment, full_name, pr_number, comment
        )

    def _sync_post_comment(
        self, full_name: str, pr_number: int, comment: str
    ) -> None:
        try:
            gh = get_github()
            repo = gh.get_repo(full_name)
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(comment)
        except Exception as e:
            logger.error("github.comment_error", error=str(e))


github_client = GitHubClient()

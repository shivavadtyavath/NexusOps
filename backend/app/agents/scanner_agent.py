"""
ScannerAgent — fetches repo files from GitHub and runs static analysis.
First pass: regex + AST + bandit (no LLM needed for this step).
"""
import asyncio
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.code_parser import analyze_file, detect_language
from app.core.github_client import github_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

# File extensions to analyze
CODE_EXTENSIONS = [
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".java", ".rs", ".cpp", ".c",
]


class ScannerAgent:
    """Scans a GitHub repo and extracts code + static issues."""

    async def scan_repo(
        self,
        repo_full_name: str,
        branch: Optional[str] = None,
        specific_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Returns: {files: [{path, code, language, static_issues, structure}]}
        """
        logger.info("scanner_agent.start", repo=repo_full_name)

        if specific_files:
            file_list = [{"path": p, "size": 0, "sha": ""} for p in specific_files]
        else:
            file_list = await github_client.list_files(
                repo_full_name,
                extensions=CODE_EXTENSIONS,
                ref=branch,
                max_files=settings.max_files_per_pr,
            )

        if not file_list:
            logger.warning("scanner_agent.no_files", repo=repo_full_name)
            return {"files": [], "total": 0}

        # Fetch and analyze files concurrently (batch of 5)
        results = []
        batch_size = 5
        for i in range(0, len(file_list), batch_size):
            batch = file_list[i:i + batch_size]
            tasks = [
                self._analyze_one(repo_full_name, f["path"], branch)
                for f in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in batch_results:
                if isinstance(r, dict):
                    results.append(r)

        logger.info("scanner_agent.done", repo=repo_full_name, files=len(results))
        return {"files": results, "total": len(results)}

    async def scan_pr_diff(
        self,
        repo_full_name: str,
        pr_number: int,
    ) -> Dict[str, Any]:
        """Scan only the files changed in a specific PR."""
        logger.info("scanner_agent.scan_pr", repo=repo_full_name, pr=pr_number)

        pr_files = await github_client.get_pr_diff(repo_full_name, pr_number)
        code_files = [
            f for f in pr_files
            if detect_language(f["path"]) and f["status"] != "removed"
        ]

        results = []
        for f in code_files[:settings.max_files_per_pr]:
            analyzed = await self._analyze_one(repo_full_name, f["path"])
            if analyzed:
                analyzed["diff_patch"] = f.get("patch", "")
                results.append(analyzed)

        return {"files": results, "total": len(results), "pr_number": pr_number}

    async def _analyze_one(
        self,
        repo_full_name: str,
        file_path: str,
        ref: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch + analyze a single file."""
        code = await github_client.get_file_contents(repo_full_name, file_path, ref)
        if not code:
            return None
        try:
            result = analyze_file(code, file_path)
            result["code"] = code
            return result
        except Exception as e:
            logger.warning("scanner_agent.analyze_error", path=file_path, error=str(e))
            return None


scanner_agent = ScannerAgent()

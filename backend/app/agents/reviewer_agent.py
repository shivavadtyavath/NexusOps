"""
ReviewerAgent — uses Groq LLM to perform deep AI code review.
Goes beyond static analysis: detects logic bugs, architecture issues,
security vulnerabilities, and suggests fixes with actual corrected code.
"""
import json
from typing import Any, Dict, List

from groq import Groq

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_groq_client = None


def get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


REVIEW_PROMPT = """You are a senior software engineer performing a code review.
Analyze the following {language} code from file `{file_path}`.

CODE:
```{language}
{code}
```

STATIC ANALYSIS ALREADY FOUND:
{static_issues}

Perform a DEEP review and identify:
1. Logic bugs (off-by-one, null pointer, race conditions, etc.)
2. Security vulnerabilities (injection, auth bypass, data exposure, etc.)
3. Performance issues (N+1 queries, unnecessary loops, memory leaks)
4. Code complexity / maintainability issues
5. Missing error handling

For each issue, provide the FIXED CODE snippet.

Return a JSON array (max 8 issues):
[
  {{
    "line_start": <int or null>,
    "line_end": <int or null>,
    "issue_type": "bug|security|performance|style|complexity",
    "severity": "critical|high|medium|low",
    "title": "<concise title>",
    "description": "<what is wrong and why>",
    "suggestion": "<how to fix it>",
    "fixed_code": "<corrected code snippet, or null if no fix>",
    "confidence": <0.0-1.0>
  }}
]

Return ONLY the JSON array. No markdown. No explanation."""


class ReviewerAgent:
    """AI-powered code reviewer using Groq LLM (free)."""

    async def review_files(
        self, files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Review a list of files, return list of issues per file."""
        all_issues = []
        for file_data in files:
            issues = await self._review_one(file_data)
            all_issues.extend(issues)
        return all_issues

    async def _review_one(self, file_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_path = file_data.get("file_path", "unknown")
        code = file_data.get("code", "")
        language = file_data.get("language", "unknown")
        static_issues = file_data.get("static_issues", [])

        if not code or len(code.strip()) < 20:
            return []

        # Truncate very large files to avoid token limits
        max_chars = 6000
        if len(code) > max_chars:
            code = code[:max_chars] + f"\n\n# ... (truncated, {len(code)} total chars)"

        # Summarize static issues
        static_summary = "\n".join(
            f"- Line {i.get('line')}: [{i.get('severity').upper()}] {i.get('title')}"
            for i in static_issues[:5]
        ) or "None found."

        prompt = REVIEW_PROMPT.format(
            language=language,
            file_path=file_path,
            code=code,
            static_issues=static_summary,
        )

        try:
            client = get_groq()
            response = client.chat.completions.create(
                model=settings.groq_code_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.15,
            )
            raw = response.choices[0].message.content.strip()
            # Clean markdown
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            ai_issues = json.loads(raw)
            if not isinstance(ai_issues, list):
                ai_issues = []

            # Tag with file info
            for issue in ai_issues:
                issue["file_path"] = file_path
                issue["source"] = "ai_review"

            logger.info("reviewer_agent.done", file=file_path, issues=len(ai_issues))
            return ai_issues

        except Exception as e:
            logger.error("reviewer_agent.error", file=file_path, error=str(e))
            # Return static issues as fallback
            return [
                {
                    "file_path": file_path,
                    "line_start": i.get("line"),
                    "line_end": i.get("line"),
                    "issue_type": i.get("issue_type", "style"),
                    "severity": i.get("severity", "low"),
                    "title": i.get("title", ""),
                    "description": i.get("description", ""),
                    "suggestion": None,
                    "fixed_code": None,
                    "confidence": i.get("confidence", 0.7),
                    "source": "static_analysis",
                }
                for i in static_issues
            ]


reviewer_agent = ReviewerAgent()

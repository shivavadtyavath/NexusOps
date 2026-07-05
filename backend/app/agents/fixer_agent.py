"""
FixerAgent — generates complete fixed versions of files with all issues resolved.
Uses Groq LLM to rewrite code sections with proper fixes.
"""
import json
from typing import Any, Dict, List, Optional

from groq import Groq

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_groq() -> Groq:
    return Groq(api_key=settings.groq_api_key)


FIX_PROMPT = """You are a senior software engineer. Fix the following {language} code.

FILE: {file_path}
ORIGINAL CODE:
```{language}
{code}
```

ISSUES TO FIX:
{issues_text}

Rules:
- Fix ALL listed issues
- Do NOT change code that is not related to the issues
- Maintain the same overall structure
- Add brief inline comments where you made changes (# FIXED: reason)
- Return ONLY the complete fixed code, no markdown fences, no explanation

Fixed code:"""


class FixerAgent:
    """Generates fixed code for identified issues."""

    async def generate_fixes(
        self,
        file_data: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> Optional[str]:
        """
        Generate a fully fixed version of the file.
        Returns the fixed code string.
        """
        code = file_data.get("code", "")
        file_path = file_data.get("file_path", "")
        language = file_data.get("language", "python")

        if not code or not issues:
            return None

        # Filter to high/critical issues only (to keep context small)
        critical_issues = [
            i for i in issues
            if i.get("severity") in ("critical", "high", "medium")
            and i.get("confidence", 0) >= settings.auto_fix_threshold
        ]

        if not critical_issues:
            # Try with all issues
            critical_issues = issues[:5]

        if not critical_issues:
            return None

        issues_text = "\n".join(
            f"{j+1}. [{i.get('severity', '').upper()}] Line {i.get('line_start')}: "
            f"{i.get('title')} — {i.get('description', '')[:200]}"
            for j, i in enumerate(critical_issues)
        )

        # Truncate code if needed
        max_chars = 5000
        code_to_fix = code[:max_chars] if len(code) > max_chars else code

        prompt = FIX_PROMPT.format(
            language=language,
            file_path=file_path,
            code=code_to_fix,
            issues_text=issues_text,
        )

        try:
            client = get_groq()
            response = client.chat.completions.create(
                model=settings.groq_code_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.1,
            )
            fixed = response.choices[0].message.content.strip()
            # Remove any accidental markdown fences
            if fixed.startswith("```"):
                lines = fixed.split("\n")
                fixed = "\n".join(
                    lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
                )
            logger.info("fixer_agent.fixed", file=file_path, issues=len(critical_issues))
            return fixed
        except Exception as e:
            logger.error("fixer_agent.error", file=file_path, error=str(e))
            return None

    async def generate_pr_description(
        self,
        repo: str,
        fixes: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
    ) -> str:
        """Generate a professional PR description for the fixes."""
        issues_summary = "\n".join(
            f"- [{i.get('severity', '').upper()}] `{i.get('file_path')}:{i.get('line_start')}` — {i.get('title')}"
            for i in issues[:15]
        )

        prompt = f"""Write a professional GitHub PR description for code fixes in repo `{repo}`.

Issues fixed:
{issues_summary}

The description should include:
- Summary of changes
- List of issues fixed with severity
- Testing notes
- Any breaking changes (usually none for fixes)

Keep it concise and professional."""

        try:
            client = get_groq()
            response = client.chat.completions.create(
                model=settings.groq_fast_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"NexusOps auto-fix: resolved {len(issues)} code quality issues in {repo}"


fixer_agent = FixerAgent()

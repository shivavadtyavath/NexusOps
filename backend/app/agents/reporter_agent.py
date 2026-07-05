"""
ReporterAgent — generates a comprehensive code health report.
Computes health score, prioritized issue list, and actionable recommendations.
"""
import json
from datetime import datetime
from typing import Any, Dict, List

from groq import Groq

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SEVERITY_WEIGHTS = {"critical": 10, "high": 5, "medium": 2, "low": 0.5}
MAX_SCORE = 100.0


def get_groq() -> Groq:
    return Groq(api_key=settings.groq_api_key)


class ReporterAgent:
    """Generates code health reports and PR review comments."""

    def compute_health_score(self, issues: List[Dict[str, Any]], total_lines: int) -> float:
        """
        Health score from 0-100.
        Penalizes based on severity weighted issues per 1000 lines.
        """
        if total_lines == 0:
            return 100.0

        penalty = sum(SEVERITY_WEIGHTS.get(i.get("severity", "low"), 0.5) for i in issues)
        # Normalize: 1 critical per 100 lines = score ~50
        normalized_penalty = (penalty / total_lines) * 1000
        score = max(0.0, round(MAX_SCORE - normalized_penalty, 1))
        return score

    def generate_report(
        self,
        repo_full_name: str,
        issues: List[Dict[str, Any]],
        files_analyzed: int,
        total_lines: int,
    ) -> Dict[str, Any]:
        """Generate a structured code health report."""
        health_score = self.compute_health_score(issues, total_lines)

        # Count by severity
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_type: Dict[str, int] = {}
        by_file: Dict[str, int] = {}

        for issue in issues:
            sev = issue.get("severity", "low")
            by_severity[sev] = by_severity.get(sev, 0) + 1
            itype = issue.get("issue_type", "other")
            by_type[itype] = by_type.get(itype, 0) + 1
            fpath = issue.get("file_path", "unknown")
            by_file[fpath] = by_file.get(fpath, 0) + 1

        # Top problematic files
        top_files = sorted(
            [{"file": f, "issues": c} for f, c in by_file.items()],
            key=lambda x: x["issues"],
            reverse=True,
        )[:10]

        # Basic recommendations (rule-based)
        recommendations = self._get_recommendations(by_severity, by_type, health_score)

        return {
            "repo": repo_full_name,
            "health_score": health_score,
            "total_issues": len(issues),
            "files_analyzed": files_analyzed,
            "total_lines": total_lines,
            "critical": by_severity["critical"],
            "high": by_severity["high"],
            "medium": by_severity["medium"],
            "low": by_severity["low"],
            "by_type": by_type,
            "by_file": top_files,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _get_recommendations(
        self, by_severity: Dict, by_type: Dict, score: float
    ) -> List[str]:
        recs = []
        if by_severity["critical"] > 0:
            recs.append(
                f"🚨 Fix {by_severity['critical']} critical issue(s) immediately — these represent serious security or correctness risks"
            )
        if by_type.get("security", 0) > 0:
            recs.append(
                f"🔒 Address {by_type['security']} security issue(s): review for hardcoded secrets, injection vulnerabilities, and authentication bypasses"
            )
        if by_type.get("performance", 0) > 0:
            recs.append(
                f"⚡ Optimize {by_type['performance']} performance issue(s): check for N+1 queries, unnecessary loops, and memory leaks"
            )
        if score < 60:
            recs.append(
                "📉 Code health is poor. Consider a dedicated refactoring sprint before adding new features"
            )
        elif score < 80:
            recs.append(
                "⚠️ Code health needs attention. Schedule regular code review sessions"
            )
        else:
            recs.append("✅ Good code health. Keep up code review practices to maintain quality")
        if by_type.get("bug", 0) > 3:
            recs.append(
                "🐛 Multiple logic bugs detected. Add unit tests for edge cases"
            )
        return recs

    async def generate_pr_review_comment(
        self, issues: List[Dict[str, Any]], repo: str, pr_number: int
    ) -> str:
        """Generate a formatted GitHub PR review comment."""
        if not issues:
            return "✅ **NexusOps**: No significant issues found. Code looks good!"

        critical = [i for i in issues if i.get("severity") == "critical"]
        high = [i for i in issues if i.get("severity") == "high"]
        medium = [i for i in issues if i.get("severity") == "medium"]
        low = [i for i in issues if i.get("severity") == "low"]

        lines = [
            f"## 🤖 NexusOps Autonomous Code Review — PR #{pr_number}",
            "",
            f"Found **{len(issues)} issue(s)** across {len(set(i.get('file_path') for i in issues))} file(s).",
            "",
            "| Severity | Count |",
            "|----------|-------|",
            f"| 🚨 Critical | {len(critical)} |",
            f"| 🔴 High | {len(high)} |",
            f"| 🟡 Medium | {len(medium)} |",
            f"| 🔵 Low | {len(low)} |",
            "",
        ]

        # Show top critical/high issues
        for issue in (critical + high)[:5]:
            lines.append(
                f"### [{issue.get('severity', '').upper()}] `{issue.get('file_path')}` "
                f"(Line {issue.get('line_start', '?')})"
            )
            lines.append(f"**{issue.get('title')}**")
            lines.append(f"{issue.get('description', '')}")
            if issue.get("suggestion"):
                lines.append(f"> 💡 {issue.get('suggestion')}")
            if issue.get("fixed_code"):
                lines.append(f"\n```\n{issue.get('fixed_code')[:300]}\n```")
            lines.append("")

        lines.append("---")
        lines.append("*Generated by [NexusOps](https://github.com) — Autonomous DevOps Intelligence Platform*")

        return "\n".join(lines)


reporter_agent = ReporterAgent()

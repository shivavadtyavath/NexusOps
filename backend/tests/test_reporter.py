"""Tests for reporter agent."""
import pytest
from app.agents.reporter_agent import ReporterAgent


def test_health_score_no_issues():
    agent = ReporterAgent()
    score = agent.compute_health_score([], total_lines=1000)
    assert score == 100.0


def test_health_score_critical_issues():
    agent = ReporterAgent()
    issues = [{"severity": "critical"} for _ in range(5)]
    score = agent.compute_health_score(issues, total_lines=500)
    assert score < 100.0
    assert score >= 0.0


def test_generate_report_structure():
    agent = ReporterAgent()
    issues = [
        {"severity": "critical", "issue_type": "security", "file_path": "app.py"},
        {"severity": "high", "issue_type": "bug", "file_path": "utils.py"},
        {"severity": "low", "issue_type": "style", "file_path": "app.py"},
    ]
    report = agent.generate_report("owner/repo", issues, files_analyzed=5, total_lines=1000)
    assert report["repo"] == "owner/repo"
    assert report["total_issues"] == 3
    assert report["critical"] == 1
    assert report["high"] == 1
    assert report["low"] == 1
    assert "health_score" in report
    assert isinstance(report["recommendations"], list)
    assert len(report["recommendations"]) > 0


def test_format_context_empty_issues():
    agent = ReporterAgent()
    report = agent.generate_report("test/repo", [], files_analyzed=10, total_lines=5000)
    assert report["health_score"] == 100.0
    assert report["total_issues"] == 0

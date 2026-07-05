"""
Code parser — extracts structure (functions, classes, complexity) from source files.
Uses regex-based parsing (no tree-sitter binary needed for basic analysis).
Also runs bandit for Python security checks.
"""
import ast
import re
import subprocess
import tempfile
import os
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Supported languages by extension
LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".go": "go",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".rs": "rust",
}


def detect_language(file_path: str) -> Optional[str]:
    for ext, lang in LANG_MAP.items():
        if file_path.endswith(ext):
            return lang
    return None


def parse_python_ast(code: str) -> Dict[str, Any]:
    """Parse Python code with AST to extract structure."""
    try:
        tree = ast.parse(code)
        functions = []
        classes = []
        imports = []
        complexity_indicators = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": len(node.args.args),
                    "decorators": [
                        getattr(d, 'id', getattr(d, 'attr', '')) for d in node.decorator_list
                    ],
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({"name": node.name, "line": node.lineno})
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom):
                    imports.append(node.module or "")
                else:
                    for alias in node.names:
                        imports.append(alias.name)
            # Complexity: count branches
            elif isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With)):
                complexity_indicators.append(node.lineno)

        return {
            "language": "python",
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "cyclomatic_complexity": len(complexity_indicators) + 1,
            "lines": len(code.splitlines()),
        }
    except SyntaxError as e:
        return {
            "language": "python",
            "parse_error": str(e),
            "lines": len(code.splitlines()),
        }


def parse_generic(code: str, language: str) -> Dict[str, Any]:
    """Generic regex-based parser for JS/TS/Go/Java/etc."""
    lines = code.splitlines()

    # Count function-like patterns
    func_patterns = {
        "javascript": r"\bfunction\s+\w+|\b\w+\s*=\s*\([^)]*\)\s*=>|\b\w+\s*\([^)]*\)\s*\{",
        "typescript": r"\bfunction\s+\w+|\b\w+\s*=\s*\([^)]*\)\s*=>|\b\w+\s*\([^)]*\)\s*:",
        "go": r"\bfunc\s+\w+",
        "java": r"(public|private|protected|static).*\w+\s*\([^)]*\)\s*\{",
        "rust": r"\bfn\s+\w+",
        "cpp": r"\b\w+\s+\w+\s*\([^)]*\)\s*\{",
    }

    pattern = func_patterns.get(language, r"\bfunction\s+\w+")
    func_matches = re.findall(pattern, code)

    # Count branches for complexity
    branch_pattern = r"\b(if|else|for|while|switch|catch|&&|\|\|)\b"
    branches = len(re.findall(branch_pattern, code))

    return {
        "language": language,
        "estimated_functions": len(func_matches),
        "cyclomatic_complexity": branches + 1,
        "lines": len(lines),
    }


def run_bandit_security_scan(code: str, filename: str = "temp.py") -> List[Dict[str, Any]]:
    """Run bandit security scanner on Python code (free, installed as dependency)."""
    issues = []
    if not filename.endswith(".py"):
        return issues

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        result = subprocess.run(
            ["python", "-m", "bandit", "-f", "json", "-q", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        import json
        if result.stdout:
            data = json.loads(result.stdout)
            for issue in data.get("results", []):
                issues.append({
                    "line": issue.get("line_number"),
                    "issue_type": "security",
                    "severity": issue.get("issue_severity", "medium").lower(),
                    "title": issue.get("issue_text", ""),
                    "description": f"[Bandit {issue.get('test_id')}] {issue.get('issue_text', '')}",
                    "confidence": 0.85 if issue.get("issue_confidence") == "HIGH" else 0.6,
                })
    except Exception as e:
        logger.warning("bandit.scan_error", error=str(e))
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    return issues


def detect_code_smells(code: str, language: str) -> List[Dict[str, Any]]:
    """Detect common code smells via regex patterns."""
    issues = []
    lines = code.splitlines()

    patterns = [
        # Security
        {
            "pattern": r"password\s*=\s*['\"][^'\"]+['\"]",
            "type": "security",
            "severity": "critical",
            "title": "Hardcoded password detected",
            "flags": re.IGNORECASE,
        },
        {
            "pattern": r"(secret|api_key|token)\s*=\s*['\"][a-zA-Z0-9_\-]{10,}['\"]",
            "type": "security",
            "severity": "critical",
            "title": "Hardcoded secret/API key detected",
            "flags": re.IGNORECASE,
        },
        {
            "pattern": r"eval\s*\(",
            "type": "security",
            "severity": "high",
            "title": "Use of eval() is dangerous",
            "flags": 0,
        },
        # SQL injection
        {
            "pattern": r'(execute|query)\s*\(\s*f["\']|\.format\s*\(',
            "type": "security",
            "severity": "high",
            "title": "Potential SQL injection via string formatting",
            "flags": 0,
        },
        # Code quality
        {
            "pattern": r"TODO|FIXME|HACK|XXX",
            "type": "style",
            "severity": "low",
            "title": "Unresolved TODO/FIXME comment",
            "flags": 0,
        },
        {
            "pattern": r"except\s*:",
            "type": "bug",
            "severity": "medium",
            "title": "Bare except clause catches all exceptions",
            "flags": 0,
        },
        {
            "pattern": r"print\s*\(",
            "type": "style",
            "severity": "low",
            "title": "Debug print statement found",
            "flags": 0,
        } if language == "python" else None,
        # Long lines
    ]

    for i, line in enumerate(lines, 1):
        # Long line check
        if len(line) > 120:
            issues.append({
                "line": i,
                "issue_type": "style",
                "severity": "low",
                "title": f"Line too long ({len(line)} chars > 120)",
                "description": f"Line {i} exceeds 120 characters. Consider breaking it up.",
                "confidence": 1.0,
            })

        # Pattern checks
        for pattern_def in patterns:
            if pattern_def is None:
                continue
            if re.search(pattern_def["pattern"], line, pattern_def.get("flags", 0)):
                issues.append({
                    "line": i,
                    "issue_type": pattern_def["type"],
                    "severity": pattern_def["severity"],
                    "title": pattern_def["title"],
                    "description": f"Line {i}: {line.strip()[:100]}",
                    "confidence": 0.9,
                })

    return issues


def analyze_file(code: str, file_path: str) -> Dict[str, Any]:
    """Full analysis of a single file."""
    language = detect_language(file_path) or "unknown"

    if language == "python":
        structure = parse_python_ast(code)
        security_issues = run_bandit_security_scan(code, file_path)
    else:
        structure = parse_generic(code, language)
        security_issues = []

    smell_issues = detect_code_smells(code, language)
    all_static_issues = security_issues + smell_issues

    return {
        "file_path": file_path,
        "language": language,
        "structure": structure,
        "static_issues": all_static_issues,
        "lines": structure.get("lines", 0),
        "complexity": structure.get("cyclomatic_complexity", 1),
    }

"""Tests for scanner and code parser."""
import pytest
from app.core.code_parser import (
    analyze_file, detect_language, detect_code_smells, parse_python_ast
)


def test_detect_language():
    assert detect_language("main.py") == "python"
    assert detect_language("app.ts") == "typescript"
    assert detect_language("index.go") == "go"
    assert detect_language("unknown.xyz") is None


def test_parse_python_ast_functions():
    code = """
def foo(x, y):
    return x + y

class Bar:
    def method(self):
        pass
"""
    result = parse_python_ast(code)
    assert result["language"] == "python"
    assert len(result["functions"]) >= 2
    assert len(result["classes"]) >= 1


def test_parse_python_ast_syntax_error():
    result = parse_python_ast("def foo(: invalid syntax")
    assert "parse_error" in result


def test_detect_hardcoded_password():
    code = 'password = "super_secret_123"'
    issues = detect_code_smells(code, "python")
    titles = [i["title"] for i in issues]
    assert any("password" in t.lower() or "secret" in t.lower() for t in titles)


def test_detect_bare_except():
    code = """
try:
    risky()
except:
    pass
"""
    issues = detect_code_smells(code, "python")
    assert any("bare except" in i["title"].lower() for i in issues)


def test_analyze_file_python():
    code = """
import os

def process(data):
    password = "admin123"
    for item in data:
        if item:
            print(item)
    return data
"""
    result = analyze_file(code, "main.py")
    assert result["language"] == "python"
    assert result["lines"] > 0
    assert isinstance(result["static_issues"], list)


def test_analyze_file_typescript():
    code = """
function greet(name: string): string {
    const secret = "api-key-abc123def456";
    return `Hello ${name}`;
}
"""
    result = analyze_file(code, "app.ts")
    assert result["language"] == "typescript"

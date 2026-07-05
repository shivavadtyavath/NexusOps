"""NexusOps MCP Server — exposes code intelligence tools via MCP."""
import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

server = Server("nexusops-mcp")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="analyze_repo",
            description="Trigger AI code analysis for a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "owner/repo format"},
                    "branch": {"type": "string", "description": "branch name (optional)"},
                },
                "required": ["repo"],
            },
        ),
        Tool(
            name="get_code_issues",
            description="Get code quality issues for a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                },
                "required": ["repo"],
            },
        ),
        Tool(
            name="get_health_score",
            description="Get the code health score for a repository",
            inputSchema={
                "type": "object",
                "properties": {"repo": {"type": "string"}},
                "required": ["repo"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "analyze_repo":
        from app.agents.orchestrator import run_analysis
        repo = arguments.get("repo", "")
        result = await run_analysis(repo, branch=arguments.get("branch"), trigger="mcp")
        return [TextContent(type="text", text=json.dumps({
            "status": result["status"],
            "files": result["files_analyzed"],
            "issues": len(result["issues"]),
            "health_score": result.get("report", {}).get("health_score"),
        }))]

    elif name == "get_code_issues":
        from app.models.database import AsyncSessionLocal, CodeIssue
        from sqlalchemy import select, desc
        async with AsyncSessionLocal() as session:
            query = select(CodeIssue).where(
                CodeIssue.repo_full_name == arguments["repo"],
                CodeIssue.is_resolved == False,
            ).order_by(desc(CodeIssue.created_at)).limit(20)
            if arguments.get("severity"):
                query = query.where(CodeIssue.severity == arguments["severity"])
            result = await session.execute(query)
            issues = [
                {"file": i.file_path, "severity": i.severity, "title": i.title, "line": i.line_start}
                for i in result.scalars().all()
            ]
        return [TextContent(type="text", text=json.dumps(issues))]

    elif name == "get_health_score":
        from app.models.database import AsyncSessionLocal, AnalysisRun
        from sqlalchemy import select, desc
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AnalysisRun)
                .where(AnalysisRun.repo_full_name == arguments["repo"])
                .order_by(desc(AnalysisRun.created_at))
                .limit(1)
            )
            run = result.scalar_one_or_none()
        score = run.health_score if run else None
        return [TextContent(type="text", text=json.dumps({"health_score": score, "repo": arguments["repo"]}))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())

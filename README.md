# 🛡️ NexusOps — Autonomous DevOps Intelligence Platform

> **The only open-source autonomous AI platform that reads your GitHub codebase, detects bugs + security vulnerabilities, generates complete fixes, posts PR reviews, and tracks code health — all powered by free tools.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-green.svg)](https://python.org)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Free%20Tier-orange.svg)](https://console.groq.com)
[![GitHub API](https://img.shields.io/badge/GitHub-Free%20API-black.svg)](https://github.com)

---

## 🎯 What NexusOps Does

NexusOps is an **autonomous AI code intelligence platform** that:

1. **Connects to any GitHub repo** via free GitHub token
2. **Scans all source files** — Python, JS, TS, Go, Java, Rust, C++ (regex + AST + Bandit)
3. **Runs AI deep review** — sends code to Groq LLM for logic bugs, security flaws, performance issues
4. **Generates complete fixes** — rewrites vulnerable code sections with corrections + inline comments
5. **Posts automatic PR reviews** — triggered by GitHub webhooks on every PR open/push
6. **Computes code health score** (0–100) based on severity-weighted issue density
7. **Exposes MCP server** — Claude Desktop can query code health via Model Context Protocol
8. **Tracks history** — all runs, issues, and health trends stored in SQLite

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       NexusOps System                           │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────────────────────────┐  │
│  │   Frontend   │    │            FastAPI Backend            │  │
│  │  (Next.js)   │◄──►│                                      │  │
│  │              │    │  ┌────────────────────────────────┐  │  │
│  │ • Repo Panel │    │  │   LangGraph Analysis Pipeline  │  │  │
│  │ • Issues     │    │  │                                │  │  │
│  │ • AI Fixes   │    │  │  Scanner → Reviewer → Reporter │  │  │
│  │ • Health     │    │  └────────────────────────────────┘  │  │
│  │ • History    │    │                                      │  │
│  └──────────────┘    │  ┌──────────────────────────────┐   │  │
│                       │  │       GitHub Integration      │   │  │
│                       │  │  • PyGithub (FREE API)       │   │  │
│                       │  │  • Webhook handler           │   │  │
│                       │  │  • PR review comments        │   │  │
│                       │  │  • Auto-fix PR creation      │   │  │
│                       │  └──────────────────────────────┘  │  │
│                       │                                      │  │
│                       │  ┌──────────┐  ┌────────────────┐   │  │
│                       │  │ SQLite   │  │  Bandit / AST  │   │  │
│                       │  │(FREE DB) │  │  (FREE static) │   │  │
│                       │  └──────────┘  └────────────────┘   │  │
│                       └──────────────────────────────────────┘  │
│                                   │                             │
│                            GitHub Webhooks                      │
└─────────────────────────────────────────────────────────────────┘

LLM: Groq (FREE) — code analysis + fix generation
Code Scan: AST (built-in) + Bandit (FREE) + regex patterns
Data: GitHub REST API (FREE — 5,000 req/hour)
DB: SQLite (local, FREE)
```

---

## 💰 Cost: $0

| Component | Tool | Cost |
|-----------|------|------|
| LLM (code review + fix gen) | Groq API free tier | **$0** |
| GitHub integration | GitHub REST API + token | **$0** |
| Security scanning | Bandit (open source) | **$0** |
| AST analysis | Python ast module (built-in) | **$0** |
| Database | SQLite | **$0** |
| Agent orchestration | LangGraph (open source) | **$0** |
| **Total** | | **$0/month** |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+, Node.js 20+
- Free Groq key → [console.groq.com](https://console.groq.com)
- GitHub Personal Access Token → [github.com/settings/tokens](https://github.com/settings/tokens) (scopes: `repo`, `read:user`)

### 1. Setup backend
```bash
git clone https://github.com/YOUR_USERNAME/NexusOps
cd NexusOps/backend

python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt
cp .env.example .env
# Edit .env → add GROQ_API_KEY and GITHUB_TOKEN
```

### 2. Run backend
```bash
uvicorn app.main:app --reload --port 8000
```
Open → http://localhost:8000/docs

### 3. Setup & run frontend
```bash
cd ../frontend
npm install
npm run dev
```
Open → http://localhost:3000

### 4. Use NexusOps
1. **Add a repo** — type `owner/repo` in the left panel and press Enter
2. **Click "Run Full Analysis"** — the LangGraph pipeline runs:
   - Scanner Agent: fetches files from GitHub, runs AST + Bandit + regex
   - Reviewer Agent: sends code to Groq for deep AI review
   - Reporter Agent: computes health score + recommendations
3. **View Issues tab** — see all bugs/security issues sorted by severity
4. **Click "AI Fix Critical"** — Groq rewrites the problematic code sections
5. **View Health tab** — code health score, severity charts, file-level breakdown

---

## 🔌 GitHub Webhook Setup

Automatically trigger analysis on every PR:

1. Go to your repo → Settings → Webhooks → Add webhook
2. Payload URL: `http://YOUR_SERVER:8000/api/v1/webhook/github`
3. Content type: `application/json`
4. Secret: use your `GITHUB_WEBHOOK_SECRET` from .env
5. Events: ✅ Push, ✅ Pull requests

NexusOps will auto-review every PR and post a comment with found issues.

---

## 📁 Project Structure

```
NexusOps/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── scanner_agent.py     # GitHub file fetch + static analysis
│   │   │   ├── reviewer_agent.py    # Groq LLM deep code review
│   │   │   ├── fixer_agent.py       # AI code fix generation
│   │   │   ├── reporter_agent.py    # Health score + recommendations
│   │   │   └── orchestrator.py      # LangGraph StateGraph pipeline
│   │   ├── core/
│   │   │   ├── github_client.py     # PyGithub wrapper (async-friendly)
│   │   │   └── code_parser.py       # AST + Bandit + regex analysis
│   │   ├── api/routes/
│   │   │   ├── repos.py             # Repo registration/management
│   │   │   ├── analysis.py          # Pipeline trigger + history
│   │   │   ├── health_report.py     # Health score endpoints
│   │   │   ├── fixes.py             # AI fix generation
│   │   │   └── webhook.py           # GitHub webhook handler
│   │   ├── mcp/server.py            # MCP server (Claude Desktop integration)
│   │   ├── models/                  # SQLAlchemy + Pydantic
│   │   └── main.py                  # FastAPI app
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                     # Next.js App Router
│       ├── components/              # RepoPanel, IssuesList, HealthDashboard, RunHistory
│       ├── store/nexusStore.ts      # Zustand global state
│       └── lib/                     # API client + TypeScript types
├── docker-compose.yml
└── README.md
```

---

## 🔌 MCP Integration (Claude Desktop)

```json
{
  "mcpServers": {
    "nexusops": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "./backend"
    }
  }
}
```

Tools: `analyze_repo`, `get_code_issues`, `get_health_score`

---

## 📊 Resume Bullets (copy-paste ready)

- Architected an **autonomous AI DevOps intelligence platform** integrating LangGraph multi-agent pipeline (Scanner → Reviewer → Reporter), Groq LLM for deep code review + automated fix generation, PyGithub for real-time PR analysis, and Bandit/AST for static security scanning — enabling zero-human code quality enforcement across GitHub repositories
- Implemented **GitHub webhook-driven autonomous PR reviews** that automatically scan changed code on every commit, post structured AI review comments with severity-classified issues (critical/high/medium/low), and generate corrected code patches with inline fix explanations
- Built a **code health scoring system** with severity-weighted metrics (0–100 scale), interactive React dashboard with recharts visualizations, MCP server for Claude Desktop integration, and SQLite persistence for historical trend tracking — deployed with Docker Compose for one-command setup

---

## 📄 License

MIT

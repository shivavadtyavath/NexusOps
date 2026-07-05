"""
NexusOps — FastAPI application entry point.
Autonomous DevOps Intelligence Platform — 100% free stack.
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.routes.analysis import router as analysis_router
from app.api.routes.fixes import router as fixes_router
from app.api.routes.health_report import router as health_router
from app.api.routes.repos import router as repos_router
from app.api.routes.webhook import router as webhook_router
from app.config import settings
from app.models.database import create_tables
from app.utils.logger import configure_logging, get_logger

configure_logging(debug=settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("nexusops.startup", version=settings.app_version)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    await create_tables()
    logger.info("nexusops.db_ready")
    yield
    logger.info("nexusops.shutdown")


app = FastAPI(
    title="NexusOps",
    description=(
        "Autonomous DevOps Intelligence Platform — "
        "AI-powered code review, bug detection, security scanning, "
        "and automated fix generation. 100% free stack: Groq + GitHub API + LangGraph."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Routers
app.include_router(repos_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(fixes_router, prefix="/api/v1")
app.include_router(webhook_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "NexusOps", "version": settings.app_version, "status": "running"}


@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "stack": "100% free — Groq + GitHub API + LangGraph + SQLite",
    }

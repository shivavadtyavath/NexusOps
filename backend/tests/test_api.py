"""Tests for NexusOps API routes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "NexusOps"


def test_list_repos_empty(client):
    response = client.get("/api/v1/repos/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_analysis_status(client):
    response = client.get("/api/v1/analysis/status")
    assert response.status_code == 200
    assert "status" in response.json()


def test_list_issues_empty(client):
    response = client.get("/api/v1/analysis/issues")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

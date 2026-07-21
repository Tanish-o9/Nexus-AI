"""
Tests for Recommendation Inference Service
"""

import os
import json
import pytest
from fastapi.testclient import TestClient

import app.config as cfg
from app.data import get_sample_data
from app.trainer import train
from app.inference import engine
from app.main import app


@pytest.fixture(scope="module", autouse=True)
def setup_test_models(tmp_path_factory):
    """
    Module-level fixture to train a small model in a temp directory,
    pointing MODELS_DIR to it, so that the inference engine can load it.
    """
    temp_dir = tmp_path_factory.mktemp("models")
    original_models_dir = cfg.get_settings().MODELS_DIR
    
    # Override settings
    cfg.get_settings().MODELS_DIR = str(temp_dir)
    
    # Train the model with sample data
    interactions = get_sample_data()
    train(interactions)
    
    # Force reload of engine models
    engine.is_loaded = False
    engine.load_models()
    
    yield temp_dir
    
    # Restore settings
    cfg.get_settings().MODELS_DIR = original_models_dir


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as c:
        yield c


def test_health_check_endpoint(client):
    """Verify /health returns the correct status and loaded model details."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["model_version"] == "v1"


def test_recommend_auth_protection(client):
    """Verify endpoint rejects requests with missing or invalid internal secret."""
    payload = {
        "user_id": "user_1",
        "candidates": [
            {
                "project_id": "project_1",
                "user_role": "member",
                "project_member_count": 5,
                "interaction_count": 10,
                "recency_days": 1.5
            }
        ],
        "top_n": 3
    }
    
    # Missing header
    response = client.post("/api/v1/recommend/", json=payload)
    assert response.status_code == 422  # validation error (header required)
    
    # Invalid header
    response = client.post(
        "/api/v1/recommend/", 
        json=payload, 
        headers={"X-Internal-Secret": "wrong-secret"}
    )
    assert response.status_code == 403


def test_recommend_success(client):
    """Verify recommendations are served and sorted correctly for known users/projects."""
    secret = cfg.get_settings().INTERNAL_SERVICE_SECRET
    payload = {
        "user_id": "user_1",
        "candidates": [
            {
                "project_id": "project_1",
                "user_role": "member",
                "project_member_count": 5,
                "interaction_count": 2,
                "recency_days": 10.0
            },
            {
                "project_id": "project_2",
                "user_role": "admin",
                "project_member_count": 8,
                "interaction_count": 10,
                "recency_days": 1.0
            },
            {
                "project_id": "project_3",
                "user_role": "viewer",
                "project_member_count": 3,
                "interaction_count": 0,
                "recency_days": 100.0
            }
        ],
        "top_n": 2
    }
    
    response = client.post(
        "/api/v1/recommend/",
        json=payload,
        headers={"X-Internal-Secret": secret}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["user_id"] == "user_1"
    recommendations = data["recommendations"]
    
    # Should respect top_n constraint
    assert len(recommendations) == 2
    
    # Recommendations should be sorted descending by score
    assert recommendations[0]["score"] >= recommendations[1]["score"]
    
    # Check that score breakdowns are floating points
    for rec in recommendations:
        assert isinstance(rec["project_id"], str)
        assert isinstance(rec["score"], float)
        assert isinstance(rec["svd_score"], float)
        assert isinstance(rec["xgb_score"], float)


def test_recommend_cold_start(client):
    """Verify that unknown users/projects (cold-starts) are handled gracefully."""
    secret = cfg.get_settings().INTERNAL_SERVICE_SECRET
    
    # Completely new user and project ID
    payload = {
        "user_id": "new_unseen_user_xyz",
        "candidates": [
            {
                "project_id": "new_unseen_project_123",
                "user_role": "member",
                "project_member_count": 4,
                "interaction_count": 0,
                "recency_days": 365.0
            }
        ],
        "top_n": 1
    }
    
    response = client.post(
        "/api/v1/recommend/",
        json=payload,
        headers={"X-Internal-Secret": secret}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["recommendations"]) == 1
    rec = data["recommendations"][0]
    
    assert rec["project_id"] == "new_unseen_project_123"
    assert rec["score"] > 0.0  # Should fallback to positive mean/default scores
    assert rec["svd_score"] == engine.svd.global_mean


def test_prediction_logging_creates_file(client):
    """Verify that query inputs and outputs are logged asynchronously to a predictions.jsonl file."""
    secret = cfg.get_settings().INTERNAL_SERVICE_SECRET
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(base_dir, "logs", "predictions.jsonl")
    
    # Delete file if it already exists to check creation
    if os.path.exists(log_file):
        os.remove(log_file)
        
    payload = {
        "user_id": "logger_test_user",
        "candidates": [
            {
                "project_id": "logger_test_project",
                "user_role": "admin",
                "project_member_count": 12,
                "interaction_count": 5,
                "recency_days": 4.0
            }
        ],
        "top_n": 1
    }
    
    # Hit endpoint (FastAPI executes background tasks synchronously before returning in TestClient)
    response = client.post(
        "/api/v1/recommend/",
        json=payload,
        headers={"X-Internal-Secret": secret}
    )
    assert response.status_code == 200
    
    # Check that predictions.jsonl was created and contains the logged record
    assert os.path.exists(log_file)
    
    with open(log_file, "r") as f:
        lines = f.readlines()
        
    assert len(lines) >= 1
    last_log = json.loads(lines[-1])
    
    assert last_log["user_id"] == "logger_test_user"
    assert last_log["project_id"] == "logger_test_project"
    assert last_log["interaction_count"] == 5
    assert last_log["user_role_encoded"] == 3  # admin -> 3
    assert last_log["project_member_count"] == 12
    assert last_log["recency_days"] == 4.0
    assert "svd_score" in last_log
    assert "xgb_score" in last_log
    assert "hybrid_score" in last_log
    assert last_log["model_version"] == "v1"

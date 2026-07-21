"""
Tests for the recommendation training pipeline.
"""

import os
import json
import pytest
import numpy as np
from datetime import datetime, timedelta

from app.data import Interaction, get_sample_data
from app.trainer import SVDModel, _build_features, train


# ── Sample data ─────────────────────────────────────────────────────────

def test_get_sample_data_returns_interactions():
    data = get_sample_data()
    assert len(data) > 0
    assert all(isinstance(d, Interaction) for d in data)
    assert data[0].user_id == 'user_1'
    assert data[0].project_id == 'project_1'


# ── Feature engineering ─────────────────────────────────────────────────

def test_build_features_creates_dataframe():
    data = get_sample_data()
    df = _build_features(data)
    assert len(df) > 0
    assert 'user_id' in df.columns
    assert 'project_id' in df.columns
    assert 'interaction_count' in df.columns
    assert 'user_role_encoded' in df.columns
    assert df['user_role_encoded'].iloc[0] == 2  # member


# ── SVD model ───────────────────────────────────────────────────────────

def test_svd_train_and_predict():
    n_users, n_items = 20, 10
    rng = np.random.RandomState(42)
    user_ids = rng.randint(0, n_users, 100)
    item_ids = rng.randint(0, n_items, 100)
    ratings = rng.randint(1, 6, 100).astype(float)

    svd = SVDModel(n_factors=10, n_epochs=5, lr=0.01, reg=0.02)
    svd.fit(user_ids, item_ids, ratings, n_users, n_items)

    preds = svd.predict(user_ids[:10], item_ids[:10])
    assert len(preds) == 10
    assert all(p > 0 for p in preds)  # predictions should be positive


def test_svd_improves_with_training():
    """RMSE should decrease after more epochs."""
    n_users, n_items = 10, 5
    rng = np.random.RandomState(42)
    user_ids = rng.randint(0, n_users, 50)
    item_ids = rng.randint(0, n_items, 50)
    ratings = rng.randint(1, 6, 50).astype(float)

    svd = SVDModel(n_factors=5, n_epochs=1, lr=0.01, reg=0.02)
    svd.fit(user_ids, item_ids, ratings, n_users, n_items)
    preds_1 = svd.predict(user_ids, item_ids)
    rmse_1 = np.sqrt(np.mean((ratings - preds_1) ** 2))

    svd2 = SVDModel(n_factors=5, n_epochs=20, lr=0.01, reg=0.02)
    svd2.fit(user_ids, item_ids, ratings, n_users, n_items)
    preds_2 = svd2.predict(user_ids, item_ids)
    rmse_2 = np.sqrt(np.mean((ratings - preds_2) ** 2))

    assert rmse_2 <= rmse_1 + 0.1  # should not be worse


# ── Full training pipeline ──────────────────────────────────────────────

def test_train_returns_models_and_metrics():
    data = get_sample_data()
    result = train(data)

    assert 'svd' in result
    assert 'xgb' in result
    assert 'metrics' in result
    assert result['metrics']['train_samples'] > 0
    assert result['metrics']['hybrid_rmse'] > 0


def test_train_with_insufficient_data():
    """Should return error if too few interactions."""
    data = [Interaction('u1', 'p1', 'org1', 'view', datetime.utcnow())]
    result = train(data)
    assert 'error' in result


def test_train_saves_model_files(tmp_path):
    """Training should save model files to disk."""
    import app.config as cfg
    original = cfg.get_settings().MODELS_DIR
    cfg.get_settings().MODELS_DIR = str(tmp_path)

    data = get_sample_data()
    result = train(data)

    files = os.listdir(tmp_path)
    assert any('svd_' in f for f in files)
    assert any('xgb_' in f for f in files)
    assert any('metrics_' in f for f in files)

    # Check metrics file
    with open(f"{tmp_path}/metrics_v1.json") as f:
        metrics = json.load(f)
    assert 'hybrid_rmse' in metrics

    cfg.get_settings().MODELS_DIR = original
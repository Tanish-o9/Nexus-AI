"""
Training Pipeline
=================
Trains a hybrid recommendation model using:
1. Collaborative filtering (SVD) — "users who liked X also liked Y"
2. XGBoost — uses features like user_role, member_count to improve predictions

Why two models?
  - SVD is great for sparse data (finds latent patterns)
  - XGBoost handles cold-start better (uses user/project features)
  - Final prediction = 0.6 * SVD_score + 0.4 * XGBoost_score

Training flow:
  1. Fetch/load interaction data
  2. Build user-item interaction matrix
  3. Train SVD on the matrix
  4. Train XGBoost on user/project features
  5. Evaluate on test set
  6. Save model + metadata to disk
"""

import json
import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import ndcg_score

from app.config import get_settings
from app.data import Interaction


# ── Feature engineering ─────────────────────────────────────────────────

def _build_features(interactions: list[Interaction]) -> pd.DataFrame:
    """
    Convert interactions list into a feature DataFrame for training.

    Each row = one (user, project) pair with:
      - user_id, project_id (encoded as ints)
      - interaction_count (how many times user interacted with project)
      - user_role_encoded (admin=3, member=2, viewer=1)
      - project_member_count (how many people in the project)
      - recency_days (days since last interaction)
    """
    rows = []
    for ix in interactions:
        rows.append({
            'user_id': ix.user_id,
            'project_id': ix.project_id,
            'interaction_type': ix.interaction_type,
            'user_role': ix.user_role,
            'project_member_count': ix.project_member_count,
            'recency_days': (datetime.utcnow() - ix.timestamp).days,
        })

    df = pd.DataFrame(rows)

    # Count interactions per (user, project) pair
    counts = df.groupby(['user_id', 'project_id']).size().reset_index(name='interaction_count')

    # Take the latest role/recency per pair
    latest = df.groupby(['user_id', 'project_id']).agg({
        'user_role': 'first',
        'project_member_count': 'first',
        'recency_days': 'min',
    }).reset_index()

    result = counts.merge(latest, on=['user_id', 'project_id'])

    # Encode categoricals
    role_map = {'admin': 3, 'member': 2, 'viewer': 1}
    result['user_role_encoded'] = result['user_role'].map(role_map).fillna(1)

    return result


def _build_user_item_matrix(df: pd.DataFrame) -> tuple:
    """Build user-item matrix for SVD training."""
    user_enc = LabelEncoder()
    item_enc = LabelEncoder()

    user_ids = user_enc.fit_transform(df['user_id'])
    item_ids = item_enc.fit_transform(df['project_id'])

    return user_ids, item_ids, user_enc, item_enc


# ── SVD (collaborative filtering) ──────────────────────────────────────

class SVDModel:
    """
    Simple SVD for collaborative filtering.
    Learns latent factors for users and items.

    Prediction: r_ui = global_mean + user_bias + item_bias + user_factors @ item_factors
    """
    def __init__(self, n_factors: int = 50, n_epochs: int = 20,
                 lr: float = 0.005, reg: float = 0.02):
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr = lr
        self.reg = reg
        self.global_mean = 0.0
        self.user_bias = None
        self.item_bias = None
        self.user_factors = None
        self.item_factors = None

    def fit(self, user_ids: np.ndarray, item_ids: np.ndarray,
            ratings: np.ndarray, n_users: int, n_items: int):
        """Train SVD using SGD."""
        rng = np.random.RandomState(42)
        self.global_mean = np.mean(ratings)

        self.user_bias = np.zeros(n_users)
        self.item_bias = np.zeros(n_items)
        self.user_factors = 0.1 * rng.randn(n_users, self.n_factors)
        self.item_factors = 0.1 * rng.randn(n_items, self.n_factors)

        for epoch in range(self.n_epochs):
            for u, i, r in zip(user_ids, item_ids, ratings):
                pred = self._predict_one(u, i)
                err = r - pred

                # Update biases
                self.user_bias[u] += self.lr * (err - self.reg * self.user_bias[u])
                self.item_bias[i] += self.lr * (err - self.reg * self.item_bias[i])

                # Update factors
                u_f = self.user_factors[u]
                i_f = self.item_factors[i]
                self.user_factors[u] += self.lr * (err * i_f - self.reg * u_f)
                self.item_factors[i] += self.lr * (err * u_f - self.reg * i_f)

    def _predict_one(self, user_id: int, item_id: int) -> float:
        return (self.global_mean + self.user_bias[user_id]
                + self.item_bias[item_id]
                + np.dot(self.user_factors[user_id], self.item_factors[item_id]))

    def predict(self, user_ids: np.ndarray, item_ids: np.ndarray) -> np.ndarray:
        preds = []
        for u, i in zip(user_ids, item_ids):
            preds.append(self._predict_one(u, i))
        return np.array(preds)


# ── Main training pipeline ─────────────────────────────────────────────

def train(interactions: list[Interaction]) -> dict[str, Any]:
    """
    Full training pipeline.

    Args:
        interactions: List of user-project interactions

    Returns:
        Dict with trained models, encoders, and metrics
    """
    settings = get_settings()
    df = _build_features(interactions)

    if len(df) < 10:
        return {'error': 'Not enough data to train'}

    # Create rating (target): interaction_count (could be weighted by type)
    df['rating'] = df['interaction_count'].clip(0, 10)

    # Train/test split
    train_df, test_df = train_test_split(
        df, test_size=settings.TEST_SPLIT_RATIO,
        random_state=settings.RANDOM_SEED
    )

    # ── SVD ──
    train_u, train_i, user_enc, item_enc = _build_user_item_matrix(train_df)
    test_u = user_enc.transform(test_df['user_id'])
    test_i = item_enc.transform(test_df['project_id'])

    n_users = len(user_enc.classes_)
    n_items = len(item_enc.classes_)

    svd = SVDModel(
        n_factors=settings.N_FACTORS,
        n_epochs=settings.N_EPOCHS,
        lr=settings.LR_ALL,
        reg=settings.REG_ALL,
    )
    svd.fit(train_u, train_i, train_df['rating'].values, n_users, n_items)

    # Evaluate SVD
    svd_train_preds = svd.predict(train_u, train_i)
    svd_test_preds = svd.predict(test_u, test_i)
    svd_train_rmse = np.sqrt(np.mean((train_df['rating'] - svd_train_preds) ** 2))
    svd_test_rmse = np.sqrt(np.mean((test_df['rating'] - svd_test_preds) ** 2))

    # ── XGBoost ──
    feature_cols = ['interaction_count', 'user_role_encoded',
                    'project_member_count', 'recency_days']

    X_train = train_df[feature_cols].values
    X_test = test_df[feature_cols].values
    y_train = train_df['rating'].values
    y_test = test_df['rating'].values

    import xgboost as xgb
    xgb_model = xgb.XGBRegressor(
        max_depth=settings.XGB_MAX_DEPTH,
        n_estimators=settings.XGB_N_ESTIMATORS,
        learning_rate=settings.XGB_LEARNING_RATE,
        random_state=settings.RANDOM_SEED,
        n_jobs=-1,
    )
    xgb_model.fit(X_train, y_train)

    xgb_train_preds = xgb_model.predict(X_train)
    xgb_test_preds = xgb_model.predict(X_test)
    xgb_train_rmse = np.sqrt(np.mean((y_train - xgb_train_preds) ** 2))
    xgb_test_rmse = np.sqrt(np.mean((y_test - xgb_test_preds) ** 2))

    # ── Hybrid (SVD + XGBoost) ──
    hybrid_train = 0.6 * svd_train_preds + 0.4 * xgb_train_preds
    hybrid_test = 0.6 * svd_test_preds + 0.4 * xgb_test_preds
    hybrid_rmse = np.sqrt(np.mean((y_test - hybrid_test) ** 2))

    metrics = {
        'svd_train_rmse': round(float(svd_train_rmse), 4),
        'svd_test_rmse': round(float(svd_test_rmse), 4),
        'xgb_train_rmse': round(float(xgb_train_rmse), 4),
        'xgb_test_rmse': round(float(xgb_test_rmse), 4),
        'hybrid_rmse': round(float(hybrid_rmse), 4),
        'train_samples': len(train_df),
        'test_samples': len(test_df),
        'n_users': n_users,
        'n_items': n_items,
    }

    # ── Save models ──
    import joblib
    model_dir = settings.MODELS_DIR
    os.makedirs(model_dir, exist_ok=True)
    version = settings.MODEL_VERSION

    joblib.dump(svd, f"{model_dir}/svd_{version}.joblib")
    joblib.dump(xgb_model, f"{model_dir}/xgb_{version}.joblib")
    joblib.dump(user_enc, f"{model_dir}/user_enc_{version}.joblib")
    joblib.dump(item_enc, f"{model_dir}/item_enc_{version}.joblib")
    joblib.dump(feature_cols, f"{model_dir}/features_{version}.joblib")

    # ── Save baseline feature distributions for drift monitoring ──
    baseline_stats = {}
    for col in feature_cols:
        series = train_df[col].values.astype(float)
        quantiles = np.linspace(0, 1, 11)
        bin_edges = np.percentile(series, quantiles * 100)
        bin_edges = np.unique(bin_edges).tolist()
        
        if len(bin_edges) < 2:
            bin_edges = [float(series.min()) - 0.001, float(series.max()) + 0.001]
            
        bin_edges[0] -= 1e-5
        bin_edges[-1] += 1e-5
        
        counts, _ = np.histogram(series, bins=bin_edges)
        total = sum(counts)
        expected_pct = (counts / total).tolist() if total > 0 else []
        
        baseline_stats[col] = {
            "bin_edges": bin_edges,
            "expected_pct": expected_pct,
            "mean": float(np.mean(series)),
            "std": float(np.std(series))
        }

    with open(f"{model_dir}/baseline_{version}.json", 'w') as f:
        json.dump(baseline_stats, f, indent=2)

    with open(f"{model_dir}/metrics_{version}.json", 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"Models saved to {model_dir}/")
    print(f"Metrics: {json.dumps(metrics, indent=2)}")

    return {
        'svd': svd,
        'xgb': xgb_model,
        'user_enc': user_enc,
        'item_enc': item_enc,
        'feature_cols': feature_cols,
        'metrics': metrics,
    }
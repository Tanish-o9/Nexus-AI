"""
Model Monitoring & Drift Detection Service
==========================================
Computes Population Stability Index (PSI) to detect feature drift
between live production logs and training baseline distributions.
Provides dashboard metrics and trigger alerts.
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, List
import numpy as np
import pandas as pd

from app.config import get_settings


def calculate_psi(
    actual: np.ndarray, expected_pct: List[float], bin_edges: List[float]
) -> float:
    """
    Computes the Population Stability Index (PSI) between actual and expected distributions.
    
    Formula: PSI = sum((Actual_i - Expected_i) * ln(Actual_i / Expected_i))
    
    Interpretations:
      - PSI < 0.1: No significant change/drift.
      - 0.1 <= PSI < 0.2: Moderate change/drift.
      - PSI >= 0.2: Significant change/drift.
    """
    # Clean NaN values
    actual = actual[~np.isnan(actual)]
    if len(actual) == 0:
        return 0.0

    # Calculate actual counts in baseline bin segments
    counts, _ = np.histogram(actual, bins=bin_edges)
    actual_pct = counts / len(actual)

    psi_val = 0.0
    epsilon = 1e-4  # Avoid division by zero or log(0)

    for a, e in zip(actual_pct, expected_pct):
        # Accumulate PSI formula terms
        psi_val += (a - e) * np.log((a + epsilon) / (e + epsilon))

    return float(psi_val)


def trigger_alert(feature_name: str, psi_val: float) -> None:
    """
    Simulates sending an alert notification (e.g. to Slack, PagerDuty, or system log)
    when feature drift crosses critical thresholds.
    """
    alert_msg = (
        f"[CRITICAL ALERT] Feature Drift Detected! "
        f"Feature: '{feature_name}', PSI Score: {psi_val:.4f} (Threshold: >= 0.2000). "
        f"Action Recommended: Trigger recommendation model retraining pipeline."
    )
    print(alert_msg)
    # Here one would dispatch HTTP POST payload to Slack webhook, AWS SNS, etc.


def evaluate_drift(limit: int = 1000) -> Dict[str, Any]:
    """
    Loads prediction log file and evaluates drift statistics against baseline expectations.
    """
    settings = get_settings()
    version = settings.MODEL_VERSION
    model_dir = settings.MODELS_DIR

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(base_dir, "logs", "predictions.jsonl")
    baseline_file = os.path.join(model_dir, f"baseline_{version}.json")

    # Guard check for missing logs
    if not os.path.exists(log_file):
        return {
            "status": "insufficient_data",
            "message": "Prediction log file 'predictions.jsonl' does not exist yet.",
            "metrics": {}
        }

    # Guard check for missing baseline
    if not os.path.exists(baseline_file):
        return {
            "status": "missing_baseline",
            "message": f"Baseline configuration for version '{version}' not found.",
            "metrics": {}
        }

    # Load baseline json stats
    with open(baseline_file, "r") as f:
        baseline_stats = json.load(f)

    # Read last N lines from predictions log
    with open(log_file, "r") as f:
        lines = f.readlines()[-limit:]

    if len(lines) < 20:
        return {
            "status": "insufficient_data",
            "message": f"Too few logged queries ({len(lines)}/20 minimum) to compute statistically valid drift.",
            "metrics": {}
        }

    # Parse JSON Lines logs into Pandas DataFrame
    records = []
    for line in lines:
        try:
            records.append(json.loads(line.strip()))
        except Exception:
            continue

    df = pd.DataFrame(records)
    
    drift_metrics = {}
    any_critical_drift = False

    for col, baseline in baseline_stats.items():
        if col not in df.columns:
            continue

        actual_values = df[col].values.astype(float)
        bin_edges = baseline["bin_edges"]
        expected_pct = baseline["expected_pct"]

        # Calculate PSI
        psi = calculate_psi(actual_values, expected_pct, bin_edges)

        # Check drift severity
        if psi >= 0.2:
            status_str = "significant_drift"
            any_critical_drift = True
            trigger_alert(col, psi)
        elif psi >= 0.1:
            status_str = "moderate_drift"
        else:
            status_str = "stable"

        drift_metrics[col] = {
            "psi": round(psi, 4),
            "status": status_str,
            "mean_baseline": round(baseline["mean"], 4),
            "mean_live": round(float(np.mean(actual_values)), 4),
            "std_baseline": round(baseline["std"], 4),
            "std_live": round(float(np.std(actual_values)), 4)
        }

    return {
        "status": "drift_detected" if any_critical_drift else "stable",
        "timestamp": datetime.utcnow().isoformat(),
        "model_version": version,
        "sample_size": len(df),
        "metrics": drift_metrics
    }


def get_dashboard_data(limit: int = 1000) -> Dict[str, Any]:
    """
    Aggregates statistical indicators for monitoring visual dashboards.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(base_dir, "logs", "predictions.jsonl")

    if not os.path.exists(log_file):
        return {
            "status": "empty",
            "total_predictions": 0,
            "recent_predictions": [],
            "score_distributions": {},
            "predictions_by_day": {}
        }

    records = []
    with open(log_file, "r") as f:
        for line in f:
            try:
                records.append(json.loads(line.strip()))
            except Exception:
                continue

    if not records:
        return {
            "status": "empty",
            "total_predictions": 0,
            "recent_predictions": [],
            "score_distributions": {},
            "predictions_by_day": {}
        }

    # Process metrics using Pandas
    df = pd.DataFrame(records)
    total_preds = len(df)
    
    # Slice recent predictions
    recent = df.tail(20)[["timestamp", "user_id", "project_id", "hybrid_score"]].to_dict(orient="records")

    # Score breakdown averages
    score_distributions = {
        "avg_hybrid_score": round(float(df["hybrid_score"].mean()), 4),
        "avg_svd_score": round(float(df["svd_score"].mean()), 4),
        "avg_xgb_score": round(float(df["xgb_score"].mean()), 4),
        "max_score": round(float(df["hybrid_score"].max()), 4),
        "min_score": round(float(df["hybrid_score"].min()), 4),
    }

    # Group count volume by date (timestamp is ISO format)
    df["date"] = df["timestamp"].apply(lambda x: x.split("T")[0])
    volume_by_day = df.groupby("date").size().to_dict()

    return {
        "status": "active",
        "total_predictions": total_preds,
        "recent_predictions": recent,
        "score_distributions": score_distributions,
        "predictions_by_day": volume_by_day
    }

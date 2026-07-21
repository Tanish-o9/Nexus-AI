"""
Asynchronous Prediction Logging for Drift Monitoring
"""

import os
import json
from datetime import datetime
import anyio

from app.config import get_settings


async def log_predictions(
    user_id: str,
    candidates: list[dict],
    model_version: str
) -> None:
    """
    Asynchronously write prediction logs to a JSON Lines file.
    
    Logs are written to `ml-service/logs/predictions.jsonl`.
    Each line represents a user-project pair prediction with input features and output scores.
    """
    settings = get_settings()
    
    # Place log folder under ml-service root or settings config path if any
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs")
    
    # Ensure logs directory exists
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "predictions.jsonl")
    
    now_str = datetime.utcnow().isoformat()
    lines = []
    
    for cand in candidates:
        log_entry = {
            "timestamp": now_str,
            "model_version": model_version,
            "user_id": user_id,
            "project_id": cand["project_id"],
            "interaction_count": cand["interaction_count"],
            "user_role_encoded": cand["user_role_encoded"],
            "project_member_count": cand["project_member_count"],
            "recency_days": cand["recency_days"],
            "svd_score": float(cand["svd_score"]),
            "xgb_score": float(cand["xgb_score"]),
            "hybrid_score": float(cand["score"])
        }
        lines.append(json.dumps(log_entry) + "\n")
        
    if not lines:
        return
        
    # Use anyio to append logs asynchronously to avoid blocking the event loop
    async with await anyio.open_file(log_file, mode="a", encoding="utf-8") as f:
        await f.writelines(lines)

"""
Recommendation Inference Engine
==============================
Loads trained models (SVD & XGBoost), builds features,
ranks project candidates, and handles cold-starts.
"""

import os
from typing import Any, Dict, List, Optional
import joblib
import numpy as np

from app.config import get_settings
from app.trainer import SVDModel
from app.schemas import RecommendationCandidate


class RecommendationEngine:
    """
    Manages loading the saved models/encoders and running
    hybrid (SVD + XGBoost) predictions on project candidates.
    """
    def __init__(self):
        self.svd: Optional[SVDModel] = None
        self.xgb: Any = None
        self.user_enc: Any = None
        self.item_enc: Any = None
        self.features: Optional[List[str]] = None
        self.version: Optional[str] = None
        self.is_loaded: bool = False

    def load_models(self) -> None:
        """
        Load versioned model files and encoders from the model directory.
        """
        settings = get_settings()
        version = settings.MODEL_VERSION
        model_dir = settings.MODELS_DIR

        svd_path = os.path.join(model_dir, f"svd_{version}.joblib")
        xgb_path = os.path.join(model_dir, f"xgb_{version}.joblib")
        user_enc_path = os.path.join(model_dir, f"user_enc_{version}.joblib")
        item_enc_path = os.path.join(model_dir, f"item_enc_{version}.joblib")
        features_path = os.path.join(model_dir, f"features_{version}.joblib")

        # Raise exception if critical model files are missing
        if not (os.path.exists(svd_path) and os.path.exists(xgb_path) and 
                os.path.exists(user_enc_path) and os.path.exists(item_enc_path)):
            raise FileNotFoundError(
                f"Trained model files not found for version '{version}' in directory '{model_dir}'. "
                f"Please run the training pipeline first."
            )

        self.svd = joblib.load(svd_path)
        self.xgb = joblib.load(xgb_path)
        self.user_enc = joblib.load(user_enc_path)
        self.item_enc = joblib.load(item_enc_path)
        
        if os.path.exists(features_path):
            self.features = joblib.load(features_path)
        else:
            self.features = ['interaction_count', 'user_role_encoded', 'project_member_count', 'recency_days']

        self.version = version
        self.is_loaded = True
        print(f"Successfully loaded models version '{version}' for inference.")

    def predict_recommendations(
        self, user_id: str, candidates: List[RecommendationCandidate]
    ) -> List[Dict[str, Any]]:
        """
        Rank candidate projects for a given user using the hybrid model.
        
        Formula: 0.6 * SVD_Score + 0.4 * XGB_Score
        
        Cold-Start Handling:
          - SVD falls back to global mean score (+ bias if partial lookup succeeds).
          - XGBoost works out of the box using input features.
        """
        if not self.is_loaded:
            self.load_models()

        role_map = {'admin': 3, 'member': 2, 'viewer': 1}
        results = []
        
        # Safeguard fallback values from SVD model
        global_mean = getattr(self.svd, "global_mean", 3.0)

        for cand in candidates:
            # ── 1. SVD Collaborative Score (mapped indices) ──
            user_idx = None
            item_idx = None

            if user_id in self.user_enc.classes_:
                user_idx = int(self.user_enc.transform([user_id])[0])
            if cand.project_id in self.item_enc.classes_:
                item_idx = int(self.item_enc.transform([cand.project_id])[0])

            if user_idx is not None and item_idx is not None:
                # Both known: predict normally
                svd_score = float(self.svd.predict(np.array([user_idx]), np.array([item_idx]))[0])
            else:
                # Cold start: partial fallback
                if user_idx is not None and getattr(self.svd, "user_bias", None) is not None:
                    svd_score = float(global_mean + self.svd.user_bias[user_idx])
                elif item_idx is not None and getattr(self.svd, "item_bias", None) is not None:
                    svd_score = float(global_mean + self.svd.item_bias[item_idx])
                else:
                    svd_score = float(global_mean)

            # ── 2. XGBoost Feature-Based Score ──
            role_encoded = role_map.get(cand.user_role.lower(), 1)
            
            # XGBoost features: ['interaction_count', 'user_role_encoded', 'project_member_count', 'recency_days']
            feature_vector = np.array([[
                float(cand.interaction_count),
                float(role_encoded),
                float(cand.project_member_count),
                float(cand.recency_days)
            ]])

            xgb_score = float(self.xgb.predict(feature_vector)[0])

            # ── 3. Combine to Hybrid Score ──
            hybrid_score = 0.6 * svd_score + 0.4 * xgb_score

            results.append({
                "project_id": cand.project_id,
                "score": round(hybrid_score, 4),
                "svd_score": round(svd_score, 4),
                "xgb_score": round(xgb_score, 4),
                "interaction_count": cand.interaction_count,
                "user_role_encoded": role_encoded,
                "project_member_count": cand.project_member_count,
                "recency_days": cand.recency_days
            })

        return results


# Global singleton instance
engine = RecommendationEngine()

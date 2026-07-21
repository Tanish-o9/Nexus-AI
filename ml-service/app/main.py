"""
FastAPI Entry Point for Nexus ML Recommendation Service
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, HTTPException, status, BackgroundTasks

from app.config import get_settings
from app.inference import engine
from app.schemas import RecommendationRequest, RecommendationResponse, RecommendationItem
from app.logging_utils import log_predictions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load models and encoders at startup.
    Failure to load does not crash the service, allowing it to boot and report unhealthy.
    """
    try:
        engine.load_models()
    except Exception as e:
        print(f"Warning: Could not load recommendation models on startup: {e}")
        print("Inference calls will attempt to load the model on-demand.")
    yield


app = FastAPI(
    title="Nexus PM - ML Recommendation Service",
    description="Microservice providing project recommendations for users.",
    version="1.0.0",
    lifespan=lifespan
)


# ── Prometheus Instrumentation ───────────────────────────────────────────
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except ImportError:
    pass


async def verify_internal_secret(
    x_internal_secret: str = Header(..., alias="X-Internal-Secret", description="Internal service auth secret token")
) -> str:
    """
    Enforces authorization using a shared internal secret key.
    """
    settings = get_settings()
    if x_internal_secret != settings.INTERNAL_SERVICE_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Invalid internal service secret token."
        )
    return x_internal_secret


@app.get("/health")
async def health_check():
    """
    Basic health check indicating model loading state.
    """
    return {
        "status": "healthy" if engine.is_loaded else "degraded",
        "model_loaded": engine.is_loaded,
        "model_version": engine.version or "none"
    }


@app.post(
    "/api/v1/recommend/",
    response_model=RecommendationResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def recommend_projects(
    request: RecommendationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generates recommended projects for a user out of a list of candidates.
    Runs SVD + XGBoost predictions and combines them dynamically.
    Logs predictions asynchronously in the background.
    """
    try:
        # Predict scores (handles cold-starts internally)
        scored_candidates = engine.predict_recommendations(request.user_id, request.candidates)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model service currently unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )

    # Sort candidates by hybrid score descending
    sorted_candidates = sorted(scored_candidates, key=lambda x: x["score"], reverse=True)

    # Extract top N recommendations
    top_candidates = sorted_candidates[:request.top_n]

    # Map to schema response
    recommendations = [
        RecommendationItem(
            project_id=cand["project_id"],
            score=cand["score"],
            svd_score=cand["svd_score"],
            xgb_score=cand["xgb_score"]
        )
        for cand in top_candidates
    ]

    # Enqueue background task to log predictions (input features + outputs)
    background_tasks.add_task(
        log_predictions,
        user_id=request.user_id,
        candidates=scored_candidates,  # Log all candidates to capture full feature space
        model_version=engine.version or "unknown"
    )

    return RecommendationResponse(
        user_id=request.user_id,
        recommendations=recommendations
    )


@app.get(
    "/api/v1/monitoring/drift",
    dependencies=[Depends(verify_internal_secret)]
)
async def get_drift_evaluation(limit: int = 1000):
    """
    Evaluates Population Stability Index (PSI) drift metrics for all features.
    """
    from app.monitoring import evaluate_drift
    return evaluate_drift(limit=limit)


@app.get(
    "/api/v1/monitoring/dashboard",
    dependencies=[Depends(verify_internal_secret)]
)
async def get_monitoring_dashboard(limit: int = 1000):
    """
    Returns prediction volumes, date distributions, and overall scores for dashboards.
    """
    from app.monitoring import get_dashboard_data
    return get_dashboard_data(limit=limit)

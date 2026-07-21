from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    APP_NAME: str = 'nexus-ml-service'
    DEBUG: bool = False

    # Internal auth
    INTERNAL_SERVICE_SECRET: str = 'change-me-in-prod'

    # Backend API (to fetch user/project data for training)
    BACKEND_URL: str = 'http://localhost:8000'

    # Model storage
    MODELS_DIR: str = 'models'
    MODEL_VERSION: str = 'v1'

    # Training
    MIN_INTERACTIONS_PER_USER: int = 3
    TEST_SPLIT_RATIO: float = 0.2
    RANDOM_SEED: int = 42

    # Collaborative filtering
    N_FACTORS: int = 50
    N_EPOCHS: int = 20
    LR_ALL: float = 0.005
    REG_ALL: float = 0.02

    # XGBoost
    XGB_MAX_DEPTH: int = 6
    XGB_N_ESTIMATORS: int = 100
    XGB_LEARNING_RATE: float = 0.1


@lru_cache
def get_settings() -> Settings:
    return Settings()
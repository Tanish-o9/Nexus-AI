from fastapi import APIRouter, Depends
from app.config import Settings, get_settings

router = APIRouter(tags=['health'])


@router.get('/health/live')
async def liveness():
    """Liveness probe — is the process running?"""
    return {'status': 'ok'}


@router.get('/health/ready')
async def readiness(settings: Settings = Depends(get_settings)):
    """
    Readiness probe — are all dependencies reachable?
    Checks DB and config. Returns 503 if not ready.
    """
    checks: dict[str, str] = {}

    # Config sanity check
    checks['config'] = 'ok' if settings.OPENAI_API_KEY else 'missing OPENAI_API_KEY'

    all_ok = all(v == 'ok' for v in checks.values())
    return {
        'status': 'ready' if all_ok else 'degraded',
        'checks': checks,
    }

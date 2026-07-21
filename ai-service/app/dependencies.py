from fastapi import Header, HTTPException, status, Depends
from .config import Settings, get_settings


def verify_internal_secret(
    x_internal_secret: str = Header(..., alias='X-Internal-Secret'),
    settings: Settings = Depends(get_settings),
) -> None:
    """
    Dependency for endpoints only callable by the Django backend.
    Raises 403 if the shared secret doesn't match.
    """
    if x_internal_secret != settings.INTERNAL_SERVICE_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid internal secret.',
        )


def get_config(settings: Settings = Depends(get_settings)) -> Settings:
    return settings

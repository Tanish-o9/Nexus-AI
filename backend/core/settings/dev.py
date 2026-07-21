from .base import *
from decouple import config

DEBUG = True

ALLOWED_HOSTS = ['*']

_USE_SQLITE = config('USE_SQLITE', default='false').lower() == 'true'

if _USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('POSTGRES_DB', default='nexus_dev'),
            'USER': config('POSTGRES_USER', default='nexus'),
            'PASSWORD': config('POSTGRES_PASSWORD', default='nexus'),
            'HOST': config('POSTGRES_HOST', default='localhost'),
            'PORT': config('POSTGRES_PORT', default='5432'),
        }
    }

# Use Redis if available; fall back to LocMemCache so local dev and tests
# work without a running Redis instance.
_REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
_USE_REDIS = config('USE_REDIS_CACHE', default='false').lower() == 'true'

if _USE_REDIS:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _REDIS_URL,
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
        }
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [_REDIS_URL]},
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }

# Never return HTTP 500 when the cache backend is unavailable — fail open.
import sys
RATELIMIT_ENABLE = 'pytest' not in sys.modules
RATELIMIT_FAIL_OPEN = True
SILENCED_SYSTEM_CHECKS = ['django_ratelimit.E003']

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

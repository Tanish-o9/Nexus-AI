from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import health_router, chat_router, documents_router, ai_module_router, agents_router, knowledge_graph_router, github_ai_router, executive_dashboard_router, integrations_router, saas_router, ai_pos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f'[{settings.APP_NAME}] starting up — model: {settings.OPENAI_MODEL}')
    from app.memory.database import create_tables
    await create_tables()
    # Create HNSW vector index + GIN full-text index for document chunks
    from app.memory.database import AsyncSessionFactory
    from app.services.vector_store import create_hnsw_index
    from app.services.hybrid_search import create_fts_index
    async with AsyncSessionFactory() as session:
        await create_hnsw_index(session)
        await create_fts_index(session)
    yield
    print(f'[{settings.APP_NAME}] shutting down')


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title='Nexus AI Service',
        description='EMAOS multi-agent execution engine for Nexus PM',
        version='1.0.0',
        docs_url='/docs' if settings.DEBUG else None,   # Hide docs in prod
        redoc_url='/redoc' if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Only the Django backend should call this service — not the browser directly.
    # In prod, lock this down to the backend's internal hostname.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['http://localhost:8000'],
        allow_methods=['POST', 'GET'],
        allow_headers=['*'],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(documents_router)
    app.include_router(ai_module_router)
    app.include_router(agents_router)
    app.include_router(knowledge_graph_router)
    app.include_router(github_ai_router)
    app.include_router(executive_dashboard_router)
    app.include_router(integrations_router)
    app.include_router(saas_router)
    app.include_router(ai_pos_router)

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={'error': 'internal_server_error', 'detail': str(exc)},
        )

    # ── Prometheus Instrumentation ───────────────────────────────────────────
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app)
    except ImportError:
        pass

    return app


app = create_app()
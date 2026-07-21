# 🔒 Environment Configuration & Secrets Management Strategy

This document establishes the architecture for managing environmental variables and sensitive credentials in **Nexus PM** across local development, staging, and production environments.

---

## 🗺️ Environment Architecture & Injection Flow

Secrets must never be committed to git. Instead, Nexus PM utilizes a multi-level delegation strategy:

```mermaid
graph LR
    EnvFile[.env (Local gitignored)] -->|Injected via docker-compose| Containers[Docker Containers]
    KMS[AWS Secrets Manager / Vault] -->|Prod Orchestration| ECS[ECS / EC2 Runtime Environment]
```

1.  **Local Development**: Environment variables are defined in local, gitignored `.env` files in each service directory. The root `docker-compose.yml` mounts these values directly into the container processes.
2.  **Production (AWS/Docker)**: Secrets are injected directly into task definitions using **AWS Secrets Manager** or **HashiCorp Vault**, avoiding the existence of `.env` files on disk.

---

## 🔍 Variable Classifications & Reference Guide

### 🎨 Frontend (`frontend/.env.example`)
Variables prefixed with `NEXT_PUBLIC_` are bundled into the client build and accessible to the browser.
*   **`PORT`**: Client development server port (default `3000`).
*   **`NEXT_PUBLIC_API_URL`**: HTTP API entrypoint of the Django REST backend.
*   **`NEXT_PUBLIC_AI_SERVICE_URL`**: HTTP entrypoint of the FastAPI AI Engine.
*   **`NEXT_PUBLIC_SOCKET_URL`**: WebSockets gateway for processing real-time notifications.

### 🔌 Backend (`backend/.env.example`)
*   **`DJANGO_SECRET_KEY`**: Cryptographic key used by Django to sign cookies, sessions, and password resets.
*   **`DJANGO_ALLOWED_HOSTS`**: Host/domain filter preventing HTTP Host Header attacks.
*   **`CORS_ALLOWED_ORIGINS`**: CORS whitelist preventing unauthorized origins from making cross-site API requests.
*   **`DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT`**: PostgreSQL database link details.
*   **`REDIS_URL`**: Redis instance link details (used for session caching, Celery queues, and Channels events).
*   **`JWT_SECRET_KEY`**: Specific secret used to sign and verify JSON Web Tokens (JWT).
*   **`AI_SERVICE_URL`**: FastAPI microservice container routing URL.

### 🤖 AI Service (`ai-service/.env.example`)
*   **`OPENAI_API_KEY`**: OpenAI API authentication token for executing models.
*   **`VECTOR_DB_URL`**: Target DB connection string for the `pgvector` store.
*   **`LANGCHAIN_TRACING_V2`**: Boolean controlling telemetry exporting to LangSmith.
*   **`LANGCHAIN_API_KEY`**: API key for LangSmith developer telemetry logs.

### 📊 ML Service (`ml-service/.env.example`)
*   **`DB_URL`**: Dedicated DB connection URL for importing user task behavior datasets.
*   **`MODEL_REGISTRY_PATH`**: Filesystem destination directory for trained, serialized model packages (e.g., joblib/ONNX files).
*   **`DRIFT_THRESHOLD`**: Acceptable performance margin before signaling model retrain alerts.

---

## 🛡️ Production Secret Guardrails
*   **Rule 1**: Never copy actual secrets into any `.env.example` file.
*   **Rule 2**: Add `.env` to all `.gitignore` configurations.
*   **Rule 3**: Set up pre-commit scanning hooks (e.g., `git-secrets` or `trufflehog`) to automatically block commits that contain high-entropy keys.

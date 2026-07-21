# 🌌 Nexus PM — Enterprise AI Project Management SaaS

Welcome to **Nexus PM**, an enterprise-grade AI-powered project management SaaS platform. Nexus PM fuses a high-performance modern web product shell with the **EMAOS (Executive Multi-Agent Orchestration System)** execution engine.

---

## 📂 Monorepo Folder Responsibility Statements

This repository is structured as a service-oriented monorepo. Below is the responsibility statement for each top-level directory:

### 🎨 [frontend/](file:///c:/Users/tanis/OneDrive/Desktop/nexus/frontend/)
Responsible for client-facing user interfaces, layout, application state management, real-time client-side event listeners, and API request handling. It provides a highly responsive UI with a premium visual design language (dark mode, glassmorphism, fluid micro-interactions).
*   **Tech Stack**: Next.js 14+ (App Router), React 18, TypeScript, Tailwind CSS, Redux Toolkit, React Query, shadcn/ui, Framer Motion.

### 🔌 [backend/](file:///c:/Users/tanis/OneDrive/Desktop/nexus/backend/)
Responsible for core enterprise platform operations, business rules enforcement, tenant/organization management, project/task lifecycle models, token-based authentication, role-based access control (RBAC), and transactional integrity. It serves as the primary system of record and the orchestration bridge between the UI and AI microservices.
*   **Tech Stack**: Django 5.x, Django REST Framework (DRF), SimpleJWT, Django Channels (Socket.IO bridge), PostgreSQL, Redis.

### 🤖 [ai-service/](file:///c:/Users/tanis/OneDrive/Desktop/nexus/ai-service/)
Responsible for cognitive pipelines, large language model (LLM) orchestration, graph-based agent topologies, tool execution environments, conversational memory persistence, and streaming token responses. It executes the EMAOS workflow to autonomously plan, execute, and verify project management tasks.
*   **Tech Stack**: FastAPI, LangChain, LangGraph, Pydantic, pgvector.

### 📊 [ml-service/](file:///c:/Users/tanis/OneDrive/Desktop/nexus/ml-service/)
Responsible for offline predictive training pipelines, active recommendation engines (suggesting tasks, workloads, and scheduling), inference endpoints, and feature monitoring/concept drift tracking. It processes telemetry and historical data to optimize team workflows.
*   **Tech Stack**: Python, Scikit-learn, XGBoost, PyTorch.

### 🐳 [docker/](file:///c:/Users/tanis/OneDrive/Desktop/nexus/docker/)
Responsible for dev and production container packaging, cross-service network orchestration, data volume persistence, reverse proxy routing, and service dependency health check ordering.
*   **Tech Stack**: Docker, Docker Compose, Nginx, PostgreSQL, Redis, Elasticsearch, Prometheus, Grafana.

### 📖 [docs/](file:///c:/Users/tanis/OneDrive/Desktop/nexus/docs/)
Responsible for maintaining project specifications, design proposals, API documentation schemas, repository conventions, environment guidelines, database diagrams, and developer onboarding materials.

### 🧪 [tests/](file:///c:/Users/tanis/OneDrive/Desktop/nexus/tests/)
Responsible for global end-to-end (E2E) UI testing, cross-service API integration suites, and system-level validation routines mapping the core customer journey.

---

## 🛠️ Project Structure At-a-Glance

```
nexus/
├── frontend/             # Next.js App Router UI
├── backend/              # Django REST API (Enterprise Engine)
├── ai-service/           # FastAPI Agentic LLM Pipelines (LangGraph)
├── ml-service/           # Recommendation & Predictor Services
├── docker/               # Container Orchestration Configurations
├── docs/                 # System Architecture & API Docs
├── tests/                # E2E & Integration Test Suites
├── .gitignore            # Monorepo Git Ignore Config
├── .env.example          # Root Configuration Template
└── docker-compose.yml    # Development Environment Orchestrator
```

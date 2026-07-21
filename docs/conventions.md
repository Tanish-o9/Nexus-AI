# 📐 Repository Standards & Naming Conventions

This document establishes the official casing, formatting, architectural layering, and syntax conventions for **Nexus PM** across all frontend, backend, AI, and ML services.

---

## 🏷️ Casing & Naming Standards

| Element | Format / Case | Example | Scope / Notes |
| :--- | :--- | :--- | :--- |
| **Frontend Folders** | `kebab-case` | `features/auth-modal` | All Next.js page paths, components, features |
| **Backend Folders** | `snake_case` | `apps/audit_logs` | Python packages and Django directories |
| **React Components**| `PascalCase` | `DashboardHeader.tsx` | UI layouts and reusable components |
| **React Hooks** | `camelCase` | `useAuthToken.ts` | React custom hooks |
| **Database Tables** | `snake_case` | `projects_project_task` | Format: `<app_name>_<model_name>` (plural) |
| **API Endpoints** | `kebab-case` | `/api/v1/user-profiles/` | Lowercase nouns, plural resources |
| **Environment Vars**| `UPPER_SNAKE` | `JWT_SECRET_KEY` | Global runtime secrets and credentials |
| **Docker Services** | `kebab-case` | `ai-service` | Services listed in `docker-compose.yml` |

---

## 🗂️ Service Layer Standards

### 1. Frontend Layering (Next.js Feature-First)
Files must be grouped by domain/feature under `features/<feature-name>/`:
*   `components/`: UI components (e.g. `LoginForm.tsx`).
*   `hooks/`: Feature-specific hooks (e.g. `useLogin.ts`).
*   `services/`: Query services and API wrappers (e.g. `authService.ts`).
*   `store/`: Redux slices (if needed for state).

### 2. Backend Layering (Django REST Framework)
To prevent model-view bloat, follow the Service Layer pattern:
*   **Models**: Simple data schemas and database constraints. No heavy business logic.
*   **Services**: Core business logic modules (`services.py`).
*   **Serializers**: Handle request input parsing, validation, and serialization.
*   **Views / ViewSets**: HTTP request entrypoints. Outsource processing logic entirely to services.

---

## 🚨 Linting & Code Quality Commands

All code pushed to code-review must pass lint checks:

*   **Frontend**: `npm run lint` / `npm run format`
*   **Python (Backend & AI)**: `ruff check .` / `black --check .`

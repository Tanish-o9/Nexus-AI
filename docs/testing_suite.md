# Nexus PM — Test Suite & Verification Guide

This document details the complete testing strategy and execution instructions for all layers of the Nexus PM system. It spans the Django backend, FastAPI AI core, FastAPI ML engine, frontend component tests, and E2E browser tests.

---

## 1. Test Architecture Overview

```
nexus/
├── backend/
│   └── tests/                # Django unit & API view tests
├── ai-service/
│   └── tests/                # Pytest unit & async LangGraph checks
├── ml-service/
│   └── tests/                # Pytest unit, inference & drift checks
├── frontend/
│   └── features/**/__tests__/# Vitest component & hooks tests
└── tests/
    └── e2e/                  # Playwright E2E browser tests
```

---

## 2. Test Execution Commands

### 2.1 Backend Tests (Django)
Runs database integration, serialization, and view logic tests:
```powershell
# Navigate to backend
cd backend
# Run Django test suite
python manage.py test
```

### 2.2 AI Service Tests (FastAPI + Pytest)
Verifies LangGraph agent actions, tool calls, and embedding retrievals:
```powershell
# Navigate to ai-service
cd ai-service
# Run pytest tests
python -m pytest tests/ -v
```

### 2.3 ML Service Tests (FastAPI + Pytest)
Verifies recommendations, SVD fallbacks, and PSI calculations:
```powershell
# Navigate to ml-service
cd ml-service
# Run pytest tests
python -m pytest tests/ -v
```

### 2.4 Frontend Component Tests (Vitest)
Executes component rendering, form validation, state updates, and mock API hooks:
```powershell
# Navigate to frontend
cd frontend
# Run vitest once
npm run test
# Run vitest in interactive watch mode
npm run test:watch
```

### 2.5 End-to-End Tests (Playwright)
Validates the user flow across frontend, backend, and AI engines:
```powershell
# Install Playwright browsers (first-time setup)
npx playwright install
# Run E2E tests headless
npx playwright test
# Run E2E tests with UI browser view
npx playwright test --ui
```

---

## 3. End-to-End Critical Path Spec

The E2E suite defined at [critical-path.spec.ts](file:///c:/Users/tanis/OneDrive/Desktop/nexus/tests/e2e/critical-path.spec.ts) drives a browser to test this workflow:

1. **User Authentication**: Visits `/login`, enters email and password, submits form, and asserts dashboard redirection.
2. **Project Creation**: Opens Projects list, clicks "New Project", inputs metadata, submits, and verifies the project appears in the table.
3. **Task Navigation**: Clicks on the new project to open its workspace.
4. **AI Conversation**: Opens the AI Chat drawer, sends a contextual prompt to the LangGraph executor.
5. **Citations Retrieval**: Asserts the streamed text returns complete and displays the corresponding source index citations (`[1]`).

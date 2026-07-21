import { apiFetch } from '@/services/api-fetch';

export interface AIContext {
  session_id?: string;
  user_id?: string;
  org_id?: string;
  project_id?: string;
}

export const aiApi = {
  chat: (payload: { message: string; context?: AIContext; history?: any[] }) =>
    apiFetch<{ content: string; session_id: string }>('/api/ai/chat/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  taskBreakdown: (payload: { task_description: string; include_estimated_hours?: boolean; format?: string; context?: AIContext }) =>
    apiFetch<any>('/api/ai/task-breakdown/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  sprintPlanning: (payload: { sprint_duration_days?: number; team_capacity_hours?: number; backlog_items?: string[]; focus_area?: string; context?: AIContext }) =>
    apiFetch<any>('/api/ai/sprint-planning/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  projectSummary: (payload: { include_recent_activity?: boolean; focus_areas?: string[]; context?: AIContext }) =>
    apiFetch<any>('/api/ai/project-summary/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  docQA: (payload: { question: string; top_k?: number; use_reranker?: boolean; context?: AIContext }) =>
    apiFetch<any>('/api/ai/doc-qa/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  meetingSummary: (payload: { meeting_notes: string; meeting_type?: string; context?: AIContext }) =>
    apiFetch<any>('/api/ai/meeting-summary/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  deadlinePrediction: (payload: { task_ids?: string[]; include_all_pending?: boolean; assumptions?: string[]; context?: AIContext }) =>
    apiFetch<any>('/api/ai/deadline-prediction/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  riskAnalysis: (payload: { focus_areas?: string[]; include_mitigation?: boolean; context?: AIContext }) =>
    apiFetch<any>('/api/ai/risk-analysis/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  workloadSuggestion: (payload: { team_members?: { name: string; current_load?: number; skills?: string[] }[]; upcoming_tasks?: string[]; consider_skills?: boolean; balance_factor?: number; context?: AIContext }) =>
    apiFetch<any>('/api/ai/workload-suggestion/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
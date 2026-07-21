import { apiFetch } from '@/services/api-fetch';

export type ProjectStatus = 'active' | 'on_hold' | 'completed' | 'archived';
export type ProjectHealth = 'on_track' | 'at_risk' | 'critical';

export interface Project {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  organizationId: string;
  memberCount: number;
  taskCount: number;
  isTemplate: boolean;
  health: ProjectHealth;
  progress: number;
  createdAt: string;
  updatedAt: string;
}

export interface GlobalAnalyticsData {
  project_status: Array<{ name: string; value: number; color: string }>;
  workload: Array<{ member: string; tasks: number }>;
  velocity: Array<{ week: string; completed: number }>;
}

export const globalAnalyticsApi = {
  getAnalytics: () => apiFetch<GlobalAnalyticsData>('/api/projects/analytics/global/'),
};

export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type TaskStatus = 'todo' | 'in_progress' | 'in_review' | 'done';

export interface User {
  id: string;
  username: string;
  email: string;
}

export interface Label {
  id: string;
  name: string;
  color: string;
  projectId: string;
}

export interface KanbanColumn {
  id: string;
  name: string;
  position: number;
  projectId: string;
}

export interface ChecklistItem {
  id: string;
  title: string;
  is_completed: boolean;
  taskId: string;
}

export interface TaskDependency {
  id: string;
  dependsOnId: string;
  dependsOnTitle: string;
}

export interface TaskAttachment {
  id: string;
  file_name: string;
  file_url: string;
  uploadedBy: User;
  createdAt: string;
}

export interface TaskComment {
  id: string;
  author: User;
  content: string;
  createdAt: string;
}

export interface TimeEntry {
  id: string;
  user: User;
  hours: number;
  date: string;
  description: string;
}

export interface GitHubCommitInfo {
  commitSha?: string;
  message?: string;
  pushedBy?: string;
  filesChanged?: string[];
  pushedAt?: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  performanceRating?: 'good' | 'very_good' | 'excellent' | 'needs_work' | null;
  githubCommitInfo?: GitHubCommitInfo;
  projectId: string;
  assigneeId?: string;
  assignees: User[];
  watchers: User[];
  labels: Label[];
  checklistItems: ChecklistItem[];
  dependencies: TaskDependency[];
  comments: TaskComment[];
  timeEntries: TimeEntry[];
  attachments: TaskAttachment[];
  kanbanColumnId?: string;
  dueDate?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectsParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: ProjectStatus | '';
  ordering?: string;
  organizationId?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CreateProjectPayload {
  name: string;
  description: string;
  organizationId: string;
  templateId?: string | null;
  isTemplate?: boolean;
  health?: ProjectHealth;
}

export type ProjectMemberRole =
  | 'owner'
  | 'manager'
  | 'developer'
  | 'frontend'
  | 'backend'
  | 'devops'
  | 'qa'
  | 'designer'
  | 'data'
  | 'security'
  | 'writer'
  | 'viewer';

export interface ProjectMember {
  id: string;
  user: User;
  userId: string;
  role: ProjectMemberRole;
  invitedBy: User | null;
  isActive: boolean;
  joinedAt: string;
}

// ── Activity Log Types ────────────────────────────────────────────────────────

export type ActivityAction =
  | 'created' | 'updated' | 'deleted' | 'status_changed'
  | 'assigned' | 'unassigned' | 'commented' | 'attachment_added'
  | 'member_added' | 'member_removed' | 'member_role_changed';

export interface ActivityLogEntry {
  id: string;
  project: string;
  task: string | null;
  actor: User | null;
  action: ActivityAction;
  field_name: string;
  old_value: string;
  new_value: string;
  description: string;
  createdAt: string;
}

function buildQuery(params: ProjectsParams): string {
  const q = new URLSearchParams();
  if (params.page) q.set('page', String(params.page));
  if (params.pageSize) q.set('page_size', String(params.pageSize));
  if (params.search) q.set('search', params.search);
  if (params.status) q.set('status', params.status);
  if (params.ordering) q.set('ordering', params.ordering);
  if (params.organizationId) q.set('organization_id', params.organizationId);
  return q.toString() ? `?${q.toString()}` : '';
}

export const projectsApi = {
  list: (params: ProjectsParams = {}) =>
    apiFetch<PaginatedResponse<Project>>(`/api/projects/${buildQuery(params)}`),

  get: (id: string) =>
    apiFetch<Project>(`/api/projects/${id}/`),

  create: (payload: CreateProjectPayload) =>
    apiFetch<Project>('/api/projects/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  update: (id: string, payload: Partial<Project> & { templateId?: string | null }) =>
    apiFetch<Project>(`/api/projects/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  delete: (id: string) =>
    apiFetch<void>(`/api/projects/${id}/`, { method: 'DELETE' }),

  // Kanban columns
  listColumns: (projectId: string) =>
    apiFetch<KanbanColumn[]>(`/api/projects/${projectId}/columns/`),

  createColumn: (projectId: string, name: string) =>
    apiFetch<KanbanColumn>(`/api/projects/${projectId}/columns/`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),

  deleteColumn: (projectId: string, columnId: string) =>
    apiFetch<void>(`/api/projects/${projectId}/columns/${columnId}/`, { method: 'DELETE' }),

  // Labels
  listLabels: (projectId: string) =>
    apiFetch<Label[]>(`/api/projects/${projectId}/labels/`),

  createLabel: (projectId: string, payload: { name: string; color: string }) =>
    apiFetch<Label>(`/api/projects/${projectId}/labels/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Tasks CRUD (nested or detail)
  listTasks: (projectId: string) =>
    apiFetch<PaginatedResponse<Task>>(`/api/projects/${projectId}/tasks/`),

  createTask: (projectId: string, payload: any) =>
    apiFetch<Task>(`/api/projects/${projectId}/tasks/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateTask: (projectId: string, taskId: string, payload: any) =>
    apiFetch<Task>(`/api/projects/${projectId}/tasks/${taskId}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteTask: (projectId: string, taskId: string) =>
    apiFetch<void>(`/api/projects/${projectId}/tasks/${taskId}/`, { method: 'DELETE' }),

  rateTask: (projectId: string, taskId: string, rating: string | null) =>
    apiFetch<Task>(`/api/projects/${projectId}/tasks/${taskId}/rate/`, {
      method: 'POST',
      body: JSON.stringify({ rating }),
    }),

  simulatePush: (projectId: string, taskId: string, payload?: { message?: string; files?: string[] }) =>
    apiFetch<Task>(`/api/github/projects/${projectId}/tasks/${taskId}/simulate-push/`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }),

  // Checklist
  createChecklistItem: (projectId: string, taskId: string, title: string) =>
    apiFetch<ChecklistItem>(`/api/projects/${projectId}/tasks/${taskId}/checklist/`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),

  updateChecklistItem: (projectId: string, taskId: string, itemId: string, payload: { is_completed: boolean }) =>
    apiFetch<ChecklistItem>(`/api/projects/${projectId}/tasks/${taskId}/checklist/${itemId}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteChecklistItem: (projectId: string, taskId: string, itemId: string) =>
    apiFetch<void>(`/api/projects/${projectId}/tasks/${taskId}/checklist/${itemId}/`, { method: 'DELETE' }),

  // Comments
  createComment: (projectId: string, taskId: string, content: string) =>
    apiFetch<TaskComment>(`/api/projects/${projectId}/tasks/${taskId}/comments/`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  // Attachments
  createAttachment: (projectId: string, taskId: string, payload: { file_name: string; file_url: string }) =>
    apiFetch<TaskAttachment>(`/api/projects/${projectId}/tasks/${taskId}/attachments/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Time logging
  createTimeEntry: (projectId: string, taskId: string, payload: { hours: number; date: string; description?: string }) =>
    apiFetch<TimeEntry>(`/api/projects/${projectId}/tasks/${taskId}/time/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Dependencies
  createDependency: (projectId: string, taskId: string, dependsOnId: string) =>
    apiFetch<TaskDependency>(`/api/projects/${projectId}/tasks/${taskId}/dependencies/`, {
      method: 'POST',
      body: JSON.stringify({ dependsOnId }),
    }),

  deleteDependency: (projectId: string, taskId: string, dependsOnId: string) =>
    apiFetch<void>(`/api/projects/${projectId}/tasks/${taskId}/dependencies/${dependsOnId}/`, { method: 'DELETE' }),

  // ── Project Members ─────────────────────────────────────────────────────────

  listMembers: (projectId: string) =>
    apiFetch<ProjectMember[]>(`/api/projects/${projectId}/members/`),

  inviteMember: (projectId: string, payload: { userId?: string; email?: string; role: ProjectMemberRole }) =>
    apiFetch<ProjectMember>(`/api/projects/${projectId}/members/invite/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateMember: (projectId: string, memberId: string, payload: { role?: ProjectMemberRole; is_active?: boolean }) =>
    apiFetch<ProjectMember>(`/api/projects/${projectId}/members/${memberId}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  removeMember: (projectId: string, memberId: string) =>
    apiFetch<void>(`/api/projects/${projectId}/members/${memberId}/`, { method: 'DELETE' }),

  // ── Activity Logs ───────────────────────────────────────────────────────────

  listActivity: (projectId: string, limit?: number) =>
    apiFetch<ActivityLogEntry[]>(`/api/projects/${projectId}/activity/${limit ? `?limit=${limit}` : ''}`),

  // ── Milestones ──────────────────────────────────────────────────────────────

  listMilestones: (projectId: string) =>
    apiFetch<Milestone[]>(`/api/projects/${projectId}/milestones/`),

  createMilestone: (projectId: string, payload: { name: string; description?: string; dueDate: string }) =>
    apiFetch<Milestone>(`/api/projects/${projectId}/milestones/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateMilestone: (projectId: string, milestoneId: string, payload: { name?: string; description?: string; dueDate?: string; isCompleted?: boolean }) =>
    apiFetch<Milestone>(`/api/projects/${projectId}/milestones/${milestoneId}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteMilestone: (projectId: string, milestoneId: string) =>
    apiFetch<void>(`/api/projects/${projectId}/milestones/${milestoneId}/`, { method: 'DELETE' }),
};

export interface Milestone {
  id: string;
  name: string;
  description: string;
  dueDate: string;
  isCompleted: boolean;
  createdAt: string;
  project: string;
}

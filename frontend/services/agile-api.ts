import { apiFetch } from '@/services/api-fetch';

export interface Sprint {
  id: string;
  projectId: string;
  name: string;
  goal: string;
  startDate: string;
  endDate: string;
  isActive: boolean;
  isCompleted: boolean;
  taskCount: number;
  totalPoints: number;
  completedPoints: number;
  createdAt: string;
}

export interface SprintBacklogItem {
  id: string;
  sprintId: string;
  taskId: string;
  taskTitle: string;
  taskStatus: string;
  taskAssignee: string;
  storyPoints: number;
}

export interface Analytics {
  totalTasks: number;
  completedTasks: number;
  inProgressTasks: number;
  todoTasks: number;
  completionRate: number;
  byPriority: Record<string, number>;
  byAssignee: { assignee__username: string; count: number; completed: number }[];
  overdueTasks: number;
}

export interface Velocity {
  averageVelocity: number;
  sprints: { sprintId: string; sprintName: string; totalPoints: number; completedPoints: number }[];
}

export interface Burndown {
  labels: string[];
  ideal: number[];
  actual: number[];
  totalPoints: number;
}

export interface WorkloadItem {
  assignee: string;
  activeTasks: number;
  completedTasks: number;
  overdueTasks: number;
  totalPoints: number;
}

export interface DeadlineRisk {
  taskId: string;
  title: string;
  assignee: string;
  dueDate: string;
  daysRemaining: number;
  riskLevel: 'low' | 'medium' | 'high' | 'overdue';
  status: string;
}

export interface SprintReport {
  id: string;
  sprintId: string;
  reportType: string;
  data: Record<string, any>;
  pdfUrl: string;
  excelUrl: string;
  createdAt: string;
}

export const agileApi = {
  // Sprints
  listSprints: (projectId: string) =>
    apiFetch<Sprint[]>(`/api/agile/${projectId}/sprints/`),

  createSprint: (projectId: string, payload: { name: string; goal?: string; startDate: string; endDate: string }) =>
    apiFetch<Sprint>(`/api/agile/${projectId}/sprints/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateSprint: (projectId: string, sprintId: string, action: 'activate' | 'complete') =>
    apiFetch<Sprint>(`/api/agile/${projectId}/sprints/${sprintId}/`, {
      method: 'PATCH',
      body: JSON.stringify({ action }),
    }),

  deleteSprint: (projectId: string, sprintId: string) =>
    apiFetch<void>(`/api/agile/${projectId}/sprints/${sprintId}/`, { method: 'DELETE' }),

  // Backlog
  listBacklog: (projectId: string, sprintId: string) =>
    apiFetch<SprintBacklogItem[]>(`/api/agile/${projectId}/sprints/${sprintId}/backlog/`),

  addToBacklog: (projectId: string, sprintId: string, taskId: string, storyPoints: number) =>
    apiFetch<SprintBacklogItem>(`/api/agile/${projectId}/sprints/${sprintId}/backlog/add/`, {
      method: 'POST',
      body: JSON.stringify({ taskId, storyPoints }),
    }),

  removeFromBacklog: (projectId: string, sprintId: string, taskId: string) =>
    apiFetch<void>(`/api/agile/${projectId}/sprints/${sprintId}/backlog/${taskId}/`, { method: 'DELETE' }),

  // Analytics
  getAnalytics: (projectId: string) =>
    apiFetch<Analytics>(`/api/agile/${projectId}/analytics/`),

  getVelocity: (projectId: string) =>
    apiFetch<Velocity>(`/api/agile/${projectId}/velocity/`),

  getBurndown: (projectId: string, sprintId: string) =>
    apiFetch<Burndown>(`/api/agile/${projectId}/sprints/${sprintId}/burndown/`),

  getWorkload: (projectId: string) =>
    apiFetch<WorkloadItem[]>(`/api/agile/${projectId}/workload/`),

  getDeadlineRisks: (projectId: string) =>
    apiFetch<DeadlineRisk[]>(`/api/agile/${projectId}/deadline-risk/`),

  // Reports
  listReports: (projectId: string) =>
    apiFetch<SprintReport[]>(`/api/agile/${projectId}/reports/`),

  generateReport: (projectId: string, sprintId: string, reportType: string = 'sprint') =>
    apiFetch<SprintReport>(`/api/agile/${projectId}/reports/`, {
      method: 'POST',
      body: JSON.stringify({ sprintId, reportType }),
    }),

  generateWeeklyReport: (projectId: string) =>
    apiFetch<SprintReport>(`/api/agile/${projectId}/reports/weekly/`, { method: 'POST' }),

  generateMonthlyReport: (projectId: string) =>
    apiFetch<SprintReport>(`/api/agile/${projectId}/reports/monthly/`, { method: 'POST' }),

  // Export URLs (use directly in <a> or window.open)
  getExportCsvUrl: (projectId: string, reportId: string) =>
    `/api/agile/${projectId}/reports/${reportId}/csv/`,

  getExportExcelUrl: (projectId: string, reportId: string) =>
    `/api/agile/${projectId}/reports/${reportId}/excel/`,
};
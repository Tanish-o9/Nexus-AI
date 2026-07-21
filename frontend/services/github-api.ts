import { apiFetch } from '@/services/api-fetch';

export interface GitHubRepo {
  id: string;
  project?: string;
  projectId?: string;
  owner: string;
  name: string;
  full_name?: string;
  fullName?: string;
  installation_id?: number | null;
  installationId?: number | null;
  webhook_secret?: string;
  webhookSecret?: string;
  is_active?: boolean;
  isActive?: boolean;
  connected_by?: any;
  connectedBy?: any;
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
}

export interface GitHubCommit {
  id: string;
  repository: string;
  sha: string;
  message: string;
  author_name: string;
  author_email: string;
  branch: string;
  url: string;
  timestamp: string;
}

export interface GitHubPR {
  id: string;
  repository: string;
  pr_number: number;
  title: string;
  body: string;
  state: 'open' | 'closed' | 'merged';
  author: string;
  head_branch: string;
  base_branch: string;
  url: string;
  is_draft: boolean;
  created_at: string;
  updated_at: string;
  merged_at: string | null;
  closed_at: string | null;
}

export interface GitHubBranch {
  id: string;
  repository: string;
  name: string;
  latest_sha: string;
  is_protected: boolean;
  is_default: boolean;
  last_commit_message: string;
  last_commit_timestamp: string | null;
}

export interface CommitTaskMapping {
  id: string;
  commit: GitHubCommit;
  task: { id: string; title: string };
  reference_type: 'manual' | 'auto';
  created_at: string;
}

export interface RepoDashboard {
  repo: GitHubRepo;
  commits: GitHubCommit[];
  pullRequests: GitHubPR[];
  branches: GitHubBranch[];
  taskMappings: CommitTaskMapping[];
}

export const githubApi = {
  // Project-scoped repos
  listProjectRepos: (projectId: string) =>
    apiFetch<GitHubRepo[]>(`/api/github/projects/${projectId}/repos/`),

  connectRepo: (projectId: string, payload: { owner: string; name: string; installationId?: number }) =>
    apiFetch<GitHubRepo>(`/api/github/projects/${projectId}/repos/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getRepoDashboard: (projectId: string, repoId: string) =>
    apiFetch<RepoDashboard>(`/api/github/projects/${projectId}/repos/${repoId}/dashboard/`),

  disconnectRepo: (repoId: string) =>
    apiFetch<void>(`/api/github/repos/${repoId}/`, { method: 'DELETE' }),

  // OAuth
  initOAuth: () =>
    apiFetch<{ authorization_url: string; state: string }>('/api/github/oauth/init/'),

  // Sync
  syncRepo: (repoId: string) =>
    apiFetch<any>(`/api/github/repos/${repoId}/sync/`, { method: 'POST' }),

  // Mappings
  listMappings: (repoId: string) =>
    apiFetch<CommitTaskMapping[]>(`/api/github/repos/${repoId}/mappings/`),

  createMapping: (repoId: string, payload: { commitSha: string; taskId: string }) =>
    apiFetch<CommitTaskMapping>(`/api/github/repos/${repoId}/mappings/manual/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
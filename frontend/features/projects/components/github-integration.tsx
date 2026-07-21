'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { githubApi, GitHubRepo, GitHubCommit, GitHubPR, GitHubBranch, CommitTaskMapping } from '@/services/github-api';
import { projectsApi, Task } from '@/services/projects-api';
import { Plus, Trash2, Loader2, GitBranch, GitCommit, GitPullRequest, Link2, ExternalLink, RefreshCw, CheckCircle2, XCircle, GitFork } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface GitHubIntegrationProps {
  projectId: string;
}

export function GitHubIntegration({ projectId }: GitHubIntegrationProps) {
  const queryClient = useQueryClient();
  const [showConnect, setShowConnect] = useState(false);
  const [owner, setOwner] = useState('');
  const [name, setName] = useState('');
  const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);

  const { data: repos = [], isLoading } = useQuery({
    queryKey: ['github-repos', projectId],
    queryFn: () => githubApi.listProjectRepos(projectId),
  });

  const { data: dashboard, isLoading: loadingDashboard } = useQuery({
    queryKey: ['github-dashboard', projectId, selectedRepoId],
    queryFn: () => githubApi.getRepoDashboard(projectId, selectedRepoId!),
    enabled: !!selectedRepoId,
  });

  const { data: tasksData } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => projectsApi.listTasks(projectId),
  });
  const tasks = tasksData?.results || [];

  const connectMutation = useMutation({
    mutationFn: (payload: { owner: string; name: string }) =>
      githubApi.connectRepo(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['github-repos', projectId] });
      toast.success('Repository connected');
      setShowConnect(false);
      setOwner(''); setName('');
    },
    onError: (err: any) => {
      const msg = typeof err?.message === 'string' ? err.message : typeof err === 'string' ? err : 'Failed to connect repository';
      toast.error(msg);
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: (repoId: string) => githubApi.disconnectRepo(repoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['github-repos', projectId] });
      if (selectedRepoId) setSelectedRepoId(null);
      toast.success('Repository disconnected');
    },
  });

  const syncMutation = useMutation({
    mutationFn: (repoId: string) => githubApi.syncRepo(repoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['github-dashboard', projectId, selectedRepoId] });
      toast.success('Repository synced');
    },
    onError: (err: any) => toast.error(err.message || 'Sync failed'),
  });

  const mapMutation = useMutation({
    mutationFn: ({ repoId, commitSha, taskId }: { repoId: string; commitSha: string; taskId: string }) =>
      githubApi.createMapping(repoId, { commitSha, taskId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['github-dashboard', projectId, selectedRepoId] });
      toast.success('Commit linked to task');
    },
  });

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (!owner.trim() || !name.trim()) return;
    connectMutation.mutate({ owner: owner.trim(), name: name.trim() });
  };

  if (isLoading) {
    return <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-indigo-400" /></div>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
          <GitFork className="h-5 w-5" /> GitHub ({repos.length})
        </h3>
        <Button onClick={() => setShowConnect(!showConnect)} size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
          <Plus className="h-4 w-4 mr-1" /> Connect Repo
        </Button>
      </div>

      {showConnect && (
        <form onSubmit={handleConnect} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input value={owner} onChange={e => setOwner(e.target.value)} placeholder="Owner (user/org)" className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-3 py-2 text-sm outline-none focus:border-indigo-500/50" />
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Repository name" className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-3 py-2 text-sm outline-none focus:border-indigo-500/50" />
          <div className="flex gap-2">
            <Button type="submit" size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white flex-1" disabled={!owner || !name}>
              {connectMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Connect'}
            </Button>
            <Button type="button" size="sm" variant="outline" onClick={() => setShowConnect(false)}>Cancel</Button>
          </div>
        </form>
      )}

      {/* Repo List */}
      <div className="flex flex-col gap-3">
        {repos.map(repo => {
          const repoFullName = repo.fullName || repo.full_name || `${repo.owner}/${repo.name}`;
          const dateStr = repo.createdAt || repo.created_at;
          const formattedDate = dateStr ? new Date(dateStr).toLocaleDateString() : 'Recently';

          return (
            <div
              key={repo.id}
              className={`flex flex-col gap-3 bg-slate-900/40 border rounded-xl p-4 cursor-pointer transition-all ${
                selectedRepoId === repo.id ? 'border-indigo-500/50 bg-indigo-500/5 shadow-lg' : 'border-slate-800 hover:border-slate-700'
              }`}
              onClick={() => setSelectedRepoId(repo.id === selectedRepoId ? null : repo.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                    <GitFork className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-base font-bold text-slate-100 flex items-center gap-2">
                      {repoFullName}
                      <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium">
                        Active
                      </span>
                    </p>
                    <p className="text-xs text-slate-500">Connected {formattedDate}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); syncMutation.mutate(repo.id); }}
                    className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-indigo-400 transition-colors border border-slate-800"
                    title="Sync commits & PRs"
                  >
                    {syncMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); if (window.confirm(`Disconnect ${repoFullName}?`)) disconnectMutation.mutate(repo.id); }}
                    className="p-2 rounded-lg hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-colors border border-slate-800"
                    title="Disconnect repo"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Webhook Info Notice */}
              <div className="bg-slate-950/80 border border-slate-800/80 rounded-lg p-3 text-xs text-slate-300 flex flex-col gap-1 select-text" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-indigo-400 flex items-center gap-1.5">
                    <Link2 className="h-3.5 w-3.5" /> GitHub Webhook Payload URL
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">Secret: {repo.webhookSecret || repo.webhook_secret || 'configured'}</span>
                </div>
                <code className="text-slate-200 bg-slate-900 border border-slate-800 p-1.5 rounded font-mono text-[11px] break-all select-all">
                  {typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}/api/github/webhook/${repo.id}/` : `/api/github/webhook/${repo.id}/`}
                </code>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Paste this Payload URL in your GitHub Repo ➔ <strong>Settings ➔ Webhooks ➔ Add webhook</strong> to trigger automatic task completion on real code pushes!
                </p>
              </div>
            </div>
          );
        })}
        {repos.length === 0 && (
          <p className="text-sm text-slate-500 text-center py-8">No repositories connected. Connect a GitHub repo to track commits and PRs.</p>
        )}
      </div>

      {/* Dashboard */}
      {selectedRepoId && dashboard && (
        <div className="flex flex-col gap-6 mt-4">
          {/* Commits */}
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <GitCommit className="h-3.5 w-3.5" /> Recent Commits
            </h4>
            <div className="flex flex-col gap-2">
              {dashboard.commits.map(commit => (
                <div key={commit.id} className="bg-slate-900/20 border border-slate-800 rounded-lg p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-300 font-mono truncate">{commit.message.split('\n')[0]}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        {commit.sha.slice(0, 8)} · {commit.author_name} · {commit.branch}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {commit.url && (
                        <a href={commit.url} target="_blank" rel="noreferrer" className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-indigo-400">
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </div>
                  {/* Link to task */}
                  <div className="mt-2 flex items-center gap-2">
                    <select
                      onChange={(e) => {
                        if (e.target.value) {
                          mapMutation.mutate({ repoId: selectedRepoId, commitSha: commit.sha, taskId: e.target.value });
                          e.target.value = '';
                        }
                      }}
                      className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-2 py-1 text-[10px] outline-none flex-1"
                      defaultValue=""
                    >
                      <option value="" disabled>Link to task...</option>
                      {tasks.map(t => <option key={t.id} value={t.id}>{t.title.slice(0, 50)}</option>)}
                    </select>
                  </div>
                </div>
              ))}
              {dashboard.commits.length === 0 && <p className="text-xs text-slate-500">No commits yet. Sync the repo or push new commits.</p>}
            </div>
          </div>

          {/* Pull Requests */}
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <GitPullRequest className="h-3.5 w-3.5" /> Open Pull Requests
            </h4>
            <div className="flex flex-col gap-2">
              {dashboard.pullRequests.map(pr => (
                <div key={pr.id} className="bg-slate-900/20 border border-slate-800 rounded-lg p-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {pr.state === 'open' ? <GitPullRequest className="h-4 w-4 text-emerald-400" /> : pr.state === 'merged' ? <GitPullRequest className="h-4 w-4 text-violet-400" /> : <GitPullRequest className="h-4 w-4 text-red-400" />}
                    <div>
                      <p className="text-xs text-slate-300">#{pr.pr_number} {pr.title}</p>
                      <p className="text-[10px] text-slate-500">{pr.author} · {pr.head_branch} → {pr.base_branch}</p>
                    </div>
                  </div>
                  {pr.url && (
                    <a href={pr.url} target="_blank" rel="noreferrer" className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-indigo-400">
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              ))}
              {dashboard.pullRequests.length === 0 && <p className="text-xs text-slate-500">No open pull requests.</p>}
            </div>
          </div>

          {/* Branches */}
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <GitBranch className="h-3.5 w-3.5" /> Branches
            </h4>
            <div className="flex flex-wrap gap-2">
              {dashboard.branches.map(branch => (
                <div key={branch.id} className={`flex items-center gap-1.5 bg-slate-900/30 border rounded-lg px-3 py-1.5 text-xs ${branch.is_default ? 'border-indigo-500/30 text-indigo-300' : 'border-slate-800 text-slate-400'}`}>
                  <GitBranch className="h-3 w-3" />
                  {branch.name}
                  {branch.is_default && <span className="text-[9px] text-indigo-400 font-semibold">default</span>}
                </div>
              ))}
            </div>
          </div>

          {/* Task Mappings */}
          {dashboard.taskMappings.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <Link2 className="h-3.5 w-3.5" /> Commit → Task Links
              </h4>
              <div className="flex flex-col gap-2">
                {dashboard.taskMappings.map(m => (
                  <div key={m.id} className="bg-slate-900/20 border border-slate-800 rounded-lg p-2.5 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-indigo-400">{m.commit.sha.slice(0, 8)}</span>
                      <Link2 className="h-3 w-3 text-slate-500" />
                      <span className="text-slate-300">{m.task.title}</span>
                    </div>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${m.reference_type === 'auto' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-indigo-500/10 text-indigo-400'}`}>
                      {m.reference_type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
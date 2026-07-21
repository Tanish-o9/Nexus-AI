'use client';

import { use, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useProject } from '@/features/projects/hooks/use-project';
import { projectsApi } from '@/services/projects-api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Briefcase, Users, CheckSquare, Calendar, Trash2, Loader2, MessageSquareText, Activity, Flag, GitBranch, BarChart3, Clock, FileText, GitFork, Sparkles } from 'lucide-react';
import { KanbanBoard } from '@/features/projects/components/kanban-board';
import { TaskDetailDialog } from '@/features/projects/components/task-detail-dialog';
import { TeamChat } from '@/features/collaboration/components/team-chat';
import { ActivityFeed } from '@/features/collaboration/components/activity-feed';
import { PresenceList } from '@/features/collaboration/components/presence-list';
import { SprintPlanning } from '@/features/agile/components/sprint-planning';
import { SprintBacklog } from '@/features/agile/components/sprint-backlog';
import { AnalyticsPanel } from '@/features/agile/components/analytics-panel';
import { ReportsPanel } from '@/features/agile/components/reports-panel';
import { ProjectMembers } from '@/features/projects/components/project-members';
import { ActivityTimeline } from '@/features/projects/components/activity-timeline';
import { ProjectMilestones } from '@/features/projects/components/project-milestones';
import { GitHubIntegration } from '@/features/projects/components/github-integration';
import { AIWorkspace } from '@/features/projects/components/ai-workspace';

const STATUS_STYLES: Record<string, string> = {
  active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  on_hold: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  completed: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  archived: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
};

type ViewType = 'overview' | 'kanban' | 'members' | 'activity' | 'milestones' | 'sprints' | 'backlog' | 'analytics' | 'reports' | 'github' | 'ai' | 'collaboration';

export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: project, isLoading, isError } = useProject(id);
  const [view, setView] = useState<ViewType>('overview');
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedSprintId, setSelectedSprintId] = useState<string | null>(null);

  const { mutate: deleteProject, isPending: isDeleting } = useMutation({
    mutationFn: () => projectsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Project deleted successfully');
      router.push('/projects/');
    },
    onError: (err: any) => {
      toast.error(err.message || 'Failed to delete project');
    },
  });

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      deleteProject();
    }
  };

  if (isLoading) {
    return (
      <div className="p-8 flex flex-col gap-6 animate-pulse">
        <div className="h-6 w-32 rounded bg-slate-800" />
        <div className="h-10 w-64 rounded-lg bg-slate-800" />
        <div className="h-4 w-96 rounded bg-slate-800/60" />
        <div className="grid grid-cols-3 gap-4 mt-4">
          {[...Array(3)].map((_, i) => <div key={i} className="h-24 rounded-xl bg-slate-800/40" />)}
        </div>
      </div>
    );
  }

  if (isError || !project) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-400 text-sm">Failed to load project.</p>
        <Link href="/projects/" className="text-indigo-400 hover:text-indigo-300 text-sm mt-2 inline-block">
          ← Back to projects
        </Link>
      </div>
    );
  }

  const tabs: { key: ViewType; label: string; icon: React.ReactNode }[] = [
    { key: 'overview', label: 'Overview', icon: <Briefcase className="h-3.5 w-3.5" /> },
    { key: 'kanban', label: 'Board', icon: <CheckSquare className="h-3.5 w-3.5" /> },
    { key: 'members', label: 'Members', icon: <Users className="h-3.5 w-3.5" /> },
    { key: 'milestones', label: 'Milestones', icon: <Flag className="h-3.5 w-3.5" /> },
    { key: 'sprints', label: 'Sprints', icon: <GitBranch className="h-3.5 w-3.5" /> },
    { key: 'backlog', label: 'Backlog', icon: <Clock className="h-3.5 w-3.5" /> },
    { key: 'analytics', label: 'Analytics', icon: <BarChart3 className="h-3.5 w-3.5" /> },
    { key: 'reports', label: 'Reports', icon: <FileText className="h-3.5 w-3.5" /> },
    { key: 'activity', label: 'Activity', icon: <Activity className="h-3.5 w-3.5" /> },
    { key: 'github', label: 'GitHub', icon: <GitFork className="h-3.5 w-3.5" /> },
    { key: 'ai', label: 'AI', icon: <Sparkles className="h-3.5 w-3.5" /> },
    { key: 'collaboration', label: 'Chat', icon: <MessageSquareText className="h-3.5 w-3.5" /> },
  ];

  return (
    <div className="flex flex-col gap-8 p-8">
      <Link href="/projects/" className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200 transition-colors w-fit">
        <ArrowLeft className="h-4 w-4" /> Back to projects
      </Link>

      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-indigo-500/10 flex items-center justify-center">
            <Briefcase className="h-6 w-6 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-100">{project.name}</h2>
            <p className="text-sm text-slate-400 mt-0.5">{project.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs px-3 py-1 rounded-full border font-medium ${STATUS_STYLES[project.status]}`}>
            {project.status.replace('_', ' ')}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDelete}
            disabled={isDeleting}
            className="border-red-950 bg-red-950/20 text-red-400 hover:bg-red-950 hover:text-red-300 flex items-center gap-1.5 transition-colors"
          >
            {isDeleting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
            Delete
          </Button>
        </div>
      </div>

      {/* 3D Glassmorphic Sub-Navigation Bar - 2 Rows */}
      <div className="glass-card-3d rounded-2xl p-3 grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2 border border-slate-800/80 shadow-[0_15px_35px_-5px_rgba(0,0,0,0.5)]">
        {tabs.map(tab => {
          const isActive = view === tab.key;
          const isAI = tab.key === 'ai';
          const isGitHub = tab.key === 'github';

          return (
            <button
              key={tab.key}
              onClick={() => setView(tab.key)}
              className={`text-xs font-semibold px-3 py-2.5 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 relative ${
                isActive
                  ? 'bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 text-white shadow-lg shadow-indigo-500/30 scale-[1.02] border border-indigo-400/40'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 hover:-translate-y-0.5 border border-slate-800/40'
              }`}
            >
              <span className={isActive ? 'text-white' : isAI ? 'text-indigo-400' : isGitHub ? 'text-purple-400' : 'text-slate-400'}>
                {tab.icon}
              </span>
              <span className="truncate">{tab.label}</span>

              {/* Special badges for AI / GitHub */}
              {isAI && (
                <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 shadow shadow-indigo-400/80 animate-ping absolute top-1 right-1" />
              )}
            </button>
          );
        })}
      </div>

      {view === 'overview' ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetaCard icon={<Users className="h-4 w-4" />} label="Members" value={String(project.memberCount)} />
          <MetaCard icon={<CheckSquare className="h-4 w-4" />} label="Tasks" value={String(project.taskCount)} />
          <MetaCard icon={<Calendar className="h-4 w-4" />} label="Last updated" value={new Date(project.updatedAt).toLocaleDateString()} />
        </div>
      ) : view === 'kanban' ? (
        <KanbanBoard
          projectId={id}
          onSelectTask={(task) => setSelectedTaskId(task.id)}
        />
      ) : view === 'members' ? (
        <ProjectMembers projectId={id} />
      ) : view === 'milestones' ? (
        <ProjectMilestones projectId={id} />
      ) : view === 'sprints' ? (
        <SprintPlanning projectId={id} onSelectSprint={(sid) => { setSelectedSprintId(sid); setView('backlog'); }} />
      ) : view === 'backlog' ? (
        <SprintBacklog projectId={id} sprintId={selectedSprintId || ''} />
      ) : view === 'analytics' ? (
        <AnalyticsPanel projectId={id} />
      ) : view === 'reports' ? (
        <ReportsPanel projectId={id} />
      ) : view === 'activity' ? (
        <ActivityTimeline projectId={id} />
      ) : view === 'github' ? (
        <GitHubIntegration projectId={id} />
      ) : view === 'ai' ? (
        <AIWorkspace projectId={id} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 flex flex-col gap-6">
            <div className="h-[500px]">
              <TeamChat projectId={id} />
            </div>
            <ActivityFeed projectId={id} />
          </div>
          <div>
            <PresenceList projectId={id} />
          </div>
        </div>
      )}

      {selectedTaskId && (
        <TaskDetailDialog
          projectId={id}
          taskId={selectedTaskId}
          onClose={() => setSelectedTaskId(null)}
        />
      )}
    </div>
  );
}

function MetaCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-5 flex items-center gap-4">
      <div className="h-9 w-9 rounded-lg bg-slate-800 flex items-center justify-center text-indigo-400">
        {icon}
      </div>
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-lg font-bold text-slate-100">{value}</p>
      </div>
    </div>
  );
}
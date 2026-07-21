import Link from 'next/link';
import { Briefcase, Users, CheckSquare, Trash2, Loader2 } from 'lucide-react';
import type { Project } from '@/services/projects-api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/services/projects-api';
import { toast } from 'sonner';

const STATUS_STYLES: Record<Project['status'], string> = {
  active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  on_hold: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  completed: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  archived: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
};

export function ProjectCard({ project }: { project: Project }) {
  const queryClient = useQueryClient();

  const { mutate: deleteProject, isPending } = useMutation({
    mutationFn: () => projectsApi.delete(project.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.refetchQueries({ queryKey: ['projects'] });
      toast.success('Project deleted successfully');
    },
    onError: (err: any) => {
      toast.error(err.message || 'Failed to delete project');
    },
  });

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete "${project.name}"?`)) {
      deleteProject();
    }
  };

  return (
    <Link href={`/projects/${project.id}`}>
      <div className="group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/30 p-5 hover:border-indigo-500/30 hover:bg-slate-900/60 transition-all cursor-pointer">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-indigo-500/10 flex items-center justify-center shrink-0">
              <Briefcase className="h-4 w-4 text-indigo-400" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-100 text-sm group-hover:text-indigo-300 transition-colors line-clamp-1">
                {project.name}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{project.description}</p>
            </div>
          </div>
          <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full border font-medium ${STATUS_STYLES[project.status]}`}>
            {project.status.replace('_', ' ')}
          </span>
        </div>

        <div className="flex items-center gap-4 mt-4 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <Users className="h-3 w-3" /> {project.memberCount} members
          </span>
          <span className="flex items-center gap-1">
            <CheckSquare className="h-3 w-3" /> {project.taskCount} tasks
          </span>
          <span className="ml-auto flex items-center gap-2">
            <span>{new Date(project.updatedAt).toLocaleDateString()}</span>
            <button
              onClick={handleDelete}
              disabled={isPending}
              className="p-1 rounded text-red-500/80 hover:bg-red-500/10 hover:text-red-400 transition-all shrink-0"
              title="Delete Project"
            >
              {isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Trash2 className="h-3.5 w-3.5" />
              )}
            </button>
          </span>
        </div>
      </div>
    </Link>
  );
}

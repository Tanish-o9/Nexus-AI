'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agileApi } from '@/services/agile-api';
import { projectsApi } from '@/services/projects-api';
import { Plus, Trash2, ListTodo, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface Props {
  projectId: string;
  sprintId: string;
}

export function SprintBacklog({ projectId, sprintId }: Props) {
  const queryClient = useQueryClient();
  const [taskId, setTaskId] = useState('');
  const [points, setPoints] = useState('1');

  const { data: backlog = [], isLoading } = useQuery({
    queryKey: ['backlog', projectId, sprintId],
    queryFn: () => agileApi.listBacklog(projectId, sprintId),
  });

  const { data: tasks } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => projectsApi.listTasks(projectId).then(r => r.results),
  });

  const addMutation = useMutation({
    mutationFn: () => agileApi.addToBacklog(projectId, sprintId, taskId, parseFloat(points)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backlog', projectId, sprintId] });
      queryClient.invalidateQueries({ queryKey: ['sprints', projectId] });
      setTaskId(''); setPoints('1');
      toast.success('Task added to sprint');
    },
    onError: (e: any) => toast.error(e.message),
  });

  const removeMutation = useMutation({
    mutationFn: (tid: string) => agileApi.removeFromBacklog(projectId, sprintId, tid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backlog', projectId, sprintId] });
      queryClient.invalidateQueries({ queryKey: ['sprints', projectId] });
    },
  });

  const unassignedTasks = tasks?.filter(t => !backlog.some(b => b.taskId === t.id)) ?? [];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800">
        <ListTodo className="h-4 w-4 text-amber-400" />
        <span className="text-sm font-semibold text-slate-200">Sprint Backlog</span>
        <span className="ml-auto text-xs text-slate-500">{backlog.length} items</span>
      </div>

      <div className="p-3 border-b border-slate-800 bg-slate-800/10">
        <div className="flex gap-2">
          <select value={taskId} onChange={(e) => setTaskId(e.target.value)} className="flex-1 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 outline-none">
            <option value="">Select task...</option>
            {unassignedTasks.map(t => <option key={t.id} value={t.id}>{t.title}</option>)}
          </select>
          <input type="number" value={points} onChange={(e) => setPoints(e.target.value)} min="0.1" step="0.5" className="w-16 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 outline-none text-center" />
          <button onClick={() => taskId && addMutation.mutate()} disabled={!taskId || addMutation.isPending} className="px-2 py-1 bg-amber-600 hover:bg-amber-700 disabled:bg-slate-700 rounded text-xs text-white transition-colors">
            <Plus className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="divide-y divide-slate-800/50 max-h-80 overflow-y-auto">
        {isLoading && <div className="py-6 text-center"><Loader2 className="h-5 w-5 animate-spin text-slate-500 mx-auto" /></div>}
        {!isLoading && backlog.length === 0 && <div className="py-6 text-center text-xs text-slate-500">No tasks in this sprint.</div>}
        {backlog.map((item) => (
          <div key={item.id} className="flex items-center gap-3 px-4 py-2.5 hover:bg-slate-800/20">
            <span className={`h-2 w-2 rounded-full shrink-0 ${item.taskStatus === 'done' ? 'bg-emerald-400' : item.taskStatus === 'in_progress' ? 'bg-sky-400' : 'bg-slate-600'}`} />
            <div className="flex-1 min-w-0">
              <p className="text-xs text-slate-200 truncate">{item.taskTitle}</p>
              <p className="text-[10px] text-slate-500">{item.taskAssignee || 'Unassigned'}</p>
            </div>
            <span className="text-xs font-mono text-amber-400">{item.storyPoints}pt</span>
            <button onClick={() => removeMutation.mutate(item.taskId)} className="p-1 rounded text-slate-600 hover:text-red-400 hover:bg-slate-800">
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
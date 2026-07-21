'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agileApi, type Sprint } from '@/services/agile-api';
import { projectsApi } from '@/services/projects-api';
import { Plus, Play, CheckCircle, Trash2, Target, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface Props {
  projectId: string;
  onSelectSprint: (sprintId: string) => void;
}

export function SprintPlanning({ projectId, onSelectSprint }: Props) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [goal, setGoal] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const { data: sprints = [], isLoading } = useQuery({
    queryKey: ['sprints', projectId],
    queryFn: () => agileApi.listSprints(projectId),
  });

  const createMutation = useMutation({
    mutationFn: () => agileApi.createSprint(projectId, { name, goal, startDate, endDate }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sprints', projectId] });
      setShowForm(false); setName(''); setGoal(''); setStartDate(''); setEndDate('');
      toast.success('Sprint created');
    },
    onError: (e: any) => toast.error(e.message),
  });

  const activateMutation = useMutation({
    mutationFn: (sprintId: string) => agileApi.updateSprint(projectId, sprintId, 'activate'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sprints', projectId] });
      toast.success('Sprint activated');
    },
  });

  const completeMutation = useMutation({
    mutationFn: (sprintId: string) => agileApi.updateSprint(projectId, sprintId, 'complete'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sprints', projectId] });
      queryClient.invalidateQueries({ queryKey: ['analytics', projectId] });
      toast.success('Sprint completed');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (sprintId: string) => agileApi.deleteSprint(projectId, sprintId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sprints', projectId] });
      toast.success('Sprint deleted');
    },
  });

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-indigo-400" />
          <span className="text-sm font-semibold text-slate-200">Sprints</span>
        </div>
        <Button onClick={() => setShowForm(!showForm)} size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs h-7">
          <Plus className="h-3.5 w-3.5 mr-1" /> New Sprint
        </Button>
      </div>

      {showForm && (
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }} className="p-4 border-b border-slate-800 bg-slate-800/20 space-y-3">
          <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Sprint name" className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-indigo-500/50" />
          <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="Sprint goal (optional)" className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-indigo-500/50" />
          <div className="flex gap-2">
            <input required type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 outline-none" />
            <input required type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 outline-none" />
          </div>
          <Button type="submit" disabled={createMutation.isPending} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs h-7">
            {createMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Create Sprint'}
          </Button>
        </form>
      )}

      <div className="divide-y divide-slate-800/50 max-h-96 overflow-y-auto">
        {isLoading && <div className="py-6 text-center"><Loader2 className="h-5 w-5 animate-spin text-slate-500 mx-auto" /></div>}
        {!isLoading && sprints.length === 0 && <div className="py-6 text-center text-xs text-slate-500">No sprints yet. Create one!</div>}
        {sprints.map((s) => (
          <div key={s.id} className="px-4 py-3 hover:bg-slate-800/20 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 flex-1 min-w-0 cursor-pointer" onClick={() => onSelectSprint(s.id)}>
                <span className={`h-2 w-2 rounded-full shrink-0 ${s.isActive ? 'bg-emerald-400' : s.isCompleted ? 'bg-indigo-400' : 'bg-slate-600'}`} />
                <span className="text-sm font-medium text-slate-200 truncate">{s.name}</span>
                {s.isActive && <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded-full">Active</span>}
                {s.isCompleted && <span className="text-[10px] bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded-full">Done</span>}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {!s.isActive && !s.isCompleted && (
                  <button onClick={() => activateMutation.mutate(s.id)} className="p-1 rounded text-slate-500 hover:text-emerald-400 hover:bg-slate-800" title="Activate">
                    <Play className="h-3.5 w-3.5" />
                  </button>
                )}
                {s.isActive && (
                  <button onClick={() => completeMutation.mutate(s.id)} className="p-1 rounded text-slate-500 hover:text-indigo-400 hover:bg-slate-800" title="Complete">
                    <CheckCircle className="h-3.5 w-3.5" />
                  </button>
                )}
                {!s.isActive && (
                  <button onClick={() => { if (confirm('Delete this sprint?')) deleteMutation.mutate(s.id); }} className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800" title="Delete">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
            {s.goal && <p className="text-[11px] text-slate-500 mt-1 truncate">{s.goal}</p>}
            <div className="flex gap-3 mt-1.5 text-[10px] text-slate-500">
              <span>{s.startDate} → {s.endDate}</span>
              <span>{s.taskCount} tasks</span>
              <span>{s.completedPoints}/{s.totalPoints} pts</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
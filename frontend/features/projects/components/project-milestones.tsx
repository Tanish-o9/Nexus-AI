'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, Milestone } from '@/services/projects-api';
import { Plus, CheckCircle2, Circle, Trash2, Loader2, Calendar, Flag } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface ProjectMilestonesProps {
  projectId: string;
}

export function ProjectMilestones({ projectId }: ProjectMilestonesProps) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');

  const { data: milestones = [], isLoading } = useQuery({
    queryKey: ['milestones', projectId],
    queryFn: () => projectsApi.listMilestones(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (payload: { name: string; description: string; dueDate: string }) =>
      projectsApi.createMilestone(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestones', projectId] });
      toast.success('Milestone created');
      setShowForm(false);
      setName(''); setDescription(''); setDueDate('');
    },
    onError: (err: any) => toast.error(err.message || 'Failed to create milestone'),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, isCompleted }: { id: string; isCompleted: boolean }) =>
      projectsApi.updateMilestone(projectId, id, { isCompleted }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestones', projectId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.deleteMilestone(projectId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestones', projectId] });
      toast.success('Milestone deleted');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !dueDate) return;
    createMutation.mutate({ name: name.trim(), description: description.trim(), dueDate });
  };

  const sorted = [...milestones].sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime());
  const upcoming = sorted.filter(m => !m.isCompleted);
  const completed = sorted.filter(m => m.isCompleted);

  if (isLoading) {
    return <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-indigo-400" /></div>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-100">Milestones ({milestones.length})</h3>
        <Button onClick={() => setShowForm(!showForm)} size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
          <Plus className="h-4 w-4 mr-1" /> Add Milestone
        </Button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 grid grid-cols-1 sm:grid-cols-4 gap-3">
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Milestone name" className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-3 py-2 text-sm outline-none focus:border-indigo-500/50" />
          <input value={description} onChange={e => setDescription(e.target.value)} placeholder="Description (optional)" className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-3 py-2 text-sm outline-none focus:border-indigo-500/50" />
          <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-3 py-2 text-sm outline-none focus:border-indigo-500/50" />
          <div className="flex gap-2">
            <Button type="submit" size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white flex-1" disabled={!name || !dueDate}>
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create'}
            </Button>
            <Button type="button" size="sm" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </form>
      )}

      {upcoming.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Upcoming</h4>
          <div className="flex flex-col gap-2">
            {upcoming.map(m => (
              <MilestoneCard key={m.id} milestone={m} onToggle={(id, done) => toggleMutation.mutate({ id, isCompleted: done })} onDelete={(id) => deleteMutation.mutate(id)} />
            ))}
          </div>
        </div>
      )}

      {completed.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Completed</h4>
          <div className="flex flex-col gap-2 opacity-60">
            {completed.map(m => (
              <MilestoneCard key={m.id} milestone={m} onToggle={(id, done) => toggleMutation.mutate({ id, isCompleted: done })} onDelete={(id) => deleteMutation.mutate(id)} />
            ))}
          </div>
        </div>
      )}

      {milestones.length === 0 && (
        <p className="text-sm text-slate-500 text-center py-8">No milestones yet. Add key dates to track progress.</p>
      )}
    </div>
  );
}

function MilestoneCard({ milestone, onToggle, onDelete }: { milestone: Milestone; onToggle: (id: string, done: boolean) => void; onDelete: (id: string) => void }) {
  const isOverdue = !milestone.isCompleted && new Date(milestone.dueDate) < new Date();
  return (
    <div className={`flex items-center justify-between bg-slate-900/30 border ${isOverdue ? 'border-red-900/50' : 'border-slate-800'} rounded-xl p-4 hover:border-slate-700 transition-colors`}>
      <div className="flex items-center gap-3">
        <button onClick={() => onToggle(milestone.id, !milestone.isCompleted)} className="text-slate-500 hover:text-indigo-400 transition-colors">
          {milestone.isCompleted ? <CheckCircle2 className="h-5 w-5 text-emerald-400" /> : <Circle className="h-5 w-5" />}
        </button>
        <div>
          <p className={`text-sm font-medium ${milestone.isCompleted ? 'text-slate-500 line-through' : 'text-slate-200'}`}>{milestone.name}</p>
          {milestone.description && <p className="text-xs text-slate-500 mt-0.5">{milestone.description}</p>}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className={`flex items-center gap-1 text-xs ${isOverdue ? 'text-red-400' : 'text-slate-500'}`}>
          <Calendar className="h-3 w-3" />
          {new Date(milestone.dueDate).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
          {isOverdue && <span className="text-red-400 font-semibold">(Overdue)</span>}
        </div>
        <button onClick={() => onDelete(milestone.id)} className="p-1 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors">
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
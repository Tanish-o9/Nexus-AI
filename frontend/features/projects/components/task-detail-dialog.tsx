'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, Task, User, Label, TaskAttachment } from '@/services/projects-api';
import { organizationsApi } from '@/services/organizations-api';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { X, CheckSquare, Plus, Trash2, Calendar, UserPlus, Clock, Paperclip, MessageSquare, Tag, AlertCircle, Loader2, Star, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface TaskDetailDialogProps {
  projectId: string;
  taskId: string;
  onClose: () => void;
}

export function TaskDetailDialog({ projectId, taskId, onClose }: TaskDetailDialogProps) {
  const queryClient = useQueryClient();
  const { activeOrgId } = useSelector((s: RootState) => s.org);

  // Inputs
  const [newChecklistTitle, setNewChecklistTitle] = useState('');
  const [newComment, setNewComment] = useState('');
  const [newHours, setNewHours] = useState('');
  const [newHoursDesc, setNewHoursDesc] = useState('');
  const [attachName, setAttachName] = useState('');
  const [attachUrl, setAttachUrl] = useState('');
  const [newLabelName, setNewLabelName] = useState('');
  const [newLabelColor, setNewLabelColor] = useState('#6366f1');

  // Queries
  const { data: task, isLoading: loadingTask } = useQuery({
    queryKey: ['task', projectId, taskId],
    queryFn: () => projectsApi.listTasks(projectId).then(res => res.results.find(t => t.id === taskId)!),
  });

  const { data: orgMembers = [] } = useQuery({
    queryKey: ['members', activeOrgId],
    queryFn: () => organizationsApi.listMembers(activeOrgId!),
    enabled: !!activeOrgId,
  });

  const { data: labels = [] } = useQuery({
    queryKey: ['labels', projectId],
    queryFn: () => projectsApi.listLabels(projectId),
  });

  // Mutations
  const rateTaskMutation = useMutation({
    mutationFn: (rating: string | null) => projectsApi.rateTask(projectId, taskId, rating),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', projectId, taskId] });
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] });
      toast.success('Task performance rated!');
    },
  });

  const deleteTaskMutation = useMutation({
    mutationFn: () => projectsApi.deleteTask(projectId, taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] });
      toast.success('Task deleted successfully');
      onClose();
    },
    onError: (err: any) => toast.error(err.message || 'Failed to delete task'),
  });

  const updateTaskMutation = useMutation({
    mutationFn: (payload: any) => projectsApi.updateTask(projectId, taskId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', projectId, taskId] });
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] });
      toast.success('Task updated');
    },
  });

  const addChecklistMutation = useMutation({
    mutationFn: (title: string) => projectsApi.createChecklistItem(projectId, taskId, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', projectId, taskId] });
      setNewChecklistTitle('');
    },
  });

  const toggleChecklistMutation = useMutation({
    mutationFn: ({ itemId, isCompleted }: { itemId: string; isCompleted: boolean }) =>
      projectsApi.updateChecklistItem(projectId, taskId, itemId, { is_completed: isCompleted }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', projectId, taskId] });
    },
  });

  const deleteChecklistMutation = useMutation({
    mutationFn: (itemId: string) => projectsApi.deleteChecklistItem(projectId, taskId, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', projectId, taskId] });
    },
  });

  const addCommentMutation = useMutation({
    mutationFn: (content: string) => projectsApi.createComment(projectId, taskId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', projectId, taskId] });
      setNewComment('');
    },
  });

  const addAttachmentMutation = useMutation({
    mutationFn: (payload: { file_name: string; file_url: string }) =>
      projectsApi.createAttachment(projectId, taskId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', projectId, taskId] });
      setAttachName('');
      setAttachUrl('');
    },
  });

  const addTimeMutation = useMutation({
    mutationFn: (payload: { hours: number; date: string; description: string }) =>
      projectsApi.createTimeEntry(projectId, taskId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', projectId, taskId] });
      setNewHours('');
      setNewHoursDesc('');
    },
  });

  const createLabelMutation = useMutation({
    mutationFn: (payload: { name: string; color: string }) => projectsApi.createLabel(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['labels', projectId] });
      setNewLabelName('');
    },
  });

  if (loadingTask || !task) {
    return <div className="p-8 text-center text-slate-400">Loading task details...</div>;
  }

  // Manage Multi-Assignees Selection
  const handleToggleAssignee = (userId: string) => {
    const isAssigned = task.assignees.some(u => u.id === userId);
    const newIds = isAssigned
      ? task.assignees.filter(u => u.id !== userId).map(u => u.id)
      : [...task.assignees.map(u => u.id), userId];
    updateTaskMutation.mutate({ assigneeIds: newIds });
  };

  // Manage Watchers Selection
  const handleToggleWatcher = (userId: string) => {
    const isWatching = task.watchers.some(u => u.id === userId);
    const newIds = isWatching
      ? task.watchers.filter(u => u.id !== userId).map(u => u.id)
      : [...task.watchers.map(u => u.id), userId];
    updateTaskMutation.mutate({ watcherIds: newIds });
  };

  // Manage Labels Selection
  const handleToggleLabel = (labelId: string) => {
    const hasLabel = task.labels.some(l => l.id === labelId);
    const newIds = hasLabel
      ? task.labels.filter(l => l.id !== labelId).map(l => l.id)
      : [...task.labels.map(l => l.id), labelId];
    updateTaskMutation.mutate({ labelIds: newIds });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-start p-6 border-b border-slate-800">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Task Details</span>
            <h3 className="text-xl font-bold text-slate-100 mt-1">{task.title}</h3>
          </div>
          <div className="flex items-center gap-2">
            {task.status === 'todo' && (
              <Button
                size="sm"
                onClick={() => {
                  updateTaskMutation.mutate({ status: 'in_progress' });
                  toast.success('Task moved to In Progress! Chalo start karte hain! 🚀');
                }}
                disabled={updateTaskMutation.isPending}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-md"
              >
                <Play className="h-3.5 w-3.5 fill-current" /> 🚀 Chalo Start Karte Hain
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (window.confirm(`Delete task "${task.title}"?`)) {
                  deleteTaskMutation.mutate();
                }
              }}
              disabled={deleteTaskMutation.isPending}
              className="border-red-950 bg-red-950/20 text-red-400 hover:bg-red-950 hover:text-red-300 flex items-center gap-1.5 transition-colors text-xs"
            >
              {deleteTaskMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
              Delete Task
            </Button>
            <button onClick={onClose} className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Info */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Description */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Description</h4>
              <p className="text-sm text-slate-300 bg-slate-950/30 border border-slate-850 p-3 rounded-lg leading-relaxed">
                {task.description || 'No description provided.'}
              </p>
            </div>

            {/* Checklist */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <CheckSquare className="h-4 w-4 text-indigo-400" /> Checklist / Subtasks
              </h4>
              <div className="flex flex-col gap-2">
                {task.checklistItems?.map(item => (
                  <div key={item.id} className="flex items-center justify-between bg-slate-950/20 p-2 rounded border border-slate-850">
                    <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={item.is_completed}
                        onChange={() => toggleChecklistMutation.mutate({ itemId: item.id, isCompleted: !item.is_completed })}
                        className="rounded border-slate-800 bg-slate-900 text-indigo-600 focus:ring-0 focus:ring-offset-0"
                      />
                      <span className={item.is_completed ? 'line-through text-slate-500' : ''}>{item.title}</span>
                    </label>
                    <button
                      onClick={() => deleteChecklistMutation.mutate(item.id)}
                      className="text-slate-500 hover:text-red-400 transition-colors p-1"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}

                <form
                  onSubmit={(e) => { e.preventDefault(); if (newChecklistTitle.trim()) addChecklistMutation.mutate(newChecklistTitle.trim()); }}
                  className="flex gap-2 mt-2"
                >
                  <input
                    type="text"
                    value={newChecklistTitle}
                    onChange={(e) => setNewChecklistTitle(e.target.value)}
                    placeholder="Add checklist item..."
                    className="bg-slate-950 border border-slate-850 text-slate-100 rounded px-3 py-1.5 text-xs outline-none focus:border-indigo-500/50 w-full"
                  />
                  <Button type="submit" size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shrink-0">
                    Add
                  </Button>
                </form>
              </div>
            </div>

            {/* Time Tracking Log */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-emerald-400" /> Time Logging
              </h4>
              <div className="flex flex-col gap-2">
                {task.timeEntries?.map(entry => (
                  <div key={entry.id} className="text-xs bg-slate-950/20 border border-slate-850 p-2.5 rounded text-slate-400 flex justify-between">
                    <span>
                      <strong className="text-slate-200">{entry.hours} hours</strong> logged by {entry.user.username}
                      {entry.description && <span className="block text-[11px] text-slate-500 mt-0.5">{entry.description}</span>}
                    </span>
                    <span>{new Date(entry.date).toLocaleDateString()}</span>
                  </div>
                ))}

                <div className="grid grid-cols-2 gap-2 mt-2 bg-slate-950/20 border border-slate-850 p-3 rounded-lg">
                  <input
                    type="number"
                    value={newHours}
                    onChange={(e) => setNewHours(e.target.value)}
                    placeholder="Hours (e.g. 2.5)"
                    className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-2.5 py-1 text-xs outline-none"
                  />
                  <input
                    type="date"
                    id="time-entry-date"
                    className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-2.5 py-1 text-xs outline-none"
                  />
                  <input
                    type="text"
                    value={newHoursDesc}
                    onChange={(e) => setNewHoursDesc(e.target.value)}
                    placeholder="Work description..."
                    className="col-span-2 bg-slate-900 border border-slate-800 text-slate-100 rounded px-2.5 py-1 text-xs outline-none"
                  />
                  <Button
                    onClick={() => {
                      const dateInput = document.getElementById('time-entry-date') as HTMLInputElement;
                      if (newHours && dateInput?.value) {
                        addTimeMutation.mutate({
                          hours: parseFloat(newHours),
                          date: dateInput.value,
                          description: newHoursDesc
                        });
                      } else {
                        toast.error('Hours and Date are required');
                      }
                    }}
                    size="sm"
                    className="col-span-2 bg-emerald-600 hover:bg-emerald-700 text-white mt-1"
                  >
                    Log Time
                  </Button>
                </div>
              </div>
            </div>

            {/* Attachments */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <Paperclip className="h-4 w-4 text-violet-400" /> Attachments
              </h4>
              <div className="flex flex-col gap-2">
                {task.attachments?.map((att: TaskAttachment) => (
                  <a
                    key={att.id}
                    href={att.file_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs bg-slate-950/20 border border-slate-850 hover:border-violet-500/30 p-2 rounded text-indigo-400 hover:text-indigo-300 flex justify-between"
                  >
                    <span>{att.file_name}</span>
                    <span className="text-slate-500 text-[10px]">Uploaded by {att.uploadedBy?.username}</span>
                  </a>
                ))}

                <div className="grid grid-cols-2 gap-2 mt-2 bg-slate-950/20 border border-slate-850 p-3 rounded-lg">
                  <input
                    type="text"
                    value={attachName}
                    onChange={(e) => setAttachName(e.target.value)}
                    placeholder="Attachment name (e.g. Spec doc)"
                    className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-2.5 py-1 text-xs outline-none"
                  />
                  <input
                    type="text"
                    value={attachUrl}
                    onChange={(e) => setAttachUrl(e.target.value)}
                    placeholder="File URL (http://...)"
                    className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-2.5 py-1 text-xs outline-none"
                  />
                  <Button
                    onClick={() => {
                      if (attachName && attachUrl) {
                        addAttachmentMutation.mutate({ file_name: attachName, file_url: attachUrl });
                      }
                    }}
                    size="sm"
                    className="col-span-2 bg-violet-600 hover:bg-violet-700 text-white"
                  >
                    Add Attachment URL
                  </Button>
                </div>
              </div>
            </div>

            {/* Comments */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <MessageSquare className="h-4 w-4 text-pink-400" /> Comments
              </h4>
              <div className="flex flex-col gap-3">
                {task.comments?.map(c => (
                  <div key={c.id} className="bg-slate-950/30 border border-slate-850/80 p-3 rounded-lg flex flex-col gap-1">
                    <div className="flex justify-between text-[10px] text-slate-500">
                      <span className="font-semibold text-slate-300">{c.author.username}</span>
                      <span>{new Date(c.createdAt).toLocaleString()}</span>
                    </div>
                    <p className="text-sm text-slate-200 leading-normal">{c.content}</p>
                  </div>
                ))}

                <form
                  onSubmit={(e) => { e.preventDefault(); if (newComment.trim()) addCommentMutation.mutate(newComment.trim()); }}
                  className="flex gap-2 mt-1"
                >
                  <input
                    type="text"
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Write a comment..."
                    className="bg-slate-950 border border-slate-850 text-slate-100 rounded px-3 py-1.5 text-xs outline-none focus:border-indigo-500/50 w-full"
                  />
                  <Button type="submit" size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shrink-0">
                    Send
                  </Button>
                </form>
              </div>
            </div>
          </div>

          {/* Sidebar controls */}
          <div className="flex flex-col gap-6 border-l border-slate-800 pl-0 lg:pl-6">
            {/* Owner Work Rating */}
            <div>
              <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Star className="h-3.5 w-3.5 fill-current text-amber-400" /> Owner Work Rating
              </h4>
              <div className="grid grid-cols-2 gap-1.5 bg-slate-950/20 border border-slate-850 p-2.5 rounded-lg">
                <button
                  type="button"
                  onClick={() => rateTaskMutation.mutate('excellent')}
                  className={`text-xs px-2 py-1.5 rounded font-semibold transition-colors ${
                    task.performanceRating === 'excellent'
                      ? 'bg-amber-500 text-slate-950 font-bold'
                      : 'bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  🌟 Excellent
                </button>
                <button
                  type="button"
                  onClick={() => rateTaskMutation.mutate('very_good')}
                  className={`text-xs px-2 py-1.5 rounded font-semibold transition-colors ${
                    task.performanceRating === 'very_good'
                      ? 'bg-emerald-500 text-slate-950 font-bold'
                      : 'bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  ⭐ Very Good
                </button>
                <button
                  type="button"
                  onClick={() => rateTaskMutation.mutate('good')}
                  className={`text-xs px-2 py-1.5 rounded font-semibold transition-colors ${
                    task.performanceRating === 'good'
                      ? 'bg-indigo-500 text-white font-bold'
                      : 'bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  👍 Good
                </button>
                <button
                  type="button"
                  onClick={() => rateTaskMutation.mutate('needs_work')}
                  className={`text-xs px-2 py-1.5 rounded font-semibold transition-colors ${
                    task.performanceRating === 'needs_work'
                      ? 'bg-rose-500 text-white font-bold'
                      : 'bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  ⚠️ Needs Work
                </button>
              </div>
            </div>

            {/* Multi-Assignees */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                <UserPlus className="h-3.5 w-3.5" /> Assignees
              </h4>
              <div className="flex flex-col gap-1 bg-slate-950/20 border border-slate-850 p-2.5 rounded-lg max-h-40 overflow-y-auto">
                {orgMembers.map(m => {
                  const isAssigned = task.assignees.some(u => u.id === m.user.id);
                  return (
                    <label key={m.id} className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer py-1 hover:text-white transition-colors">
                      <input
                        type="checkbox"
                        checked={isAssigned}
                        onChange={() => handleToggleAssignee(m.user.id)}
                        className="rounded border-slate-800 bg-slate-900 text-indigo-600 focus:ring-0"
                      />
                      <span>{m.user.username}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Watchers */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Watchers</h4>
              <div className="flex flex-col gap-1 bg-slate-950/20 border border-slate-850 p-2.5 rounded-lg max-h-40 overflow-y-auto">
                {orgMembers.map(m => {
                  const isWatching = task.watchers.some(u => u.id === m.user.id);
                  return (
                    <label key={m.id} className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer py-1 hover:text-white transition-colors">
                      <input
                        type="checkbox"
                        checked={isWatching}
                        onChange={() => handleToggleWatcher(m.user.id)}
                        className="rounded border-slate-800 bg-slate-900 text-indigo-600 focus:ring-0"
                      />
                      <span>{m.user.username}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Labels */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Tag className="h-3.5 w-3.5" /> Task Labels
              </h4>
              <div className="flex flex-col gap-2 bg-slate-950/20 border border-slate-850 p-2.5 rounded-lg">
                <div className="flex flex-col gap-1 max-h-32 overflow-y-auto">
                  {labels.map(l => {
                    const hasLabel = task.labels.some(tl => tl.id === l.id);
                    return (
                      <label key={l.id} className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer py-1">
                        <input
                          type="checkbox"
                          checked={hasLabel}
                          onChange={() => handleToggleLabel(l.id)}
                          className="rounded border-slate-800 bg-slate-900 text-indigo-600 focus:ring-0"
                        />
                        <span className="px-1.5 py-0.5 rounded text-[10px]" style={{ backgroundColor: `${l.color}15`, color: l.color, border: `1px solid ${l.color}30` }}>
                          {l.name}
                        </span>
                      </label>
                    );
                  })}
                </div>

                <div className="border-t border-slate-900 pt-2 mt-1 flex flex-col gap-1">
                  <input
                    type="text"
                    value={newLabelName}
                    onChange={(e) => setNewLabelName(e.target.value)}
                    placeholder="New label name..."
                    className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-2.5 py-1 text-[11px] outline-none"
                  />
                  <div className="flex gap-2 items-center">
                    <input
                      type="color"
                      value={newLabelColor}
                      onChange={(e) => setNewLabelColor(e.target.value)}
                      className="bg-transparent border-0 w-8 h-6 rounded cursor-pointer p-0"
                    />
                    <Button
                      onClick={() => {
                        if (newLabelName.trim()) {
                          createLabelMutation.mutate({ name: newLabelName.trim(), color: newLabelColor });
                        }
                      }}
                      size="sm"
                      className="bg-indigo-600 hover:bg-indigo-700 text-white text-[10px] h-6 py-0 px-2"
                    >
                      Create Label
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
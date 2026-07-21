'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, Task, KanbanColumn, TaskStatus } from '@/services/projects-api';
import { Plus, Trash2, Calendar, CheckSquare, Users, Loader2, X, GitBranch, Star, Upload, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface KanbanBoardProps {
  projectId: string;
  onSelectTask: (task: Task) => void;
}

export function KanbanBoard({ projectId, onSelectTask }: KanbanBoardProps) {
  const queryClient = useQueryClient();
  const [newColumnName, setNewColumnName] = useState('');
  const [showCreateTask, setShowCreateTask] = useState(false);

  // New task form state
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [taskPriority, setTaskPriority] = useState<'low' | 'medium' | 'high' | 'critical'>('medium');
  const [taskStatus, setTaskStatus] = useState<TaskStatus>('todo');
  const [taskColId, setTaskColId] = useState<string | null>(null);
  const [taskAssigneeId, setTaskAssigneeId] = useState('');
  const [taskDueDate, setTaskDueDate] = useState('');

  // Queries
  const { data: columns = [], isLoading: loadingCols } = useQuery({
    queryKey: ['columns', projectId],
    queryFn: () => projectsApi.listColumns(projectId),
  });

  const { data: tasksData, isLoading: loadingTasks } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => projectsApi.listTasks(projectId),
  });

  const { data: members = [] } = useQuery({
    queryKey: ['project-members', projectId],
    queryFn: () => projectsApi.listMembers(projectId),
  });

  const tasks = tasksData?.results || [];

  // Mutations
  const createColumnMutation = useMutation({
    mutationFn: (name: string) => projectsApi.createColumn(projectId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['columns', projectId] });
      toast.success('Column created successfully');
      setNewColumnName('');
    },
    onError: (err: any) => toast.error(err.message || 'Failed to create column'),
  });

  const deleteColumnMutation = useMutation({
    mutationFn: (colId: string) => projectsApi.deleteColumn(projectId, colId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['columns', projectId] });
      toast.success('Column deleted');
    },
  });

  const createTaskMutation = useMutation({
    mutationFn: (payload: any) => projectsApi.createTask(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] });
      queryClient.invalidateQueries({ queryKey: ['analytics', projectId] });
      toast.success('Task created and assigned successfully!');
      setShowCreateTask(false);
      resetTaskForm();
    },
    onError: (err: any) => toast.error(err.message || 'Failed to create task'),
  });

  const deleteTaskMutation = useMutation({
    mutationFn: (taskId: string) => projectsApi.deleteTask(projectId, taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] });
      queryClient.invalidateQueries({ queryKey: ['analytics', projectId] });
      toast.success('Task deleted successfully');
    },
    onError: (err: any) => toast.error(err.message || 'Failed to delete task'),
  });

  const simulatePushMutation = useMutation({
    mutationFn: ({ taskId, files }: { taskId: string; files?: string[] }) =>
      projectsApi.simulatePush(projectId, taskId, { files }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] });
      queryClient.invalidateQueries({ queryKey: ['analytics', projectId] });
      toast.success('Code pushed! Task moved to IN REVIEW for Owner Approval 🚀');
    },
    onError: (err: any) => toast.error(err.message || 'Failed to simulate GitHub push'),
  });

  const rateTaskMutation = useMutation({
    mutationFn: ({ taskId, rating }: { taskId: string; rating: string }) =>
      projectsApi.rateTask(projectId, taskId, rating),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] });
      queryClient.invalidateQueries({ queryKey: ['analytics', projectId] });
      toast.success('Task rated by Owner & moved to DONE! 🎉');
    },
    onError: (err: any) => toast.error(err.message || 'Failed to rate task'),
  });

  const updateTaskMutation = useMutation({
    mutationFn: ({ taskId, payload }: { taskId: string; payload: any }) =>
      projectsApi.updateTask(projectId, taskId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] });
      queryClient.invalidateQueries({ queryKey: ['analytics', projectId] });
    },
  });

  const resetTaskForm = () => {
    setTaskTitle('');
    setTaskDescription('');
    setTaskPriority('medium');
    setTaskStatus('todo');
    setTaskColId(null);
    setTaskAssigneeId('');
    setTaskDueDate('');
  };

  const handleCreateColumn = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newColumnName.trim()) return;
    createColumnMutation.mutate(newColumnName.trim());
  };

  const handleCreateTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle.trim()) {
      toast.error('Task title is required');
      return;
    }
    if (!taskDescription.trim()) {
      toast.error('Task description is required');
      return;
    }
    if (!taskAssigneeId) {
      toast.error('Please select a team member to assign this task');
      return;
    }
    if (!taskDueDate) {
      toast.error('Please select a due date for this task');
      return;
    }

    const payload: any = {
      title: taskTitle.trim(),
      description: taskDescription.trim(),
      priority: taskPriority,
      status: taskStatus,
      dueDate: taskDueDate,
      assigneeId: taskAssigneeId,
      assigneeIds: [taskAssigneeId],
    };

    if (taskColId) {
      payload.kanbanColumnId = taskColId;
    }

    createTaskMutation.mutate(payload);
  };

  const openCreateTaskForCol = (colStatus: TaskStatus, customId?: string) => {
    setTaskStatus(colStatus);
    setTaskColId(customId || null);
    setShowCreateTask(true);
  };

  // Drag & Drop
  const handleDragStart = (e: React.DragEvent, taskId: string) => {
    e.dataTransfer.setData('text/plain', taskId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, targetStatus: TaskStatus, targetColId?: string) => {
    e.preventDefault();
    const taskId = e.dataTransfer.getData('text/plain');
    if (!taskId) return;

    const payload: any = { status: targetStatus };
    if (targetColId) {
      payload.kanbanColumnId = targetColId;
    } else {
      payload.kanbanColumnId = null;
    }

    updateTaskMutation.mutate({ taskId, payload });
  };

  if (loadingCols || loadingTasks) {
    return <div className="p-8 text-center text-slate-400">Loading Kanban Board...</div>;
  }

  interface ColDef {
    id: string;
    name: string;
    status: TaskStatus;
    customId?: string;
  }

  const columnData: ColDef[] = columns.length > 0 
    ? columns.map(c => ({ id: c.id, name: c.name, status: 'in_progress' as TaskStatus, customId: c.id }))
    : [
        { id: 'todo', name: 'To Do', status: 'todo' as TaskStatus },
        { id: 'in_progress', name: 'In Progress', status: 'in_progress' as TaskStatus },
        { id: 'in_review', name: 'In Review', status: 'in_review' as TaskStatus },
        { id: 'done', name: 'Done', status: 'done' as TaskStatus },
      ];

  const getTasksForColumn = (col: typeof columnData[0]) => {
    if (col.customId) {
      return tasks.filter(t => t.kanbanColumnId === col.customId);
    }
    return tasks.filter(t => t.status === col.status && !t.kanbanColumnId);
  };

  return (
    <div className="flex flex-col gap-6 h-full">
      {/* Header Actions */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <Button
          onClick={() => { resetTaskForm(); setShowCreateTask(true); }}
          size="sm"
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium shadow-sm"
        >
          <Plus className="h-4 w-4 mr-1.5" /> New Task
        </Button>

        <form onSubmit={handleCreateColumn} className="flex gap-2 max-w-sm">
          <input
            type="text"
            value={newColumnName}
            onChange={(e) => setNewColumnName(e.target.value)}
            placeholder="New custom column name..."
            className="bg-slate-900 border border-slate-800 text-slate-100 rounded-lg px-3 py-1.5 text-sm outline-none focus:border-indigo-500/50 w-full"
          />
          <Button type="submit" size="sm" variant="outline" className="shrink-0 border-slate-800 text-slate-300 hover:text-white">
            <Plus className="h-4 w-4 mr-1" /> Add Column
          </Button>
        </form>
      </div>

      {/* Create Task Modal */}
      {showCreateTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <form onSubmit={handleCreateTask} className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg p-6 shadow-2xl flex flex-col gap-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-slate-100">Create New Task</h3>
              <button type="button" onClick={() => setShowCreateTask(false)} className="text-slate-400 hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex flex-col gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Task Title <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Design Landing Page"
                  value={taskTitle}
                  onChange={(e) => setTaskTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500/50"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Description <span className="text-red-400">*</span>
                </label>
                <textarea
                  placeholder="Add details about this task..."
                  value={taskDescription}
                  onChange={(e) => setTaskDescription(e.target.value)}
                  rows={3}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500/50 resize-none"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Assign to Member <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={taskAssigneeId}
                    onChange={(e) => setTaskAssigneeId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500/50"
                    required
                  >
                    <option value="">-- Select Member --</option>
                    {members.map(m => (
                      <option key={m.user.id} value={m.user.id}>
                        {m.user.username} ({m.role})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Priority <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={taskPriority}
                    onChange={(e) => setTaskPriority(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500/50"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Status Column <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={taskStatus}
                    onChange={(e) => setTaskStatus(e.target.value as TaskStatus)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500/50"
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="in_review">In Review</option>
                    <option value="done">Done</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Due Date <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="date"
                    value={taskDueDate}
                    onChange={(e) => setTaskDueDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500/50"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-2 justify-end pt-2 border-t border-slate-800">
              <Button type="button" variant="outline" size="sm" onClick={() => setShowCreateTask(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium"
                disabled={createTaskMutation.isPending || !taskTitle.trim() || !taskDescription.trim() || !taskAssigneeId || !taskDueDate}
              >
                {createTaskMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin text-white" /> : 'Create Task'}
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Board Columns container */}
      <div className="flex gap-4 overflow-x-auto pb-4 h-[calc(100vh-280px)]">
        {columnData.map((col) => {
          const colTasks = getTasksForColumn(col);
          return (
            <div
              key={col.id}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, col.status, col.customId)}
              className="flex flex-col w-72 shrink-0 bg-slate-900/40 border border-slate-800 rounded-xl p-4"
            >
              {/* Header */}
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-slate-200 text-sm tracking-wide">{col.name}</h4>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-medium">
                    {colTasks.length}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => openCreateTaskForCol(col.status, col.customId)}
                    title="Add task to this column"
                    className="p-1 rounded hover:bg-indigo-500/10 text-slate-400 hover:text-indigo-400 transition-colors"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                  {col.customId && (
                    <button
                      onClick={() => deleteColumnMutation.mutate(col.customId!)}
                      className="p-1 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Tasks List */}
              <div className="flex flex-col gap-3 overflow-y-auto flex-1 pr-1">
                {colTasks.map((task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, task.id)}
                    onClick={() => onSelectTask(task)}
                    className="group border border-slate-800 bg-slate-950/40 p-4 rounded-lg hover:border-indigo-500/30 hover:bg-slate-900/30 cursor-pointer transition-all flex flex-col gap-3 select-none"
                  >
                    <div className="flex justify-between items-start gap-2">
                      <span className={`text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded border ${
                        task.priority === 'critical' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                        task.priority === 'high' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                        task.priority === 'medium' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' :
                        'bg-slate-500/10 text-slate-400 border-slate-500/20'
                      }`}>
                        {task.priority}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`Delete task "${task.title}"?`)) {
                            deleteTaskMutation.mutate(task.id);
                          }
                        }}
                        title="Delete task"
                        className="p-1 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>

                    <h5 className="font-medium text-slate-100 text-sm leading-snug group-hover:text-indigo-300 transition-colors flex items-center justify-between gap-2">
                      <span>{task.title}</span>
                      {task.performanceRating && (
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1 shrink-0 ${
                          task.performanceRating === 'excellent' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                          task.performanceRating === 'very_good' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                          task.performanceRating === 'good' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' :
                          'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        }`}>
                          <Star className="h-3 w-3 fill-current" />
                          {task.performanceRating === 'excellent' ? 'Excellent' :
                           task.performanceRating === 'very_good' ? 'Very Good' :
                           task.performanceRating === 'good' ? 'Good' : 'Needs Work'}
                        </span>
                      )}
                    </h5>

                    {task.description && (
                      <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                        {task.description}
                      </p>
                    )}

                    {/* GitHub Commit Info */}
                    {task.githubCommitInfo?.pushedBy && (
                      <div className="bg-slate-900/80 border border-slate-800 rounded p-2 text-[11px] text-slate-300 flex flex-col gap-1">
                        <div className="flex items-center justify-between text-indigo-400 font-medium">
                          <span className="flex items-center gap-1">
                            <GitBranch className="h-3 w-3" /> Pushed by {task.githubCommitInfo.pushedBy}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">{task.githubCommitInfo.commitSha}</span>
                        </div>
                        <div className="text-slate-400 truncate font-mono text-[10px]">{task.githubCommitInfo.message}</div>
                        {task.githubCommitInfo.filesChanged && task.githubCommitInfo.filesChanged.length > 0 && (
                          <div className="text-[10px] text-emerald-400/90 font-medium truncate">
                            📁 {task.githubCommitInfo.filesChanged.join(', ')}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Chalo Start Karte Hain Button for To Do Tasks */}
                    {task.status === 'todo' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          updateTaskMutation.mutate({ taskId: task.id, payload: { status: 'in_progress' } });
                          toast.success('Task moved to In Progress! Chalo start karte hain! 🚀');
                        }}
                        disabled={updateTaskMutation.isPending}
                        className="w-full text-[11px] bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-1.5 px-2 rounded flex items-center justify-center gap-1.5 transition-colors shadow-sm"
                      >
                        <Play className="h-3 w-3 fill-current" /> 🚀 Chalo Start Karte Hain
                      </button>
                    )}

                    {/* Push Code for In Progress Tasks */}
                    {task.status === 'in_progress' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          const filesInput = prompt("Files added/modified (comma-separated):", "backend/views.py, frontend/page.tsx");
                          if (filesInput === null) return;
                          const filesList = filesInput.split(',').map(f => f.trim()).filter(Boolean);
                          simulatePushMutation.mutate({ taskId: task.id, files: filesList });
                        }}
                        disabled={simulatePushMutation.isPending}
                        className="w-full text-[11px] bg-indigo-900/80 hover:bg-indigo-800 border border-indigo-700/50 text-indigo-200 font-medium py-1.5 px-2 rounded flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <Upload className="h-3 w-3 text-indigo-400" /> Push Code (Move to In Review)
                      </button>
                    )}

                    {/* Owner Review Controls for In Review Tasks */}
                    {task.status === 'in_review' && (
                      <div className="flex flex-col gap-1.5 bg-amber-500/10 border border-amber-500/20 p-2.5 rounded-lg text-xs" onClick={(e) => e.stopPropagation()}>
                        <span className="font-bold text-amber-300 text-[10px] uppercase tracking-wider flex items-center gap-1">
                          <Star className="h-3 w-3 fill-current text-amber-400" /> Owner Review Required
                        </span>
                        <p className="text-[10px] text-slate-400">Rate this work to approve and move to DONE:</p>
                        <div className="grid grid-cols-2 gap-1 mt-0.5">
                          <button
                            onClick={() => rateTaskMutation.mutate({ taskId: task.id, rating: 'excellent' })}
                            className="text-[10px] bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-1 px-1.5 rounded transition-colors"
                          >
                            🌟 Excellent
                          </button>
                          <button
                            onClick={() => rateTaskMutation.mutate({ taskId: task.id, rating: 'very_good' })}
                            className="text-[10px] bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold py-1 px-1.5 rounded transition-colors"
                          >
                            ⭐ Very Good
                          </button>
                          <button
                            onClick={() => rateTaskMutation.mutate({ taskId: task.id, rating: 'good' })}
                            className="text-[10px] bg-indigo-500 hover:bg-indigo-400 text-white font-bold py-1 px-1.5 rounded transition-colors"
                          >
                            👍 Good
                          </button>
                          <button
                            onClick={() => rateTaskMutation.mutate({ taskId: task.id, rating: 'needs_work' })}
                            className="text-[10px] bg-rose-500 hover:bg-rose-400 text-white font-bold py-1 px-1.5 rounded transition-colors"
                          >
                            ⚠️ Needs Work
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Labels */}
                    {task.labels && task.labels.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {task.labels.map(l => (
                          <span
                            key={l.id}
                            className="text-[9px] font-semibold px-1.5 py-0.5 rounded"
                            style={{ backgroundColor: `${l.color}15`, color: l.color, border: `1px solid ${l.color}30` }}
                          >
                            {l.name}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Metadata Footer */}
                    <div className="flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-900 pt-3 mt-1">
                      {task.dueDate ? (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(task.dueDate).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        </span>
                      ) : (
                        <div />
                      )}

                      <div className="flex items-center gap-3">
                        {task.checklistItems && task.checklistItems.length > 0 && (
                          <span className="flex items-center gap-1">
                            <CheckSquare className="h-3 w-3" />
                            {task.checklistItems.filter(i => i.is_completed).length}/{task.checklistItems.length}
                          </span>
                        )}
                        {task.assignees && task.assignees.length > 0 ? (
                          <span className="flex items-center gap-1 text-indigo-400 font-medium">
                            <Users className="h-3 w-3" />
                            {task.assignees.map(a => a.username).join(', ')}
                          </span>
                        ) : null}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
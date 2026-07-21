'use client';

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useSelector } from 'react-redux';
import { projectsApi } from '@/services/projects-api';
import type { RootState } from '@/store';
import { toast } from 'sonner';
import { X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface CreateProjectDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CreateProjectDialog({ isOpen, onClose }: CreateProjectDialogProps) {
  const queryClient = useQueryClient();
  const activeOrgId = useSelector((s: RootState) => s.org.activeOrgId);
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const { mutate, isPending } = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Project created successfully');
      setName('');
      setDescription('');
      onClose();
    },
    onError: (err: any) => {
      toast.error(err.message || 'Failed to create project');
    },
  });

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isPending) return;
    if (!name.trim()) {
      toast.error('Project name is required');
      return;
    }
    if (!activeOrgId) {
      toast.error('Please select or create an organization first');
      return;
    }
    mutate({
      name,
      description,
      organizationId: activeOrgId,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
          <h2 className="text-lg font-bold text-slate-100">Create New Project</h2>
          <button onClick={onClose} className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-slate-300">Project Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Website Redesign"
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none transition-colors"
              disabled={isPending}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-slate-300">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide a brief description of the project"
              rows={3}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none transition-colors resize-none"
              disabled={isPending}
            />
          </div>

          <div className="flex justify-end gap-3 mt-4 border-t border-slate-800 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isPending}
              className="border-slate-850 bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-white"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isPending}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold flex items-center gap-1.5"
            >
              {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Create Project
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

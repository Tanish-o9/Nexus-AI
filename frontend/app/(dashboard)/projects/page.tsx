'use client';

import { useState } from 'react';
import { ProjectsList } from '@/features/projects/components/projects-list';
import { OrgSwitcher } from '@/features/organizations/components/org-switcher';
import { CreateProjectDialog } from '@/features/projects/components/create-project-dialog';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

export default function ProjectsPage() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  return (
    <div className="flex flex-col gap-6 p-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Projects</h2>
          <p className="text-sm text-slate-400 mt-0.5">Manage and track all your projects</p>
        </div>
        <div className="flex items-center gap-3">
          <OrgSwitcher />
          <Button 
            onClick={() => setIsCreateOpen(true)}
            className="bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white shadow-lg shadow-indigo-500/25 text-sm"
          >
            <Plus className="h-4 w-4 mr-1.5" /> New Project
          </Button>
        </div>
      </div>

      <ProjectsList />

      {isCreateOpen && (
        <CreateProjectDialog 
          isOpen={isCreateOpen} 
          onClose={() => setIsCreateOpen(false)} 
        />
      )}
    </div>
  );
}

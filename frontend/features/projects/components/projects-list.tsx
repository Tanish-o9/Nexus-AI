'use client';

import { useState } from 'react';
import { useProjects } from '@/features/projects/hooks/use-projects';
import { ProjectCard } from './project-card';
import { ProjectsFilters } from './projects-filters';
import { Button } from '@/components/ui/button';
import type { ProjectStatus } from '@/services/projects-api';

const PAGE_SIZE = 9;

export function ProjectsList() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<ProjectStatus | ''>('');
  const [ordering, setOrdering] = useState('-updated_at');

  const { data, isLoading, isError } = useProjects({
    page,
    pageSize: PAGE_SIZE,
    search,
    status,
    ordering,
  });

  function handleSearch(v: string) { setSearch(v); setPage(1); }
  function handleStatus(v: ProjectStatus | '') { setStatus(v); setPage(1); }
  function handleOrdering(v: string) { setOrdering(v); setPage(1); }

  const totalPages = data ? Math.ceil(data.count / PAGE_SIZE) : 1;

  return (
    <div className="flex flex-col gap-6">
      <ProjectsFilters
        search={search}
        status={status}
        ordering={ordering}
        onSearch={handleSearch}
        onStatus={handleStatus}
        onOrdering={handleOrdering}
      />

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-28 rounded-xl bg-slate-800/40 animate-pulse" />
          ))}
        </div>
      )}

      {isError && (
        <p className="text-sm text-red-400 text-center py-12">Failed to load projects.</p>
      )}

      {!isLoading && !isError && data?.results.length === 0 && (
        <p className="text-sm text-slate-500 text-center py-12">No projects found.</p>
      )}

      {!isLoading && !isError && data && data.results.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.results.map((p) => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-slate-500">
            {data?.count ?? 0} projects · page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-300 disabled:opacity-40"
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page === totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-300 disabled:opacity-40"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

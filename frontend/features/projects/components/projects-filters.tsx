'use client';

import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import type { ProjectStatus } from '@/services/projects-api';

const STATUSES: { value: ProjectStatus | ''; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'active', label: 'Active' },
  { value: 'on_hold', label: 'On hold' },
  { value: 'completed', label: 'Completed' },
  { value: 'archived', label: 'Archived' },
];

const ORDERINGS = [
  { value: '-updated_at', label: 'Recently updated' },
  { value: '-created_at', label: 'Newest first' },
  { value: 'name', label: 'Name A–Z' },
  { value: '-name', label: 'Name Z–A' },
];

interface Props {
  search: string;
  status: ProjectStatus | '';
  ordering: string;
  onSearch: (v: string) => void;
  onStatus: (v: ProjectStatus | '') => void;
  onOrdering: (v: string) => void;
}

export function ProjectsFilters({ search, status, ordering, onSearch, onStatus, onOrdering }: Props) {
  return (
    <div className="flex flex-wrap gap-3">
      <div className="relative flex-1 min-w-48">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <Input
          placeholder="Search projects…"
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          className="pl-9 bg-slate-900/50 border-slate-800 text-slate-200 placeholder:text-slate-500"
        />
      </div>

      <select
        value={status}
        onChange={(e) => onStatus(e.target.value as ProjectStatus | '')}
        className="px-3 py-2 rounded-lg bg-slate-900/50 border border-slate-800 text-slate-300 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
      >
        {STATUSES.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>

      <select
        value={ordering}
        onChange={(e) => onOrdering(e.target.value)}
        className="px-3 py-2 rounded-lg bg-slate-900/50 border border-slate-800 text-slate-300 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
      >
        {ORDERINGS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

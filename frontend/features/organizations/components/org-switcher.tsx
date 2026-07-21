'use client';

import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useOrganizations } from '@/features/organizations/hooks/use-organizations';
import { setActiveOrg } from '@/features/organizations/store/org-slice';
import type { RootState } from '@/store';
import { Building2, ChevronDown } from 'lucide-react';

export function OrgSwitcher() {
  const dispatch = useDispatch();
  const activeOrgId = useSelector((s: RootState) => s.org.activeOrgId);
  const { data, isLoading } = useOrganizations();

  const orgs = data?.results ?? [];
  const active = orgs.find((o) => o.id === activeOrgId) ?? orgs[0];

  // Sync the auto-selected first org into Redux so other components
  // (e.g. CreateProjectDialog) can read a non-null activeOrgId.
  useEffect(() => {
    if (!activeOrgId && orgs.length > 0) {
      dispatch(setActiveOrg(orgs[0].id));
    }
  }, [activeOrgId, orgs, dispatch]);

  if (isLoading) return <div className="h-9 w-48 rounded-lg bg-slate-800/50 animate-pulse" />;
  if (!orgs.length) return null;

  return (
    <div className="relative inline-block">
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-800 bg-slate-900/50 text-sm text-slate-300">
        <Building2 className="h-4 w-4 text-indigo-400 shrink-0" />
        <select
          value={active?.id ?? ''}
          onChange={(e) => dispatch(setActiveOrg(e.target.value))}
          className="bg-transparent focus:outline-none text-slate-300 pr-4 cursor-pointer"
        >
          {orgs.map((org) => (
            <option key={org.id} value={org.id}>{org.name}</option>
          ))}
        </select>
        <ChevronDown className="h-3 w-3 text-slate-500 pointer-events-none" />
      </div>
    </div>
  );
}

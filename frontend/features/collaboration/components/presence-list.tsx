'use client';

import { useQuery } from '@tanstack/react-query';
import { collaborationApi, type UserPresence } from '@/services/collaboration-api';
import { Users, Loader2 } from 'lucide-react';

interface Props {
  projectId: string;
}

export function PresenceList({ projectId }: Props) {
  const { data: presenceList = [], isLoading } = useQuery({
    queryKey: ['presence', projectId],
    queryFn: () => collaborationApi.listPresence(projectId),
    refetchInterval: 15_000,
  });

  const online = presenceList.filter((p) => p.isOnline);
  const offline = presenceList.filter((p) => !p.isOnline);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800">
        <Users className="h-4 w-4 text-emerald-400" />
        <span className="text-sm font-semibold text-slate-200">Team ({presenceList.length})</span>
        <span className="ml-auto text-xs text-emerald-400">{online.length} online</span>
      </div>
      <div className="max-h-48 overflow-y-auto divide-y divide-slate-800/50">
        {isLoading && (
          <div className="flex justify-center py-4"><Loader2 className="h-4 w-4 animate-spin text-slate-500" /></div>
        )}
        {!isLoading && presenceList.length === 0 && (
          <div className="py-4 text-center text-xs text-slate-500">No members found.</div>
        )}
        {online.map((p) => (
          <div key={p.userId} className="flex items-center gap-3 px-4 py-2.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shrink-0" />
            <span className="text-sm text-slate-200">{p.username}</span>
          </div>
        ))}
        {offline.map((p) => (
          <div key={p.userId} className="flex items-center gap-3 px-4 py-2.5 opacity-60">
            <span className="h-2 w-2 rounded-full bg-slate-600 shrink-0" />
            <span className="text-sm text-slate-400">{p.username}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
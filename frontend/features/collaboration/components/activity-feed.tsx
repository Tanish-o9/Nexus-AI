'use client';

import { useQuery } from '@tanstack/react-query';
import { collaborationApi, type ActivityFeedItem } from '@/services/collaboration-api';
import { Activity, BotMessageSquare, CheckSquare, MessageSquare, UserPlus, Zap, Loader2 } from 'lucide-react';

const TYPE_ICON: Record<string, React.ReactNode> = {
  task_created: <CheckSquare className="h-3.5 w-3.5" />,
  task_updated: <Zap className="h-3.5 w-3.5" />,
  task_completed: <CheckSquare className="h-3.5 w-3.5" />,
  comment_added: <MessageSquare className="h-3.5 w-3.5" />,
  member_joined: <UserPlus className="h-3.5 w-3.5" />,
  project_updated: <Zap className="h-3.5 w-3.5" />,
  chat_message: <MessageSquare className="h-3.5 w-3.5" />,
};

const TYPE_COLOR: Record<string, string> = {
  task_created: 'bg-emerald-500/10 text-emerald-400',
  task_updated: 'bg-amber-500/10 text-amber-400',
  task_completed: 'bg-indigo-500/10 text-indigo-400',
  comment_added: 'bg-pink-500/10 text-pink-400',
  member_joined: 'bg-violet-500/10 text-violet-400',
  project_updated: 'bg-amber-500/10 text-amber-400',
  chat_message: 'bg-sky-500/10 text-sky-400',
};

interface Props {
  projectId: string;
}

export function ActivityFeed({ projectId }: Props) {
  const { data: items = [], isLoading } = useQuery({
    queryKey: ['activity', projectId],
    queryFn: () => collaborationApi.listActivity(projectId),
    refetchInterval: 30_000, // Poll every 30s
  });

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800">
        <Activity className="h-4 w-4 text-violet-400" />
        <span className="text-sm font-semibold text-slate-200">Activity Feed</span>
      </div>
      <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/50">
        {isLoading && (
          <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-slate-500" /></div>
        )}
        {!isLoading && items.length === 0 && (
          <div className="py-6 text-center text-sm text-slate-500">No activity yet.</div>
        )}
        {items.map((item) => (
          <div key={item.id} className="flex gap-3 px-4 py-3 hover:bg-slate-800/20 transition-colors">
            <div className={`h-7 w-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${TYPE_COLOR[item.activityType] || 'bg-slate-800 text-slate-400'}`}>
              {TYPE_ICON[item.activityType] || <Activity className="h-3.5 w-3.5" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-slate-300">{item.description}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">
                {item.actor?.username ?? 'System'} · {new Date(item.createdAt).toLocaleString()}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
'use client';

import { useDispatch, useSelector } from 'react-redux';
import { markRead, markAllRead } from '@/features/notifications/store/notifications-slice';
import type { RootState } from '@/store';
import { Bell, BotMessageSquare, CheckCheck, MessageSquare, Briefcase, Zap } from 'lucide-react';

const TYPE_ICON: Record<string, React.ReactNode> = {
  task_assigned: <Briefcase className="h-3.5 w-3.5" />,
  mention: <MessageSquare className="h-3.5 w-3.5" />,
  agent_completed: <BotMessageSquare className="h-3.5 w-3.5" />,
  project_update: <Zap className="h-3.5 w-3.5" />,
};

const TYPE_COLOR: Record<string, string> = {
  task_assigned: 'bg-indigo-500/10 text-indigo-400',
  mention: 'bg-violet-500/10 text-violet-400',
  agent_completed: 'bg-emerald-500/10 text-emerald-400',
  project_update: 'bg-amber-500/10 text-amber-400',
};

interface Props {
  open: boolean;
  onClose: () => void;
}

export function NotificationsPanel({ open, onClose }: Props) {
  const dispatch = useDispatch();
  const notifications = useSelector((s: RootState) => s.notifications.items);
  const unread = notifications.filter((n) => !n.read).length;

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="absolute right-0 top-12 z-50 w-80 rounded-xl border border-slate-800 bg-slate-900/95 backdrop-blur-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-slate-400" />
            <span className="text-sm font-semibold text-slate-200">Notifications</span>
            {unread > 0 && (
              <span className="text-xs bg-indigo-500 text-white px-1.5 py-0.5 rounded-full font-medium">
                {unread}
              </span>
            )}
          </div>
          {unread > 0 && (
            <button
              onClick={() => dispatch(markAllRead())}
              className="flex items-center gap-1 text-xs text-slate-400 hover:text-indigo-400 transition-colors"
            >
              <CheckCheck className="h-3.5 w-3.5" /> Mark all read
            </button>
          )}
        </div>

        {/* List */}
        <div className="max-h-96 overflow-y-auto divide-y divide-slate-800/50">
          {notifications.length === 0 && (
            <div className="py-10 text-center text-sm text-slate-500">
              No notifications yet
            </div>
          )}
          {notifications.map((n) => (
            <button
              key={n.id}
              onClick={() => dispatch(markRead(n.id))}
              className={`w-full text-left px-4 py-3 flex gap-3 hover:bg-slate-800/40 transition-colors ${
                !n.read ? 'bg-slate-800/20' : ''
              }`}
            >
              <div className={`h-7 w-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${TYPE_COLOR[n.type]}`}>
                {TYPE_ICON[n.type]}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-xs font-medium truncate ${n.read ? 'text-slate-400' : 'text-slate-200'}`}>
                  {n.title}
                </p>
                <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{n.body}</p>
                <p className="text-xs text-slate-600 mt-1">
                  {new Date(n.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
              {!n.read && (
                <div className="h-2 w-2 rounded-full bg-indigo-400 shrink-0 mt-1.5" />
              )}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}

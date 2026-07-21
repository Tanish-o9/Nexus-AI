'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { useSelector } from 'react-redux';
import { Bell } from 'lucide-react';
import type { RootState } from '@/store';
import { NotificationsPanel } from '@/features/notifications/components/notifications-panel';

const TITLE_MAP: Record<string, string> = {
  '/dashboard': 'Executive Dashboard',
  '/projects': 'Projects',
  '/organizations': 'Organizations',
  '/ai-chat': 'AI Chat',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
};

export function Topbar() {
  const pathname = usePathname();
  const user = useSelector((s: RootState) => s.auth.user);
  const unread = useSelector(
    (s: RootState) => s.notifications.items.filter((n) => !n.read).length
  );
  const [panelOpen, setPanelOpen] = useState(false);

  const title =
    Object.entries(TITLE_MAP).find(([key]) => pathname.startsWith(key))?.[1] ?? 'Nexus PM';
  const initials = user?.username?.slice(0, 2).toUpperCase() ?? 'NX';

  return (
    <header className="h-16 shrink-0 border-b border-slate-800 bg-slate-900/40 backdrop-blur-xl flex items-center justify-between px-6">
      <h1 className="text-lg font-semibold text-slate-100 tracking-tight">{title}</h1>

      <div className="flex items-center gap-3">
        {/* Bell with unread badge */}
        <div className="relative">
          <button
            onClick={() => setPanelOpen((o) => !o)}
            className="relative p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-all"
          >
            <Bell className="h-4 w-4" />
            {unread > 0 && (
              <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-indigo-400 shadow shadow-indigo-400/50" />
            )}
          </button>
          <NotificationsPanel open={panelOpen} onClose={() => setPanelOpen(false)} />
        </div>

        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center text-xs font-bold text-white shadow shadow-indigo-500/20">
          {initials}
        </div>
      </div>
    </header>
  );
}

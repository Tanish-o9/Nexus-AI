'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useDispatch } from 'react-redux';
import {
  LayoutDashboard,
  Briefcase,
  Users,
  MessageSquareText,
  BarChart2,
  Settings,
  Sparkles,
  LogOut,
} from 'lucide-react';
import { logout } from '@/features/auth/store/auth-slice';

const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/projects', label: 'Projects', icon: Briefcase },
  { href: '/organizations', label: 'Organizations', icon: Users },
  { href: '/ai-chat', label: 'AI Chat', icon: MessageSquareText },
  { href: '/analytics', label: 'Analytics', icon: BarChart2 },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const dispatch = useDispatch();

  return (
    <aside className="w-64 shrink-0 border-r border-slate-800/80 bg-slate-950/80 backdrop-blur-2xl flex flex-col p-5 gap-6 hidden md:flex shadow-[5px_0_30px_0_rgba(0,0,0,0.4)]">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-2 py-1">
        <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30 transform hover:scale-105 transition-transform">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <span className="font-extrabold text-xl bg-gradient-to-r from-indigo-200 via-violet-200 to-white bg-clip-text text-transparent tracking-tight">
          Nexus PM
        </span>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1.5 flex-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + '/');
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                active
                  ? 'bg-gradient-to-r from-indigo-600/20 to-violet-600/20 text-indigo-300 border border-indigo-500/30 shadow-md shadow-indigo-500/10 -translate-y-0.5'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/60 hover:translate-x-1'
              }`}
            >
              <Icon className={`h-4 w-4 shrink-0 ${active ? 'text-indigo-400' : ''}`} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <button
        onClick={() => dispatch(logout())}
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
      >
        <LogOut className="h-4 w-4 shrink-0" />
        Sign out
      </button>
    </aside>
  );
}

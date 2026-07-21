'use client';

import React, { Suspense } from 'react';
import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';
import { PageSkeleton } from '@/components/layout/page-skeleton';
import { ErrorBoundary } from '@/components/layout/error-boundary';
import { useAuthGuard } from '@/hooks/use-auth-guard';
import { useNotifications } from '@/features/notifications/hooks/use-notifications';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthGuard();
  useNotifications();

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <Topbar />
        <main className="flex-1 overflow-y-auto">
          <ErrorBoundary>
            <Suspense fallback={<PageSkeleton />}>
              {children}
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}

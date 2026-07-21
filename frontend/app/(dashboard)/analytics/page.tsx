'use client';

import dynamic from 'next/dynamic';
import { BarChart2, TrendingUp, PieChart, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { globalAnalyticsApi } from '@/services/projects-api';

// Dynamic imports prevent recharts from running on the server (it uses browser APIs)
const ProjectStatusChart = dynamic(
  () => import('@/features/analytics/components/project-status-chart').then((m) => m.ProjectStatusChart),
  { ssr: false, loading: () => <ChartSkeleton /> }
);
const TaskVelocityChart = dynamic(
  () => import('@/features/analytics/components/task-velocity-chart').then((m) => m.TaskVelocityChart),
  { ssr: false, loading: () => <ChartSkeleton /> }
);
const WorkloadChart = dynamic(
  () => import('@/features/analytics/components/workload-chart').then((m) => m.WorkloadChart),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['global-analytics'],
    queryFn: globalAnalyticsApi.getAnalytics,
    staleTime: 0,
    refetchOnMount: 'always',
  });

  return (
    <div className="flex flex-col gap-6 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Analytics</h2>
          <p className="text-sm text-slate-400 mt-0.5">Real time portfolio health & team workload</p>
        </div>
        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-indigo-400">
            <Loader2 className="h-4 w-4 animate-spin" />
            Updating analytics...
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard icon={<PieChart className="h-4 w-4" />} title="Project Status Breakdown">
          <ProjectStatusChart data={data?.project_status} />
        </ChartCard>

        <ChartCard icon={<TrendingUp className="h-4 w-4" />} title="Task Velocity (last 8 weeks)">
          <TaskVelocityChart data={data?.velocity} />
        </ChartCard>

        <ChartCard
          icon={<BarChart2 className="h-4 w-4" />}
          title="Team Workload"
          subtitle="Amber = above threshold (12 tasks)"
          className="lg:col-span-2"
        >
          <WorkloadChart data={data?.workload} />
        </ChartCard>
      </div>
    </div>
  );
}

function ChartCard({
  icon, title, subtitle, children, className = '',
}: {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-xl border border-slate-800 bg-slate-900/30 p-5 ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-indigo-400">{icon}</span>
        <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
        {subtitle && <span className="text-xs text-slate-500 ml-auto">{subtitle}</span>}
      </div>
      {children}
    </div>
  );
}

function ChartSkeleton() {
  return <div className="h-60 rounded-lg bg-slate-800/40 animate-pulse" />;
}

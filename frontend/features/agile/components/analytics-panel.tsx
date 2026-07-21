'use client';

import { useQuery } from '@tanstack/react-query';
import { agileApi } from '@/services/agile-api';
import { BarChart2, TrendingUp, AlertTriangle, Users, Clock, Loader2 } from 'lucide-react';

interface Props {
  projectId: string;
}

export function AnalyticsPanel({ projectId }: Props) {
  const { data: analytics, isLoading: aLoading } = useQuery({
    queryKey: ['analytics', projectId],
    queryFn: () => agileApi.getAnalytics(projectId),
    staleTime: 0,
    refetchOnMount: 'always',
  });

  const { data: velocity, isLoading: vLoading } = useQuery({
    queryKey: ['velocity', projectId],
    queryFn: () => agileApi.getVelocity(projectId),
    staleTime: 0,
    refetchOnMount: 'always',
  });

  const { data: workload } = useQuery({
    queryKey: ['workload', projectId],
    queryFn: () => agileApi.getWorkload(projectId),
    staleTime: 0,
    refetchOnMount: 'always',
  });

  const { data: risks } = useQuery({
    queryKey: ['risks', projectId],
    queryFn: () => agileApi.getDeadlineRisks(projectId),
    staleTime: 0,
    refetchOnMount: 'always',
  });

  if (aLoading || vLoading) return <div className="py-8 text-center"><Loader2 className="h-5 w-5 animate-spin text-slate-500 mx-auto" /></div>;
  if (!analytics) return null;

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard icon={<BarChart2 className="h-4 w-4" />} label="Total Tasks" value={String(analytics.totalTasks)} color="text-indigo-400" />
        <StatCard icon={<TrendingUp className="h-4 w-4" />} label="Completion" value={`${analytics.completionRate}%`} color="text-emerald-400" />
        <StatCard icon={<AlertTriangle className="h-4 w-4" />} label="Overdue" value={String(analytics.overdueTasks)} color="text-red-400" />
        <StatCard icon={<TrendingUp className="h-4 w-4" />} label="Velocity" value={String(velocity?.averageVelocity ?? 0)} color="text-amber-400" />
      </div>

      {/* By Priority */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">By Priority</h4>
        <div className="space-y-2">
          {Object.entries(analytics.byPriority).map(([priority, count]) => {
            const pct = analytics.totalTasks ? Math.round((count / analytics.totalTasks) * 100) : 0;
            const color = priority === 'critical' ? 'bg-red-500' : priority === 'high' ? 'bg-amber-500' : priority === 'medium' ? 'bg-sky-500' : 'bg-slate-500';
            return (
              <div key={priority} className="flex items-center gap-3">
                <span className="text-xs text-slate-300 w-16 capitalize">{priority}</span>
                <div className="flex-1 h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                </div>
                <span className="text-xs text-slate-500 w-8 text-right">{count}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Workload */}
      {workload && workload.length > 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Users className="h-3.5 w-3.5" /> Workload
          </h4>
          <div className="space-y-2">
            {workload.map((w) => (
              <div key={w.assignee} className="flex items-center justify-between text-xs">
                <span className="text-slate-200">{w.assignee}</span>
                <div className="flex gap-3 text-slate-500">
                  <span className={w.activeTasks > 0 ? 'text-sky-400' : ''}>{w.activeTasks} active</span>
                  <span className={w.overdueTasks > 0 ? 'text-red-400' : ''}>{w.overdueTasks} overdue</span>
                  <span>{w.totalPoints} pts</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Deadline Risks */}
      {risks && risks.length > 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" /> Deadline Risks
          </h4>
          <div className="space-y-1.5">
            {risks.slice(0, 8).map((r) => (
              <div key={r.taskId} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <span className={`h-2 w-2 rounded-full shrink-0 ${r.riskLevel === 'overdue' ? 'bg-red-500' : r.riskLevel === 'high' ? 'bg-amber-500' : r.riskLevel === 'medium' ? 'bg-yellow-500' : 'bg-slate-500'}`} />
                  <span className="text-slate-300 truncate">{r.title}</span>
                </div>
                <span className={`shrink-0 ml-2 ${r.riskLevel === 'overdue' ? 'text-red-400' : 'text-slate-500'}`}>
                  {r.daysRemaining < 0 ? `${Math.abs(r.daysRemaining)}d overdue` : `${r.daysRemaining}d left`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
      <div className="flex items-center gap-2 mb-1">
        <span className={color}>{icon}</span>
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-lg font-bold text-slate-100">{value}</p>
    </div>
  );
}
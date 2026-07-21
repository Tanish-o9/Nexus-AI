'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agileApi, type SprintReport } from '@/services/agile-api';
import { FileText, Download, FileSpreadsheet, Loader2, FileBarChart } from 'lucide-react';
import { toast } from 'sonner';

interface Props {
  projectId: string;
}

export function ReportsPanel({ projectId }: Props) {
  const queryClient = useQueryClient();
  const [generating, setGenerating] = useState<'weekly' | 'monthly' | null>(null);

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ['reports', projectId],
    queryFn: () => agileApi.listReports(projectId),
  });

  const weeklyMutation = useMutation({
    mutationFn: () => agileApi.generateWeeklyReport(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', projectId] });
      toast.success('Weekly report generated');
    },
    onError: (e: any) => toast.error(e.message),
  });

  const monthlyMutation = useMutation({
    mutationFn: () => agileApi.generateMonthlyReport(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', projectId] });
      toast.success('Monthly report generated');
    },
    onError: (e: any) => toast.error(e.message),
  });

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-violet-400" />
          <span className="text-sm font-semibold text-slate-200">Reports</span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => { weeklyMutation.mutate(); }}
            disabled={weeklyMutation.isPending}
            className="text-xs px-2.5 py-1 rounded bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600/30 disabled:opacity-50 transition-colors"
          >
            {weeklyMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Weekly'}
          </button>
          <button
            onClick={() => { monthlyMutation.mutate(); }}
            disabled={monthlyMutation.isPending}
            className="text-xs px-2.5 py-1 rounded bg-violet-600/20 text-violet-400 hover:bg-violet-600/30 disabled:opacity-50 transition-colors"
          >
            {monthlyMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Monthly'}
          </button>
        </div>
      </div>

      <div className="divide-y divide-slate-800/50 max-h-80 overflow-y-auto">
        {isLoading && <div className="py-6 text-center"><Loader2 className="h-5 w-5 animate-spin text-slate-500 mx-auto" /></div>}
        {!isLoading && reports.length === 0 && <div className="py-6 text-center text-xs text-slate-500">No reports yet. Generate one!</div>}
        {reports.map((r) => (
          <div key={r.id} className="flex items-center justify-between px-4 py-3 hover:bg-slate-800/20">
            <div className="flex items-center gap-3 min-w-0">
              <FileBarChart className="h-4 w-4 text-slate-500 shrink-0" />
              <div className="min-w-0">
                <p className="text-xs text-slate-200 capitalize truncate">{r.reportType} report</p>
                <p className="text-[10px] text-slate-500">{new Date(r.createdAt).toLocaleDateString()}</p>
              </div>
            </div>
            <div className="flex gap-1 shrink-0">
              <a
                href={agileApi.getExportCsvUrl(projectId, r.id)}
                download
                className="p-1.5 rounded text-slate-500 hover:text-emerald-400 hover:bg-slate-800 transition-colors"
                title="Download CSV"
              >
                <FileSpreadsheet className="h-3.5 w-3.5" />
              </a>
              <a
                href={agileApi.getExportExcelUrl(projectId, r.id)}
                download
                className="p-1.5 rounded text-slate-500 hover:text-indigo-400 hover:bg-slate-800 transition-colors"
                title="Download Excel"
              >
                <Download className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
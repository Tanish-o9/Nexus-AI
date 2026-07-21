'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { projectsApi, ActivityLogEntry, ActivityAction } from '@/services/projects-api';
import { Loader2, Activity, MessageSquare, Paperclip, UserPlus, UserMinus, Shield, CheckSquare, Plus, Edit3, Trash2, ArrowRight, GitCommit } from 'lucide-react';

interface ActivityTimelineProps {
  projectId: string;
  limit?: number;
}

const ACTION_CONFIG: Record<ActivityAction, { icon: React.ReactNode; color: string; bg: string }> = {
  created: { icon: <Plus className="h-3.5 w-3.5" />, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  updated: { icon: <Edit3 className="h-3.5 w-3.5" />, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
  deleted: { icon: <Trash2 className="h-3.5 w-3.5" />, color: 'text-red-400', bg: 'bg-red-500/10' },
  status_changed: { icon: <ArrowRight className="h-3.5 w-3.5" />, color: 'text-amber-400', bg: 'bg-amber-500/10' },
  assigned: { icon: <UserPlus className="h-3.5 w-3.5" />, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
  unassigned: { icon: <UserMinus className="h-3.5 w-3.5" />, color: 'text-slate-400', bg: 'bg-slate-500/10' },
  commented: { icon: <MessageSquare className="h-3.5 w-3.5" />, color: 'text-pink-400', bg: 'bg-pink-500/10' },
  attachment_added: { icon: <Paperclip className="h-3.5 w-3.5" />, color: 'text-violet-400', bg: 'bg-violet-500/10' },
  member_added: { icon: <UserPlus className="h-3.5 w-3.5" />, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  member_removed: { icon: <UserMinus className="h-3.5 w-3.5" />, color: 'text-red-400', bg: 'bg-red-500/10' },
  member_role_changed: { icon: <Shield className="h-3.5 w-3.5" />, color: 'text-amber-400', bg: 'bg-amber-500/10' },
};

function formatTimeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function ActivityTimeline({ projectId, limit = 30 }: ActivityTimelineProps) {
  const { data: activities = [], isLoading } = useQuery({
    queryKey: ['project-activity', projectId, limit],
    queryFn: () => projectsApi.listActivity(projectId, limit),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Activity className="h-4 w-4 text-indigo-400" />
        <h3 className="text-sm font-semibold text-slate-300">Activity Timeline</h3>
      </div>

      {/* Timeline */}
      <div className="relative pl-6">
        {/* Vertical line */}
        <div className="absolute left-2.5 top-2 bottom-2 w-px bg-slate-800" />

        {activities.length === 0 ? (
          <p className="text-sm text-slate-500 py-4 pl-2">No activity yet.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {activities.map((activity) => {
              const config = ACTION_CONFIG[activity.action] || ACTION_CONFIG.updated;
              return (
                <div key={activity.id} className="relative flex items-start gap-3 group">
                  {/* Dot */}
                  <div className={`absolute -left-[18px] top-1 w-5 h-5 rounded-full ${config.bg} flex items-center justify-center ring-2 ring-slate-950 ${config.color}`}>
                    {config.icon}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 bg-slate-900/20 border border-slate-800/50 rounded-lg p-3 hover:border-slate-700/50 transition-colors">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {activity.actor && (
                          <span className="font-semibold text-slate-200">{activity.actor.username}</span>
                        )}
                        {activity.description && (
                          <span className="text-slate-400"> {activity.description}</span>
                        )}
                      </p>
                      <span className="text-[10px] text-slate-600 whitespace-nowrap shrink-0">
                        {formatTimeAgo(activity.createdAt)}
                      </span>
                    </div>

                    {/* Show field changes if available */}
                    {activity.field_name && activity.old_value !== activity.new_value && (
                      <div className="mt-1.5 flex items-center gap-1.5 text-[10px] text-slate-500">
                        <span className="bg-slate-800 px-1.5 py-0.5 rounded">{activity.field_name}</span>
                        {activity.old_value && (
                          <>
                            <span className="line-through text-red-400/60">{activity.old_value}</span>
                            <ArrowRight className="h-2.5 w-2.5" />
                          </>
                        )}
                        <span className="text-emerald-400/80">{activity.new_value}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
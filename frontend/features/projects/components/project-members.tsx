'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, ProjectMember, ProjectMemberRole } from '@/services/projects-api';
import { organizationsApi } from '@/services/organizations-api';
import { authApi, AuthUser } from '@/services/auth-api';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { UserPlus, Shield, Trash2, Loader2, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface ProjectMembersProps {
  projectId: string;
}

const ROLE_OPTIONS: { value: ProjectMemberRole; label: string; color: string }[] = [
  { value: 'owner', label: 'Owner (Project Admin)', color: 'text-amber-400' },
  { value: 'manager', label: 'Product Manager', color: 'text-indigo-400' },
  { value: 'developer', label: 'Fullstack Developer', color: 'text-emerald-400' },
  { value: 'frontend', label: 'Frontend Engineer', color: 'text-cyan-400' },
  { value: 'backend', label: 'Backend Engineer', color: 'text-blue-400' },
  { value: 'devops', label: 'DevOps / SRE', color: 'text-orange-400' },
  { value: 'qa', label: 'QA / Test Engineer', color: 'text-violet-400' },
  { value: 'designer', label: 'UI/UX Designer', color: 'text-pink-400' },
  { value: 'data', label: 'Data / ML Engineer', color: 'text-teal-400' },
  { value: 'security', label: 'Security Engineer', color: 'text-red-400' },
  { value: 'writer', label: 'Technical Writer', color: 'text-yellow-400' },
  { value: 'viewer', label: 'Viewer / Read-only Guest', color: 'text-slate-400' },
];

export function ProjectMembers({ projectId }: ProjectMembersProps) {
  const queryClient = useQueryClient();
  const { activeOrgId } = useSelector((s: RootState) => s.org);
  const [showInvite, setShowInvite] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [customInput, setCustomInput] = useState('');
  const [selectedRole, setSelectedRole] = useState<ProjectMemberRole>('developer');

  // Queries
  const { data: members = [], isLoading } = useQuery({
    queryKey: ['project-members', projectId],
    queryFn: () => projectsApi.listMembers(projectId),
  });

  const { data: orgMembers = [] } = useQuery({
    queryKey: ['members', activeOrgId],
    queryFn: () => organizationsApi.listMembers(activeOrgId!),
    enabled: !!activeOrgId,
  });

  const { data: allUsers = [] } = useQuery<AuthUser[]>({
    queryKey: ['all-users'],
    queryFn: () => authApi.listUsers(),
  });

  // Get users not already in project
  const memberUserIds = new Set(members.map(m => m.user.id));

  // Combine org members and system users
  const candidateUsersMap = new Map<string, { id: string; username: string; email: string }>();
  orgMembers.forEach(om => {
    if (om.user && !memberUserIds.has(om.user.id)) {
      candidateUsersMap.set(om.user.id, om.user);
    }
  });
  allUsers.forEach(u => {
    if (u && !memberUserIds.has(u.id)) {
      candidateUsersMap.set(u.id, u);
    }
  });

  const candidateUsers = Array.from(candidateUsersMap.values());

  // Mutations
  const inviteMutation = useMutation({
    mutationFn: (payload: { userId?: string; email?: string; role: ProjectMemberRole }) =>
      projectsApi.inviteMember(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-members', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      queryClient.invalidateQueries({ queryKey: ['members', activeOrgId] });
      toast.success('Member added to project successfully');
      setShowInvite(false);
      setSelectedUserId('');
      setCustomInput('');
    },
    onError: (err: any) => toast.error(err.message || 'Failed to invite member'),
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ memberId, role }: { memberId: string; role: ProjectMemberRole }) =>
      projectsApi.updateMember(projectId, memberId, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-members', projectId] });
      toast.success('Role updated');
    },
    onError: (err: any) => toast.error(err.message || 'Failed to update role'),
  });

  const removeMutation = useMutation({
    mutationFn: (memberId: string) => projectsApi.removeMember(projectId, memberId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-members', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      toast.success('Member removed');
    },
    onError: (err: any) => toast.error(err.message || 'Failed to remove member'),
  });

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    const userId = selectedUserId || undefined;
    const email = customInput.trim() || undefined;

    if (!userId && !email) {
      toast.error('Please select a user or enter an email/username');
      return;
    }

    inviteMutation.mutate({ userId, email, role: selectedRole });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-100">
          Team Members ({members.length})
        </h3>
        <Button
          onClick={() => setShowInvite(!showInvite)}
          size="sm"
          className="bg-indigo-600 hover:bg-indigo-700 text-white"
        >
          <UserPlus className="h-4 w-4 mr-1" /> Invite
        </Button>
      </div>

      {/* Invite Form */}
      {showInvite && (
        <form onSubmit={handleInvite} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex flex-col gap-4">
          <p className="text-xs font-medium text-slate-400">
            Select a registered user or enter an email/username to add to project:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {candidateUsers.length > 0 ? (
              <select
                value={selectedUserId}
                onChange={(e) => {
                  setSelectedUserId(e.target.value);
                  if (e.target.value) setCustomInput('');
                }}
                className="bg-slate-900 border border-slate-800 text-slate-100 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500/50"
              >
                <option value="">Select a user ({candidateUsers.length} available)...</option>
                {candidateUsers.map(u => (
                  <option key={u.id} value={u.id}>
                    {u.username} ({u.email})
                  </option>
                ))}
              </select>
            ) : null}

            <div className="relative">
              <input
                type="text"
                placeholder={candidateUsers.length > 0 ? "Or enter email / username..." : "Enter user email or username..."}
                value={customInput}
                onChange={(e) => {
                  setCustomInput(e.target.value);
                  if (e.target.value) setSelectedUserId('');
                }}
                className="w-full bg-slate-900 border border-slate-800 text-slate-100 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500/50"
              />
            </div>

            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value as ProjectMemberRole)}
              className="bg-slate-900 border border-slate-800 text-slate-100 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500/50"
            >
              {ROLE_OPTIONS.map(r => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-2 justify-end">
            <Button type="button" size="sm" variant="outline" onClick={() => setShowInvite(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
              disabled={!selectedUserId && !customInput.trim()}
            >
              {inviteMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin text-white" /> : 'Send Invite'}
            </Button>
          </div>
        </form>
      )}

      {/* Members List */}
      <div className="flex flex-col gap-2">
        {members.map(member => {
          const roleInfo = ROLE_OPTIONS.find(r => r.value === member.role);
          return (
            <div
              key={member.id}
              className="flex items-center justify-between bg-slate-900/30 border border-slate-800 rounded-xl p-4 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-full bg-indigo-500/10 flex items-center justify-center text-sm font-bold text-indigo-400">
                  {member.user.username.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-200">{member.user.username}</p>
                  <p className="text-xs text-slate-500">{member.user.email}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {/* Role Badge / Selector */}
                <div className="flex items-center gap-1.5">
                  <Shield className={`h-3.5 w-3.5 ${roleInfo?.color || 'text-slate-400'}`} />
                  {member.role === 'owner' ? (
                    <span className={`text-xs font-semibold ${roleInfo?.color}`}>Owner</span>
                  ) : (
                    <select
                      value={member.role}
                      onChange={(e) => {
                        const newRole = e.target.value as ProjectMemberRole;
                        if (newRole !== member.role) {
                          updateRoleMutation.mutate({ memberId: member.id, role: newRole });
                        }
                      }}
                      className="bg-slate-900 border border-slate-800 text-slate-100 rounded px-2 py-1 text-xs outline-none focus:border-indigo-500/50"
                    >
                      {ROLE_OPTIONS.filter(r => r.value !== 'owner').map(r => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                  )}
                </div>

                {/* Remove Button */}
                {member.role !== 'owner' && (
                  <button
                    onClick={() => {
                      if (window.confirm(`Remove ${member.user.username} from the project?`)) {
                        removeMutation.mutate(member.id);
                      }
                    }}
                    className="p-1.5 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {members.length === 0 && (
          <p className="text-sm text-slate-500 text-center py-8">No members yet. Invite someone to get started.</p>
        )}
      </div>
    </div>
  );
}
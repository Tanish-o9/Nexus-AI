'use client';

import React, { useState } from 'react';
import { useOrganizations } from '@/features/organizations/hooks/use-organizations';
import { useDispatch, useSelector } from 'react-redux';
import { setActiveOrg } from '@/features/organizations/store/org-slice';
import { organizationsApi } from '@/services/organizations-api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { RootState } from '@/store';
import { Building2, Users, CheckCircle2, Plus, X, Loader2, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function OrganizationsPage() {
  const dispatch = useDispatch();
  const queryClient = useQueryClient();
  const activeOrgId = useSelector((s: RootState) => s.org.activeOrgId);
  const { data, isLoading, isError } = useOrganizations();

  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState('');

  const orgs = data?.results ?? [];

  const { mutate: createOrg, isPending } = useMutation({
    mutationFn: organizationsApi.create,
    onSuccess: (newOrg) => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
      toast.success('Organization created successfully');
      
      // Auto-activate the newly created org if no active org is set
      if (!activeOrgId) {
        dispatch(setActiveOrg(newOrg.id));
      }
      
      setName('');
      setIsOpen(false);
    },
    onError: (err: any) => {
      toast.error(err.message || 'Failed to create organization');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isPending) return;
    if (!name.trim()) {
      toast.error('Organization name is required');
      return;
    }
    createOrg(name.trim());
  };

  return (
    <div className="flex flex-col gap-6 p-8 relative min-h-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Organizations</h2>
          <p className="text-sm text-slate-400 mt-0.5">Switch context or manage your organizations</p>
        </div>
        <Button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-1.5 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white shadow-lg shadow-indigo-500/25"
        >
          <Plus className="h-4 w-4" />
          New Org
        </Button>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-slate-800/40 animate-pulse" />
          ))}
        </div>
      )}

      {isError && <p className="text-sm text-red-400">Failed to load organizations.</p>}

      {!isLoading && !isError && orgs.length === 0 && (
        <div className="flex flex-col items-center justify-center p-12 rounded-xl border border-dashed border-slate-800 bg-slate-900/10">
          <Building2 className="h-8 w-8 text-slate-600 mb-2" />
          <p className="text-sm text-slate-400">No organizations found.</p>
          <p className="text-xs text-slate-500 mt-1">Create one to start collaborating.</p>
        </div>
      )}

      {!isLoading && !isError && orgs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {orgs.map((org) => {
            const isActive = org.id === activeOrgId;
            return (
              <button
                key={org.id}
                onClick={() => dispatch(setActiveOrg(org.id))}
                className={`text-left rounded-xl border p-5 transition-all ${
                  isActive
                    ? 'border-indigo-500/40 bg-indigo-500/5'
                    : 'border-slate-800 bg-slate-900/30 hover:border-slate-700 hover:bg-slate-900/60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-lg bg-slate-800 flex items-center justify-center">
                      <Building2 className="h-4 w-4 text-indigo-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-100 text-sm">{org.name}</p>
                      <p className="text-xs text-slate-500">/{org.slug}</p>
                    </div>
                  </div>
                  {isActive && <CheckCircle2 className="h-4 w-4 text-indigo-400 shrink-0" />}
                </div>
                <div className="flex items-center gap-1.5 mt-3 text-xs text-slate-500">
                  <Users className="h-3 w-3" /> {org.memberCount} members
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Members Management Panel */}
      {activeOrgId && <MembersPanel orgId={activeOrgId} />}

      {/* Creation Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <h2 className="text-lg font-bold text-slate-100">Create Organization</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-semibold text-slate-300">Organization Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Acme Corp"
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none transition-colors"
                  disabled={isPending}
                  required
                />
              </div>

              <div className="flex justify-end gap-3 mt-4 border-t border-slate-800 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsOpen(false)}
                  disabled={isPending}
                  className="border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-white"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isPending}
                  className="bg-indigo-500 hover:bg-indigo-600 text-white min-w-[80px]"
                >
                  {isPending ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : 'Create'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ── MembersPanel Subcomponent ────────────────────────────────────────────────
import { useQuery } from '@tanstack/react-query';

function MembersPanel({ orgId }: { orgId: string }) {
  const queryClient = useQueryClient();
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [selectedMemberActivity, setSelectedMemberActivity] = useState<string | null>(null);
  const [newSkillText, setNewSkillText] = useState<{ [membershipId: string]: string }>({});

  const { data: members = [], isLoading, isError } = useQuery({
    queryKey: ['members', orgId],
    queryFn: () => organizationsApi.listMembers(orgId),
  });

  const inviteMutation = useMutation({
    mutationFn: () => organizationsApi.inviteMember(orgId, inviteEmail, inviteRole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', orgId] });
      toast.success('Member invited successfully');
      setInviteEmail('');
    },
    onError: (err: any) => toast.error(err.message || 'Invitation failed'),
  });

  const removeMutation = useMutation({
    mutationFn: (memId: string) => organizationsApi.removeMember(orgId, memId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', orgId] });
      toast.success('Member removed');
    },
    onError: (err: any) => toast.error(err.message || 'Failed to remove member'),
  });

  const roleMutation = useMutation({
    mutationFn: ({ memId, role }: { memId: string; role: string }) =>
      organizationsApi.updateMemberRole(orgId, memId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', orgId] });
      toast.success('Role updated');
    },
  });

  const skillsMutation = useMutation({
    mutationFn: ({ memId, skills }: { memId: string; skills: string[] }) =>
      organizationsApi.updateMemberSkills(orgId, memId, skills),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', orgId] });
      toast.success('Skills updated');
    },
  });

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    inviteMutation.mutate();
  };

  const handleAddSkill = (memId: string, currentSkills: string[]) => {
    const text = newSkillText[memId]?.trim();
    if (!text) return;
    const newSkills = [...(currentSkills || []), text];
    skillsMutation.mutate({ memId, skills: newSkills });
    setNewSkillText(prev => ({ ...prev, [memId]: '' }));
  };

  return (
    <div className="mt-8 border-t border-slate-800 pt-8 flex flex-col gap-6">
      <div className="flex justify-between items-start flex-wrap gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Users className="h-5 w-5 text-indigo-400" /> Members & Access
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Manage collaborator roles, skills, and activities</p>
        </div>

        {/* Invite Form */}
        <form onSubmit={handleInvite} className="flex items-center gap-2 bg-slate-900/60 border border-slate-800 p-2 rounded-lg max-w-md w-full">
          <input
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="colleague@domain.com"
            className="bg-transparent text-slate-100 placeholder-slate-500 text-xs px-2.5 py-1 w-full outline-none"
            required
          />
          <select
            value={inviteRole}
            onChange={(e) => setInviteRole(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-slate-300 text-xs rounded px-2 py-1 outline-none cursor-pointer"
          >
            <option value="viewer">Viewer</option>
            <option value="member">Member</option>
            <option value="admin">Admin</option>
          </select>
          <Button type="submit" size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shrink-0 h-7 text-xs">
            Invite
          </Button>
        </form>
      </div>

      {isLoading ? (
        <div className="text-slate-500 text-xs">Loading members...</div>
      ) : isError ? (
        <div className="text-red-400 text-xs">Failed to load members.</div>
      ) : (
        <div className="flex flex-col gap-3">
          {members.map(member => (
            <div key={member.id} className="border border-slate-850 bg-slate-900/10 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-slate-200">{member.user.username}</span>
                  <span className="text-[10px] text-slate-500">({member.user.email})</span>
                </div>

                {/* Skills tags list */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  {member.skills?.map((skill, index) => (
                    <span key={index} className="text-[9px] font-bold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded-full">
                      {skill}
                    </span>
                  ))}
                  
                  {/* Inline Add Skill */}
                  <div className="flex items-center gap-1">
                    <input
                      type="text"
                      value={newSkillText[member.id] || ''}
                      onChange={(e) => setNewSkillText(prev => ({ ...prev, [member.id]: e.target.value }))}
                      placeholder="+ Add skill"
                      className="bg-slate-950 border border-slate-800 text-[10px] rounded-full px-2 py-0.5 text-slate-300 placeholder-slate-600 w-16 outline-none"
                    />
                    {(newSkillText[member.id] || '').trim() && (
                      <button
                        onClick={() => handleAddSkill(member.id, member.skills)}
                        className="text-xs text-indigo-400 font-bold hover:text-indigo-300"
                      >
                        ✓
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Actions & Role Select */}
              <div className="flex items-center gap-3">
                <select
                  value={member.role}
                  onChange={(e) => roleMutation.mutate({ memId: member.id, role: e.target.value })}
                  className="bg-slate-950 border border-slate-850 text-slate-300 text-xs rounded px-2.5 py-1 outline-none"
                >
                  <option value="viewer">Viewer</option>
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                  <option value="owner">Owner</option>
                </select>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedMemberActivity(member.id)}
                  className="border-slate-800 text-slate-400 hover:text-slate-200 text-xs py-1 h-7"
                >
                  Activity Log
                </Button>

                <button
                  onClick={() => removeMutation.mutate(member.id)}
                  className="p-1 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Activity Sidebar Modal */}
      {selectedMemberActivity && (
        <ActivityLogModal
          orgId={orgId}
          membershipId={selectedMemberActivity}
          onClose={() => setSelectedMemberActivity(null)}
        />
      )}
    </div>
  );
}

function ActivityLogModal({ orgId, membershipId, onClose }: { orgId: string; membershipId: string; onClose: () => void }) {
  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['activity', orgId, membershipId],
    queryFn: () => organizationsApi.listMemberActivity(orgId, membershipId),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md shadow-2xl p-6 flex flex-col gap-4 max-h-[80vh]">
        <div className="flex justify-between items-center border-b border-slate-800 pb-3">
          <h4 className="font-bold text-slate-100 text-sm">Recent Activity Log</h4>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-200">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex flex-col gap-3 overflow-y-auto flex-1 pr-1">
          {isLoading ? (
            <div className="text-slate-500 text-xs">Loading activity stream...</div>
          ) : logs.length === 0 ? (
            <div className="text-slate-500 text-xs text-center py-8">No recent actions logged.</div>
          ) : (
            logs.map(log => (
              <div key={log.id} className="text-xs bg-slate-950/20 border border-slate-850 p-2.5 rounded text-slate-300">
                <span className="font-semibold text-indigo-400 uppercase tracking-wide block text-[9px] mb-1">{log.action}</span>
                <span className="text-slate-400">{log.resourceType} : {log.resourceId}</span>
                <span className="block text-[10px] text-slate-500 mt-1">{new Date(log.createdAt).toLocaleString()}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

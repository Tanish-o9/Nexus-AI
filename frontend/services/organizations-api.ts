import { apiFetch } from '@/services/api-fetch';

export interface Organization {
  id: string;
  name: string;
  slug: string;
  memberCount: number;
  createdAt: string;
}

export interface Membership {
  id: string;
  user: { id: string; username: string; email: string };
  organization: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  isActive: boolean;
  skills: string[];
  joinedAt: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const organizationsApi = {
  list: () =>
    apiFetch<PaginatedResponse<Organization>>('/api/organizations/'),

  get: (id: string) =>
    apiFetch<Organization>(`/api/organizations/${id}/`),

  create: (name: string) =>
    apiFetch<Organization>('/api/organizations/', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),

  listMembers: (orgId: string) =>
    apiFetch<Membership[]>(`/api/organizations/${orgId}/members/`),

  inviteMember: (orgId: string, email: string, role: string) =>
    apiFetch<Membership>(`/api/organizations/${orgId}/members/invite/`, {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    }),

  removeMember: (orgId: string, membershipId: string) =>
    apiFetch<void>(`/api/organizations/${orgId}/members/${membershipId}/`, {
      method: 'DELETE',
    }),

  updateMemberRole: (orgId: string, membershipId: string, role: string) =>
    apiFetch<Membership>(`/api/organizations/${orgId}/members/${membershipId}/role/`, {
      method: 'PATCH',
      body: JSON.stringify({ role }),
    }),

  updateMemberSkills: (orgId: string, membershipId: string, skills: string[]) =>
    apiFetch<Membership>(`/api/organizations/${orgId}/members/${membershipId}/update/`, {
      method: 'PATCH',
      body: JSON.stringify({ skills }),
    }),

  listMemberActivity: (orgId: string, membershipId: string) =>
    apiFetch<any[]>(`/api/organizations/${orgId}/members/${membershipId}/activity/`),
};

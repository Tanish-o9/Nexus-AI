// Relative URL — proxied to backend via Next.js rewrites in next.config.ts
const API_BASE = '';

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  organizationId: string | null;
  totpEnabled?: boolean;
}

export interface AuthResponse {
  user: AuthUser;
  token: string;
  refreshToken: string;
  sessionId: string;
}

export interface TwoFactorRequiredResponse {
  requires2FA: true;
  tempToken: string;
}

export interface LoginResult extends AuthResponse {
  requires2FA?: false;
}

export interface UserSession {
  id: string;
  ipAddress: string | null;
  userAgent: string;
  createdAt: string;
  lastActive: string;
  isCurrent: boolean;
}

export interface TwoFactorSetupResponse {
  secret: string;
  uri: string;
}

export interface MessageResponse {
  message: string;
}

async function post<T>(path: string, body: unknown, token?: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.detail ?? data?.message ?? 'Request failed');
  return data as T;
}

async function del(path: string, token: string): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok && res.status !== 204) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data?.detail ?? 'Request failed');
  }
}

export const authApi = {
  login: (payload: LoginPayload) =>
    post<LoginResult | TwoFactorRequiredResponse>('/api/auth/login/', payload),

  register: (payload: RegisterPayload) =>
    post<AuthResponse>('/api/auth/register/', payload),

  logout: (refreshToken: string, token?: string) =>
    post<void>('/api/auth/logout/', { refreshToken }, token),

  refreshToken: (refresh: string) =>
    post<{ access: string; refresh?: string }>('/api/auth/token/refresh/', { refresh }),

  forgotPassword: (email: string) =>
    post<MessageResponse>('/api/auth/forgot-password/', { email }),

  verify2FA: (tempToken: string, code: string) =>
    post<AuthResponse>('/api/auth/2fa/verify/', { tempToken, code }),

  setup2FA: (token: string) =>
    post<TwoFactorSetupResponse>('/api/auth/2fa/setup/', {}, token),

  confirm2FA: (code: string, token: string) =>
    post<MessageResponse>('/api/auth/2fa/confirm/', { code }, token),

  disable2FA: (code: string, password: string, token: string) =>
    post<MessageResponse>('/api/auth/2fa/disable/', { code, password }, token),

  listSessions: (token: string, currentSessionId?: string) =>
    fetch(
      `${API_BASE}/api/auth/sessions/${currentSessionId ? `?current=${currentSessionId}` : ''}`,
      { headers: { Authorization: `Bearer ${token}` } },
    ).then(async (res) => {
      if (!res.ok) throw new Error('Failed to load sessions');
      return res.json() as Promise<UserSession[]>;
    }),

  revokeSession: (sessionId: string, token: string) =>
    del(`/api/auth/sessions/${sessionId}/`, token),

  revokeAllSessions: (token: string, keepCurrent?: string) =>
    post<{ revoked: number }>('/api/auth/sessions/revoke-all/', { keepCurrent }, token),

  listUsers: (query?: string) =>
    fetch(`${API_BASE}/api/auth/users/${query ? `?q=${encodeURIComponent(query)}` : ''}`).then((res) =>
      res.ok ? (res.json() as Promise<AuthUser[]>) : []
    ),
};

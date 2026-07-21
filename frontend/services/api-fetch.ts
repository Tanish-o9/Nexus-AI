import { store } from '@/store';
import { logout, setCredentials } from '@/features/auth/store/auth-slice';

const API_BASE = '';

let refreshPromise: Promise<string | null> | null = null;

async function tryRefreshToken(): Promise<string | null> {
  const { refreshToken } = store.getState().auth;
  if (!refreshToken) return null;

  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE}/api/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    })
      .then(async (res) => {
        if (!res.ok) return null;
        const data = await res.json();
        const state = store.getState().auth;
        store.dispatch(setCredentials({
          user: state.user!,
          token: data.access,
          refreshToken: data.refresh ?? state.refreshToken,
          sessionId: state.sessionId,
        }));
        return data.access as string;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = store.getState().auth.token;

  const doFetch = (bearer?: string) =>
    fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
        ...options.headers,
      },
    });

  let res = await doFetch(token ?? undefined);

  if (res.status === 401 && store.getState().auth.refreshToken) {
    const newToken = await tryRefreshToken();
    if (newToken) {
      res = await doFetch(newToken);
    }
  }

  if (res.status === 401) {
    store.dispatch(logout());
    throw new Error('Session expired. Please log in again.');
  }

  if (!res.ok) {
    let errorDetail = 'Request failed';
    try {
      const errorData = await res.json();
      errorDetail = errorData?.detail ?? errorData?.message ?? errorDetail;
    } catch {
      // Ignore JSON parse errors for non-JSON error responses
    }
    throw new Error(errorDetail);
  }

  if (res.status === 204) {
    return null as T;
  }

  const text = await res.text();
  if (!text || !text.trim()) {
    return null as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    return null as T;
  }
}

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  organizationId: string | null;
  totpEnabled?: boolean;
}

export interface AuthState {
  user: UserProfile | null;
  token: string | null;
  refreshToken: string | null;
  sessionId: string | null;
  isAuthenticated: boolean;
  isHydrated: boolean;
}

const initialState: AuthState = {
  user: null,
  token: null,
  refreshToken: null,
  sessionId: null,
  isAuthenticated: false,
  isHydrated: false,
};

function saveState(state: AuthState) {
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem('auth', JSON.stringify({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        sessionId: state.sessionId,
        isAuthenticated: state.isAuthenticated,
      }));
    } catch {
      // ignore
    }
  }
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    hydrate: (state) => {
      if (typeof window !== 'undefined') {
        try {
          const saved = localStorage.getItem('auth');
          if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed.token) {
              state.user = parsed.user ?? null;
              state.token = parsed.token;
              state.refreshToken = parsed.refreshToken ?? null;
              state.sessionId = parsed.sessionId ?? null;
              state.isAuthenticated = true;
            }
          }
        } catch {
          // ignore
        }
      }
      state.isHydrated = true;
    },
    setCredentials: (
      state,
      action: PayloadAction<{
        user: UserProfile;
        token: string;
        refreshToken: string;
        sessionId?: string | null;
      }>
    ) => {
      const { user, token, refreshToken, sessionId } = action.payload;
      state.user = user;
      state.token = token;
      state.refreshToken = refreshToken;
      state.sessionId = sessionId ?? state.sessionId;
      state.isAuthenticated = true;
      state.isHydrated = true;
      saveState(state);
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.sessionId = null;
      state.isAuthenticated = false;
      state.isHydrated = true;
      saveState(state);
    },
  },
});

export const { hydrate, setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;

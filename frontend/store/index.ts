import { configureStore } from '@reduxjs/toolkit';
import authReducer from '@/features/auth/store/auth-slice';
import orgReducer from '@/features/organizations/store/org-slice';
import notificationsReducer from '@/features/notifications/store/notifications-slice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    org: orgReducer,
    notifications: notificationsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

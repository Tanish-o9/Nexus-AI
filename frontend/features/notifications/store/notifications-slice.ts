import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface AppNotification {
  id: string;
  type: 'task_assigned' | 'mention' | 'agent_completed' | 'project_update';
  title: string;
  body: string;
  read: boolean;
  createdAt: string;
}

interface NotificationsState {
  items: AppNotification[];
}

const initialState: NotificationsState = { items: [] };

const notificationsSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    addNotification: (state, action: PayloadAction<AppNotification>) => {
      // Prepend so newest is first; cap at 50
      state.items = [action.payload, ...state.items].slice(0, 50);
    },
    markRead: (state, action: PayloadAction<string>) => {
      const n = state.items.find((i) => i.id === action.payload);
      if (n) n.read = true;
    },
    markAllRead: (state) => {
      state.items.forEach((n) => { n.read = true; });
    },
    clearNotifications: (state) => {
      state.items = [];
    },
  },
});

export const { addNotification, markRead, markAllRead, clearNotifications } =
  notificationsSlice.actions;
export default notificationsSlice.reducer;

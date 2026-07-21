'use client';

import { useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { io, type Socket } from 'socket.io-client';
import { store } from '@/store';
import { addNotification, type AppNotification } from '@/features/notifications/store/notifications-slice';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? 'http://localhost:8000';

export function useNotifications() {
  const dispatch = useDispatch();
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Don't reconnect if already connected
    if (socketRef.current?.connected) return;

    const token = store.getState().auth.token;

    const socket = io(WS_URL, {
      path: '/ws/socket.io',
      auth: { token },
      transports: ['websocket'],
      reconnectionAttempts: 5,
      reconnectionDelay: 2000,
    });

    socketRef.current = socket;

    socket.on('notification', (payload: AppNotification) => {
      dispatch(addNotification(payload));
    });

    socket.on('connect_error', (err) => {
      console.warn('[Socket] connection error:', err.message);
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}

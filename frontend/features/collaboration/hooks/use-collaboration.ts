'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { io, type Socket } from 'socket.io-client';
import { store } from '@/store';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? 'http://localhost:8000';

export interface WsChatMessage {
  id: string;
  authorId: string;
  authorUsername: string;
  authorEmail: string;
  content: string;
  mentionIds: string[];
  createdAt: string;
}

export interface WsPresence {
  userId: string;
  username: string;
  isOnline: boolean;
}

interface UseCollaborationOptions {
  projectId: string;
  enabled?: boolean;
}

export function useCollaboration({ projectId, enabled = true }: UseCollaborationOptions) {
  const socketRef = useRef<Socket | null>(null);
  const [messages, setMessages] = useState<WsChatMessage[]>([]);
  const [presence, setPresence] = useState<Map<string, WsPresence>>(new Map());
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!enabled || !projectId) return;

    const token = store.getState().auth.token;
    const socket = io(WS_URL, {
      path: '/ws/socket.io',
      auth: { token },
      transports: ['websocket'],
      reconnectionAttempts: 5,
      reconnectionDelay: 2000,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      setConnected(true);
      // Join the chat room for this project
      socket.emit('join', { projectId });
    });

    socket.on('disconnect', () => setConnected(false));
    socket.on('connect_error', (err) => console.warn('[Collab WS]', err.message));

    socket.on('message', (msg: WsChatMessage) => {
      setMessages((prev) => [msg, ...prev]);
    });

    socket.on('presence', (p: WsPresence) => {
      setPresence((prev) => new Map(prev).set(p.userId, p));
    });

    socket.on('typing', (data: { userId: string; isTyping: boolean }) => {
      setTypingUsers((prev) => {
        const next = new Set(prev);
        if (data.isTyping) next.add(data.userId);
        else next.delete(data.userId);
        return next;
      });
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
      setConnected(false);
    };
  }, [projectId, enabled]);

  const sendMessage = useCallback((content: string, mentionIds?: string[]) => {
    const socket = socketRef.current;
    if (!socket) return;
    socket.emit('message', { content, mentionIds: mentionIds ?? [] });
  }, []);

  const sendTyping = useCallback((isTyping: boolean) => {
    socketRef.current?.emit('typing', { isTyping });
  }, []);

  return {
    messages,
    presence,
    typingUsers,
    connected,
    sendMessage,
    sendTyping,
  };
}
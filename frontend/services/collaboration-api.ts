import { apiFetch } from '@/services/api-fetch';

export interface UserBrief {
  id: string;
  username: string;
  email: string;
}

export interface ChatReaction {
  id: string;
  emoji: string;
  user: UserBrief;
  userId: string;
  createdAt: string;
}

export interface ChatAttachment {
  id: string;
  fileName: string;
  fileUrl: string;
  fileSize: number;
  mimeType: string;
  uploadedBy: UserBrief;
  createdAt: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  author: UserBrief;
  reactions: ChatReaction[];
  attachments: ChatAttachment[];
  replyToId: string | null;
  createdAt: string;
}

export interface ActivityFeedItem {
  id: string;
  actor: UserBrief | null;
  activityType: string;
  description: string;
  metadata: Record<string, any>;
  createdAt: string;
}

export interface UserPresence {
  userId: string;
  username: string;
  isOnline: boolean;
  lastSeen: string;
}

export const collaborationApi = {
  // Chat
  listMessages: (projectId: string) =>
    apiFetch<ChatMessage[]>(`/api/collab/${projectId}/chat/`),

  sendMessage: (projectId: string, payload: { content: string; replyToId?: string | null; mentionIds?: string[] }) =>
    apiFetch<ChatMessage>(`/api/collab/${projectId}/chat/send/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  toggleReaction: (projectId: string, msgId: string, emoji: string) =>
    apiFetch<ChatReaction>(`/api/collab/${projectId}/chat/${msgId}/react/`, {
      method: 'POST',
      body: JSON.stringify({ emoji }),
    }),

  uploadAttachment: (projectId: string, msgId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiFetch<ChatAttachment>(`/api/collab/${projectId}/chat/${msgId}/attach/`, {
      method: 'POST',
      body: formData,
      headers: {}, // Let fetch set Content-Type for FormData
    });
  },

  // Activity feed
  listActivity: (projectId: string) =>
    apiFetch<ActivityFeedItem[]>(`/api/collab/${projectId}/activity/`),

  // Presence
  listPresence: (projectId: string) =>
    apiFetch<UserPresence[]>(`/api/collab/${projectId}/presence/`),
};
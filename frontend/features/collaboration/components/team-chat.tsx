'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSelector } from 'react-redux';
import { collaborationApi, type ChatMessage, type ChatReaction } from '@/services/collaboration-api';
import { RootState } from '@/store';
import { useCollaboration } from '@/features/collaboration/hooks/use-collaboration';
import { MessageSquare, Send, Smile, Paperclip, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const EMOJIS = ['👍', '❤️', '😄', '🎉', '🚀', '👀'];

interface Props {
  projectId: string;
}

export function TeamChat({ projectId }: Props) {
  const queryClient = useQueryClient();
  const userId = useSelector((s: RootState) => s.auth.user?.id);
  const [input, setInput] = useState('');
  const [showEmoji, setShowEmoji] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const typingTimeout = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // REST history (initial load & mutations)
  const { data: history = [], isLoading } = useQuery({
    queryKey: ['chat', projectId],
    queryFn: () => collaborationApi.listMessages(projectId),
  });

  // WebSocket real-time
  const { messages: wsMessages, connected, sendMessage, sendTyping } = useCollaboration({ projectId });

  // Merge: REST history + WS messages (dedup by id)
  const allMessages = [...history];
  for (const wsMsg of wsMessages) {
    if (!allMessages.some((m) => m.id === wsMsg.id)) {
      allMessages.unshift({
        id: wsMsg.id,
        content: wsMsg.content,
        author: { id: wsMsg.authorId, username: wsMsg.authorUsername, email: wsMsg.authorEmail },
        reactions: [],
        attachments: [],
        replyToId: null,
        createdAt: wsMsg.createdAt,
      });
    }
  }
  allMessages.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

  // Mutation fallback (when WS is disconnected)
  const sendMutation = useMutation({
    mutationFn: (content: string) => collaborationApi.sendMessage(projectId, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', projectId] });
      queryClient.invalidateQueries({ queryKey: ['activity', projectId] });
    },
  });

  const handleSend = useCallback(() => {
    const text = input.trim();
    if (!text) return;
    if (connected) {
      sendMessage(text);
    } else {
      sendMutation.mutate(text);
    }
    setInput('');
  }, [input, connected, sendMessage, sendMutation]);

  const handleInputChange = useCallback((value: string) => {
    setInput(value);
    if (connected) {
      sendTyping(true);
      clearTimeout(typingTimeout.current);
      typingTimeout.current = setTimeout(() => sendTyping(false), 1500);
    }
  }, [connected, sendTyping]);

  // Reaction toggle
  const reactMutation = useMutation({
    mutationFn: ({ msgId, emoji }: { msgId: string; emoji: string }) =>
      collaborationApi.toggleReaction(projectId, msgId, emoji),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['chat', projectId] }),
  });

  return (
    <div className="flex flex-col h-full rounded-xl border border-slate-800 bg-slate-900/30 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800 shrink-0">
        <MessageSquare className="h-4 w-4 text-indigo-400" />
        <span className="text-sm font-semibold text-slate-200">Team Chat</span>
        <span className={`ml-auto h-2 w-2 rounded-full ${connected ? 'bg-emerald-400' : 'bg-slate-600'}`} />
      </div>

      {/* Messages */}
      <div ref={listRef} className="flex-1 overflow-y-auto p-3 space-y-2">
        {isLoading && (
          <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-slate-500" /></div>
        )}
        {!isLoading && allMessages.length === 0 && (
          <div className="py-8 text-center text-sm text-slate-500">No messages yet. Start the conversation!</div>
        )}
        {allMessages.map((msg) => (
          <div key={msg.id} className={`group flex gap-2 ${msg.author.id === userId ? 'flex-row-reverse' : ''}`}>
            <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
              msg.author.id === userId
                ? 'bg-indigo-600/20 text-indigo-200'
                : 'bg-slate-800/50 text-slate-300'
            }`}>
              <p className="text-[10px] font-semibold text-slate-500 mb-0.5">
                {msg.author.id === userId ? 'You' : msg.author.username}
              </p>
              <p className="leading-relaxed">{msg.content}</p>
              {/* Reactions */}
              <div className="flex items-center gap-1 mt-1.5">
                {msg.reactions.map((r) => (
                  <button
                    key={`${r.id}-${r.emoji}`}
                    onClick={() => reactMutation.mutate({ msgId: msg.id, emoji: r.emoji })}
                    className={`text-xs px-1.5 py-0.5 rounded-full border transition-colors ${
                      r.userId === userId
                        ? 'bg-indigo-500/20 border-indigo-500/30 text-indigo-300'
                        : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    {r.emoji}
                  </button>
                ))}
                {/* Reaction button */}
                <div className="relative">
                  <button
                    onClick={() => setShowEmoji(showEmoji === msg.id ? null : msg.id)}
                    className="opacity-0 group-hover:opacity-100 text-xs p-0.5 rounded text-slate-500 hover:text-slate-300 transition-all"
                  >
                    <Smile className="h-3.5 w-3.5" />
                  </button>
                  {showEmoji === msg.id && (
                    <div className="absolute bottom-6 left-0 flex gap-1 bg-slate-800 border border-slate-700 rounded-lg p-1.5 z-10 shadow-xl">
                      {EMOJIS.map((e) => (
                        <button
                          key={e}
                          onClick={() => { reactMutation.mutate({ msgId: msg.id, emoji: e }); setShowEmoji(null); }}
                          className="text-lg hover:scale-125 transition-transform"
                        >
                          {e}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <p className="text-[10px] text-slate-600 mt-1">
                {new Date(msg.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-slate-800 shrink-0">
        <div className="flex gap-2 items-center bg-slate-800/50 rounded-lg px-3 py-2">
          <input
            type="text"
            value={input}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Type a message... (use @name to mention)"
            className="flex-1 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sendMutation.isPending}
            className="p-1.5 rounded-lg text-indigo-400 hover:bg-indigo-500/20 disabled:text-slate-600 transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
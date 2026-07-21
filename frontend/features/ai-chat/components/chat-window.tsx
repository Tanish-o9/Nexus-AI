'use client';

import { useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';
import { useChatStream } from '@/features/ai-chat/hooks/use-chat-stream';
import { ChatMessage } from './chat-message';
import { ChatInput } from './chat-input';

export function ChatWindow() {
  const { messages, isStreaming, sendMessage, cancelStream, clearMessages } = useChatStream();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom whenever messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-slate-800 shrink-0">
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow shadow-emerald-400/50 animate-pulse" />
          <span className="text-sm font-semibold text-slate-300">Nexus AI Assistant Engine Online</span>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            Clear chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-6">
        {messages.length === 0 && <EmptyState />}
        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-6 pb-6 pt-3 border-t border-slate-800 shrink-0">
        <ChatInput
          onSend={sendMessage}
          onCancel={cancelStream}
          isStreaming={isStreaming}
        />
      </div>
    </div>
  );
}

function EmptyState() {
  const SUGGESTIONS = [
    'Who completed tasks in project Lol?',
    'Summarize the status of all active projects',
    'Which tasks are overdue or in review?',
    'What are the top risks across my portfolio?',
  ];

  return (
    <div className="flex flex-col items-center justify-center flex-1 gap-6 text-center py-12">
      <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-indigo-500 via-violet-500 to-purple-600 flex items-center justify-center shadow-xl shadow-indigo-500/30 animate-float-3d">
        <Sparkles className="h-8 w-8 text-white" />
      </div>
      <div>
        <h3 className="text-xl font-extrabold text-slate-100">Ask Nexus AI Assistant</h3>
        <p className="text-sm text-slate-400 mt-1">Your intelligent enterprise project management co-pilot</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
        {SUGGESTIONS.map((s) => (
          <div
            key={s}
            className="rounded-lg border border-slate-800 bg-slate-900/30 px-3 py-2.5 text-xs text-slate-400 text-left hover:border-indigo-500/30 hover:text-slate-300 transition-all cursor-default"
          >
            {s}
          </div>
        ))}
      </div>
    </div>
  );
}

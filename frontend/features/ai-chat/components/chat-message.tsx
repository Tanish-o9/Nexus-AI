import { ExternalLink, FileText, Sparkles, User } from 'lucide-react';
import type { Message } from '@/features/ai-chat/types';

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`h-8 w-8 rounded-full shrink-0 flex items-center justify-center ${
        isUser
          ? 'bg-indigo-500/20 text-indigo-400'
          : 'bg-gradient-to-tr from-indigo-500 to-violet-500 text-white shadow shadow-indigo-500/20'
      }`}>
        {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
      </div>

      <div className={`flex flex-col gap-2 max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* File attachment badge */}
        {message.fileRef && (
          <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded-full border border-slate-700">
            <FileText className="h-3 w-3" />
            {message.fileRef}
          </div>
        )}

        {/* Bubble */}
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-indigo-500/20 text-slate-100 border border-indigo-500/30 rounded-tr-sm shadow-md'
            : 'glass-card-3d bg-slate-900/80 text-slate-200 border border-slate-800/80 rounded-tl-sm shadow-xl'
        }`}>
          {!message.content && message.isStreaming ? (
            <div className="flex items-center gap-3 py-1 px-1">
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-indigo-400 animate-bounce shadow shadow-indigo-400/80" style={{ animationDelay: '0ms' }} />
                <span className="h-2.5 w-2.5 rounded-full bg-violet-400 animate-bounce shadow shadow-violet-400/80" style={{ animationDelay: '150ms' }} />
                <span className="h-2.5 w-2.5 rounded-full bg-purple-400 animate-bounce shadow shadow-purple-400/80" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-xs font-semibold text-indigo-300 tracking-wide animate-pulse">Nexus AI is thinking & typing...</span>
            </div>
          ) : (
            <>
              {message.content}
              {message.isStreaming && (
                <span className="inline-block w-2 h-4 bg-gradient-to-b from-indigo-400 to-violet-400 ml-1.5 animate-pulse rounded-sm align-middle shadow shadow-indigo-400/80" />
              )}
            </>
          )}
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="flex flex-col gap-2 w-full mt-1">
            <p className="text-xs text-slate-500 font-medium">Sources</p>
            {message.citations.map((c) => (
              <div
                key={c.id}
                className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-3 text-xs"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-medium text-slate-300 line-clamp-1">{c.title}</span>
                  <a
                    href={c.source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-400 hover:text-indigo-300 shrink-0 transition-colors"
                  >
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
                <p className="text-slate-500 line-clamp-2">{c.excerpt}</p>
              </div>
            ))}
          </div>
        )}

        <span className="text-xs text-slate-600">
          {message.createdAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}

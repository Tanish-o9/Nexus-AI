'use client';

import { useState, useRef, type KeyboardEvent } from 'react';
import { Paperclip, Send, Square, X, Sparkles, CornerDownLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  onSend: (content: string, fileRef?: string) => void;
  onCancel: () => void;
  isStreaming: boolean;
}

const QUICK_CHIPS = [
  'Who completed tasks in project Lol?',
  'Summarize active project status',
  'What are the top sprint risks?',
  'Generate task breakdown',
];

export function ChatInput({ onSend, onCancel, isStreaming }: Props) {
  const [text, setText] = useState('');
  const [attachedFile, setAttachedFile] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleSend(overrideContent?: string) {
    const contentToSend = (overrideContent || text).trim();
    if (!contentToSend || isStreaming) return;
    onSend(contentToSend, attachedFile ?? undefined);
    setText('');
    setAttachedFile(null);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) setAttachedFile(file.name);
    e.target.value = '';
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Quick Prompt Chips */}
      {!text && !attachedFile && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
          <span className="text-[11px] font-medium text-slate-500 shrink-0 flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-indigo-400" />
            Quick Prompts:
          </span>
          {QUICK_CHIPS.map((chip) => (
            <button
              key={chip}
              onClick={() => handleSend(chip)}
              disabled={isStreaming}
              className="text-xs text-slate-300 bg-slate-900/60 hover:bg-indigo-600/20 border border-slate-800 hover:border-indigo-500/40 px-3 py-1 rounded-full transition-all shrink-0 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50"
            >
              {chip}
            </button>
          ))}
        </div>
      )}

      {/* File attachment badge */}
      {attachedFile && (
        <div className="flex items-center gap-2 self-start text-xs text-indigo-300 bg-indigo-950/60 px-3 py-1.5 rounded-full border border-indigo-500/30 shadow-md">
          <Paperclip className="h-3.5 w-3.5 text-indigo-400" />
          <span className="max-w-60 truncate font-medium">{attachedFile}</span>
          <button onClick={() => setAttachedFile(null)} className="text-slate-400 hover:text-white transition-colors ml-1">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* 3D Glassmorphic Command Input Container */}
      <div className="relative glass-card-3d rounded-2xl p-2.5 flex items-end gap-2.5 transition-all duration-300 focus-within:border-indigo-500/60 focus-within:shadow-[0_0_30px_rgba(99,102,241,0.35)]">
        {/* File attach button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isStreaming}
          title="Attach document / reference file"
          className="p-2.5 rounded-xl text-slate-400 hover:text-indigo-300 hover:bg-indigo-600/15 border border-transparent hover:border-indigo-500/20 transition-all disabled:opacity-40"
        >
          <Paperclip className="h-4.5 w-4.5" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.txt,.md,.docx"
          onChange={handleFileChange}
        />

        {/* Textarea */}
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Nexus AI Assistant anything… (e.g., project status, task assignees, sprint risks)"
          rows={1}
          disabled={isStreaming}
          className="flex-1 resize-none bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none max-h-44 py-2 leading-relaxed disabled:opacity-60"
          style={{ fieldSizing: 'content' } as React.CSSProperties}
        />

        {/* Send / Stop Action Button */}
        {isStreaming ? (
          <Button
            size="sm"
            onClick={onCancel}
            className="shrink-0 bg-red-500/15 hover:bg-red-500/30 text-red-300 border border-red-500/30 rounded-xl px-4 py-2 font-medium text-xs transition-all shadow-lg"
          >
            <Square className="h-3.5 w-3.5 mr-1.5 fill-red-400" /> Stop AI
          </Button>
        ) : (
          <Button
            size="sm"
            onClick={() => handleSend()}
            disabled={!text.trim()}
            className="glow-button-3d shrink-0 bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl px-4 py-2.5 transition-all disabled:opacity-30 disabled:hover:transform-none"
          >
            <Send className="h-4 w-4 mr-1" />
            <CornerDownLeft className="h-3 w-3 opacity-70" />
          </Button>
        )}
      </div>

      {/* Footer Branding & Keyboard Hint */}
      <div className="flex items-center justify-between text-[11px] text-slate-500 px-2">
        <span className="flex items-center gap-1 text-slate-400 font-medium">
          <Sparkles className="h-3 w-3 text-indigo-400" />
          Nexus AI Assistant Engine v2.0
        </span>
        <span>Press <kbd className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300 font-mono text-[10px]">Enter ↵</kbd> to send</span>
      </div>
    </div>
  );
}

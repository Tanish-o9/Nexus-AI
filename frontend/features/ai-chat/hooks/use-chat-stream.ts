'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { store } from '@/store';
import { aiApi } from '@/services/ai-api';
import type { Message, Citation } from '@/features/ai-chat/types';

const CITATION_DELIMITER = '\n\n__CITATIONS__';

function parseCitations(raw: string): { content: string; citations: Citation[] } {
  const idx = raw.indexOf(CITATION_DELIMITER);
  if (idx === -1) return { content: raw, citations: [] };
  const content = raw.slice(0, idx);
  try {
    const citations = JSON.parse(raw.slice(idx + CITATION_DELIMITER.length)) as Citation[];
    return { content, citations };
  } catch {
    return { content, citations: [] };
  }
}

function makeId() {
  return Math.random().toString(36).slice(2, 10);
}

export function useChatStream() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const sendMessage = useCallback(async (content: string, fileRef?: string) => {
    if (isStreaming) return;

    // 1. Append user message
    const userMsg: Message = {
      id: makeId(),
      role: 'user',
      content,
      fileRef,
      createdAt: new Date(),
    };

    // 2. Append assistant streaming placeholder
    const assistantId = makeId();
    const assistantPlaceholder: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      createdAt: new Date(),
    };

    setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);
    setIsStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const { token, sessionId } = store.getState().auth;
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (sessionId) headers['X-Session-ID'] = sessionId;

      let res = await fetch('/api/ai/chat/', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: content,
          history: messages.slice(-20).map((item) => ({ role: item.role, content: item.content })),
        }),
        signal: controller.signal,
      });

      if (!res.ok) {
        // Fallback to standard aiApi if SSE header fetch receives error status
        const fallbackData = await aiApi.chat({
          message: content,
          history: messages.slice(-20).map((item) => ({ role: item.role, content: item.content })),
        });
        const replyContent = typeof fallbackData === 'string' ? fallbackData : (fallbackData as any)?.content || (fallbackData as any)?.result || JSON.stringify(fallbackData, null, 2);
        const { content: finalContent, citations } = parseCitations(replyContent);

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: finalContent, citations, isStreaming: false }
              : m
          )
        );
        return;
      }

      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('text/event-stream') && res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let accumulated = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunkText = decoder.decode(value, { stream: true });
          const lines = chunkText.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              if (dataStr === '[DONE]') continue;
              accumulated += dataStr;

              const { content: finalContent, citations } = parseCitations(accumulated);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: finalContent, citations, isStreaming: true }
                    : m
                )
              );
            }
          }
        }

        const { content: finalContent, citations } = parseCitations(accumulated);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: finalContent, citations, isStreaming: false }
              : m
          )
        );
      } else {
        const data = await res.json();
        const replyContent = typeof data === 'string' ? data : (data as any)?.content || (data as any)?.result || JSON.stringify(data, null, 2);
        const { content: finalContent, citations } = parseCitations(replyContent);

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: finalContent, citations, isStreaming: false }
              : m
          )
        );
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      const errorMsg = err instanceof Error ? err.message : 'Something went wrong. Please try again.';
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: errorMsg, isStreaming: false }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [isStreaming, messages]);

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isStreaming, sendMessage, cancelStream, clearMessages };
}

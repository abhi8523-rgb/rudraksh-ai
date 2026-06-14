'use client';

import { useState, useCallback, useRef } from 'react';
import type { Message, Conversation, ModuleType } from '@/types';
import { streamResponse, createAbortController } from '@/lib/streaming';

/* ════════════════════════════════════════════════════════════════
   useChat — Chat state management hook (FIXED API)
   
   Supports two calling styles:
   1. Default chat:  useChat()
   2. Module-specific: useChat('/api/v1/coders/generate')
      or useChat({ endpoint: '...', model: '...' })
   ════════════════════════════════════════════════════════════════ */

interface UseChatOptions {
  endpoint?: string;
  model?: string;
  module?: string;
  systemPrompt?: string;
}

export function useChat(optionsOrEndpoint?: UseChatOptions | string) {
  // Support both useChat('/api/coders') and useChat({ endpoint: '...' })
  const options: UseChatOptions =
    typeof optionsOrEndpoint === 'string'
      ? { endpoint: optionsOrEndpoint }
      : optionsOrEndpoint || {};

  const {
    endpoint = '/api/v1/llm/chat',
    model = 'deepseek-r1:14b',
    module = 'chat',
    systemPrompt,
  } = options;

  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentModel, setCurrentModel] = useState(model);
  const abortRef = useRef<AbortController | null>(null);

  const generateId = () =>
    `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;

  const sendMessage = useCallback(
    async (content: string, extraBody?: Record<string, unknown>) => {
      if (!content.trim() || isStreaming) return;

      setError(null);
      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: content.trim(),
        timestamp: Date.now(),
      };

      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        model: currentModel,
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);

      const controller = createAbortController();
      abortRef.current = controller;

      const allMessages = [...messages, userMessage];
      const chatHistory = systemPrompt
        ? [
            { role: 'system' as const, content: systemPrompt },
            ...allMessages,
          ]
        : allMessages;

      await streamResponse({
        endpoint,
        body: {
          messages: chatHistory.map((m) => ({
            role: m.role,
            content: m.content,
          })),
          model: currentModel,
          module,
          stream: true,
          ...extraBody,
        },
        onToken: (token) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === 'assistant') {
              updated[updated.length - 1] = {
                ...last,
                content: last.content + token,
              };
            }
            return updated;
          });
        },
        onDone: (fullText) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === 'assistant') {
              updated[updated.length - 1] = {
                ...last,
                content: fullText || last.content,
                isStreaming: false,
                tokens: fullText.split(/\s+/).length,
              };
            }
            return updated;
          });
          setIsStreaming(false);
          abortRef.current = null;
        },
        onError: (err) => {
          setError(err);
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === 'assistant' && !last.content) {
              updated.pop();
            }
            return updated;
          });
          setIsStreaming(false);
          abortRef.current = null;
        },
        signal: controller.signal,
      });
    },
    [messages, isStreaming, currentModel, endpoint, module, systemPrompt]
  );

  const stopStreaming = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setIsStreaming(false);
    setMessages((prev) => {
      const updated = [...prev];
      const last = updated[updated.length - 1];
      if (last && last.role === 'assistant') {
        updated[updated.length - 1] = { ...last, isStreaming: false };
      }
      return updated;
    });
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const removeMessage = useCallback((id: string) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const retryLast = useCallback(() => {
    const lastUser = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUser) {
      setMessages((prev) => {
        const idx = prev.lastIndexOf(lastUser);
        return prev.slice(0, idx);
      });
      sendMessage(lastUser.content);
    }
  }, [messages, sendMessage]);

  const conversation: Conversation = {
    id: 'current',
    title: messages[0]?.content.slice(0, 50) || 'New Chat',
    messages,
    model: currentModel,
    module: module as Conversation['module'],
    createdAt: messages[0]?.timestamp || Date.now(),
    updatedAt: messages[messages.length - 1]?.timestamp || Date.now(),
  };

  return {
    messages,
    isStreaming,
    error,
    currentModel,
    conversation,
    sendMessage,
    stopStreaming,
    clearMessages,
    removeMessage,
    retryLast,
    setCurrentModel,
    setMessages,
  };
}

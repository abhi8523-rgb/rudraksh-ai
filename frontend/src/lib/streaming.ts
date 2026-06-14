import { API_BASE_URL } from './constants';
import type { StreamEvent } from '@/types';

/* ════════════════════════════════════════════════════════════════
   Rudraksh AI — SSE Streaming Client
   POST-based SSE using fetch + ReadableStream + AbortController
   ════════════════════════════════════════════════════════════════ */

export interface StreamOptions {
  endpoint: string;
  body: Record<string, unknown>;
  onToken: (token: string) => void;
  onDone?: (fullText: string) => void;
  onError?: (error: string) => void;
  onMetadata?: (metadata: Record<string, unknown>) => void;
  signal?: AbortSignal;
}

export async function streamResponse(options: StreamOptions): Promise<void> {
  const { endpoint, body, onToken, onDone, onError, onMetadata, signal } = options;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  };

  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('rudraksh_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal,
    });

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({ detail: response.statusText }));
      onError?.(errBody.detail || `HTTP ${response.status}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError?.('No readable stream available');
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed === ':') continue;

        if (trimmed.startsWith('data: ')) {
          const data = trimmed.slice(6);
          if (data === '[DONE]') {
            onDone?.(fullText);
            return;
          }

          try {
            const event: StreamEvent = JSON.parse(data);
            switch (event.type) {
              case 'token':
                if (event.content) {
                  fullText += event.content;
                  onToken(event.content);
                }
                break;
              case 'done':
                onDone?.(fullText);
                return;
              case 'error':
                onError?.(event.content || 'Stream error');
                return;
              case 'metadata':
                if (event.metadata) onMetadata?.(event.metadata);
                break;
            }
          } catch {
            // Raw text token (non-JSON SSE)
            fullText += data;
            onToken(data);
          }
        }
      }
    }

    // Stream ended without explicit [DONE]
    onDone?.(fullText);
  } catch (err) {
    if ((err as Error).name === 'AbortError') {
      onDone?.('' );
      return;
    }
    onError?.((err as Error).message);
  }
}

export function createAbortController(): AbortController {
  return new AbortController();
}

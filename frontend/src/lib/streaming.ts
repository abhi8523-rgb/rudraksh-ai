import { API_BASE_URL } from './constants';

/* ════════════════════════════════════════════════════════════════
   Neel AI — SSE Streaming Client (FIXED PROTOCOL)
   
   Handles BOTH formats:
   - Backend sends: { content: "hello", done: false }
   - Also supports: { type: "token", content: "hello" }
   
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
  const { endpoint, body, onToken, onDone, onError, onMetadata, signal } =
    options;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  };

  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('neel_token');
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
      const errBody = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
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
            const event = JSON.parse(data);

            // Handle error events from backend
            if (event.error) {
              onError?.(event.error);
              return;
            }

            // Backend sends { content: "...", done: true/false }
            // Also handle { type: "token", content: "..." }
            const content = event.content || '';
            const isDone = event.done === true;

            if (content) {
              fullText += content;
              onToken(content);
            }

            // Pass metadata (token counts, etc.) on final chunk
            if (isDone) {
              const metadata: Record<string, unknown> = {};
              if (event.eval_count) metadata.eval_count = event.eval_count;
              if (event.total_duration) metadata.total_duration = event.total_duration;
              if (event.usage) metadata.usage = event.usage;
              if (Object.keys(metadata).length > 0) {
                onMetadata?.(metadata);
              }
              onDone?.(fullText);
              return;
            }
          } catch {
            // Non-JSON SSE data — treat as raw text token
            if (data.trim()) {
              fullText += data;
              onToken(data);
            }
          }
        }
      }
    }

    // Stream ended without explicit [DONE] or done:true
    onDone?.(fullText);
  } catch (err) {
    if ((err as Error).name === 'AbortError') {
      onDone?.(fullText || '');
      return;
    }
    onError?.((err as Error).message);
  }
}

export function createAbortController(): AbortController {
  return new AbortController();
}

'use client';

import { useState, useCallback, useRef } from 'react';
import { streamResponse, createAbortController } from '@/lib/streaming';

/* ════════════════════════════════════════════════════════════════
   useStreaming — Generic streaming response hook
   ════════════════════════════════════════════════════════════════ */

interface UseStreamingOptions {
  endpoint: string;
}

export function useStreaming(options: UseStreamingOptions) {
  const { endpoint } = options;

  const [output, setOutput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<Record<string, unknown> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const startStream = useCallback(
    async (body: Record<string, unknown>) => {
      setOutput('');
      setError(null);
      setMetadata(null);
      setIsStreaming(true);

      const controller = createAbortController();
      abortRef.current = controller;

      await streamResponse({
        endpoint,
        body,
        onToken: (token) => {
          setOutput((prev) => prev + token);
        },
        onDone: () => {
          setIsStreaming(false);
          abortRef.current = null;
        },
        onError: (err) => {
          setError(err);
          setIsStreaming(false);
          abortRef.current = null;
        },
        onMetadata: (meta) => {
          setMetadata(meta);
        },
        signal: controller.signal,
      });
    },
    [endpoint]
  );

  const stopStream = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
  }, []);

  const reset = useCallback(() => {
    stopStream();
    setOutput('');
    setError(null);
    setMetadata(null);
  }, [stopStream]);

  return {
    output,
    isStreaming,
    error,
    metadata,
    startStream,
    stopStream,
    reset,
  };
}

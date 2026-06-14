'use client';

import { motion } from 'framer-motion';

/* ════════════════════════════════════════════════════════════════
   StreamingText — Real-time token-by-token text display
   ════════════════════════════════════════════════════════════════ */

interface StreamingTextProps {
  text: string;
  isStreaming: boolean;
}

export default function StreamingText({ text, isStreaming }: StreamingTextProps) {
  return (
    <span className="whitespace-pre-wrap">
      {text}
      {isStreaming && (
        <motion.span
          animate={{ opacity: [1, 0.3, 1] }}
          transition={{ duration: 1, repeat: Infinity, ease: 'easeInOut' }}
          className="inline-block w-2 h-4 ml-0.5 bg-blue-400 rounded-sm align-text-bottom"
        />
      )}
    </span>
  );
}

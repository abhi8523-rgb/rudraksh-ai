'use client';

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '@/types';
import CodeBlock from './CodeBlock';
import StreamingText from './StreamingText';

/* ════════════════════════════════════════════════════════════════
   MessageBubble — Individual message with avatar, timestamp, copy
   ════════════════════════════════════════════════════════════════ */

interface MessageBubbleProps {
  message: Message;
  onRetry?: () => void;
  onDelete?: () => void;
}

export default function MessageBubble({ message, onRetry, onDelete }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [message.content]);

  const formatTime = (ts: number) => {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 px-6 py-4 group ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center text-sm
        ${isUser
          ? 'bg-gradient-to-br from-blue-500 to-indigo-600'
          : 'bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/20'
        }`}
      >
        {isUser ? '👤' : '✧'}
      </div>

      {/* Content */}
      <div className={`flex-1 min-w-0 max-w-3xl ${isUser ? 'flex flex-col items-end' : ''}`}>
        {/* Header */}
        <div className={`flex items-center gap-2 mb-1 ${isUser ? 'flex-row-reverse' : ''}`}>
          <span className="text-xs font-semibold text-gray-400">
            {isUser ? 'You' : 'Rudraksh AI'}
          </span>
          <span className="text-[10px] text-gray-600">{formatTime(message.timestamp)}</span>
          {message.model && (
            <span className="text-[10px] text-gray-700 font-mono">{message.model}</span>
          )}
        </div>

        {/* Message Body */}
        <div
          className={`
            rounded-2xl px-4 py-3 text-sm leading-relaxed
            ${isUser
              ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10 border border-blue-500/10 text-gray-200'
              : 'bg-white/[0.02] border border-white/[0.04] text-gray-300'
            }
          `}
        >
          {message.isStreaming ? (
            <StreamingText text={message.content} isStreaming={true} />
          ) : isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none
              prose-p:my-2 prose-headings:my-3 prose-ul:my-2 prose-ol:my-2
              prose-code:text-blue-300 prose-code:bg-blue-500/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
              prose-pre:my-0 prose-pre:p-0 prose-pre:bg-transparent
              prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
              prose-blockquote:border-blue-500/30 prose-blockquote:text-gray-400
              prose-strong:text-white prose-em:text-gray-300
              prose-table:text-xs prose-th:text-gray-400 prose-td:text-gray-300
              prose-hr:border-white/10">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code(props) {
                    const { children, className, ...rest } = props;
                    const match = /language-(\w+)/.exec(className || '');
                    const codeStr = String(children).replace(/\n$/, '');
                    if (match) {
                      return <CodeBlock code={codeStr} language={match[1]} />;
                    }
                    return <code className={className} {...rest}>{children}</code>;
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className={`flex items-center gap-1 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity ${isUser ? 'flex-row-reverse' : ''}`}>
          <button
            onClick={handleCopy}
            className="p-1 text-gray-600 hover:text-gray-400 transition-colors rounded"
            title="Copy"
          >
            {copied ? (
              <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            )}
          </button>
          {!isUser && onRetry && (
            <button onClick={onRetry} className="p-1 text-gray-600 hover:text-gray-400 transition-colors rounded" title="Retry">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          )}
          {onDelete && (
            <button onClick={onDelete} className="p-1 text-gray-600 hover:text-rose-400 transition-colors rounded" title="Delete">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
          {message.tokens && (
            <span className="text-[10px] text-gray-700 ml-2">{message.tokens} tokens</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}

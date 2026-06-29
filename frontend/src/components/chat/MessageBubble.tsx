'use client';

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '@/types';
import CodeBlock from './CodeBlock';
import StreamingText from './StreamingText';

/* MessageBubble — Light theme message display */

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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`flex gap-3 px-4 py-3 group ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium ${
        isUser
          ? 'bg-blue-600 text-white'
          : 'bg-slate-100 text-slate-600 border border-slate-200'
      }`}>
        {isUser ? 'Y' : 'N'}
      </div>

      {/* Content */}
      <div className={`flex-1 min-w-0 max-w-2xl ${isUser ? 'flex flex-col items-end' : ''}`}>
        {/* Header */}
        <div className={`flex items-center gap-2 mb-1 ${isUser ? 'flex-row-reverse' : ''}`}>
          <span className="text-xs font-medium text-slate-500">
            {isUser ? 'You' : 'Neel AI'}
          </span>
          <span className="text-[10px] text-slate-400">{formatTime(message.timestamp)}</span>
          {message.model && (
            <span className="text-[10px] text-slate-400 font-mono bg-slate-100 px-1.5 py-0.5 rounded">{message.model}</span>
          )}
        </div>

        {/* Message Body */}
        <div
          className={`rounded-xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-slate-50 border border-slate-200 text-slate-800'
          }`}
        >
          {message.isStreaming ? (
            <StreamingText text={message.content} isStreaming={true} />
          ) : isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none
              prose-p:my-2 prose-headings:my-3 prose-ul:my-2 prose-ol:my-2
              prose-code:text-blue-700 prose-code:bg-blue-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
              prose-pre:my-0 prose-pre:p-0 prose-pre:bg-transparent
              prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
              prose-blockquote:border-blue-300 prose-blockquote:text-slate-500
              prose-strong:text-slate-900">
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
        <div className={`flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity ${isUser ? 'flex-row-reverse' : ''}`}>
          <button
            onClick={handleCopy}
            className="p-1 text-slate-400 hover:text-slate-600 transition-colors rounded"
            title="Copy"
          >
            {copied ? (
              <svg className="w-3.5 h-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            )}
          </button>
          {message.tokens && (
            <span className="text-[10px] text-slate-400 ml-2">{message.tokens} tokens</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}

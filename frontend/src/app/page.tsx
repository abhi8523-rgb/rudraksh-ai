'use client';

import { useState, useRef, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import MessageBubble from '@/components/chat/MessageBubble';
import { useChat } from '@/hooks/useChat';
import { APP_NAME } from '@/lib/constants';

/* Main Chat Page */

export default function ChatPage() {
  const { messages, isStreaming, error, sendMessage, stopStreaming } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center animate-[fade-in_0.4s_ease-out]">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center mb-5 shadow-md">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3 20.25V4.5A2.25 2.25 0 015.25 2.25h13.5A2.25 2.25 0 0121 4.5v10.5a2.25 2.25 0 01-2.25 2.25H7.5L3 20.25z" />
              </svg>
            </div>
            <h1 className="text-xl font-semibold text-slate-900 mb-2">
              Welcome to {APP_NAME}
            </h1>
            <p className="text-slate-500 max-w-md text-sm leading-relaxed mb-8">
              Your sovereign intelligence suite. Ask anything, generate code, analyze data,
              or let Trident execute complex multi-step tasks autonomously.
            </p>
            <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
              {[
                { text: 'Generate a Python FastAPI server' },
                { text: 'Create a marketing campaign strategy' },
                { text: 'Explain quantum computing simply' },
                { text: 'Summarize a research paper' },
              ].map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => { setInput(suggestion.text); inputRef.current?.focus(); }}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-all text-left text-sm text-slate-600"
                >
                  {suggestion.text}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-1">
            <AnimatePresence>
              {messages.map((msg, i) => (
                <MessageBubble key={msg.id || i} message={msg} />
              ))}
            </AnimatePresence>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mx-4 mb-2 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
          <strong>Connection Error:</strong> {error}
          <span className="block text-xs text-red-500 mt-1">Make sure the backend is running on localhost:8001</span>
        </div>
      )}

      {/* Input Bar */}
      <div className="border-t border-slate-200 bg-white p-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2 rounded-xl bg-slate-50 border border-slate-200 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Neel AI..."
              rows={1}
              className="flex-1 bg-transparent px-4 py-3 text-sm text-slate-900 placeholder-slate-400 resize-none outline-none max-h-40 scrollbar-thin"
              style={{ minHeight: '44px' }}
            />
            <div className="flex items-center p-2">
              {isStreaming ? (
                <button
                  onClick={stopStreaming}
                  className="p-2 rounded-lg bg-red-100 text-red-600 hover:bg-red-200 transition-colors"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <rect x="5" y="5" width="10" height="10" rx="1" />
                  </svg>
                </button>
              ) : (
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="p-2 rounded-lg bg-blue-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors shadow-sm"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
                  </svg>
                </button>
              )}
            </div>
          </div>
          <p className="text-center text-[11px] text-slate-400 mt-2">
            Neel AI runs locally — your data never leaves your machine
          </p>
        </div>
      </div>
    </div>
  );
}

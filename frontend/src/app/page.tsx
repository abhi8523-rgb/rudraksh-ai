'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MessageBubble from '@/components/chat/MessageBubble';
import CodeBlock from '@/components/chat/CodeBlock';
import { useChat } from '@/hooks/useChat';
import { APP_NAME } from '@/lib/constants';

/* ════════════════════════════════════════════════════════════════
   Main Chat Page — The default landing experience
   ════════════════════════════════════════════════════════════════ */

export default function ChatPage() {
  const { messages, isStreaming, sendMessage, stopStreaming } = useChat();
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
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 scrollbar-thin">
        {messages.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center"
          >
            <div className="relative mb-6">
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-blue-500/20 to-indigo-600/20 blur-2xl" />
              <div className="relative w-20 h-20 rounded-3xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                <span className="text-4xl">🔱</span>
              </div>
            </div>
            <h1 className="text-2xl font-bold font-heading bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent mb-2">
              Welcome to {APP_NAME}
            </h1>
            <p className="text-gray-500 max-w-md">
              Your sovereign intelligence suite. Ask anything, generate code, analyze data, 
              or let Shivoham execute complex multi-step tasks autonomously.
            </p>
            <div className="grid grid-cols-2 gap-3 mt-8 max-w-lg w-full">
              {[
                { icon: '💻', text: 'Generate a Python FastAPI server' },
                { icon: '📊', text: 'Create a marketing campaign strategy' },
                { icon: '🎓', text: 'Explain quantum computing simply' },
                { icon: '🔬', text: 'Summarize a research paper' },
              ].map((suggestion, i) => (
                <motion.button
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 * (i + 1) }}
                  onClick={() => { setInput(suggestion.text); inputRef.current?.focus(); }}
                  className="flex items-center gap-2 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06] hover:border-white/[0.1] transition-all text-left text-sm text-gray-400 hover:text-gray-300"
                >
                  <span>{suggestion.icon}</span>
                  <span>{suggestion.text}</span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        ) : (
          <AnimatePresence>
            {messages.map((msg, i) => (
              <MessageBubble key={i} role={msg.role} content={msg.content} />
            ))}
          </AnimatePresence>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="border-t border-white/[0.06] bg-[#0a0a1a]/60 backdrop-blur-xl p-4">
        <div className="max-w-3xl mx-auto">
          <div className="relative flex items-end gap-2 rounded-2xl bg-white/[0.04] border border-white/[0.08] focus-within:border-blue-500/30 focus-within:shadow-[0_0_20px_rgba(59,130,246,0.1)] transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Rudraksh AI..."
              rows={1}
              className="flex-1 bg-transparent px-4 py-3 text-sm text-white placeholder-gray-600 resize-none outline-none max-h-40 scrollbar-thin"
              style={{ minHeight: '44px' }}
            />
            <div className="flex items-center gap-1 p-2">
              {isStreaming ? (
                <button
                  onClick={stopStreaming}
                  className="p-2 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <rect x="5" y="5" width="10" height="10" rx="1" />
                  </svg>
                </button>
              ) : (
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="p-2 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:shadow-[0_0_15px_rgba(59,130,246,0.3)] transition-all"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
                  </svg>
                </button>
              )}
            </div>
          </div>
          <p className="text-center text-[11px] text-gray-600 mt-2">
            Rudraksh AI runs locally — your data never leaves your machine
          </p>
        </div>
      </div>
    </div>
  );
}

'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { useChat } from '@/hooks/useChat';
import MessageBubble from '@/components/chat/MessageBubble';

const TOOLS = [
  { id: 'generate', name: 'Generate Code', icon: '✨', desc: 'Create code from description', color: 'from-violet-500 to-purple-600' },
  { id: 'refactor', name: 'Refactor', icon: '🔄', desc: 'Improve existing code', color: 'from-blue-500 to-cyan-500' },
  { id: 'document', name: 'Document', icon: '📝', desc: 'Generate documentation', color: 'from-emerald-500 to-teal-500' },
  { id: 'scan', name: 'Security Scan', icon: '🛡️', desc: 'Find vulnerabilities', color: 'from-red-500 to-rose-600' },
];

const LANGUAGES = ['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'Go', 'Rust', 'C#', 'Ruby', 'PHP'];

export default function CodersPage() {
  const [activeTool, setActiveTool] = useState('generate');
  const [language, setLanguage] = useState('Python');
  const [input, setInput] = useState('');
  const { messages, isStreaming, sendMessage } = useChat('/api/coders');

  const handleSubmit = () => {
    if (!input.trim()) return;
    const endpoint = activeTool;
    sendMessage(input, { action: endpoint, language, stream: true });
    setInput('');
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">⚡ Coders</h1>
        <p className="text-gray-500 mt-1">Code generation, refactoring, documentation & security analysis</p>
      </motion.div>

      {/* Tool Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {TOOLS.map((tool) => (
          <motion.button key={tool.id} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTool(tool.id)}
            className={`p-4 rounded-2xl border transition-all text-left ${
              activeTool === tool.id 
                ? 'border-violet-500/30 bg-violet-500/10 shadow-[0_0_20px_rgba(139,92,246,0.15)]' 
                : 'border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04]'
            }`}
          >
            <span className="text-2xl">{tool.icon}</span>
            <div className="mt-2 text-sm font-semibold text-white">{tool.name}</div>
            <div className="text-xs text-gray-500">{tool.desc}</div>
          </motion.button>
        ))}
      </div>

      {/* Language + Input */}
      <Card className="p-5 space-y-4">
        <div className="flex flex-wrap gap-2">
          {LANGUAGES.map((lang) => (
            <button key={lang} onClick={() => setLanguage(lang)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                language === lang
                  ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                  : 'bg-white/[0.03] text-gray-500 border border-white/[0.06] hover:text-gray-300'
              }`}
            >
              {lang}
            </button>
          ))}
        </div>
        <textarea value={input} onChange={(e) => setInput(e.target.value)}
          placeholder={activeTool === 'generate' ? 'Describe the code you want to generate...' : 'Paste your code here...'}
          rows={6}
          className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-sm text-white placeholder-gray-600 resize-none outline-none focus:border-violet-500/30 font-mono"
        />
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600">Language: {language} • Tool: {TOOLS.find(t => t.id === activeTool)?.name}</span>
          <Button onClick={handleSubmit} disabled={!input.trim() || isStreaming}>
            {isStreaming ? 'Processing...' : `Run ${TOOLS.find(t => t.id === activeTool)?.name}`}
          </Button>
        </div>
      </Card>

      {/* Results */}
      {messages.length > 0 && (
        <div className="space-y-3">
          {messages.map((msg, i) => (
            <MessageBubble key={i} role={msg.role} content={msg.content} />
          ))}
        </div>
      )}
    </div>
  );
}

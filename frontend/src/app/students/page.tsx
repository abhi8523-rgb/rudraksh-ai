'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { useChat } from '@/hooks/useChat';
import MessageBubble from '@/components/chat/MessageBubble';

const TOOLS = [
  { id: 'guide', name: 'Study Guide', icon: '📚', desc: 'Personalized study plans' },
  { id: 'explain', name: 'Explain Concept', icon: '💡', desc: 'Clear, multi-level explanations' },
  { id: 'cite', name: 'Citation Helper', icon: '📑', desc: 'Format APA, MLA, Chicago & more' },
  { id: 'summarize', name: 'Summarize', icon: '📋', desc: 'Condense texts efficiently' },
];

const LEVELS = ['High School', 'Undergraduate', 'Graduate', 'PhD', 'Self-Study'];

export default function StudentsPage() {
  const [activeTool, setActiveTool] = useState('explain');
  const [level, setLevel] = useState('Undergraduate');
  const [input, setInput] = useState('');
  const { messages, isStreaming, sendMessage } = useChat('/api/students');

  const handleSubmit = () => {
    if (!input.trim()) return;
    sendMessage(input, { action: activeTool, level, stream: true });
    setInput('');
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">🎓 Students</h1>
        <p className="text-gray-500 mt-1">Study guides, concept explanations, citations & summarization</p>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {TOOLS.map((tool) => (
          <motion.button key={tool.id} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTool(tool.id)}
            className={`p-4 rounded-2xl border transition-all text-left ${
              activeTool === tool.id ? 'border-emerald-500/30 bg-emerald-500/10 shadow-[0_0_20px_rgba(16,185,129,0.15)]' : 'border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04]'
            }`}
          >
            <span className="text-2xl">{tool.icon}</span>
            <div className="mt-2 text-sm font-semibold text-white">{tool.name}</div>
            <div className="text-xs text-gray-500">{tool.desc}</div>
          </motion.button>
        ))}
      </div>

      <Card className="p-5 space-y-4">
        <div>
          <label className="text-xs text-gray-500 font-medium mb-2 block">Academic Level</label>
          <div className="flex flex-wrap gap-2">
            {LEVELS.map((l) => (
              <button key={l} onClick={() => setLevel(l)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  level === l ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-white/[0.03] text-gray-500 border border-white/[0.06] hover:text-gray-300'
                }`}
              >{l}</button>
            ))}
          </div>
        </div>
        <textarea value={input} onChange={(e) => setInput(e.target.value)}
          placeholder={activeTool === 'explain' ? 'What concept would you like explained?' : 'Enter your study topic or text...'}
          rows={5} className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-sm text-white placeholder-gray-600 resize-none outline-none focus:border-emerald-500/30"
        />
        <div className="flex justify-end">
          <Button onClick={handleSubmit} disabled={!input.trim() || isStreaming}>
            {isStreaming ? 'Processing...' : `Run ${TOOLS.find(t => t.id === activeTool)?.name}`}
          </Button>
        </div>
      </Card>

      {messages.length > 0 && (
        <div className="space-y-3">{messages.map((msg, i) => <MessageBubble key={i} role={msg.role} content={msg.content} />)}</div>
      )}
    </div>
  );
}

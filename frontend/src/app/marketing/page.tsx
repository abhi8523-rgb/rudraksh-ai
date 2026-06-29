'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { useChat } from '@/hooks/useChat';
import MessageBubble from '@/components/chat/MessageBubble';

const TOOLS = [
  { id: 'campaign', name: 'Campaign Strategy', icon: 'ðŸŽ¯', desc: 'Full marketing campaign plan' },
  { id: 'seo', name: 'SEO Analysis', icon: 'ðŸ”', desc: 'Keyword research & optimization' },
  { id: 'ab-test', name: 'A/B Testing', icon: 'âš—ï¸', desc: 'Design rigorous experiments' },
  { id: 'persona', name: 'Customer Personas', icon: 'ðŸ‘¤', desc: 'Build detailed buyer personas' },
];

export default function MarketingPage() {
  const [activeTool, setActiveTool] = useState('campaign');
  const [input, setInput] = useState('');
  const { messages, isStreaming, sendMessage } = useChat('/api/marketing');

  const handleSubmit = () => {
    if (!input.trim()) return;
    sendMessage(input, { action: activeTool, stream: true });
    setInput('');
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">ðŸ“Š Marketing</h1>
        <p className="text-gray-500 mt-1">Campaign strategy, SEO, A/B testing & customer personas</p>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {TOOLS.map((tool) => (
          <motion.button key={tool.id} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTool(tool.id)}
            className={`p-4 rounded-2xl border transition-all text-left ${
              activeTool === tool.id ? 'border-amber-500/30 bg-amber-500/10 shadow-[0_0_20px_rgba(245,158,11,0.15)]' : 'border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04]'
            }`}
          >
            <span className="text-2xl">{tool.icon}</span>
            <div className="mt-2 text-sm font-semibold text-white">{tool.name}</div>
            <div className="text-xs text-gray-500">{tool.desc}</div>
          </motion.button>
        ))}
      </div>

      <Card className="p-5 space-y-4">
        <textarea value={input} onChange={(e) => setInput(e.target.value)}
          placeholder={`Describe your ${TOOLS.find(t => t.id === activeTool)?.name.toLowerCase()} needs...`}
          rows={5} className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-sm text-white placeholder-gray-600 resize-none outline-none focus:border-amber-500/30"
        />
        <div className="flex justify-end">
          <Button onClick={handleSubmit} disabled={!input.trim() || isStreaming}>
            {isStreaming ? 'Generating...' : `Run ${TOOLS.find(t => t.id === activeTool)?.name}`}
          </Button>
        </div>
      </Card>

      {messages.length > 0 && (
        <div className="space-y-3">{messages.map((msg, i) => <MessageBubble key={msg.id || i} message={msg} />)}</div>
      )}
    </div>
  );
}

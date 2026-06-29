'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { useChat } from '@/hooks/useChat';
import MessageBubble from '@/components/chat/MessageBubble';

const TOOLS = [
  { id: 'calendar', name: 'Content Calendar', icon: 'ðŸ“…', desc: 'Plan your posting schedule' },
  { id: 'trends', name: 'Trend Analysis', icon: 'ðŸ“ˆ', desc: 'Discover trending topics' },
  { id: 'draft', name: 'Post Drafts', icon: 'âœï¸', desc: 'Write platform-optimized posts' },
  { id: 'engagement', name: 'Engagement Sim', icon: 'ðŸŽ¯', desc: 'Predict content performance' },
];

const PLATFORMS = ['Instagram', 'Twitter/X', 'LinkedIn', 'TikTok', 'Facebook', 'YouTube'];

export default function SocialMediaPage() {
  const [activeTool, setActiveTool] = useState('calendar');
  const [platforms, setPlatforms] = useState<string[]>(['Instagram']);
  const [input, setInput] = useState('');
  const { messages, isStreaming, sendMessage } = useChat('/api/social');

  const togglePlatform = (p: string) => {
    setPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]);
  };

  const handleSubmit = () => {
    if (!input.trim()) return;
    sendMessage(input, { action: activeTool, platforms: platforms.join(', '), stream: true });
    setInput('');
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-pink-400 to-rose-400 bg-clip-text text-transparent">ðŸ“± Social Media</h1>
        <p className="text-gray-500 mt-1">Content planning, trend analysis & multi-platform drafting</p>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {TOOLS.map((tool) => (
          <motion.button key={tool.id} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTool(tool.id)}
            className={`p-4 rounded-2xl border transition-all text-left ${
              activeTool === tool.id ? 'border-pink-500/30 bg-pink-500/10 shadow-[0_0_20px_rgba(236,72,153,0.15)]' : 'border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04]'
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
          <label className="text-xs text-gray-500 font-medium mb-2 block">Platforms</label>
          <div className="flex flex-wrap gap-2">
            {PLATFORMS.map((p) => (
              <button key={p} onClick={() => togglePlatform(p)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  platforms.includes(p) ? 'bg-pink-500/20 text-pink-300 border border-pink-500/30' : 'bg-white/[0.03] text-gray-500 border border-white/[0.06] hover:text-gray-300'
                }`}
              >{p}</button>
            ))}
          </div>
        </div>
        <textarea value={input} onChange={(e) => setInput(e.target.value)}
          placeholder={activeTool === 'calendar' ? 'Describe your brand, niche, and goals...' : 'Describe your content or topic...'}
          rows={5} className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-sm text-white placeholder-gray-600 resize-none outline-none focus:border-pink-500/30"
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

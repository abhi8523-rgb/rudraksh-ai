'use client';

import { useState } from 'react';
import { useChat } from '@/hooks/useChat';
import MessageBubble from '@/components/chat/MessageBubble';

const TOOLS = [
  { id: 'calendar', name: 'Content Calendar', desc: 'Plan weekly/monthly content' },
  { id: 'trends', name: 'Trend Analysis', desc: 'Identify trending topics' },
  { id: 'draft', name: 'Draft Posts', desc: 'Write platform-specific content' },
  { id: 'engagement', name: 'Engagement Sim', desc: 'Predict post performance' },
];

export default function SocialMediaPage() {
  const [activeTool, setActiveTool] = useState('calendar');
  const [input, setInput] = useState('');
  const { messages, isStreaming, sendMessage } = useChat('/api/chat');

  const handleSubmit = () => {
    if (!input.trim()) return;
    sendMessage(input, { action: activeTool, stream: true });
    setInput('');
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto overflow-y-auto h-full">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Social Media</h1>
        <p className="text-slate-500 text-sm mt-1">Content planning, drafting & scheduling</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {TOOLS.map((tool) => (
          <button key={tool.id} onClick={() => setActiveTool(tool.id)}
            className={`p-4 rounded-xl border transition-all text-left ${
              activeTool === tool.id ? 'border-pink-300 bg-pink-50 shadow-sm' : 'border-slate-200 bg-white hover:bg-slate-50'
            }`}>
            <div className="text-sm font-medium text-slate-900">{tool.name}</div>
            <div className="text-xs text-slate-500 mt-1">{tool.desc}</div>
          </button>
        ))}
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-sm">
        <textarea value={input} onChange={(e) => setInput(e.target.value)}
          placeholder="Describe your social media goal..."
          rows={4}
          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-900 placeholder-slate-400 resize-none outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
        />
        <div className="flex justify-end">
          <button onClick={handleSubmit} disabled={!input.trim() || isStreaming}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium disabled:opacity-40 hover:bg-blue-700 transition-colors shadow-sm">
            {isStreaming ? 'Generating...' : `Run ${TOOLS.find(t => t.id === activeTool)?.name}`}
          </button>
        </div>
      </div>

      {messages.length > 0 && (
        <div className="space-y-1">{messages.map((msg, i) => <MessageBubble key={msg.id || i} message={msg} />)}</div>
      )}
    </div>
  );
}

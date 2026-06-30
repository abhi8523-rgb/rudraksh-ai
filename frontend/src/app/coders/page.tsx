'use client';

import { useState } from 'react';
import { useChat } from '@/hooks/useChat';
import MessageBubble from '@/components/chat/MessageBubble';

const TOOLS = [
  { id: 'generate', name: 'Generate Code', desc: 'Create code from description' },
  { id: 'refactor', name: 'Refactor', desc: 'Improve existing code' },
  { id: 'document', name: 'Document', desc: 'Generate documentation' },
  { id: 'scan', name: 'Security Scan', desc: 'Find vulnerabilities' },
];

const LANGUAGES = ['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'Go', 'Rust', 'C#', 'Ruby', 'PHP'];

export default function CodersPage() {
  const [activeTool, setActiveTool] = useState('generate');
  const [language, setLanguage] = useState('Python');
  const [input, setInput] = useState('');
  const { messages, isStreaming, sendMessage } = useChat('/api/chat');

  const handleSubmit = () => {
    if (!input.trim()) return;
    sendMessage(input, { action: activeTool, language, stream: true });
    setInput('');
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto overflow-y-auto h-full">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Coders</h1>
        <p className="text-slate-500 text-sm mt-1">Code generation, refactoring, documentation & security analysis</p>
      </div>

      {/* Tool Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {TOOLS.map((tool) => (
          <button key={tool.id}
            onClick={() => setActiveTool(tool.id)}
            className={`p-4 rounded-xl border transition-all text-left ${
              activeTool === tool.id
                ? 'border-blue-300 bg-blue-50 shadow-sm'
                : 'border-slate-200 bg-white hover:bg-slate-50'
            }`}
          >
            <div className="text-sm font-medium text-slate-900">{tool.name}</div>
            <div className="text-xs text-slate-500 mt-1">{tool.desc}</div>
          </button>
        ))}
      </div>

      {/* Language + Input */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-sm">
        <div className="flex flex-wrap gap-2">
          {LANGUAGES.map((lang) => (
            <button key={lang} onClick={() => setLanguage(lang)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                language === lang
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'bg-slate-50 text-slate-500 border border-slate-200 hover:text-slate-700'
              }`}
            >
              {lang}
            </button>
          ))}
        </div>
        <textarea value={input} onChange={(e) => setInput(e.target.value)}
          placeholder={activeTool === 'generate' ? 'Describe the code you want to generate...' : 'Paste your code here...'}
          rows={6}
          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-900 placeholder-slate-400 resize-none outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 font-mono"
        />
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-500">Language: {language} · Tool: {TOOLS.find(t => t.id === activeTool)?.name}</span>
          <button onClick={handleSubmit} disabled={!input.trim() || isStreaming}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium disabled:opacity-40 hover:bg-blue-700 transition-colors shadow-sm">
            {isStreaming ? 'Processing...' : `Run ${TOOLS.find(t => t.id === activeTool)?.name}`}
          </button>
        </div>
      </div>

      {/* Results */}
      {messages.length > 0 && (
        <div className="space-y-1">
          {messages.map((msg, i) => (
            <MessageBubble key={msg.id || i} message={msg} />
          ))}
        </div>
      )}
    </div>
  );
}

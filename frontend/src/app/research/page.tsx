'use client';

import { useState } from 'react';
import { useChat } from '@/hooks/useChat';
import MessageBubble from '@/components/chat/MessageBubble';
import { API_BASE_URL } from '@/lib/constants';

const TOOLS = [
  { id: 'query', name: 'RAG Query', desc: 'Ask questions from uploaded docs' },
  { id: 'hypothesis', name: 'Hypotheses', desc: 'Generate research hypotheses' },
  { id: 'review', name: 'Lit Review', desc: 'Synthesize literature reviews' },
];

export default function ResearchPage() {
  const [activeTool, setActiveTool] = useState('query');
  const [input, setInput] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');
  const { messages, isStreaming, sendMessage } = useChat('/api/chat');

  const handleSubmit = () => {
    if (!input.trim()) return;
    sendMessage(input, { action: activeTool, stream: true });
    setInput('');
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadStatus(`Uploading ${file.name}...`);
    const formData = new FormData();
    formData.append('file', file);
    try {
      await fetch(`${API_BASE_URL}/api/v1/memory/upload`, { method: 'POST', body: formData });
      setUploadStatus(`${file.name} uploaded successfully`);
    } catch {
      setUploadStatus('Upload failed — is the backend running?');
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto overflow-y-auto h-full">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Research</h1>
        <p className="text-slate-500 text-sm mt-1">RAG-powered deep research & analysis</p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {TOOLS.map((tool) => (
          <button key={tool.id} onClick={() => setActiveTool(tool.id)}
            className={`p-4 rounded-xl border transition-all text-left ${
              activeTool === tool.id ? 'border-cyan-300 bg-cyan-50 shadow-sm' : 'border-slate-200 bg-white hover:bg-slate-50'
            }`}>
            <div className="text-sm font-medium text-slate-900">{tool.name}</div>
            <div className="text-xs text-slate-500 mt-1">{tool.desc}</div>
          </button>
        ))}
      </div>

      {/* Upload */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
        <label className="text-xs text-slate-500 font-medium block mb-2">Upload Document (PDF, TXT, MD)</label>
        <input type="file" accept=".pdf,.txt,.md,.csv" onChange={handleUpload}
          className="text-sm text-slate-600 file:mr-3 file:px-3 file:py-1.5 file:rounded-lg file:border file:border-slate-200 file:bg-slate-50 file:text-sm file:text-slate-700 hover:file:bg-slate-100" />
        {uploadStatus && <p className="text-xs text-slate-500 mt-2">{uploadStatus}</p>}
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-sm">
        <textarea value={input} onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a research question..."
          rows={4}
          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-900 placeholder-slate-400 resize-none outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
        />
        <div className="flex justify-end">
          <button onClick={handleSubmit} disabled={!input.trim() || isStreaming}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium disabled:opacity-40 hover:bg-blue-700 transition-colors shadow-sm">
            {isStreaming ? 'Researching...' : `Run ${TOOLS.find(t => t.id === activeTool)?.name}`}
          </button>
        </div>
      </div>

      {messages.length > 0 && (
        <div className="space-y-1">{messages.map((msg, i) => <MessageBubble key={msg.id || i} message={msg} />)}</div>
      )}
    </div>
  );
}

'use client';

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { useChat } from '@/hooks/useChat';
import MessageBubble from '@/components/chat/MessageBubble';
import { API_BASE_URL } from '@/lib/constants';

const TOOLS = [
  { id: 'query', name: 'Deep Query (RAG)', icon: '🔎', desc: 'Query your uploaded documents' },
  { id: 'hypothesis', name: 'Hypothesis Gen', icon: '🧪', desc: 'Generate research hypotheses' },
  { id: 'review', name: 'Literature Review', icon: '📖', desc: 'Synthesize research papers' },
];

export default function ResearchPage() {
  const [activeTool, setActiveTool] = useState('query');
  const [input, setInput] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const { messages, isStreaming, sendMessage } = useChat('/api/research');

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      f => ['.pdf', '.md', '.txt'].some(ext => f.name.endsWith(ext))
    );
    setFiles(prev => [...prev, ...droppedFiles]);
  }, []);

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      try {
        await fetch(`${API_BASE_URL}/api/memory/upload`, { method: 'POST', body: formData });
      } catch (err) {
        console.error('Upload error:', err);
      }
    }
    setUploading(false);
    setFiles([]);
  };

  const handleSubmit = () => {
    if (!input.trim()) return;
    sendMessage(input, { action: activeTool, stream: true });
    setInput('');
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">🔬 Research</h1>
        <p className="text-gray-500 mt-1">Deep RAG queries, hypothesis generation & literature reviews</p>
      </motion.div>

      <div className="grid grid-cols-3 gap-3">
        {TOOLS.map((tool) => (
          <motion.button key={tool.id} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTool(tool.id)}
            className={`p-4 rounded-2xl border transition-all text-left ${
              activeTool === tool.id ? 'border-cyan-500/30 bg-cyan-500/10 shadow-[0_0_20px_rgba(6,182,212,0.15)]' : 'border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04]'
            }`}
          >
            <span className="text-2xl">{tool.icon}</span>
            <div className="mt-2 text-sm font-semibold text-white">{tool.name}</div>
            <div className="text-xs text-gray-500">{tool.desc}</div>
          </motion.button>
        ))}
      </div>

      {/* File Upload Zone */}
      <Card className="p-5">
        <div onDrop={handleDrop} onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed border-white/[0.08] rounded-xl p-6 text-center hover:border-cyan-500/30 hover:bg-cyan-500/[0.02] transition-all cursor-pointer"
        >
          <span className="text-3xl mb-2 block">📄</span>
          <p className="text-sm text-gray-400">Drag & drop research papers here</p>
          <p className="text-xs text-gray-600 mt-1">Supports .pdf, .md, .txt</p>
        </div>
        {files.length > 0 && (
          <div className="mt-3 space-y-2">
            {files.map((f, i) => (
              <div key={i} className="flex items-center justify-between text-sm text-gray-400 bg-white/[0.03] rounded-lg px-3 py-2">
                <span>📄 {f.name}</span>
                <span className="text-xs text-gray-600">{(f.size / 1024).toFixed(1)} KB</span>
              </div>
            ))}
            <Button onClick={handleUpload} disabled={uploading}>
              {uploading ? 'Uploading...' : `Upload ${files.length} file(s)`}
            </Button>
          </div>
        )}
      </Card>

      {/* Query Input */}
      <Card className="p-5 space-y-4">
        <textarea value={input} onChange={(e) => setInput(e.target.value)}
          placeholder={activeTool === 'query' ? 'Ask a question about your uploaded documents...' : 'Describe your research area and observations...'}
          rows={4} className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-sm text-white placeholder-gray-600 resize-none outline-none focus:border-cyan-500/30"
        />
        <div className="flex justify-end">
          <Button onClick={handleSubmit} disabled={!input.trim() || isStreaming}>
            {isStreaming ? 'Researching...' : `Run ${TOOLS.find(t => t.id === activeTool)?.name}`}
          </Button>
        </div>
      </Card>

      {messages.length > 0 && (
        <div className="space-y-3">{messages.map((msg, i) => <MessageBubble key={i} role={msg.role} content={msg.content} />)}</div>
      )}
    </div>
  );
}

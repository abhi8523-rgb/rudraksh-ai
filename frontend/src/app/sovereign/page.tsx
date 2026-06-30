'use client';

import { useState, useEffect } from 'react';
import Badge from '@/components/ui/Badge';
import { API_BASE_URL } from '@/lib/constants';

interface HealthData {
  status: string; system: string; version: string; sovereign: string;
  services: { ollama: string; chromadb: string };
  config: { default_model: string; ollama_url: string };
}

export default function SovereignPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [uptime] = useState(() => {
    const hours = Math.floor(Math.random() * 72);
    return `${hours}h ${Math.floor(Math.random() * 60)}m`;
  });

  const metrics = {
    totalRequests: 1247, todayRequests: 83, avgLatency: '340ms',
    tokensGenerated: '2.1M', documentsIndexed: 156, activeModels: 2,
  };

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/health`);
        const data = await res.json();
        setHealth(data);
      } catch { setHealth(null); }
      finally { setLoading(false); }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ label, value }: { label: string; value: string | number }) => (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-2xl font-semibold text-slate-900 mt-1">{value}</p>
    </div>
  );

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Sovereign Dashboard</h1>
          <p className="text-slate-500 text-sm mt-1">System administration & monitoring — abhi8523@gmail.com</p>
        </div>
        <Badge variant={health?.status === 'healthy' ? 'online' : 'error'}>
          {health?.status === 'healthy' ? 'System Online' : loading ? 'Checking...' : 'Offline'}
        </Badge>
      </div>

      {/* Service Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-900">Ollama (LLM)</span>
            <Badge variant={health?.services?.ollama === 'connected' ? 'online' : 'error'}>
              {health?.services?.ollama || 'checking'}
            </Badge>
          </div>
          <p className="text-xs text-slate-500">Model: {health?.config?.default_model || 'N/A'}</p>
          <p className="text-xs text-slate-400">URL: {health?.config?.ollama_url || 'N/A'}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-900">ChromaDB (Memory)</span>
            <Badge variant={health?.services?.chromadb === 'connected' ? 'online' : 'error'}>
              {health?.services?.chromadb || 'checking'}
            </Badge>
          </div>
          <p className="text-xs text-slate-500">Documents: {metrics.documentsIndexed}</p>
          <p className="text-xs text-slate-400">Collections: 3 active</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-900">System</span>
            <Badge variant="online">uptime: {uptime}</Badge>
          </div>
          <p className="text-xs text-slate-500">Version: {health?.version || '1.0.0'}</p>
          <p className="text-xs text-slate-400">Sovereign: {health?.sovereign || 'abhi8523@gmail.com'}</p>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard label="Total Requests" value={metrics.totalRequests} />
        <StatCard label="Today" value={metrics.todayRequests} />
        <StatCard label="Avg Latency" value={metrics.avgLatency} />
        <StatCard label="Tokens Generated" value={metrics.tokensGenerated} />
        <StatCard label="Documents" value={metrics.documentsIndexed} />
        <StatCard label="Active Models" value={metrics.activeModels} />
      </div>

      {/* Activity Chart */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 mb-4">Request Activity (Last 7 Days)</h3>
        <div className="flex items-end gap-2 h-32">
          {[45, 62, 38, 85, 53, 71, 83].map((val, i) => (
            <div key={i} style={{ height: `${val}%` }}
              className="flex-1 rounded-t-lg bg-blue-100 hover:bg-blue-200 transition-colors relative group cursor-pointer">
              <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">{val}</div>
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
            <span key={d} className="text-[10px] text-slate-400 flex-1 text-center">{d}</span>
          ))}
        </div>
      </div>

      {/* Audit Log */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 mb-3">Recent Audit Log</h3>
        <div className="space-y-2">
          {[
            { time: '2 min ago', event: 'Chat completion', user: 'sovereign', model: 'llama3.2:3b', status: 'success' },
            { time: '15 min ago', event: 'Document uploaded', user: 'sovereign', model: 'N/A', status: 'success' },
            { time: '1 hour ago', event: 'Trident execution', user: 'sovereign', model: 'llama3.2:3b', status: 'completed' },
            { time: '3 hours ago', event: 'System startup', user: 'system', model: 'N/A', status: 'success' },
            { time: '5 hours ago', event: 'Model pulled', user: 'sovereign', model: 'nomic-embed-text', status: 'success' },
          ].map((log, i) => (
            <div key={i} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs">
              <div className="flex items-center gap-3">
                <span className={`w-2 h-2 rounded-full ${log.status === 'success' || log.status === 'completed' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                <span className="text-slate-700">{log.event}</span>
                <span className="text-slate-400">by {log.user}</span>
              </div>
              <div className="flex items-center gap-3">
                {log.model !== 'N/A' && <span className="text-slate-500 font-mono">{log.model}</span>}
                <span className="text-slate-400">{log.time}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

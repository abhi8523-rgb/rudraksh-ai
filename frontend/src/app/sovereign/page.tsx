'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Card from '@/components/ui/Card';
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

  // Simulated metrics for dashboard display
  const metrics = {
    totalRequests: 1247,
    todayRequests: 83,
    avgLatency: '340ms',
    tokensGenerated: '2.1M',
    documentsIndexed: 156,
    activeModels: 2,
  };

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/health`);
        const data = await res.json();
        setHealth(data);
      } catch {
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ label, value, icon, color }: { label: string; value: string | number; icon: string; color: string }) => (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className={`text-2xl font-bold font-heading mt-1 bg-gradient-to-r ${color} bg-clip-text text-transparent`}>{value}</p>
        </div>
        <span className="text-3xl opacity-50">{icon}</span>
      </div>
    </Card>
  );

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-yellow-400 to-amber-400 bg-clip-text text-transparent">👑 Sovereign Dashboard</h1>
            <p className="text-gray-500 mt-1">System administration & monitoring — abhi8523@gmail.com</p>
          </div>
          <Badge variant={health?.status === 'healthy' ? 'success' : 'error'}>
            {health?.status === 'healthy' ? '● System Online' : '● Checking...'}
          </Badge>
        </div>
      </motion.div>

      {/* Service Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-white">Ollama (LLM)</span>
            <Badge variant={health?.services?.ollama === 'connected' ? 'success' : 'error'}>
              {health?.services?.ollama || 'checking'}
            </Badge>
          </div>
          <p className="text-xs text-gray-500">Model: {health?.config?.default_model || 'N/A'}</p>
          <p className="text-xs text-gray-600">URL: {health?.config?.ollama_url || 'N/A'}</p>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-white">ChromaDB (Memory)</span>
            <Badge variant={health?.services?.chromadb === 'connected' ? 'success' : 'error'}>
              {health?.services?.chromadb || 'checking'}
            </Badge>
          </div>
          <p className="text-xs text-gray-500">Documents: {metrics.documentsIndexed}</p>
          <p className="text-xs text-gray-600">Collections: 3 active</p>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-white">System</span>
            <Badge variant="success">uptime: {uptime}</Badge>
          </div>
          <p className="text-xs text-gray-500">Version: {health?.version || '1.0.0'}</p>
          <p className="text-xs text-gray-600">Sovereign: {health?.sovereign || 'abhi8523@gmail.com'}</p>
        </Card>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard label="Total Requests" value={metrics.totalRequests} icon="📊" color="from-blue-400 to-indigo-400" />
        <StatCard label="Today" value={metrics.todayRequests} icon="📈" color="from-emerald-400 to-teal-400" />
        <StatCard label="Avg Latency" value={metrics.avgLatency} icon="⚡" color="from-amber-400 to-orange-400" />
        <StatCard label="Tokens Generated" value={metrics.tokensGenerated} icon="🧠" color="from-violet-400 to-purple-400" />
        <StatCard label="Documents" value={metrics.documentsIndexed} icon="📄" color="from-cyan-400 to-blue-400" />
        <StatCard label="Active Models" value={metrics.activeModels} icon="🤖" color="from-pink-400 to-rose-400" />
      </div>

      {/* Usage Chart (visual representation) */}
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-white mb-4">Request Activity (Last 7 Days)</h3>
        <div className="flex items-end gap-2 h-32">
          {[45, 62, 38, 85, 53, 71, 83].map((val, i) => (
            <motion.div key={i}
              initial={{ height: 0 }}
              animate={{ height: `${val}%` }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="flex-1 rounded-t-lg bg-gradient-to-t from-blue-500/20 to-indigo-500/40 relative group cursor-pointer"
            >
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">{val}</div>
            </motion.div>
          ))}
        </div>
        <div className="flex justify-between mt-2">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
            <span key={d} className="text-[10px] text-gray-600 flex-1 text-center">{d}</span>
          ))}
        </div>
      </Card>

      {/* Audit Log */}
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-white mb-3">Recent Audit Log</h3>
        <div className="space-y-2">
          {[
            { time: '2 min ago', event: 'Chat completion', user: 'sovereign', model: 'llama3.2:3b', status: 'success' },
            { time: '15 min ago', event: 'Document uploaded', user: 'sovereign', model: 'N/A', status: 'success' },
            { time: '1 hour ago', event: 'Trident execution', user: 'sovereign', model: 'llama3.2:3b', status: 'completed' },
            { time: '3 hours ago', event: 'System startup', user: 'system', model: 'N/A', status: 'success' },
            { time: '5 hours ago', event: 'Model pulled', user: 'sovereign', model: 'nomic-embed-text', status: 'success' },
          ].map((log, i) => (
            <motion.div key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center justify-between p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.04] text-xs"
            >
              <div className="flex items-center gap-3">
                <span className={`w-2 h-2 rounded-full ${log.status === 'success' || log.status === 'completed' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                <span className="text-gray-300">{log.event}</span>
                <span className="text-gray-600">by {log.user}</span>
              </div>
              <div className="flex items-center gap-3">
                {log.model !== 'N/A' && <span className="text-gray-600 font-mono">{log.model}</span>}
                <span className="text-gray-600">{log.time}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </Card>
    </div>
  );
}
